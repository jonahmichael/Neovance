"""
SQLAlchemy models for PostgreSQL/TimescaleDB HIL system
Core tables: alerts, outcomes, realtime_vitals, babies
"""

from sqlalchemy import Column, String, Float, Boolean, Text, DateTime, ForeignKey, Integer, BigInteger
from sqlalchemy.dialects.postgresql import JSONB, BIGINT
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Optional, Dict, Any
from database import Base

class Baby(Base):
    """Patient information table"""
    __tablename__ = 'babies'
    
    mrn = Column(String(10), primary_key=True)
    name = Column(String(100), nullable=False)
    gestational_age_weeks = Column(Integer)
    birth_weight = Column(Float)
    current_weight = Column(Float)
    maternal_gbs = Column(String(20))  # positive, negative, unknown
    maternal_fever = Column(Boolean)
    rom_hours = Column(Float)  # Rupture of membranes duration
    antibiotics_given = Column(Boolean)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    alerts = relationship("Alert", back_populates="patient")
    vitals = relationship("RealtimeVital", back_populates="patient")

class Alert(Base):
    """
    Core HIL table: AI predictions + doctor actions for supervised learning
    This is a TimescaleDB hypertable partitioned by timestamp
    """
    __tablename__ = 'alerts'
    
    id = Column(BIGINT, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    mrn = Column(String(10), ForeignKey('babies.mrn'), nullable=False, index=True)
    risk_score = Column(Float)  # AI predicted risk (0-1)
    features_json = Column(JSONB)  # CRITICAL: snapshot of all patient features
    doctor_id = Column(String(10), index=True)
    doctor_action = Column(String(50))  # 'Treat', 'Lab', 'Observe', 'Dismiss'
    action_detail = Column(Text)  # e.g., 'Ampi+Genta', '4 hours'
    
    # Relationships
    patient = relationship("Baby", back_populates="alerts")
    outcome = relationship("Outcome", back_populates="alert", uselist=False)

class Outcome(Base):
    """
    The reward signal table - links delayed outcomes back to doctor actions
    This provides the ground truth for HIL learning
    """
    __tablename__ = 'outcomes'
    
    id = Column(BIGINT, primary_key=True, autoincrement=True)
    alert_id = Column(BIGINT, ForeignKey('alerts.id'), nullable=False, index=True)
    outcome_time = Column(DateTime(timezone=True))
    sepsis_confirmed = Column(Boolean, index=True)  # THE BINARY REWARD
    lab_result = Column(Text)
    patient_status_6hr = Column(String(50))  # 'Improved', 'Worsened', 'Stable'
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    alert = relationship("Alert", back_populates="outcome")

class RealtimeVital(Base):
    """
    High-frequency vitals from Pathway ETL
    This is a TimescaleDB hypertable for time-series data
    """
    __tablename__ = 'realtime_vitals'
    
    id = Column(BIGINT, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    mrn = Column(String(10), ForeignKey('babies.mrn'), nullable=False, index=True)
    hr = Column(Float)  # Heart rate
    spo2 = Column(Float)  # SpO2 percentage  
    rr = Column(Float)  # Respiratory rate
    temp = Column(Float)  # Temperature
    map = Column(Float)  # Mean arterial pressure
    risk_score = Column(Float)  # EOS risk score
    status = Column(String(20), index=True)  # ROUTINE_CARE, ENHANCED_MONITORING, HIGH_RISK
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    patient = relationship("Baby", back_populates="vitals")

# Pydantic models for API serialization
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any

class AlertCreate(BaseModel):
    """Schema for creating new HIL alert entries"""
    timestamp: datetime
    mrn: str
    risk_score: float
    features_json: Dict[str, Any]  # Patient state snapshot
    doctor_id: str
    doctor_action: str
    action_detail: Optional[str] = None

class AlertResponse(BaseModel):
    """Schema for alert API responses"""
    id: int
    timestamp: datetime
    mrn: str
    risk_score: float
    features_json: Dict[str, Any]
    doctor_id: str
    doctor_action: str
    action_detail: Optional[str]
    
    class Config:
        from_attributes = True

class OutcomeCreate(BaseModel):
    """Schema for creating outcome entries"""
    alert_id: int
    outcome_time: datetime
    sepsis_confirmed: bool
    lab_result: Optional[str] = None
    patient_status_6hr: Optional[str] = None

class VitalCreate(BaseModel):
    """Schema for creating vital entries (from Pathway)"""
    timestamp: datetime
    mrn: str
    hr: float
    spo2: float
    rr: float
    temp: float
    map: float
    risk_score: float
    status: str

class HILDataPoint(BaseModel):
    """Complete HIL training data point"""
    alert_id: int
    timestamp: datetime
    mrn: str
    risk_score: float
    features_json: Dict[str, Any]
    doctor_action: str
    action_detail: Optional[str]
    sepsis_confirmed: Optional[bool]
    patient_status_6hr: Optional[str]
    positive_outcome: Optional[bool]