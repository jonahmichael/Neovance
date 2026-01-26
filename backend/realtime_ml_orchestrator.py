#!/usr/bin/env python3
"""
Real-time ML Prediction Orchestrator (Pathway Integration)
Connects live data stream to ML prediction service and HIL workflow

This orchestrates the complete workflow:
1. Pathway reads live vitals → 2. Trigger thresholds → 3. Call ML API → 4. Alert Frontend
"""

import pathway as pw
import requests
import json
import pandas as pd
from typing import Dict, Any
import logging
import asyncio
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API endpoints
PREDICTION_API_URL = "http://localhost:8001/predict_risk"
HIL_LOGGING_URL = "http://localhost:8001/log_doctor_action"

# Critical thresholds for triggering ML prediction
CRITICAL_THRESHOLDS = {
    'hr_high': 180,
    'hr_low': 80,
    'spo2_low': 90,
    'temp_high': 38.5,
    'temp_low': 36.0,
    'map_low': 25,
    'rr_high': 50
}

class SepsisMLOrchestrator:
    """Orchestrates real-time sepsis prediction workflow"""
    
    def __init__(self):
        self.last_predictions = {}  # Cache to avoid duplicate alerts
        self.alert_cooldown = 300   # 5 minutes cooldown between alerts
        
    def check_critical_thresholds(self, row) -> bool:
        """Check if vital signs cross critical thresholds"""
        try:
            hr = row.get('hr', 120)
            spo2 = row.get('spo2', 97)
            temp = row.get('temp', 37.0)
            map_val = row.get('map', 40)
            rr = row.get('rr', 25)
            
            # Check each threshold
            critical_conditions = [
                hr >= CRITICAL_THRESHOLDS['hr_high'],
                hr <= CRITICAL_THRESHOLDS['hr_low'],
                spo2 <= CRITICAL_THRESHOLDS['spo2_low'],
                temp >= CRITICAL_THRESHOLDS['temp_high'],
                temp <= CRITICAL_THRESHOLDS['temp_low'],
                map_val <= CRITICAL_THRESHOLDS['map_low'],
                rr >= CRITICAL_THRESHOLDS['rr_high']
            ]
            
            return any(critical_conditions)
            
        except Exception as e:
            logger.error(f"Threshold check error: {e}")
            return False
    
    def should_trigger_prediction(self, mrn: str) -> bool:
        """Check if we should trigger ML prediction (avoid spam)"""
        current_time = datetime.now().timestamp()
        
        if mrn in self.last_predictions:
            time_since_last = current_time - self.last_predictions[mrn]
            if time_since_last < self.alert_cooldown:
                return False
        
        self.last_predictions[mrn] = current_time
        return True
    
    def format_patient_data_for_api(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Format pathway row data for ML prediction API"""
        try:
            # Extract and format data for API
            patient_data = {
                'mrn': row.get('mrn', 'UNKNOWN'),
                'timestamp': datetime.now().isoformat(),
                
                # Demographics (use defaults if not available)
                'gestational_age_at_birth_weeks': row.get('ga_weeks', 38) + (row.get('ga_days', 0) / 7.0),
                'birth_weight_kg': row.get('birth_weight', 3.0),
                'sex': row.get('sex', 'unknown'),
                'race': row.get('race', 'unknown'),
                
                # Maternal factors
                'ga_weeks': int(row.get('ga_weeks', 38)),
                'ga_days': int(row.get('ga_days', 0)),
                'maternal_temp_celsius': row.get('temp_celsius', 37.0),
                'rom_hours': row.get('rom_hours', 8.0),
                'gbs_status': row.get('gbs_status', 'negative'),
                'antibiotic_type': row.get('antibiotic_type', 'none'),
                'clinical_exam': row.get('clinical_exam', 'normal'),
                
                # Current vital signs
                'hr': float(row.get('hr', 120)),
                'spo2': float(row.get('spo2', 97)),
                'rr': float(row.get('rr', 25)),
                'temp_celsius': float(row.get('temp', 37.0)),
                'map': float(row.get('map', 40)),
                
                # Risk factors (defaults)
                'comorbidities': row.get('comorbidities', 'no'),
                'central_venous_line': row.get('central_venous_line', 'no'),
                'intubated_at_time_of_sepsis_evaluation': row.get('intubated', 'no'),
                'inotrope_at_time_of_sepsis_eval': row.get('inotropes', 'no'),
                'ecmo': row.get('ecmo', 'no'),
                'stat_abx': row.get('stat_abx', 'no'),
                'time_to_antibiotics': row.get('time_to_antibiotics', None)
            }
            
            return patient_data
            
        except Exception as e:
            logger.error(f"Data formatting error: {e}")
            return None
    
    def call_ml_prediction_api(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """Call the ML prediction service"""
        try:
            response = requests.post(
                PREDICTION_API_URL,
                json=patient_data,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                prediction = response.json()
                logger.info(f"ML Prediction: MRN {patient_data['mrn']}, Risk: {prediction.get('risk_score', 0):.3f}")
                return prediction
            else:
                logger.error(f"Prediction API error: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"API call failed: {e}")
            return None
    
    def trigger_frontend_alert(self, prediction: Dict[str, Any]):
        """Send alert to frontend (placeholder - implement via WebSocket/SSE)"""
        try:
            # In real implementation, this would send via WebSocket or Server-Sent Events
            # For now, log the alert information
            
            mrn = prediction.get('mrn', 'UNKNOWN')
            risk_score = prediction.get('risk_score', 0.0)
            alert_reason = prediction.get('alert_reason', 'Unknown reason')
            is_critical = prediction.get('is_critical_alert', False)
            
            alert_type = "🚨 CRITICAL ALERT" if is_critical else "⚠️ ALERT"
            
            logger.info(
                f"{alert_type}: MRN {mrn} | Risk: {risk_score:.1%} | {alert_reason}"
            )
            
            # Store alert for frontend polling (simple implementation)
            # In production, use WebSocket or Redis pub/sub
            with open('data/active_alerts.json', 'a') as f:
                alert_data = {
                    'timestamp': datetime.now().isoformat(),
                    'mrn': mrn,
                    'risk_score': risk_score,
                    'alert_reason': alert_reason,
                    'is_critical': is_critical,
                    'prediction': prediction
                }
                f.write(json.dumps(alert_data) + '\\n')
                
        except Exception as e:
            logger.error(f"Frontend alert failed: {e}")
    
    def process_critical_patient(self, row: Dict[str, Any]):
        """Process a patient who has crossed critical thresholds"""
        try:
            mrn = row.get('mrn', 'UNKNOWN')
            
            # Check cooldown to avoid alert spam
            if not self.should_trigger_prediction(mrn):
                logger.debug(f"Skipping prediction for {mrn} (cooldown active)")
                return
            
            # Format data for ML API
            patient_data = self.format_patient_data_for_api(row)
            if not patient_data:
                logger.error(f"Failed to format patient data for {mrn}")
                return
            
            # Call ML prediction service
            prediction = self.call_ml_prediction_api(patient_data)
            if not prediction:
                logger.error(f"Failed to get ML prediction for {mrn}")
                return
            
            # Check if prediction indicates significant risk
            risk_score = prediction.get('risk_score', 0.0)
            
            if risk_score >= 0.2:  # Only alert for moderate+ risk
                self.trigger_frontend_alert(prediction)
                logger.info(f"Alert triggered for {mrn}: Risk {risk_score:.1%}")
            else:
                logger.debug(f"Low risk for {mrn}: {risk_score:.1%}, no alert needed")
                
        except Exception as e:
            logger.error(f"Critical patient processing failed: {e}")


def create_ml_prediction_pipeline():
    """Create Pathway pipeline with ML prediction integration"""
    
    # Initialize orchestrator
    orchestrator = SepsisMLOrchestrator()
    
    # Read the live data stream
    stream = pw.io.csv.read(
        'data/stream_eos.csv',
        mode='streaming',
        schema=pw.schema_from_types({
            'timestamp': str,
            'mrn': str,
            'hr': float,
            'spo2': float,
            'rr': float,
            'temp': float,
            'map': float,
            'ga_weeks': int,
            'ga_days': int,
            'temp_celsius': float,
            'rom_hours': float,
            'gbs_status': str,
            'antibiotic_type': str,
            'clinical_exam': str
        })
    )
    
    # Transform to include trend analysis
    enhanced_stream = stream.select(
        *pw.this,
        hr_trend=pw.apply(
            lambda hr, mrn: pw.this.hr - pw.this.hr.lag(1).defaults(pw.this.hr),
            pw.this.hr, pw.this.mrn
        ),
        temp_trend=pw.apply(
            lambda temp, mrn: pw.this.temp - pw.this.temp.lag(1).defaults(pw.this.temp),
            pw.this.temp, pw.this.mrn
        )
    )
    
    # Filter for critical patients
    critical_stream = enhanced_stream.filter(
        lambda row: orchestrator.check_critical_thresholds(row._asdict())
    )
    
    # Process critical patients through ML prediction
    def ml_prediction_handler(key, row):
        """Handler for critical patients - triggers ML prediction"""
        row_dict = row._asdict()
        orchestrator.process_critical_patient(row_dict)
    
    # Subscribe to critical stream
    critical_stream.subscribe(ml_prediction_handler)
    
    # Also create a periodic summary for monitoring
    summary_stream = stream.reduce(
        count=pw.reducers.count(),
        avg_hr=pw.reducers.avg(pw.this.hr),
        avg_spo2=pw.reducers.avg(pw.this.spo2),
        avg_temp=pw.reducers.avg(pw.this.temp),
        by=pw.this.mrn
    ).select(
        *pw.this,
        monitoring_timestamp=datetime.now().isoformat()
    )
    
    return stream, critical_stream, summary_stream


def main():
    """Main execution function"""
    logger.info("🚀 Starting Real-time ML Prediction Orchestrator")
    logger.info("="*60)
    logger.info("Workflow: Live Data → Critical Threshold → ML Prediction → Alert")
    logger.info(f"Prediction API: {PREDICTION_API_URL}")
    logger.info(f"Critical Thresholds: {CRITICAL_THRESHOLDS}")
    logger.info("="*60)
    
    try:
        # Test API connection
        test_response = requests.get("http://localhost:8001/health", timeout=5)
        if test_response.status_code == 200:
            logger.info("✅ ML Prediction Service is running")
        else:
            logger.warning("⚠️ ML Prediction Service may not be running")
    except:
        logger.warning("⚠️ Cannot connect to ML Prediction Service")
        logger.info("💡 Start it with: python sepsis_prediction_service.py")
    
    # Create and run the pipeline
    try:
        stream, critical_stream, summary_stream = create_ml_prediction_pipeline()
        
        # Write outputs for monitoring
        pw.io.csv.write(critical_stream, 'data/critical_alerts.csv')
        pw.io.csv.write(summary_stream, 'data/patient_monitoring.csv')
        
        logger.info("🔄 Pipeline started - monitoring for critical patients...")
        
        # Run the pipeline
        pw.run()
        
    except KeyboardInterrupt:
        logger.info("\\n⏹️ Pipeline stopped by user")
    except Exception as e:
        logger.error(f"Pipeline error: {e}")
        raise


if __name__ == "__main__":
    main()