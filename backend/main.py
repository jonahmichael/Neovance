"""
Neovance-AI: FastAPI Real-Time Monitoring Server
WebSocket streaming and historical data endpoints for NICU monitoring dashboard
"""

import asyncio
import random
import uuid
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, String, Float, DateTime, desc
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel


# ============================================================================
# DATABASE SETUP
# ============================================================================

DATABASE_URL = "sqlite:///./realtime_data.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # Required for SQLite
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ============================================================================
# DATABASE MODEL
# ============================================================================

class RiskMonitor(Base):
    """SQLAlchemy model for risk_monitor table"""
    __tablename__ = "risk_monitor"
    
    timestamp = Column(String, primary_key=True)
    patient_id = Column(String, nullable=False)
    hr = Column(Float, nullable=False)          # Heart Rate
    spo2 = Column(Float, nullable=False)        # Oxygen Saturation
    rr = Column(Float, nullable=False)          # Respiratory Rate
    temp = Column(Float, nullable=False)        # Temperature
    map = Column(Float, nullable=False)         # Mean Arterial Pressure
    risk_score = Column(Float, nullable=False)  # Calculated Risk Score
    status = Column(String, nullable=False)     # OK / WARNING / CRITICAL
    created_at = Column(DateTime, default=datetime.utcnow)


# ============================================================================
# PYDANTIC SCHEMAS
# ============================================================================

class RiskMonitorResponse(BaseModel):
    """Response model for risk monitor data"""
    timestamp: str
    patient_id: str
    hr: float
    spo2: float
    rr: float
    temp: float
    map: float
    risk_score: float
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class ActionRequest(BaseModel):
    """Pydantic model for clinical action submission"""
    patient_id: str
    action: str
    notes: Optional[str] = None
    timestamp: Optional[str] = None


class ActionResponse(BaseModel):
    """Response model for action submission"""
    success: bool
    message: str
    action_id: Optional[str] = None


# ============================================================================
# FASTAPI APP
# ============================================================================

app = FastAPI(
    title="Neovance-AI Monitoring API",
    description="Real-time NICU patient monitoring with WebSocket streaming",
    version="1.0.0"
)

# Enable CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# GLOBAL STATE FOR SMOOTH DATA AND SEPSIS SIMULATION
# ============================================================================

# Global base values for smooth data generation
global_hr_base = 80.0
global_spo2_base = 98.0
global_rr_base = 16.0
global_temp_base = 37.0
global_map_base = 35.0

# Sepsis trigger state
global_sepsis_triggered = False
sepsis_step_counter = 0


# ============================================================================
# MOCK DATA GENERATOR WITH SMOOTH TRANSITIONS
# ============================================================================

def generate_smooth_vitals():
    """
    Generate realistic vital signs with smooth transitions.
    Uses global base values that drift slowly, creating more realistic data.
    """
    global global_hr_base, global_spo2_base, global_rr_base
    global global_temp_base, global_map_base
    global global_sepsis_triggered, sepsis_step_counter
    
    # Sepsis spike logic
    if global_sepsis_triggered and sepsis_step_counter < 5:
        # Simulate sepsis onset: HR increases, SpO2 drops, RR increases
        global_hr_base += random.uniform(8, 12)
        global_spo2_base -= random.uniform(1.5, 3)
        global_rr_base += random.uniform(3, 5)
        global_temp_base += random.uniform(0.3, 0.5)
        sepsis_step_counter += 1
        print(f"[SEPSIS] Step {sepsis_step_counter}/5 - Condition worsening")
    elif global_sepsis_triggered and sepsis_step_counter >= 5:
        # End spike, maintain critical state
        global_sepsis_triggered = False
        print("[SEPSIS] Spike complete - maintaining critical state")
    
    # Add small random jitter to current base
    hr = global_hr_base + random.uniform(-0.5, 0.5)
    spo2 = global_spo2_base + random.uniform(-0.3, 0.3)
    rr = global_rr_base + random.uniform(-0.4, 0.4)
    temp = global_temp_base + random.uniform(-0.1, 0.1)
    map_val = global_map_base + random.uniform(-0.5, 0.5)
    
    # Slowly drift back toward normal if not in sepsis
    if not global_sepsis_triggered:
        global_hr_base += (80.0 - global_hr_base) * 0.05
        global_spo2_base += (98.0 - global_spo2_base) * 0.05
        global_rr_base += (16.0 - global_rr_base) * 0.05
        global_temp_base += (37.0 - global_temp_base) * 0.05
        global_map_base += (35.0 - global_map_base) * 0.05
    
    # Clamp to realistic ranges
    hr = max(60, min(180, hr))
    spo2 = max(85, min(100, spo2))
    rr = max(10, min(80, rr))
    temp = max(35.5, min(40.0, temp))
    map_val = max(20, min(50, map_val))
    
    # Calculate risk score
    risk_score = abs(hr - 80) * 0.5 + abs(spo2 - 98) * 3 + abs(temp - 37) * 10
    
    # Determine status
    if risk_score > 20:
        status = "CRITICAL"
    elif risk_score > 10:
        status = "WARNING"
    else:
        status = "OK"
    
    return {
        "hr": round(hr, 1),
        "spo2": round(spo2, 1),
        "rr": round(rr, 1),
        "temp": round(temp, 2),
        "map": round(map_val, 1),
        "risk_score": round(risk_score, 2),
        "status": status
    }


