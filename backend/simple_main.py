#!/usr/bin/env python3
"""
Simple FastAPI backend without database dependencies
Provides mock data for the frontend vitals dashboard
"""

import asyncio
import json
import random
import time
from datetime import datetime
from typing import Dict, List, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Neovance Simple Backend", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:3002", "http://localhost:3003"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
active_connections: List[WebSocket] = []
sepsis_triggered = False
sepsis_start_time = None

# Mock data models
class VitalData(BaseModel):
    timestamp: str
    hr: int  # Heart rate (bpm)
    spo2: int  # Oxygen saturation (%)
    rr: int  # Respiratory rate (breaths/min) 
    temp: float  # Temperature (Celsius)
    map: int  # Mean arterial pressure (mmHg)
    risk_score: float
    status: str

class MockAlert(BaseModel):
    alert_id: int
    baby_id: str
    model_risk_score: float
    alert_status: str
    timestamp: str
    doctor_action: Optional[str] = None
    action_detail: Optional[str] = None
    observation_duration: Optional[str] = None
    lab_tests: Optional[List[str]] = None
    antibiotics: Optional[List[str]] = None
    updated_at: str

# Mock vital generation
def generate_normal_vitals() -> VitalData:
    """Generate stable, normal vital signs"""
    return VitalData(
        timestamp=datetime.now().isoformat(),
        hr=135 + random.randint(-5, 5),  # 130-140 bpm
        spo2=94 + random.randint(-2, 2),  # 92-96%
        rr=45 + random.randint(-5, 5),   # 40-50 breaths/min
        temp=37.0 + random.uniform(-0.3, 0.3),  # 36.7-37.3°C
        map=42 + random.randint(-5, 5),  # 37-47 mmHg
        risk_score=0.15 + random.uniform(0, 0.1),  # Low risk
        status="OK"
    )

def generate_sepsis_vitals() -> VitalData:
    """Generate high-risk sepsis vital signs"""
    return VitalData(
        timestamp=datetime.now().isoformat(),
        hr=195 + random.randint(-5, 15),  # 190-210 bpm (severe tachycardia)
        spo2=80 + random.randint(-2, 6),  # 78-86% (severe hypoxia)
        rr=85 + random.randint(-5, 15),   # 80-100 breaths/min (severe tachypnea)
        temp=38.7 + random.uniform(0, 0.8),  # 38.7-39.5°C (high fever)
        map=25 + random.randint(-3, 5),   # 22-30 mmHg (severe hypotension)
        risk_score=0.88 + random.uniform(0, 0.1),  # Very high risk
        status="CRITICAL"
    )

@app.get("/")
async def root():
    return {
        "message": "Neovance Simple Backend",
        "status": "running",
        "sepsis_active": sepsis_triggered,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/v1/alerts/pending")
async def get_pending_alerts(role: str = "nurse"):
    """Mock alerts endpoint - returns empty or mock alert based on sepsis trigger"""
    
    if sepsis_triggered and sepsis_start_time:
        # Return mock alert if sepsis was triggered recently
        time_since_trigger = time.time() - sepsis_start_time
        if time_since_trigger < 120:  # Alert active for 2 minutes
            mock_alert = MockAlert(
                alert_id=999,
                baby_id="B001",
                model_risk_score=0.875,
                alert_status="PENDING_DOCTOR_ACTION" if role == "doctor" else "PENDING_NURSE_ACTION",
                timestamp=datetime.fromtimestamp(sepsis_start_time).isoformat(),
                updated_at=datetime.now().isoformat()
            )
            return {"alerts": [mock_alert.dict()]}
    
    return {"alerts": []}

@app.post("/trigger-sepsis")
async def trigger_sepsis():
    """Trigger sepsis simulation"""
    global sepsis_triggered, sepsis_start_time
    sepsis_triggered = True
    sepsis_start_time = time.time()
    
    print(f"🚨 SEPSIS TRIGGERED at {datetime.now().isoformat()}")
    
    return {
        "message": "Sepsis simulation triggered",
        "timestamp": datetime.now().isoformat(),
        "active_duration": "30 seconds"
    }

@app.get("/api/baby/{baby_id}")
async def get_baby_profile(baby_id: str):
    """Mock baby profile endpoint"""
    return {
        "baby_id": baby_id,
        "name": "Baby Johnson",
        "dob": "2024-12-01",
        "gestational_age": "28 weeks",
        "weight": "1.2 kg",
        "admission_date": "2024-12-01",
        "room": "NICU-A3",
        "status": "Critical" if sepsis_triggered else "Stable"
    }

@app.websocket("/ws/live")
async def websocket_vitals(websocket: WebSocket):
    """WebSocket endpoint for real-time vitals"""
    await websocket.accept()
    active_connections.append(websocket)
    
    try:
        while True:
            # Check if sepsis was triggered recently
            current_time = time.time()
            is_sepsis_active = (
                sepsis_triggered and 
                sepsis_start_time and 
                (current_time - sepsis_start_time) < 30  # 30 seconds of sepsis vitals
            )
            
            # Generate appropriate vitals
            if is_sepsis_active:
                vitals = generate_sepsis_vitals()
            else:
                vitals = generate_normal_vitals()
                
            # Send to all connected clients
            message = vitals.json()
            for connection in active_connections.copy():
                try:
                    await connection.send_text(message)
                except:
                    active_connections.remove(connection)
            
            await asyncio.sleep(2)  # Send vitals every 2 seconds
            
    except WebSocketDisconnect:
        if websocket in active_connections:
            active_connections.remove(websocket)

# Reset sepsis trigger automatically
async def sepsis_auto_reset():
    """Auto-reset sepsis trigger after 30 seconds"""
    global sepsis_triggered, sepsis_start_time
    while True:
        if sepsis_triggered and sepsis_start_time:
            if time.time() - sepsis_start_time > 30:
                sepsis_triggered = False
                sepsis_start_time = None
                print(f"🔄 SEPSIS AUTO-RESET at {datetime.now().isoformat()}")
        await asyncio.sleep(5)

@app.on_event("startup")
async def startup_event():
    """Start background tasks"""
    asyncio.create_task(sepsis_auto_reset())
    print("🚀 Simple Neovance Backend started successfully!")
    print("📊 Mock data mode - no database required")
    print("🌐 WebSocket vitals available at ws://localhost:8000/ws/live")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "simple_main:app",
        host="0.0.0.0", 
        port=8000,
        reload=True,
        log_level="info"
    )