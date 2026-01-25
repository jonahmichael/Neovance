"""
Neovance-AI: FastAPI Real-Time Monitoring Server
WebSocket streaming and historical data endpoints for NICU monitoring dashboard
"""

import asyncio
import random
from datetime import datetime, timedelta
from typing import List

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
# MOCK DATA GENERATOR
# ============================================================================

def generate_mock_vitals():
    """Generate realistic mock vital signs for 28-week premature infant"""
    # Normal ranges for 28-week preemie
    hr = random.gauss(145, 15)      # Heart rate: 120-170 bpm
    spo2 = random.gauss(95, 2.5)    # SpO2: 90-100%
    rr = random.gauss(50, 10)       # Respiratory rate: 40-60 bpm
    temp = random.gauss(37.0, 0.5)  # Temperature: 36.5-37.5°C
    map_val = random.gauss(35, 5)   # MAP: 30-40 mmHg
    
    # Clamp values to realistic ranges
    hr = max(100, min(180, hr))
    spo2 = max(85, min(100, spo2))
    rr = max(20, min(80, rr))
    temp = max(35.5, min(38.5, temp))
    map_val = max(25, min(45, map_val))
    
    # Simple risk score calculation (for demo purposes)
    # In production, use the weighted deviation formula
    risk_score = abs(hr - 145) * 0.5 + abs(spo2 - 95) * 3 + abs(temp - 37) * 10
    
    # Determine status based on risk score
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
    Runs as a background task on app startup.
    """
    await asyncio.sleep(2)  # Wait for DB initialization
    
    print("[MOCK DATA] Starting continuous data generation...")
    
    while True:
        try:
            db = SessionLocal()
            
            # Generate mock vitals
            vitals = generate_mock_vitals()
            
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
            
            print(f"[MOCK DATA] Inserted: HR={vitals['hr']} SpO2={vitals['spo2']}% "
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
                "history": "/history"
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
    print("  - API Docs:      http://localhost:8000/docs")
    print("="*70)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