async def insert_mock_data_continuously():
    """
    Continuously insert mock data into the database.
    Uses smooth transitions for realistic data patterns.
    """
    await asyncio.sleep(2)
    
    print("[MOCK DATA] Starting continuous data generation...")
    
    while True:
        try:
            db = SessionLocal()
            
            # Generate smooth vitals
            vitals = generate_smooth_vitals()
            
            # Create new record
            record = RiskMonitor(
                timestamp=datetime.now().isoformat(),
                patient_id="Baby_A",
                hr=vitals["hr"],
                spo2=vitals["spo2"],
                rr=vitals["rr"],
                temp=vitals["temp"],
                map=vitals["map"],
                risk_score=vitals["risk_score"],
                status=vitals["status"]
            )
            
            db.add(record)
            db.commit()
            db.refresh(record)
            
            print(f"[MOCK DATA] HR={vitals['hr']} SpO2={vitals['spo2']}% "
                  f"Risk={vitals['risk_score']} {vitals['status']}")
            
            db.close()
            
            # Wait 3 seconds before next insertion
            await asyncio.sleep(3)
            
        except Exception as e:
            print(f"[ERROR] Mock data insertion failed: {e}")
            await asyncio.sleep(5)


# ============================================================================
# STARTUP EVENT
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize database and start mock data generation on startup"""
    print("[STARTUP] Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("[STARTUP] Database tables created successfully")
    
    # Start background task for continuous mock data generation
    asyncio.create_task(insert_mock_data_continuously())
    print("[STARTUP] Mock data generator started")


# ============================================================================
# WEBSOCKET ENDPOINT - LIVE FEED
# ============================================================================

@app.websocket("/ws/live")
async def websocket_live_feed(websocket: WebSocket):
    """
    WebSocket endpoint for real-time data streaming.
    Sends the latest patient data every 1 second.
    """
    await websocket.accept()
    print("[WEBSOCKET] Client connected to live feed")
    
    try:
        while True:
            db = SessionLocal()
            
            # Query the latest record
            latest_record = db.query(RiskMonitor)\
                .order_by(desc(RiskMonitor.timestamp))\
                .first()
            
            if latest_record:
                # Convert to dict for JSON serialization
                data = {
                    "timestamp": latest_record.timestamp,
                    "patient_id": latest_record.patient_id,
                    "hr": latest_record.hr,
                    "spo2": latest_record.spo2,
                    "rr": latest_record.rr,
                    "temp": latest_record.temp,
                    "map": latest_record.map,
                    "risk_score": latest_record.risk_score,
                    "status": latest_record.status,
                    "created_at": latest_record.created_at.isoformat()
                }
                
                # Send data to client
                await websocket.send_json(data)
            
            db.close()
            
            # Wait 1 second before next update
            await asyncio.sleep(1)
            
    except WebSocketDisconnect:
        print("[WEBSOCKET] Client disconnected from live feed")
    except Exception as e:
        print(f"[WEBSOCKET ERROR] {e}")
    finally:
        try:
            await websocket.close()
        except:
            pass


# ============================================================================
# HTTP ENDPOINT - HISTORICAL DATA
# ============================================================================

@app.get("/history", response_model=List[RiskMonitorResponse])
async def get_history():
    """
    Get historical data from the last 30 minutes.
    Returns all records within the time window.
    """
    db = SessionLocal()
    
    try:
        # Calculate cutoff time (30 minutes ago)
        cutoff_time = datetime.now() - timedelta(minutes=30)
        
        # Query records from last 30 minutes
        records = db.query(RiskMonitor)\
            .filter(RiskMonitor.created_at >= cutoff_time)\
            .order_by(desc(RiskMonitor.timestamp))\
            .all()
        
        print(f"[HISTORY] Returning {len(records)} records from last 30 minutes")
        
        return records
        
    except Exception as e:
        print(f"[HISTORY ERROR] {e}")
        return []
    finally:
        db.close()


# ============================================================================
# HEALTH CHECK ENDPOINT
# ============================================================================

@app.get("/")
async def root():
    """Health check endpoint"""
    db = SessionLocal()
    
    try:
        # Get total record count
        total_records = db.query(RiskMonitor).count()
        
        # Get latest record
        latest = db.query(RiskMonitor)\
            .order_by(desc(RiskMonitor.timestamp))\
            .first()
        
        return {
            "status": "operational",
            "service": "Neovance-AI Monitoring API",
            "database": "connected",
            "total_records": total_records,
            "latest_timestamp": latest.timestamp if latest else None,
            "endpoints": {
                "websocket": "/ws/live",
                "history": "/history",
                "stats": "/stats",
                "action": "/action (POST)"
            }
        }
    finally:
        db.close()


# ============================================================================
# STATISTICS ENDPOINT
# ============================================================================

@app.get("/stats")
async def get_statistics():
    """Get current statistics about the monitoring system"""
    db = SessionLocal()
    
    try:
        # Last 30 minutes data
        cutoff_time = datetime.now() - timedelta(minutes=30)
        recent_records = db.query(RiskMonitor)\
            .filter(RiskMonitor.created_at >= cutoff_time)\
            .all()
        
        if not recent_records:
            return {"message": "No recent data available"}
        
        # Calculate statistics
        risk_scores = [r.risk_score for r in recent_records]
        statuses = [r.status for r in recent_records]
        
        return {
            "time_window": "Last 30 minutes",
            "total_records": len(recent_records),
            "risk_score": {
                "min": round(min(risk_scores), 2),
                "max": round(max(risk_scores), 2),
                "avg": round(sum(risk_scores) / len(risk_scores), 2)
            },
            "status_distribution": {
                "OK": statuses.count("OK"),
                "WARNING": statuses.count("WARNING"),
                "CRITICAL": statuses.count("CRITICAL")
            }
        }
    finally:
        db.close()


# ============================================================================
# ACTION LOGGING ENDPOINT
# ============================================================================

@app.post("/action", response_model=ActionResponse)
async def log_action(action_req: ActionRequest):
    """
    Log a clinical action taken by medical staff.
    Stores action details and returns confirmation.
    """
    try:
        # Generate unique action ID
        action_id = str(uuid.uuid4())[:8]
        
        # Use provided timestamp or current time
        timestamp = action_req.timestamp or datetime.now().isoformat()
        
        # Log the action (in production, this would save to database)
        print(f"[ACTION LOGGED] ID: {action_id}")
        print(f"  Patient: {action_req.patient_id}")
        print(f"  Action: {action_req.action}")
        print(f"  Notes: {action_req.notes or 'N/A'}")
        print(f"  Timestamp: {timestamp}")
        
        return ActionResponse(
            success=True,
            message="Action logged successfully",
            action_id=action_id
        )
        
    except Exception as e:
        print(f"[ACTION ERROR] {e}")
        return ActionResponse(
            success=False,
            message=f"Failed to log action: {str(e)}",
            action_id=None
        )


# ============================================================================
# SEPSIS TRIGGER ENDPOINT
# ============================================================================

@app.post("/trigger-sepsis")
async def trigger_sepsis():
    """
    Trigger a controlled sepsis simulation spike.
    This causes vitals to deteriorate rapidly over 15 seconds.
    """
    global global_sepsis_triggered, sepsis_step_counter
    
    global_sepsis_triggered = True
    sepsis_step_counter = 0
    
    print("[SEPSIS TRIGGER] Sepsis spike initiated - 15 second demonstration")
    
    return {
        "success": True,
        "message": "Sepsis spike initiated",
        "duration": "15 seconds (5 steps)",
        "effects": "HR increases, SpO2 decreases, RR increases"
    }


# ============================================================================
# RUN SERVER
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    print("="*70)
    print("NEOVANCE-AI: Real-Time Monitoring API Server")
    print("="*70)
    print("Starting FastAPI server with WebSocket support...")
    print("Endpoints:")
    print("  - Health Check:  http://localhost:8000/")
    print("  - WebSocket:     ws://localhost:8000/ws/live")
    print("  - History:       http://localhost:8000/history")
    print("  - Statistics:    http://localhost:8000/stats")
    print("  - Log Action:    http://localhost:8000/action (POST)")
    print("  - API Docs:      http://localhost:8000/docs")
    print("="*70)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
