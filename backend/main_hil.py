#!/usr/bin/env python3

"""
HIL-enabled FastAPI backend with PostgreSQL/TimescaleDB support
Integration point for Human-in-the-Loop learning system
"""

import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
import json
from datetime import datetime
from typing import List, Dict, Any

# HIL System imports
from database import get_db_session, init_database, check_database_health
from models import Baby, RealtimeVital, Alert, Outcome
from hil_endpoints import router as hil_router

# Legacy endpoints for compatibility
from main import router as legacy_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    print("[STARTUP] Initializing HIL Backend...")
    
    # Initialize database
    try:
        await init_database()
        print("[STARTUP] Database initialized")
    except Exception as e:
        print(f"[STARTUP ERROR] Database initialization failed: {e}")
    
    # Check database health
    health = await check_database_health()
    if health["database_connected"]:
        print("[STARTUP] ✓ PostgreSQL connected")
        if health["timescaledb_enabled"]:
            print("[STARTUP] ✓ TimescaleDB enabled")
        else:
            print("[STARTUP] ⚠ TimescaleDB not detected")
    else:
        print(f"[STARTUP ERROR] Database connection failed: {health.get('error')}")
    
    print("[STARTUP] HIL Backend ready for Human-in-the-Loop learning")
    
    yield
    
    print("[SHUTDOWN] HIL Backend stopped")

# FastAPI app with HIL support
app = FastAPI(
    title="Neovance AI - HIL Backend",
    description="Human-in-the-Loop NICU Monitoring System with PostgreSQL/TimescaleDB",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include HIL endpoints
app.include_router(hil_router)

# Include legacy endpoints for compatibility
app.include_router(legacy_router)

# WebSocket manager for real-time data
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"[WEBSOCKET] Client connected to HIL feed")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        print(f"[WEBSOCKET] Client disconnected")

    async def broadcast(self, data: dict):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(data))
            except:
                disconnected.append(connection)
        
        # Remove disconnected clients
        for connection in disconnected:
            try:
                self.active_connections.remove(connection)
            except ValueError:
                pass

manager = ConnectionManager()

@app.websocket("/ws/hil_live")
async def websocket_hil_feed(websocket: WebSocket, db: AsyncSession = Depends(get_db_session)):
    """WebSocket endpoint for real-time HIL data feed"""
    await manager.connect(websocket)
    
    try:
        while True:
            # Get latest vitals and recent alerts
            vitals_query = select(RealtimeVital).order_by(
                RealtimeVital.timestamp.desc()
            ).limit(10)
            
            alerts_query = select(Alert).order_by(
                Alert.timestamp.desc()
            ).limit(5)
            
            vitals_result = await db.execute(vitals_query)
            alerts_result = await db.execute(alerts_query)
            
            latest_vitals = vitals_result.scalars().all()
            recent_alerts = alerts_result.scalars().all()
            
            # Format data for frontend
            hil_data = {
                "timestamp": datetime.now().isoformat(),
                "type": "hil_update",
                "vitals": [
                    {
                        "mrn": vital.mrn,
                        "timestamp": vital.timestamp.isoformat(),
                        "hr": vital.hr,
                        "spo2": vital.spo2,
                        "rr": vital.rr,
                        "temp": vital.temp,
                        "map": vital.map,
                        "risk_score": vital.risk_score,
                        "status": vital.status
                    } for vital in latest_vitals
                ],
                "recent_alerts": [
                    {
                        "id": alert.id,
                        "timestamp": alert.timestamp.isoformat(),
                        "mrn": alert.mrn,
                        "doctor_id": alert.doctor_id,
                        "action": alert.doctor_action,
                        "risk_score": alert.risk_score
                    } for alert in recent_alerts
                ]
            }
            
            await websocket.send_text(json.dumps(hil_data))
            await asyncio.sleep(2)  # Update every 2 seconds
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/")
async def root():
    """Root endpoint with HIL system information"""
    return {
        "message": "Neovance AI - HIL Backend",
        "version": "2.0.0",
        "database": "PostgreSQL + TimescaleDB",
        "features": [
            "Human-in-the-Loop Learning",
            "Real-time Time-series Data",
            "Doctor Action Logging",
            "Outcome Tracking",
            "Supervised Learning Ready"
        ],
        "endpoints": {
            "hil_system": "/hil/",
            "doctor_actions": "/hil/doctor_action",
            "outcomes": "/hil/outcome", 
            "training_data": "/hil/training_data",
            "analytics": "/hil/analytics/doctor_performance",
            "websocket": "/ws/hil_live",
            "health": "/hil/health"
        }
    }

@app.get("/health")
async def health_check():
    """Overall system health check"""
    db_health = await check_database_health()
    
    return {
        "system_status": "operational" if db_health["database_connected"] else "error",
        "timestamp": datetime.now().isoformat(),
        "database": db_health,
        "hil_ready": db_health["database_connected"] and db_health.get("timescaledb_enabled", False)
    }

# Legacy baby endpoint with HIL integration
@app.get("/baby/{mrn}")
async def get_baby_hil(mrn: str, db: AsyncSession = Depends(get_db_session)):
    """Get baby information with latest vitals and HIL data"""
    try:
        # Get baby info
        baby_query = select(Baby).where(Baby.mrn == mrn)
        result = await db.execute(baby_query)
        baby = result.scalar_one_or_none()
        
        if not baby:
            raise HTTPException(status_code=404, detail=f"Baby {mrn} not found")
        
        # Get latest vitals
        vitals_query = select(RealtimeVital).where(
            RealtimeVital.mrn == mrn
        ).order_by(RealtimeVital.timestamp.desc()).limit(20)
        
        vitals_result = await db.execute(vitals_query)
        vitals = vitals_result.scalars().all()
        
        # Get recent doctor actions
        alerts_query = select(Alert).where(
            Alert.mrn == mrn
        ).order_by(Alert.timestamp.desc()).limit(10)
        
        alerts_result = await db.execute(alerts_query)
        alerts = alerts_result.scalars().all()
        
        return {
            "mrn": baby.mrn,
            "name": baby.name,
            "gestational_age_weeks": baby.gestational_age_weeks,
            "birth_weight": baby.birth_weight,
            "current_weight": baby.current_weight,
            "vitals": [
                {
                    "timestamp": vital.timestamp.isoformat(),
                    "hr": vital.hr,
                    "spo2": vital.spo2,
                    "rr": vital.rr,
                    "temp": vital.temp,
                    "map": vital.map,
                    "risk_score": vital.risk_score,
                    "status": vital.status
                } for vital in vitals
            ],
            "recent_actions": [
                {
                    "timestamp": alert.timestamp.isoformat(),
                    "doctor_id": alert.doctor_id,
                    "action": alert.doctor_action,
                    "detail": alert.action_detail,
                    "risk_score": alert.risk_score
                } for alert in alerts
            ],
            "hil_ready": True
        }
        
    except Exception as e:
        print(f"[ERROR] Baby data retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    
    print("🏥 Starting Neovance AI HIL Backend")
    print("Database: PostgreSQL + TimescaleDB")
    print("Features: Human-in-the-Loop Learning")
    
    uvicorn.run(
        "main_hil:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )