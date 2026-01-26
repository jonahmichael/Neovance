"""
FastAPI endpoints for HIL (Human-in-the-Loop) system
PostgreSQL/TimescaleDB integration for doctor action logging
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from datetime import datetime
from typing import List, Dict, Any
import json

from database import get_db_session, execute_raw_sql
from models import Alert, Outcome, Baby, RealtimeVital
from models import AlertCreate, AlertResponse, OutcomeCreate, HILDataPoint

router = APIRouter(prefix="/hil", tags=["HIL System"])

@router.post("/doctor_action", response_model=AlertResponse)
async def log_doctor_action(
    alert_data: AlertCreate,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Core HIL endpoint: Log doctor action with patient state snapshot
    This creates the training data for supervised learning
    """
    try:
        # Get current patient vitals to build features_json
        latest_vital_query = select(RealtimeVital).where(
            RealtimeVital.mrn == alert_data.mrn
        ).order_by(RealtimeVital.timestamp.desc()).limit(1)
        
        result = await db.execute(latest_vital_query)
        latest_vital = result.scalar_one_or_none()
        
        if not latest_vital:
            raise HTTPException(status_code=404, f"No vitals found for patient {alert_data.mrn}")
        
        # Get patient information
        patient_query = select(Baby).where(Baby.mrn == alert_data.mrn)
        result = await db.execute(patient_query)
        patient = result.scalar_one_or_none()
        
        if not patient:
            raise HTTPException(status_code=404, f"Patient {alert_data.mrn} not found")
        
        # Build comprehensive features_json for ML
        features_json = {
            "timestamp": alert_data.timestamp.isoformat(),
            "vitals": {
                "hr": latest_vital.hr,
                "spo2": latest_vital.spo2,
                "rr": latest_vital.rr,
                "temp": latest_vital.temp,
                "map": latest_vital.map
            },
            "derived_features": {
                "hypotension": latest_vital.map < 30,
                "tachycardia": latest_vital.hr > 120,
                "hypoxia": latest_vital.spo2 < 90,
                "fever": latest_vital.temp > 38.0,
                "hypothermia": latest_vital.temp < 36.0
            },
            "patient_context": {
                "gestational_age_weeks": patient.gestational_age_weeks,
                "birth_weight": patient.birth_weight,
                "current_weight": patient.current_weight,
                "maternal_gbs": patient.maternal_gbs,
                "maternal_fever": patient.maternal_fever,
                "rom_hours": patient.rom_hours,
                "antibiotics_given": patient.antibiotics_given
            },
            "eos_factors": {
                "risk_score": alert_data.risk_score,
                "risk_category": latest_vital.status,
                "clinical_exam": "normal"  # Would be input from UI
            },
            "ai_prediction": {
                "risk_score": alert_data.risk_score,
                "confidence": 0.85,  # Would come from ML model
                "model_version": "eos_v1.0"
            },
            "feature_version": "1.0"
        }
        
        # Create alert record
        alert = Alert(
            timestamp=alert_data.timestamp,
            mrn=alert_data.mrn,
            risk_score=alert_data.risk_score,
            features_json=features_json,
            doctor_id=alert_data.doctor_id,
            doctor_action=alert_data.doctor_action,
            action_detail=alert_data.action_detail
        )
        
        db.add(alert)
        await db.commit()
        await db.refresh(alert)
        
        print(f"[HIL LOGGED] Doctor {alert_data.doctor_id} action '{alert_data.doctor_action}' for {alert_data.mrn}")
        
        return AlertResponse(
            id=alert.id,
            timestamp=alert.timestamp,
            mrn=alert.mrn,
            risk_score=alert.risk_score,
            features_json=alert.features_json,
            doctor_id=alert.doctor_id,
            doctor_action=alert.doctor_action,
            action_detail=alert.action_detail
        )
        
    except Exception as e:
        await db.rollback()
        print(f"[ERROR] HIL logging failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to log doctor action: {str(e)}")

@router.post("/outcome", response_model=Dict[str, Any])
async def log_outcome(
    outcome_data: OutcomeCreate,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Log delayed outcome/reward signal for HIL learning
    This provides the ground truth for supervised learning
    """
    try:
        # Verify alert exists
        alert_query = select(Alert).where(Alert.id == outcome_data.alert_id)
        result = await db.execute(alert_query)
        alert = result.scalar_one_or_none()
        
        if not alert:
            raise HTTPException(status_code=404, f"Alert {outcome_data.alert_id} not found")
        
        # Create outcome record
        outcome = Outcome(
            alert_id=outcome_data.alert_id,
            outcome_time=outcome_data.outcome_time,
            sepsis_confirmed=outcome_data.sepsis_confirmed,
            lab_result=outcome_data.lab_result,
            patient_status_6hr=outcome_data.patient_status_6hr
        )
        
        db.add(outcome)
        await db.commit()
        
        print(f"[HIL OUTCOME] Alert {outcome_data.alert_id} outcome: sepsis_confirmed={outcome_data.sepsis_confirmed}")
        
        return {
            "message": "Outcome logged successfully",
            "alert_id": outcome_data.alert_id,
            "sepsis_confirmed": outcome_data.sepsis_confirmed,
            "learning_ready": True
        }
        
    except Exception as e:
        await db.rollback()
        print(f"[ERROR] Outcome logging failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to log outcome: {str(e)}")

@router.get("/training_data", response_model=List[HILDataPoint])
async def get_hil_training_data(
    limit: int = 100,
    doctor_id: str = None,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get HIL training dataset for supervised learning
    Returns alerts with their corresponding outcomes
    """
    try:
        # Use the HIL training data view
        query = """
        SELECT 
            alert_id, timestamp, mrn, risk_score, features_json,
            doctor_action, action_detail, sepsis_confirmed, 
            patient_status_6hr, positive_outcome
        FROM hil_training_data
        WHERE doctor_action IS NOT NULL
        """
        
        params = {"limit": limit}
        
        if doctor_id:
            query += " AND doctor_id = :doctor_id"
            params["doctor_id"] = doctor_id
            
        query += " ORDER BY timestamp DESC LIMIT :limit"
        
        result = await execute_raw_sql(query, params)
        rows = result.fetchall()
        
        training_data = []
        for row in rows:
            training_data.append(HILDataPoint(
                alert_id=row[0],
                timestamp=row[1],
                mrn=row[2],
                risk_score=row[3],
                features_json=row[4],
                doctor_action=row[5],
                action_detail=row[6],
                sepsis_confirmed=row[7],
                patient_status_6hr=row[8],
                positive_outcome=row[9]
            ))
        
        return training_data
        
    except Exception as e:
        print(f"[ERROR] Training data retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get training data: {str(e)}")

@router.get("/analytics/doctor_performance")
async def get_doctor_performance(
    doctor_id: str = None,
    days: int = 7,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get doctor performance analytics for HIL system
    """
    try:
        query = """
        SELECT 
            a.doctor_id,
            COUNT(*) as total_actions,
            AVG(a.risk_score) as avg_risk_score,
            SUM(CASE WHEN o.sepsis_confirmed = true THEN 1 ELSE 0 END) as true_positives,
            SUM(CASE WHEN o.sepsis_confirmed = false THEN 1 ELSE 0 END) as false_positives,
            AVG(CASE WHEN o.sepsis_confirmed = true THEN 1.0 ELSE 0.0 END) as precision
        FROM alerts a
        LEFT JOIN outcomes o ON a.id = o.alert_id
        WHERE a.timestamp >= NOW() - INTERVAL ':days days'
        """
        
        params = {"days": days}
        
        if doctor_id:
            query += " AND a.doctor_id = :doctor_id"
            params["doctor_id"] = doctor_id
            
        query += " GROUP BY a.doctor_id ORDER BY total_actions DESC"
        
        result = await execute_raw_sql(query, params)
        rows = result.fetchall()
        
        performance_data = []
        for row in rows:
            performance_data.append({
                "doctor_id": row[0],
                "total_actions": row[1],
                "avg_risk_score": float(row[2]) if row[2] else 0,
                "true_positives": row[3] or 0,
                "false_positives": row[4] or 0,
                "precision": float(row[5]) if row[5] else 0
            })
        
        return {
            "period_days": days,
            "doctor_performance": performance_data
        }
        
    except Exception as e:
        print(f"[ERROR] Analytics retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get analytics: {str(e)}")

@router.get("/health")
async def hil_health_check(db: AsyncSession = Depends(get_db_session)):
    """
    Health check for HIL system components
    """
    try:
        # Check if TimescaleDB hypertables are working
        hypertable_check = await execute_raw_sql(
            "SELECT * FROM timescaledb_information.hypertables WHERE hypertable_name IN ('alerts', 'realtime_vitals')"
        )
        hypertables = hypertable_check.fetchall()
        
        # Check recent data
        recent_alerts = await execute_raw_sql(
            "SELECT COUNT(*) FROM alerts WHERE timestamp >= NOW() - INTERVAL '1 hour'"
        )
        alert_count = recent_alerts.scalar()
        
        recent_vitals = await execute_raw_sql(
            "SELECT COUNT(*) FROM realtime_vitals WHERE timestamp >= NOW() - INTERVAL '1 hour'"
        )
        vitals_count = recent_vitals.scalar()
        
        return {
            "hil_system_status": "operational",
            "timescaledb_hypertables": len(hypertables),
            "recent_alerts": alert_count,
            "recent_vitals": vitals_count,
            "database_type": "PostgreSQL + TimescaleDB"
        }
        
    except Exception as e:
        return {
            "hil_system_status": "error",
            "error": str(e)
        }