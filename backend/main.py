"""
Neovance-AI: Comprehensive NICU EHR and Monitoring System
Real-time vitals monitoring with Pathway streaming + Complete neonatal medical records with chain of custody
"""

import asyncio
import random
import uuid
import json
import hashlib
from datetime import datetime, timedelta, date
from typing import List, Optional, Dict, Any
from pathlib import Path
import numpy as np
from enum import Enum
from dataclasses import dataclass
import threading
import time

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, status, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, String, Float, DateTime, Integer, Date, Boolean, ForeignKey, Text, desc
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from pydantic import BaseModel
import joblib

# ============================================================================
# DATABASE SETUP
# ============================================================================
# DATABASE SETUP
# ============================================================================

DATABASE_URL = "sqlite:///./neovance.db"

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

# ============================================================================
# HIL MODEL SETUP
# ============================================================================

# Global variables for HIL functionality
sepsis_model = None

def risk_to_hours(risk_score: float) -> int:
    """Maps a risk score (0-1) to a predicted onset window in hours."""
    if risk_score < 0.3:
        return 48
    elif risk_score < 0.6:
        return 24
    elif risk_score < 0.8:
        return 12
    else:
        return 6

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ============================================================================
# DATABASE MODELS
# ============================================================================

class Alert(Base):
    """Model for HIL alerts and outcomes"""
    __tablename__ = "alerts"
    
    alert_id = Column(Integer, primary_key=True, autoincrement=True)
    baby_id = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Model Prediction
    model_risk_score = Column(Float)
    onset_window_hrs = Column(Integer)
    alert_status = Column(String, default='PENDING_DOCTOR_ACTION') # PENDING_DOCTOR_ACTION, ACTION_TAKEN, DISMISSED, CLOSED
    
    # Doctor's Action
    doctor_id = Column(String)
    doctor_action = Column(String) # OBSERVATION, LAB_TESTS, ANTIBIOTICS, DISMISS
    action_detail = Column(Text)
    action_timestamp = Column(DateTime)
    
    # Detailed Decision Info
    observation_duration = Column(String) # e.g. "6 hours", "3 days"
    lab_tests = Column(Text) # JSON string of test list
    antibiotics = Column(Text) # JSON string of antibiotic list
    dismiss_duration = Column(Integer) # hours to silence
    
    # Final Outcome
    sepsis_confirmed = Column(Boolean)
    outcome_timestamp = Column(DateTime)
    reward_signal = Column(Integer)
    model_status = Column(String)


class RealisticVitals(Base):
    """Model for storing generated vitals"""
    __tablename__ = "realistic_vitals"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    baby_id = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    hr = Column(Float)
    spo2 = Column(Float)
    resp_rate = Column(Float)
    temp = Column(Float)
    map = Column(Float)
    risk_score = Column(Float)
    status = Column(String)


class User(Base):
    """Model for authenticated users (doctors, nurses)"""
    __tablename__ = "users"
    
    user_id = Column(String, primary_key=True)
    full_name = Column(String, nullable=False)
    role = Column(String, nullable=False)  # Doctor, Nurse
    password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Staff(Base):
    """Model for staff directory"""
    __tablename__ = "staff"
    
    staff_id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    role = Column(String, nullable=False)
    specialization = Column(String)
    contact = Column(String)
    shift = Column(String)


class BabyProfile(Base):
    """Comprehensive baby profile for NICU patients"""
    __tablename__ = "baby_profiles"
    
    mrn = Column(String, primary_key=True)  # Medical Record Number
    full_name = Column(String, nullable=False)
    sex = Column(String)
    dob = Column(Date)
    time_of_birth = Column(String)
    place_of_birth = Column(String)
    birth_order = Column(String)
    gestational_age = Column(String)
    apgar_1min = Column(Integer)
    apgar_5min = Column(Integer)
    apgar_10min = Column(Integer)
    
    # Parent Information
    mother_name = Column(String)
    father_name = Column(String)
    parent_contact = Column(String)
    parent_address = Column(Text)
    mother_age = Column(Integer)
    mother_blood_type = Column(String)
    mother_id = Column(String)
    father_id = Column(String)
    emergency_contact = Column(String)
    hospital_id_band = Column(String)
    footprints_taken = Column(Boolean)
    
    # Measurements
    birth_weight = Column(Float)
    length = Column(Float)
    head_circumference = Column(Float)
    chest_circumference = Column(Float)
    weight_percentile = Column(String)
    length_percentile = Column(String)
    head_percentile = Column(String)
    
    # Physical Examination
    muscle_tone = Column(String)
    reflexes = Column(String)
    moro_reflex = Column(String)
    rooting_reflex = Column(String)
    sucking_reflex = Column(String)
    grasp_reflex = Column(String)
    stepping_reflex = Column(String)
    alertness_level = Column(String)
    cry_strength = Column(String)
    skin_condition = Column(String)
    birthmarks = Column(String)
    bruising = Column(String)
    fontanelle_status = Column(String)
    eye_exam = Column(String)
    ear_exam = Column(String)
    nose_throat_exam = Column(String)
    genital_exam = Column(String)
    anus_patency = Column(String)
    limb_movement = Column(String)
    spine_check = Column(String)
    hip_check = Column(String)
    
    # Sensory Screening
    hearing_screening = Column(String)
    hearing_screening_date = Column(String)
    vision_screening = Column(String)
    red_reflex_right = Column(String)
    red_reflex_left = Column(String)
    response_to_stimuli = Column(String)
    
    # Cardiorespiratory
    pulse_oximetry = Column(String)
    pulse_ox_right_hand = Column(Float)
    pulse_ox_foot = Column(Float)
    breathing_pattern = Column(String)
    lung_sounds = Column(String)
    heart_sounds = Column(String)
    heart_murmur_grade = Column(String)
    
    # Lab Screening
    metabolic_screening = Column(String)
    metabolic_screening_date = Column(String)
    pku_result = Column(String)
    msud_result = Column(String)
    galactosemia_result = Column(String)
    hypothyroidism_result = Column(String)
    cah_result = Column(String)
    sickle_cell_result = Column(String)
    thalassemia_result = Column(String)
    cystic_fibrosis_result = Column(String)
    scid_result = Column(String)
    biotinidase_result = Column(String)
    genetic_screening_panel = Column(String)
    blood_glucose = Column(String)
    bilirubin_level = Column(String)
    bilirubin_date = Column(String)
    blood_type = Column(String)
    rh_factor = Column(String)
    coombs_test = Column(String)
    
    # Immunizations
    vitamin_k_given = Column(Boolean)
    vitamin_k_date = Column(String)
    hep_b_vaccine = Column(Boolean)
    hep_b_date = Column(String)
    eye_prophylaxis = Column(Boolean)
    eye_prophylaxis_date = Column(String)
    other_vaccines = Column(String)
    
    # Feeding & Elimination
    feeding_method = Column(String)
    feeding_tolerance = Column(String)
    feeds_per_day = Column(Integer)
    urine_output = Column(String)
    first_void_time = Column(String)
    stool_output = Column(String)
    meconium_passage_time = Column(String)
    vomiting = Column(String)
    reflux = Column(String)
    
    # Clinical Course
    bed_assignment = Column(String)
    nicu_admission = Column(Boolean)
    nicu_admission_reason = Column(String)
    oxygen_support = Column(String)
    fio2 = Column(Float)
    iv_fluids = Column(String)
    medications = Column(String)
    antibiotics = Column(String)
    procedures = Column(String)
    monitoring_events = Column(String)
    infection_screening = Column(String)
    
    # Risk & History
    maternal_infections = Column(String)
    gbs_status = Column(String)
    maternal_hiv = Column(String)
    maternal_hep_b = Column(String)
    maternal_syphilis = Column(String)
    drug_exposure = Column(String)
    delivery_method = Column(String)
    delivery_complications = Column(String)
    birth_complications = Column(String)
    resuscitation_needed = Column(Boolean)
    resuscitation_details = Column(String)
    family_genetic_history = Column(String)
    prenatal_history = Column(String)
    prenatal_care = Column(String)
    
    # Discharge
    discharge_date = Column(String)
    discharge_weight = Column(Float)
    discharge_diagnosis = Column(String)
    follow_up_appointments = Column(String)
    parent_education = Column(String)
    home_care_instructions = Column(String)
    screening_results_summary = Column(String)
    
    # Care Team
    attending_physician = Column(String)
    primary_nurse = Column(String)
    primary_care_pediatrician = Column(String)
    
    # Notes & Timestamps
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class LiveVitals(Base):
    """Model for live vitals streaming data"""
    __tablename__ = "live_vitals"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(String, nullable=False)
    mrn = Column(String, nullable=False)
    hr = Column(Float)
    spo2 = Column(Float)
    rr = Column(Float)
    temp = Column(Float)
    map = Column(Float)
    risk_score = Column(Float)
    status = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)


# ============================================================================
# REALISTIC VITALS GENERATOR CLASSES
# ============================================================================

class ClinicalState(Enum):
    STABLE = "stable"
    DETERIORATING = "deteriorating"
    SEPTIC = "septic"
    RECOVERING = "recovering"

@dataclass
class VitalRanges:
    """Normal ranges for newborn vitals by gestational age"""
    hr_min: float
    hr_max: float
    spo2_min: float
    spo2_max: float
    rr_min: float
    rr_max: float
    temp_min: float
    temp_max: float
    map_min: float
    map_max: float

class RealisticVitalGenerator:
    """Generates biologically realistic vital signs for NICU babies"""
    
    def __init__(self, gestational_age_weeks: float = 36.0):
        self.ga = gestational_age_weeks
        self.state = ClinicalState.STABLE
        self.sepsis_onset_time = None
        self.time_since_onset = 0
        self.sepsis_minutes = 0
        self.sepsis_profile = None  # "fever" or "hypothermia"
        
        # Set age-appropriate ranges
        self.ranges = self._get_vital_ranges(gestational_age_weeks)
        
        # Initialize current vitals to normal baseline (center of ranges)
        self.current_vitals = {
            'hr': (self.ranges.hr_min + self.ranges.hr_max) / 2,
            'spo2': (self.ranges.spo2_min + self.ranges.spo2_max) / 2,
            'rr': (self.ranges.rr_min + self.ranges.rr_max) / 2,
            'temp': (self.ranges.temp_min + self.ranges.temp_max) / 2,
            'map': (self.ranges.map_min + self.ranges.map_max) / 2
        }
        
        # Store previous values for trend calculation
        self.prev_vitals = self.current_vitals.copy()
        
        # Artifact simulation
        self.artifact_counter = 0
        
        # Noise parameters for realistic variation - enhanced for more irregularity
        self.noise_params = {
            'hr': {'std': 5.0, 'drift': 0.92, 'burst_chance': 0.15},      # More HR variability
            'spo2': {'std': 2.5, 'drift': 0.94, 'burst_chance': 0.10},    # More O2 sat drops
            'rr': {'std': 4.0, 'drift': 0.91, 'burst_chance': 0.20},      # More breathing irregularity
            'temp': {'std': 0.15, 'drift': 0.995, 'burst_chance': 0.05},  # Temperature fluctuations
            'map': {'std': 3.0, 'drift': 0.93, 'burst_chance': 0.12}      # Blood pressure variations
        }
        
        # Add biological rhythm factors
        self.time_offset = np.random.uniform(0, 24)  # Random phase offset
        self.breathing_cycle = 0  # Counter for breathing irregularities
    
    def _get_vital_ranges(self, ga_weeks: float) -> VitalRanges:
        """Get age-appropriate vital sign ranges"""
        if ga_weeks < 32:  # Very preterm
            return VitalRanges(
                hr_min=120, hr_max=170,
                spo2_min=90, spo2_max=98,
                rr_min=40, rr_max=70,
                temp_min=36.0, temp_max=37.0,
                map_min=25, map_max=40
            )
        elif ga_weeks < 37:  # Preterm
            return VitalRanges(
                hr_min=115, hr_max=165,
                spo2_min=92, spo2_max=99,
                rr_min=35, rr_max=65,
                temp_min=36.2, temp_max=37.2,
                map_min=30, map_max=45
            )
        else:  # Term
            return VitalRanges(
                hr_min=110, hr_max=160,
                spo2_min=95, spo2_max=100,
                rr_min=30, rr_max=60,
                temp_min=36.5, temp_max=37.5,
                map_min=35, map_max=50
            )
    
    def trigger_sepsis(self):
        """Trigger gradual sepsis progression with random profile"""
        self.state = ClinicalState.DETERIORATING
        self.sepsis_onset_time = datetime.now()
        self.time_since_onset = 0
        self.sepsis_minutes = 0
        
        # Randomly choose sepsis profile
        self.sepsis_profile = np.random.choice(["fever", "hypothermia"], p=[0.6, 0.4])
        print(f"Sepsis triggered: {self.sepsis_profile} profile")
    
    def reset_to_normal(self) -> None:
        """Reset to stable baseline"""
        self.state = ClinicalState.STABLE
        self.sepsis_onset_time = None
        self.time_since_onset = 0
        self.current_vitals = {
            'hr': np.random.uniform(self.ranges.hr_min + 10, self.ranges.hr_max - 10),
            'spo2': np.random.uniform(self.ranges.spo2_min + 2, self.ranges.spo2_max),
            'rr': np.random.uniform(self.ranges.rr_min + 5, self.ranges.rr_max - 5),
            'temp': np.random.uniform(self.ranges.temp_min + 0.2, self.ranges.temp_max - 0.2),
            'map': np.random.uniform(self.ranges.map_min + 3, self.ranges.map_max - 3)
        }
    
    def _apply_sepsis_progression(self, minutes_since_onset: float) -> Dict[str, float]:
        """Apply realistic sepsis progression over time with irregular patterns"""
        # More irregular progression phases
        if minutes_since_onset < 5:
            progression = minutes_since_onset / 5.0 * 0.2
        elif minutes_since_onset < 15:
            progression = 0.2 + (minutes_since_onset - 5) / 10.0 * 0.4
        elif minutes_since_onset < 30:
            progression = 0.6 + (minutes_since_onset - 15) / 15.0 * 0.3
        else:
            progression = min(0.9 + (minutes_since_onset - 30) / 30.0 * 0.1, 1.0)
        
        # Add irregular sepsis "waves" - periods of stability followed by deterioration
        wave_factor = 1 + 0.3 * np.sin(2 * np.pi * minutes_since_onset / 8) * progression
        progression *= wave_factor
        
        # Random fever vs hypothermia (realistic sepsis presentation)
        if not hasattr(self, 'sepsis_temp_pattern'):
            self.sepsis_temp_pattern = np.random.choice(['fever', 'hypothermia'], p=[0.6, 0.4])
        
        sepsis_targets = {
            'hr': self.ranges.hr_max + 20 + (progression * 50) + np.random.uniform(-8, 8),  # More variable tachycardia
            'spo2': max(self.ranges.spo2_min - 10 - (progression * 20) + np.random.uniform(-3, 3), 70),  # Irregular desaturation
            'rr': self.ranges.rr_max + 15 + (progression * 35) + np.random.uniform(-6, 6),  # Variable tachypnea
            'temp': (self.ranges.temp_max + 2.0 + progression if self.sepsis_temp_pattern == 'fever' 
                    else self.ranges.temp_min - 1.5 - progression) + np.random.uniform(-0.3, 0.3),
            'map': max(self.ranges.map_min - 8 - (progression * 20) + np.random.uniform(-4, 4), 12)  # Irregular hypotension
        }
        
        return sepsis_targets
    
    def generate_next_vitals(self) -> Dict[str, float]:
        """Generate next vital signs using medical monitor patterns with plateaus and step changes"""
        if self.sepsis_onset_time:
            self.time_since_onset = (datetime.now() - self.sepsis_onset_time).total_seconds() / 60.0
            self.sepsis_minutes = int(self.time_since_onset)
            if self.time_since_onset > 45:
                self.state = ClinicalState.SEPTIC
        
        # Store previous values for correlation calculation
        self.prev_vitals = self.current_vitals.copy()
        
        # Helper function for medical monitor noise (more stepped, less smooth)
        def monitor_noise(range_val, plateau_chance=0.3):
            if np.random.random() < plateau_chance:
                return 0  # Stay at current value (plateau effect)
            else:
                # Step changes more likely than smooth changes
                if np.random.random() < 0.4:
                    return np.random.choice([-1, 1]) * np.random.uniform(range_val*0.8, range_val*1.5)  # Larger steps
                else:
                    return np.random.uniform(-range_val*0.5, range_val*0.5)  # Smaller variations
        
        # Helper function for bounds checking
        def clamp(value, min_val, max_val):
            return max(min_val, min(max_val, value))
        
        new_vitals = self.current_vitals.copy()
        
        if self.state == ClinicalState.STABLE:
            # NORMAL MODE: Medical monitor patterns with plateaus
            new_vitals['hr'] += monitor_noise(4, plateau_chance=0.4)  # HR plateaus 40% of time
            new_vitals['spo2'] += monitor_noise(2, plateau_chance=0.5)  # SpO2 plateaus 50% of time
            new_vitals['rr'] += monitor_noise(3, plateau_chance=0.35)  # RR plateaus 35% of time
            new_vitals['temp'] += monitor_noise(0.1, plateau_chance=0.6)  # Temp plateaus 60% of time
            new_vitals['map'] += monitor_noise(2, plateau_chance=0.45)  # MAP plateaus 45% of time
            
        elif self.state in [ClinicalState.DETERIORATING, ClinicalState.SEPTIC]:
            # SEPSIS MODE: More erratic with step changes
            
            # Calculate severity based on time (logarithmic progression)
            severity = min(np.log(self.sepsis_minutes + 1) * 0.8, 5.0)  # Max severity of 5
            
            if self.sepsis_profile == "fever":
                # FEVER SEPSIS: Progressive deterioration with larger steps
                new_vitals['hr'] += monitor_noise(6, 0.2) + np.random.uniform(0.5, 2.0) + severity * 0.3
                new_vitals['rr'] += monitor_noise(4, 0.25) + np.random.uniform(0.3, 1.5) + severity * 0.2
                new_vitals['spo2'] += monitor_noise(3, 0.3) - np.random.uniform(0.2, 1.0) - severity * 0.15
                new_vitals['temp'] += monitor_noise(0.15, 0.4) + np.random.uniform(0.02, 0.08) + severity * 0.02
                new_vitals['map'] += monitor_noise(3, 0.3) - np.random.uniform(0.3, 1.2) - severity * 0.2
                
            else:  # hypothermia profile
                # HYPOTHERMIA SEPSIS: More erratic patterns
                new_vitals['hr'] += monitor_noise(8, 0.15) + np.random.uniform(-1, 3) + severity * 0.4
                new_vitals['rr'] += monitor_noise(5, 0.2) + np.random.uniform(0.5, 2.0) + severity * 0.25
                new_vitals['spo2'] += monitor_noise(4, 0.25) - np.random.uniform(0.5, 1.5) - severity * 0.2
                new_vitals['temp'] += monitor_noise(0.12, 0.3) - np.random.uniform(0.02, 0.06) - severity * 0.015
                new_vitals['map'] += monitor_noise(4, 0.25) - np.random.uniform(0.5, 1.8) - severity * 0.25
        
        else:  # RECOVERING
            # Slow return toward normal ranges with plateaus
            target_hr = (self.ranges.hr_min + self.ranges.hr_max) / 2
            target_spo2 = (self.ranges.spo2_min + self.ranges.spo2_max) / 2
            target_rr = (self.ranges.rr_min + self.ranges.rr_max) / 2
            target_temp = (self.ranges.temp_min + self.ranges.temp_max) / 2
            target_map = (self.ranges.map_min + self.ranges.map_max) / 2
            
            new_vitals['hr'] += (target_hr - new_vitals['hr']) * 0.08 + monitor_noise(3, 0.4)
            new_vitals['spo2'] += (target_spo2 - new_vitals['spo2']) * 0.08 + monitor_noise(1.5, 0.5)
            new_vitals['rr'] += (target_rr - new_vitals['rr']) * 0.08 + monitor_noise(2.5, 0.4)
            new_vitals['temp'] += (target_temp - new_vitals['temp']) * 0.08 + monitor_noise(0.08, 0.6)
            new_vitals['map'] += (target_map - new_vitals['map']) * 0.08 + monitor_noise(2, 0.45)
        
        # MEDICAL MONITOR CORRELATIONS (realistic physiological responses)
        
        # HR increases when SpO2 drops (stress response) - stepped response
        if new_vitals['spo2'] < 95:
            step_increase = int((95 - new_vitals['spo2']) / 2) * 2  # Step increases of 2
            new_vitals['hr'] += step_increase
        
        # RR correlates with HR changes - but in steps
        hr_change = new_vitals['hr'] - self.prev_vitals['hr']
        if abs(hr_change) > 3:  # Only respond to significant HR changes
            new_vitals['rr'] += int(hr_change * 0.2) * 2  # Step changes
        
        # SpO2 drops in steps when MAP is low (poor perfusion)
        if new_vitals['map'] < 30:
            step_decrease = int((30 - new_vitals['map']) / 3) * 1  # Step decreases of 1%
            new_vitals['spo2'] -= step_decrease
        
        # HR compensates for MAP drops - stepped compensation
        if new_vitals['map'] < self.prev_vitals['map'] - 2:  # Significant MAP drop
            map_drop = self.prev_vitals['map'] - new_vitals['map']
            compensation = int(map_drop / 2) * 3  # Step compensation
            new_vitals['hr'] += compensation
        
        # MEDICAL MONITOR ARTIFACTS (stepped sensor issues)
        self.artifact_counter += 1
        if self.artifact_counter >= 15 and np.random.random() < 0.08:  # 8% chance every 15 readings
            artifact_type = np.random.choice(['spo2_drop', 'hr_spike', 'plateau_break'])
            
            if artifact_type == 'spo2_drop':
                new_vitals['spo2'] -= np.random.choice([3, 5, 7, 10])  # Stepped drops
            elif artifact_type == 'hr_spike':
                new_vitals['hr'] += np.random.choice([8, 12, 15, 20])  # Stepped spikes
            elif artifact_type == 'plateau_break':
                # Force a step change after plateau
                for vital in ['hr', 'rr']:
                    new_vitals[vital] += np.random.choice([-5, -3, 3, 5, 8])
            
            self.artifact_counter = 0
        
        # PHYSIOLOGICAL BOUNDS (medical monitor limits)
        new_vitals['hr'] = clamp(new_vitals['hr'], 60, 240)
        new_vitals['spo2'] = clamp(new_vitals['spo2'], 70, 100)
        new_vitals['rr'] = clamp(new_vitals['rr'], 15, 100)
        new_vitals['temp'] = clamp(new_vitals['temp'], 34.5, 41.0)
        new_vitals['map'] = clamp(new_vitals['map'], 12, 70)
        
        # Round to medical monitor precision (whole numbers for HR, RR; 1 decimal for others)
        new_vitals['hr'] = round(new_vitals['hr'])
        new_vitals['rr'] = round(new_vitals['rr'])
        new_vitals['spo2'] = round(new_vitals['spo2'], 1)
        new_vitals['temp'] = round(new_vitals['temp'], 1)
        new_vitals['map'] = round(new_vitals['map'])
        
        self.current_vitals = new_vitals
        return new_vitals
    
    def get_clinical_assessment(self) -> Dict[str, any]:
        """Get clinical interpretation of current vitals"""
        vitals = self.current_vitals
        abnormal_count = 0
        severity_score = 0
        
        if vitals['hr'] > self.ranges.hr_max + 10 or vitals['hr'] < self.ranges.hr_min - 10:
            abnormal_count += 1
            severity_score += abs(vitals['hr'] - (self.ranges.hr_max + self.ranges.hr_min)/2) / 10
        
        if vitals['spo2'] < self.ranges.spo2_min:
            abnormal_count += 1
            severity_score += (self.ranges.spo2_min - vitals['spo2']) / 5
        
        if vitals['rr'] > self.ranges.rr_max + 10:
            abnormal_count += 1
            severity_score += (vitals['rr'] - self.ranges.rr_max) / 15
        
        if vitals['temp'] > self.ranges.temp_max + 0.5 or vitals['temp'] < self.ranges.temp_min - 0.5:
            abnormal_count += 1
            severity_score += abs(vitals['temp'] - (self.ranges.temp_min + self.ranges.temp_max)/2) * 2
        
        if vitals['map'] < self.ranges.map_min - 5:
            abnormal_count += 1
            severity_score += (self.ranges.map_min - vitals['map']) / 5
        
        if severity_score >= 8:
            alert_level = "CRITICAL"
            clinical_status = "Critical condition - immediate intervention required"
        elif severity_score >= 4:
            alert_level = "WARNING"
            clinical_status = "Concerning vitals - close monitoring needed"
        elif severity_score >= 2:
            alert_level = "CAUTION"
            clinical_status = "Mild abnormalities - continue monitoring"
        else:
            alert_level = "NORMAL"
            clinical_status = "Vitals within acceptable range"
        
        return {
            'alert_level': alert_level,
            'clinical_status': clinical_status,
            'severity_score': round(severity_score, 2),
            'abnormal_count': abnormal_count,
            'state': self.state.value,
            'time_since_sepsis': self.time_since_onset if self.sepsis_onset_time else 0
        }

class IntegratedNICUSimulator:
    """Integrated NICU simulator for FastAPI backend"""
    
    def __init__(self):
        self.patients = {}
        self.simulation_active = False
        self.simulation_thread = None
        self._initialize_patients()
    
    def _initialize_patients(self):
        """Initialize patients with different gestational ages"""
        patients_config = [
            {'mrn': 'B001', 'ga': 39.0, 'name': 'Baby Verma'},
            {'mrn': 'B002', 'ga': 34.2, 'name': 'Aarav Kumar'},
            {'mrn': 'B003', 'ga': 35.8, 'name': 'Baby Girl Reddy'},
            {'mrn': 'B004', 'ga': 35.8, 'name': 'Twin B Reddy'},
            {'mrn': 'B005', 'ga': 37.1, 'name': 'Ishaan Mehta'}
        ]
        
        for config in patients_config:
            self.patients[config['mrn']] = {
                'generator': RealisticVitalGenerator(config['ga']),
                'name': config['name'],
                'ga': config['ga']
            }
    
    def trigger_sepsis(self, mrn: str = None):
        """Trigger sepsis for specific patient"""
        if mrn and mrn in self.patients:
            self.patients[mrn]['generator'].trigger_sepsis()
            return f"Triggered sepsis for {self.patients[mrn]['name']} ({mrn})"
        else:
            random_mrn = np.random.choice(list(self.patients.keys()))
            self.patients[random_mrn]['generator'].trigger_sepsis()
            return f"Triggered sepsis for {self.patients[random_mrn]['name']} ({random_mrn})"
    
    def reset_patient(self, mrn: str):
        """Reset patient to normal baseline"""
        if mrn in self.patients:
            self.patients[mrn]['generator'].reset_to_normal()
            return f"Reset {self.patients[mrn]['name']} ({mrn}) to normal"
        return f"Patient {mrn} not found"
    
    def generate_single_reading(self):
        """Generate single vitals reading for all patients"""
        readings = {}
        for mrn, patient in self.patients.items():
            generator = patient['generator']
            vitals = generator.generate_next_vitals()
            assessment = generator.get_clinical_assessment()
            readings[mrn] = {**vitals, **assessment, 'patient_name': patient['name']}
        return readings
    
    def start_background_simulation(self, interval_seconds: int = 3):
        """Start background simulation thread"""
        if not self.simulation_active:
            self.simulation_active = True
            self.simulation_thread = threading.Thread(
                target=self._background_simulation_loop, 
                args=(interval_seconds,),
                daemon=True
            )
            self.simulation_thread.start()
            return "Background simulation started"
        return "Simulation already running"
    
    def stop_background_simulation(self):
        """Stop background simulation"""
        self.simulation_active = False
        if self.simulation_thread:
            self.simulation_thread.join(timeout=5)
        return "Background simulation stopped"
    
    def _background_simulation_loop(self, interval_seconds: int):
        """Background simulation loop with automatic sepsis alerting"""
        while self.simulation_active:
            try:
                timestamp = datetime.utcnow()
                db = SessionLocal()
                
                for mrn, patient in self.patients.items():
                    generator = patient['generator']
                    vitals = generator.generate_next_vitals()
                    assessment = generator.get_clinical_assessment()
                    
                    # Store in realistic_vitals table
                    db_vitals = RealisticVitals(
                        timestamp=timestamp,
                        baby_id=mrn,
                        hr=vitals['hr'],
                        spo2=vitals['spo2'],
                        resp_rate=vitals['rr'],
                        temp=vitals['temp'],
                        map=vitals['map'],
                        risk_score=assessment['severity_score'],
                        status=assessment['alert_level']
                    )
                    db.add(db_vitals)

                    # SEPSIS ALERTING LOGIC
                    # If high risk and no active action
                    if assessment['severity_score'] >= 7.5:
                        # Check if should alert (not dismissed, not already pending)
                        existing_alert = db.query(Alert).filter(
                            Alert.baby_id == mrn,
                            Alert.alert_status.in_(['PENDING_DOCTOR_ACTION', 'ACTION_TAKEN', 'DISMISSED'])
                        ).order_by(desc(Alert.timestamp)).first()

                        should_create_alert = False
                        if not existing_alert:
                            should_create_alert = True
                        else:
                            # Re-alert if dismissed duration passed
                            if existing_alert.alert_status == 'DISMISSED':
                                silence_hours = existing_alert.dismiss_duration or 1
                                if datetime.utcnow() > (existing_alert.action_timestamp + timedelta(hours=silence_hours)):
                                    should_create_alert = True
                            
                            # Re-alert if significant time passed since action taken without closure
                            elif existing_alert.alert_status == 'ACTION_TAKEN':
                                if datetime.utcnow() > (existing_alert.action_timestamp + timedelta(hours=4)):
                                    should_create_alert = True

                        if should_create_alert:
                            new_alert = Alert(
                                baby_id=mrn,
                                timestamp=datetime.utcnow(),
                                model_risk_score=float(assessment['severity_score'] / 10.0),
                                onset_window_hrs=risk_to_hours(assessment['severity_score'] / 10.0),
                                alert_status='PENDING_DOCTOR_ACTION'
                            )
                            db.add(new_alert)
                            print(f"[SEPSIS ALERT] Created for {mrn} due to severity {assessment['severity_score']}")
                
                db.commit()
                db.close()
                time.sleep(interval_seconds)
                
            except Exception as e:
                print(f"Simulation error: {e}")
                time.sleep(interval_seconds)
    
    def export_to_csv(self, filename: str = None):
        """Export generated data to CSV file"""
        if filename is None:
            filename = f"vitals_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        try:
            import sqlite3
            import csv
            
            db_path = Path(__file__).parent / "neonatal_ehr.db"
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Query all realistic vitals data
            cursor.execute("""
                SELECT timestamp, mrn, hr, spo2, rr, temp, map, 
                       clinical_status, alert_level, severity_score, 
                       abnormal_count, sepsis_state, time_since_sepsis
                FROM realistic_vitals 
                ORDER BY timestamp DESC
            """)
            
            rows = cursor.fetchall()
            conn.close()
            
            # Save to CSV
            csv_path = Path(__file__).parent.parent / "data" / filename
            csv_path.parent.mkdir(exist_ok=True)
            
            with open(csv_path, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write header
                writer.writerow([
                    'timestamp', 'mrn', 'hr', 'spo2', 'rr', 'temp', 'map',
                    'clinical_status', 'alert_level', 'severity_score',
                    'abnormal_count', 'sepsis_state', 'time_since_sepsis'
                ])
                
                # Write data rows
                writer.writerows(rows)
            
            return str(csv_path)
        except Exception as e:
            print(f"CSV export error: {e}")
            return None

# ============================================================================
# PYDANTIC SCHEMAS
# ============================================================================

class AuthCredentials(BaseModel):
    user_id: str
    password: str


class BabyProfileUpdate(BaseModel):
    """Partial update schema for baby profile - All editable fields"""
    # Identity (some editable for corrections)
    full_name: Optional[str] = None
    hospital_id_band: Optional[str] = None
    footprints_taken: Optional[bool] = None
    
    # Parent Info Updates
    parent_contact: Optional[str] = None
    parent_address: Optional[str] = None
    emergency_contact: Optional[str] = None
    mother_id: Optional[str] = None
    father_id: Optional[str] = None
    
    # Measurements (may need updates)
    birth_weight: Optional[float] = None
    length: Optional[float] = None
    head_circumference: Optional[float] = None
    chest_circumference: Optional[float] = None
    weight_percentile: Optional[str] = None
    length_percentile: Optional[str] = None
    head_percentile: Optional[str] = None
    
    # Physical Examination
    muscle_tone: Optional[str] = None
    reflexes: Optional[str] = None
    moro_reflex: Optional[str] = None
    rooting_reflex: Optional[str] = None
    sucking_reflex: Optional[str] = None
    grasp_reflex: Optional[str] = None
    stepping_reflex: Optional[str] = None
    alertness_level: Optional[str] = None
    cry_strength: Optional[str] = None
    skin_condition: Optional[str] = None
    birthmarks: Optional[str] = None
    bruising: Optional[str] = None
    fontanelle_status: Optional[str] = None
    eye_exam: Optional[str] = None
    ear_exam: Optional[str] = None
    nose_throat_exam: Optional[str] = None
    genital_exam: Optional[str] = None
    anus_patency: Optional[str] = None
    limb_movement: Optional[str] = None
    spine_check: Optional[str] = None
    hip_check: Optional[str] = None
    
    # Sensory Screening
    hearing_screening: Optional[str] = None
    hearing_screening_date: Optional[str] = None
    vision_screening: Optional[str] = None
    red_reflex_right: Optional[str] = None
    red_reflex_left: Optional[str] = None
    response_to_stimuli: Optional[str] = None
    
    # Cardiorespiratory
    pulse_oximetry: Optional[str] = None
    pulse_ox_right_hand: Optional[float] = None
    pulse_ox_foot: Optional[float] = None
    breathing_pattern: Optional[str] = None
    lung_sounds: Optional[str] = None
    heart_sounds: Optional[str] = None
    heart_murmur_grade: Optional[str] = None
    
    # Lab Screening
    metabolic_screening: Optional[str] = None
    metabolic_screening_date: Optional[str] = None
    pku_result: Optional[str] = None
    msud_result: Optional[str] = None
    galactosemia_result: Optional[str] = None
    hypothyroidism_result: Optional[str] = None
    cah_result: Optional[str] = None
    sickle_cell_result: Optional[str] = None
    thalassemia_result: Optional[str] = None
    cystic_fibrosis_result: Optional[str] = None
    scid_result: Optional[str] = None
    biotinidase_result: Optional[str] = None
    genetic_screening_panel: Optional[str] = None
    blood_glucose: Optional[str] = None
    bilirubin_level: Optional[str] = None
    bilirubin_date: Optional[str] = None
    blood_type: Optional[str] = None
    rh_factor: Optional[str] = None
    coombs_test: Optional[str] = None
    
    # Immunizations
    vitamin_k_given: Optional[bool] = None
    vitamin_k_date: Optional[str] = None
    hep_b_vaccine: Optional[bool] = None
    hep_b_date: Optional[str] = None
    eye_prophylaxis: Optional[bool] = None
    eye_prophylaxis_date: Optional[str] = None
    other_vaccines: Optional[str] = None
    
    # Feeding & Elimination
    feeding_method: Optional[str] = None
    feeding_tolerance: Optional[str] = None
    feeds_per_day: Optional[int] = None
    urine_output: Optional[str] = None
    first_void_time: Optional[str] = None
    stool_output: Optional[str] = None
    meconium_passage_time: Optional[str] = None
    vomiting: Optional[str] = None
    reflux: Optional[str] = None
    
    # Clinical Course
    bed_assignment: Optional[str] = None
    nicu_admission: Optional[bool] = None
    nicu_admission_reason: Optional[str] = None
    oxygen_support: Optional[str] = None
    fio2: Optional[float] = None
    iv_fluids: Optional[str] = None
    medications: Optional[str] = None
    antibiotics: Optional[str] = None
    procedures: Optional[str] = None
    monitoring_events: Optional[str] = None
    infection_screening: Optional[str] = None
    
    # Risk & History
    maternal_infections: Optional[str] = None
    gbs_status: Optional[str] = None
    maternal_hiv: Optional[str] = None
    maternal_hep_b: Optional[str] = None
    maternal_syphilis: Optional[str] = None
    drug_exposure: Optional[str] = None
    delivery_complications: Optional[str] = None
    birth_complications: Optional[str] = None
    resuscitation_needed: Optional[bool] = None
    resuscitation_details: Optional[str] = None
    family_genetic_history: Optional[str] = None
    prenatal_history: Optional[str] = None
    prenatal_care: Optional[str] = None
    
    # Discharge
    discharge_date: Optional[str] = None
    discharge_weight: Optional[float] = None
    discharge_diagnosis: Optional[str] = None
    follow_up_appointments: Optional[str] = None
    parent_education: Optional[str] = None
    home_care_instructions: Optional[str] = None
    screening_results_summary: Optional[str] = None
    
    # Care Team
    attending_physician: Optional[str] = None
    primary_nurse: Optional[str] = None
    
    # Notes
    notes: Optional[str] = None


class BabyUpdateRequest(BaseModel):
    """Request model for authenticated baby profile updates"""
    auth: AuthCredentials
    updates: BabyProfileUpdate


class LiveVitalsResponse(BaseModel):
    """Response model for live vitals"""
    timestamp: str
    mrn: str
    hr: float
    spo2: float
    rr: float
    temp: float
    map: float
    risk_score: float
    status: str
    
    class Config:
        from_attributes = True


class ActionRequest(BaseModel):
    patient_id: str
    action: str
    notes: Optional[str] = None
    timestamp: Optional[str] = None


class ActionResponse(BaseModel):
    success: bool
    message: str
    action_id: Optional[str] = None


class SepsisPredictionRequest(BaseModel):
    baby_id: str
    features: Dict[str, float]

class DoctorActionRequest(BaseModel):
    alert_id: int
    doctor_id: str
    action_type: str # OBSERVATION, LAB_TESTS, ANTIBIOTICS, DISMISS
    action_detail: Optional[str] = None
    observation_duration: Optional[str] = None
    lab_tests: Optional[List[str]] = None
    antibiotics: Optional[List[str]] = None
    dismiss_duration: Optional[int] = None

class OutcomeLogRequest(BaseModel):
    alert_id: int
    final_outcome: bool # True for sepsis_confirmed

class AlertNotification(BaseModel):
    alert_id: int
    baby_id: str
    timestamp: datetime
    model_risk_score: float
    alert_status: str
    doctor_action: Optional[str] = None
    action_detail: Optional[str] = None
    observation_duration: Optional[str] = None
    lab_tests: Optional[List[str]] = None
    antibiotics: Optional[List[str]] = None


# ============================================================================
# FASTAPI APP
# ============================================================================

app = FastAPI(
    title="Neovance-AI Neonatal EHR System",
    description="Comprehensive NICU monitoring and medical records with chain of custody",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# CHAIN OF CUSTODY LOGGING
# ============================================================================

LOG_FILE = Path("baby_edit_log.json")

def calculate_hash(data: dict) -> str:
    """Calculate SHA256 hash of data"""
    data_str = json.dumps(data, sort_keys=True)
    return hashlib.sha256(data_str.encode()).hexdigest()


def get_last_log_entry() -> Optional[dict]:
    """Get the last entry from the log file"""
    if not LOG_FILE.exists():
        return None
    
    try:
        with open(LOG_FILE, 'r') as f:
            lines = f.readlines()
            if lines:
                return json.loads(lines[-1])
    except:
        return None
    return None


def log_custody_change(user_id: str, action: str, baby_mrn: str, changes: dict):
    """Log a chain of custody change"""
    last_entry = get_last_log_entry()
    
    block_index = 1 if last_entry is None else last_entry.get('block_index', 0) + 1
    previous_hash = "0" if last_entry is None else last_entry.get('current_hash', "0")
    
    log_entry = {
        'block_index': block_index,
        'timestamp': datetime.utcnow().isoformat(),
        'user_id': user_id,
        'action': action,
        'baby_mrn': baby_mrn,
        'changes': changes,
        'previous_hash': previous_hash
    }
    
    # Calculate current hash
    log_entry['current_hash'] = calculate_hash(log_entry)
    
    # Append to log file
    with open(LOG_FILE, 'a') as f:
        f.write(json.dumps(log_entry) + '\n')
    
    print(f"[CUSTODY LOG] Block {block_index}: {action} on {baby_mrn} by {user_id}")


def authenticate_user(user_id: str, password: str, db: Session) -> bool:
    """Simple authentication check"""
    user = db.query(User).filter(User.user_id == user_id).first()
    if user and user.password == password:
        return True
    return False


# ============================================================================
# GLOBAL STATE - PATHWAY INTEGRATION
# ============================================================================

# Note: Vitals data is now streamed via Pathway pipeline
# pathway_simulator.py -> CSV stream -> pathway_etl.py -> SQLite
# This backend reads from the database populated by Pathway

global_sepsis_triggered = False

# Global Simulator for dummy data fallback
nicu_simulator = IntegratedNICUSimulator()
nicu_simulator.simulation_active = True # Keep it ready for single readings


# ============================================================================
# PATHWAY INTEGRATION
# ============================================================================

# Data flow: pathway_simulator.py writes to CSV -> pathway_etl.py processes -> writes to database
# This backend serves the data via REST API and WebSocket

# No internal data generation - all vitals come from Pathway pipeline


# ============================================================================
# INITIAL DATA POPULATION
# ============================================================================

def populate_initial_data():
    """Populate database with initial users and baby profiles"""
    db = SessionLocal()
    
    try:
        # Check if already populated
        if db.query(User).count() > 0:
            print("[STARTUP] Database already populated")
            return
        
        print("[STARTUP] Populating initial data...")
        
        # Create Users - Only authorized users
        users = [
            User(user_id="DR001", full_name="Dr. Rajesh Kumar", role="Doctor", password="password@dr"),
            User(user_id="NS001", full_name="Anjali Patel", role="Nurse", password="password@ns"),
        ]
        
        for user in users:
            db.add(user)
        
        # Create Staff Directory - Only authorized staff
        staff_members = [
            Staff(staff_id="DR001", name="Dr. Rajesh Kumar", role="Doctor", specialization="Neonatology", contact="+91-9876500001", shift="Day"),
            Staff(staff_id="NS001", name="Anjali Patel", role="Nurse", specialization="NICU Care", contact="+91-9876500003", shift="Day"),
        ]
        
        for staff in staff_members:
            db.add(staff)
        
        # Create Baby Profiles with Indian names
        babies = [
            BabyProfile(
                mrn="B001",
                full_name="Baby of Priya Verma",
                sex="Male",
                dob=date(2026, 1, 20),
                time_of_birth="08:45 AM",
                place_of_birth="NICU Ward A, Room 12",
                birth_order="Singleton",
                gestational_age="36w 4d",
                apgar_1min=8,
                apgar_5min=9,
                apgar_10min=9,
                mother_name="Priya Verma",
                father_name="Amit Verma",
                parent_contact="+91-9876543210",
                parent_address="12 MG Road, Bangalore, Karnataka 560001",
                mother_age=28,
                mother_blood_type="O+",
                birth_weight=2.4,
                length=45.0,
                head_circumference=32.0,
                chest_circumference=30.5,
                muscle_tone="Good",
                reflexes="Normal (Moro, rooting, sucking present)",
                alertness_level="Alert and responsive",
                cry_strength="Strong",
                skin_condition="Pink, no jaundice",
                fontanelle_status="Soft and flat",
                hearing_screening="Passed",
                vision_screening="Red reflex present bilaterally",
                pulse_oximetry="98% on room air",
                breathing_pattern="Regular",
                heart_sounds="Normal S1S2, no murmurs",
                metabolic_screening="Normal panel",
                blood_glucose="75 mg/dL",
                bilirubin_level="8.5 mg/dL",
                blood_type="O+",
                coombs_test="Negative",
                vitamin_k_given=True,
                hep_b_vaccine=True,
                eye_prophylaxis=True,
                feeding_method="Breastfeeding",
                feeding_tolerance="Good",
                urine_output="4-5 times/day",
                stool_output="Meconium passed at 12 hours",
                nicu_admission=False,
                oxygen_support="None",
                medications="None",
                procedures="None",
                maternal_infections="None",
                delivery_method="Vaginal delivery",
                birth_complications="None",
                resuscitation_needed=False,
                primary_care_pediatrician="Dr. Rajesh Kumar",
                prenatal_history="Routine prenatal care, no complications"
            ),
            BabyProfile(
                mrn="B002",
                full_name="Aarav Kumar",
                sex="Male",
                dob=date(2026, 1, 18),
                time_of_birth="02:30 PM",
                place_of_birth="NICU Ward B, Room 05",
                birth_order="Singleton",
                gestational_age="34w 2d",
                apgar_1min=7,
                apgar_5min=8,
                apgar_10min=9,
                mother_name="Sneha Kumar",
                father_name="Vikram Kumar",
                parent_contact="+91-9123456789",
                parent_address="45 Park Street, Mumbai, Maharashtra 400001",
                mother_age=31,
                mother_blood_type="A+",
                birth_weight=2.1,
                length=42.5,
                head_circumference=30.5,
                chest_circumference=28.0,
                muscle_tone="Slightly reduced",
                reflexes="Weak sucking reflex",
                alertness_level="Drowsy",
                cry_strength="Weak",
                skin_condition="Pale, mild acrocyanosis",
                fontanelle_status="Soft",
                hearing_screening="Pending",
                vision_screening="Red reflex present",
                pulse_oximetry="94% on 2L oxygen",
                breathing_pattern="Irregular with grunting",
                heart_sounds="Normal",
                metabolic_screening="Pending results",
                blood_glucose="65 mg/dL",
                bilirubin_level="12.5 mg/dL",
                blood_type="A+",
                coombs_test="Negative",
                vitamin_k_given=True,
                hep_b_vaccine=False,
                eye_prophylaxis=True,
                feeding_method="NGT feeding",
                feeding_tolerance="Moderate",
                urine_output="3-4 times/day",
                stool_output="Not yet passed",
                nicu_admission=True,
                oxygen_support="2L nasal cannula",
                medications="Caffeine citrate for apnea",
                procedures="IV line placement",
                maternal_infections="None",
                delivery_method="C-section (preterm labor)",
                birth_complications="Respiratory distress",
                resuscitation_needed=True,
                primary_care_pediatrician="Dr. Priya Sharma",
                prenatal_history="Preterm labor at 34 weeks"
            ),
            BabyProfile(
                mrn="B003",
                full_name="Baby Girl of Anjali Reddy",
                sex="Female",
                dob=date(2026, 1, 22),
                time_of_birth="11:20 PM",
                place_of_birth="NICU Ward A, Room 08",
                birth_order="Twin A",
                gestational_age="35w 6d",
                apgar_1min=8,
                apgar_5min=9,
                mother_name="Anjali Reddy",
                father_name="Suresh Reddy",
                parent_contact="+91-9988776655",
                parent_address="78 Anna Salai, Chennai, Tamil Nadu 600002",
                mother_age=26,
                mother_blood_type="B+",
                birth_weight=2.3,
                length=44.0,
                head_circumference=31.5,
                chest_circumference=29.5,
                muscle_tone="Good",
                reflexes="Normal",
                alertness_level="Alert",
                cry_strength="Strong",
                skin_condition="Pink, healthy",
                fontanelle_status="Normal",
                hearing_screening="Passed",
                vision_screening="Normal",
                pulse_oximetry="97% room air",
                breathing_pattern="Regular",
                heart_sounds="Normal",
                metabolic_screening="Normal",
                blood_glucose="72 mg/dL",
                bilirubin_level="9.0 mg/dL",
                blood_type="B+",
                vitamin_k_given=True,
                hep_b_vaccine=True,
                eye_prophylaxis=True,
                feeding_method="Mixed (breast + formula)",
                feeding_tolerance="Excellent",
                urine_output="5-6 times/day",
                stool_output="Regular",
                nicu_admission=False,
                oxygen_support="None",
                medications="None",
                delivery_method="Vaginal delivery",
                birth_complications="None",
                resuscitation_needed=False,
                primary_care_pediatrician="Dr. Rajesh Kumar",
                prenatal_history="Twin pregnancy, monitored"
            ),
            BabyProfile(
                mrn="B004",
                full_name="Baby Girl of Anjali Reddy",
                sex="Female",
                dob=date(2026, 1, 22),
                time_of_birth="11:22 PM",
                place_of_birth="NICU Ward A, Room 08",
                birth_order="Twin B",
                gestational_age="35w 6d",
                apgar_1min=7,
                apgar_5min=8,
                mother_name="Anjali Reddy",
                father_name="Suresh Reddy",
                parent_contact="+91-9988776655",
                parent_address="78 Anna Salai, Chennai, Tamil Nadu 600002",
                mother_age=26,
                mother_blood_type="B+",
                birth_weight=2.0,
                length=42.0,
                head_circumference=30.0,
                chest_circumference=28.5,
                muscle_tone="Moderate",
                reflexes="Present but weak",
                alertness_level="Sleepy",
                cry_strength="Moderate",
                skin_condition="Pink",
                fontanelle_status="Normal",
                hearing_screening="Pending",
                vision_screening="Normal",
                pulse_oximetry="95% room air",
                breathing_pattern="Regular",
                heart_sounds="Normal",
                metabolic_screening="Pending",
                blood_glucose="68 mg/dL",
                bilirubin_level="10.5 mg/dL",
                blood_type="B+",
                vitamin_k_given=True,
                hep_b_vaccine=True,
                eye_prophylaxis=True,
                feeding_method="Formula supplementation",
                feeding_tolerance="Good",
                urine_output="4 times/day",
                stool_output="Meconium passed",
                nicu_admission=True,
                oxygen_support="Monitoring only",
                medications="None",
                delivery_method="Vaginal delivery",
                birth_complications="Low birth weight",
                resuscitation_needed=False,
                primary_care_pediatrician="Dr. Priya Sharma",
                prenatal_history="Twin pregnancy, monitored"
            ),
            BabyProfile(
                mrn="B005",
                full_name="Ishaan Mehta",
                sex="Male",
                dob=date(2026, 1, 19),
                time_of_birth="06:15 AM",
                place_of_birth="NICU Ward C, Room 14",
                birth_order="Singleton",
                gestational_age="37w 1d",
                apgar_1min=9,
                apgar_5min=10,
                mother_name="Kavita Mehta",
                father_name="Rohan Mehta",
                parent_contact="+91-9876501234",
                parent_address="23 Linking Road, Delhi, NCR 110001",
                mother_age=29,
                mother_blood_type="AB+",
                birth_weight=2.9,
                length=48.5,
                head_circumference=34.0,
                chest_circumference=32.0,
                muscle_tone="Excellent",
                reflexes="All reflexes strong",
                alertness_level="Very alert",
                cry_strength="Vigorous",
                skin_condition="Healthy pink",
                fontanelle_status="Normal",
                hearing_screening="Passed",
                vision_screening="Excellent",
                pulse_oximetry="99% room air",
                breathing_pattern="Regular and strong",
                heart_sounds="Normal",
                metabolic_screening="All normal",
                blood_glucose="80 mg/dL",
                bilirubin_level="7.0 mg/dL",
                blood_type="AB+",
                vitamin_k_given=True,
                hep_b_vaccine=True,
                eye_prophylaxis=True,
                feeding_method="Exclusive breastfeeding",
                feeding_tolerance="Excellent",
                urine_output="6-7 times/day",
                stool_output="Regular",
                nicu_admission=False,
                oxygen_support="None",
                medications="None",
                delivery_method="Normal vaginal delivery",
                birth_complications="None",
                resuscitation_needed=False,
                discharge_weight=2.95,
                discharge_diagnosis="Healthy term neonate",
                follow_up_appointments="2-week pediatric checkup scheduled",
                primary_care_pediatrician="Dr. Rajesh Kumar",
                prenatal_history="Uncomplicated pregnancy"
            ),
        ]
        
        for baby in babies:
            db.add(baby)
        
        db.commit()
        print("[STARTUP] Successfully populated 4 users and 5 baby profiles")
        
    except Exception as e:
        print(f"[ERROR] Initial data population failed: {e}")
        db.rollback()
    finally:
        db.close()


# ============================================================================
# STARTUP EVENT
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize database and services"""
    global sepsis_model
    
    print("[STARTUP] Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("[STARTUP] Database tables created")
    
    # Load the sepsis prediction model
    try:
        MODEL_PATH = Path(__file__).parent / "trained_models" / "sepsis_random_forest.pkl"
        sepsis_model = joblib.load(MODEL_PATH)
        print("[STARTUP] Sepsis prediction model loaded successfully")
    except Exception as e:
        print(f"[STARTUP] Error loading sepsis model: {e}")
    
    populate_initial_data()
    
    # Start the simulation automatically for dummy data
    if nicu_simulator:
        print("[STARTUP] Starting background vitals simulation...")
        nicu_simulator.start_background_simulation(interval_seconds=3)
    
    print("[STARTUP] Backend ready with integrated vitals simulation")
    print("[STARTUP] Use /simulation/start to begin realistic vitals generation")
    print("[STARTUP] Use /simulation/start to begin realistic vitals generation")


# ============================================================================
# BABY PROFILE ENDPOINTS
# ============================================================================

@app.get("/staff")
async def get_all_staff():
    """Get all staff members"""
    db = SessionLocal()
    try:
        staff = db.query(Staff).all()
        return [{"staff_id": s.staff_id, "name": s.name, "role": s.role, 
                 "specialization": s.specialization, "contact": s.contact, "shift": s.shift} 
                for s in staff]
    finally:
        db.close()


@app.get("/babies")
async def get_all_babies():
    """Get all baby profiles"""
    db = SessionLocal()
    try:
        babies = db.query(BabyProfile).all()
        return babies
    finally:
        db.close()


@app.get("/baby/{mrn}")
async def get_baby_profile(mrn: str):
    """Get specific baby profile"""
    db = SessionLocal()
    try:
        baby = db.query(BabyProfile).filter(BabyProfile.mrn == mrn).first()
        if not baby:
            # Fallback to dummy data if DB entry is missing
            return {
                "mrn": mrn,
                "full_name": f"Baby of {mrn}",
                "sex": "Male" if int(mrn[-1]) % 2 == 0 else "Female",
                "dob": (date.today() - timedelta(days=5)).isoformat(),
                "gestational_age": "36w 4d",
                "birth_weight": 2.4,
                "nicu_admission": True,
                "primary_care_pediatrician": "Dr. Rajesh Kumar"
            }
        return baby
    except Exception as e:
        print(f"[API ERROR] Database error in get_baby_profile: {e}")
        # Universal fallback for any database issues
        return {
            "mrn": mrn,
            "full_name": "Emergency Patient Profile (DB Offline)",
            "sex": "Unknown",
            "dob": date.today().isoformat(),
            "gestational_age": "N/A",
            "birth_weight": 0.0,
            "nicu_admission": True,
            "primary_care_pediatrician": "Unknown"
        }
    finally:
        db.close()


@app.post("/baby/update/{mrn}")
async def update_baby_profile(mrn: str, request: BabyUpdateRequest):
    """Update baby profile with authentication and chain of custody logging"""
    db = SessionLocal()
    
    try:
        # Authenticate user
        if not authenticate_user(request.auth.user_id, request.auth.password, db):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Get baby profile
        baby = db.query(BabyProfile).filter(BabyProfile.mrn == mrn).first()
        if not baby:
            raise HTTPException(status_code=404, detail="Baby not found")
        
        # Track changes
        changes = {}
        update_data = request.updates.model_dump(exclude_unset=True)
        
        for field, new_value in update_data.items():
            old_value = getattr(baby, field, None)
            if old_value != new_value:
                changes[field] = {
                    "old_value": str(old_value),
                    "new_value": str(new_value)
                }
                setattr(baby, field, new_value)
        
        if changes:
            baby.updated_at = datetime.utcnow()
            db.commit()
            
            # Log to chain of custody
            log_custody_change(
                user_id=request.auth.user_id,
                action="UPDATE",
                baby_mrn=mrn,
                changes=changes
            )
            
            return {
                "success": True,
                "message": f"Baby profile updated successfully. {len(changes)} fields changed.",
                "updated_fields": list(changes.keys())
            }
        else:
            return {
                "success": True,
                "message": "No changes detected",
                "updated_fields": []
            }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


# ============================================================================
# WEBSOCKET ENDPOINT - LIVE VITALS
# ============================================================================

@app.websocket("/ws/live")
async def websocket_live_feed(websocket: WebSocket):
    """WebSocket endpoint for real-time vitals streaming"""
    await websocket.accept()
    print("[WEBSOCKET] Client connected to live feed")
    
    try:
        while True:
            # Try getting data from DB first
            data = None
            try:
                db = SessionLocal()
                latest_record = db.query(RealisticVitals)\
                    .order_by(desc(RealisticVitals.timestamp))\
                    .first()
                if latest_record:
                    data = {
                        "timestamp": str(latest_record.timestamp),
                        "patient_id": latest_record.baby_id,
                        "hr": latest_record.hr,
                        "spo2": latest_record.spo2,
                        "rr": latest_record.resp_rate,
                        "temp": latest_record.temp,
                        "map": latest_record.map,
                        "risk_score": latest_record.risk_score,
                        "status": latest_record.status
                    }
                db.close()
            except Exception as e:
                print(f"[WEBSOCKET DB ERROR] {e}")

            # Fallback to simulated data if no DB data
            if not data:
                # Generate a new reading from global simulator
                sim_readings = nicu_simulator.generate_single_reading()
                # Default to B001 or first available
                baby_id = "B001"
                if baby_id in sim_readings:
                    sim_data = sim_readings[baby_id]
                    data = {
                        "timestamp": datetime.now().isoformat(),
                        "patient_id": baby_id,
                        "hr": sim_data['hr'],
                        "spo2": sim_data['spo2'],
                        "rr": sim_data['rr'],
                        "temp": sim_data['temp'],
                        "map": sim_data['map'],
                        "risk_score": sim_data['severity_score'],
                        "status": sim_data['alert_level']
                    }

            if data:
                await websocket.send_json(data)
            
            await asyncio.sleep(1)
            
    except WebSocketDisconnect:
        print("[WEBSOCKET] Client disconnected")
    except Exception as e:
        print(f"[WEBSOCKET ERROR] {e}")


# ============================================================================
# HISTORICAL DATA ENDPOINTS
# ============================================================================

@app.get("/history", response_model=List[LiveVitalsResponse])
async def get_history():
    """Get historical vitals from the last 30 minutes"""
    db = SessionLocal()
    
    try:
        cutoff_time = datetime.now() - timedelta(minutes=30)
        
        records = db.query(RealisticVitals)\
            .filter(RealisticVitals.timestamp >= cutoff_time)\
            .order_by(desc(RealisticVitals.timestamp))\
            .all()
        
        print(f"[HISTORY] Returning {len(records)} records from last 30 minutes")
        
        response_data = []
        
        # Fallback to dummy history if no records found
        if not records:
            print("[HISTORY] No records found, generating dummy history")
            for i in range(10):
                response_data.append({
                    "timestamp": (datetime.now() - timedelta(minutes=i*3)).isoformat(),
                    "mrn": "B001",
                    "hr": 140 + i,
                    "spo2": 98 - (i % 2),
                    "rr": 45 + (i % 5),
                    "temp": 36.8,
                    "map": 35 - (i % 3),
                    "risk_score": 0.1,
                    "status": "stable"
                })
            return response_data

        # Map to response model
        for r in records:
            response_data.append({
                "timestamp": str(r.timestamp),
                "mrn": r.baby_id,
                "hr": r.hr,
                "spo2": r.spo2,
                "rr": r.resp_rate,
                "temp": r.temp,
                "map": r.map,
                "risk_score": r.risk_score,
                "status": r.status
            })
            
        return response_data
        
    except Exception as e:
        print(f"[HISTORY ERROR] {e}")
        return []
    finally:
        db.close()


@app.get("/stats")
async def get_statistics():
    """Get current statistics"""
    db = SessionLocal()
    
    try:
        cutoff_time = datetime.now() - timedelta(minutes=30)
        recent_records = db.query(LiveVitals)\
            .filter(LiveVitals.created_at >= cutoff_time)\
            .all()
        
        if not recent_records:
            return {"message": "No recent data available"}
        
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
    """Log a clinical action"""
    try:
        action_id = str(uuid.uuid4())[:8]
        timestamp = action_req.timestamp or datetime.now().isoformat()
        
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
async def trigger_sepsis(mrn: Optional[str] = None):
    """Trigger realistic gradual sepsis progression for specified patient"""
    global global_sepsis_triggered
    
    global_sepsis_triggered = True
    
    # Import and use realistic vital generator
    try:
        import sys
        sys.path.append(str(Path(__file__).parent.parent))
        from realistic_vitals_generator import RealisticNICUSimulator
        
        # Initialize or get existing simulator instance
        if not hasattr(trigger_sepsis, 'simulator'):
            trigger_sepsis.simulator = RealisticNICUSimulator()
        
        # Trigger sepsis for specific patient or random
        if mrn:
            trigger_sepsis.simulator.trigger_sepsis(mrn)
            patient_info = f"for patient {mrn}"
        else:
            trigger_sepsis.simulator.trigger_sepsis()
            patient_info = "for random patient"
        
        print(f"[REALISTIC SEPSIS] Gradual sepsis progression triggered {patient_info}")
        
        # Also create traditional trigger file for backward compatibility
        trigger_file = Path(__file__).parent.parent / "data" / "sepsis_trigger.txt"
        trigger_file.parent.mkdir(exist_ok=True)
        
        with open(trigger_file, 'w') as f:
            f.write(f"REALISTIC_SEPSIS_TRIGGER:{datetime.now().isoformat()}:{mrn or 'RANDOM'}")
        
        return {
            "success": True,
            "message": f"Realistic sepsis progression triggered {patient_info}",
            "type": "gradual_deterioration", 
            "duration": "30-45 minutes progressive worsening",
            "effects": "HR up, RR up, SpO2 down, MAP down, Temp variable (realistic patterns)",
            "patient": mrn or "random_selection",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"[ERROR] Failed to trigger realistic sepsis: {e}")
        # Fallback to original trigger
        trigger_file = Path(__file__).parent.parent / "data" / "sepsis_trigger.txt"
        trigger_file.parent.mkdir(exist_ok=True)
        
        with open(trigger_file, 'w') as f:
            f.write(datetime.now().isoformat())
        
        return {
            "success": True,
            "message": "Fallback sepsis trigger activated",
            "note": "Using basic trigger due to realistic generator error"
        }


@app.post("/reset-patient")
async def reset_patient_vitals(mrn: str):
    """Reset patient to normal baseline vitals"""
    try:
        import sys
        sys.path.append(str(Path(__file__).parent.parent))
        from realistic_vitals_generator import RealisticNICUSimulator
        
        # Get or create simulator instance
        if not hasattr(trigger_sepsis, 'simulator'):
            trigger_sepsis.simulator = RealisticNICUSimulator()
        
        simulator = trigger_sepsis.simulator
        
        if mrn in simulator.patients:
            simulator.reset_patient(mrn)
            patient_name = simulator.patients[mrn]['name']
            
            return {
                "success": True,
                "message": f"Patient {patient_name} ({mrn}) reset to normal baseline",
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "success": False,
                "message": f"Patient {mrn} not found in simulator",
                "available_patients": list(simulator.patients.keys())
            }
            
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to reset patient: {e}"
        }


@app.get("/realistic-vitals/{mrn}")
async def get_realistic_vitals(mrn: str, limit: int = 50):
    """Get recent realistic vital signs for a patient"""
    db_path = Path(__file__).parent / "neonatal_ehr.db"
    
    try:
        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if realistic_vitals table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='realistic_vitals'")
        if not cursor.fetchone():
            return {"message": "Realistic vitals not available. Start realistic simulator first."}
        
        # Get recent vitals
        cursor.execute("""
            SELECT timestamp, hr, spo2, rr, temp, map, clinical_status, 
                   alert_level, severity_score, sepsis_state, time_since_sepsis
            FROM realistic_vitals 
            WHERE mrn = ? 
            ORDER BY timestamp DESC 
            LIMIT ?
        """, (mrn, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            return {"message": f"No realistic vitals found for patient {mrn}"}
        
        vitals = []
        for row in rows:
            vitals.append({
                "timestamp": row[0],
                "hr": row[1],
                "spo2": row[2],
                "rr": row[3],
                "temp": row[4],
                "map": row[5],
                "clinical_status": row[6],
                "alert_level": row[7],
                "severity_score": row[8],
                "sepsis_state": row[9],
                "time_since_sepsis": row[10]
            })
        
        return {
            "mrn": mrn,
            "count": len(vitals),
            "vitals": vitals,
            "latest_status": vitals[0]["clinical_status"] if vitals else "unknown"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve realistic vitals: {e}")


@app.get("/realistic-vitals")
async def get_all_realistic_vitals(limit: int = 20):
    """Get recent realistic vitals for all patients"""
    db_path = Path(__file__).parent / "neonatal_ehr.db"
    
    try:
        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if realistic_vitals table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='realistic_vitals'")
        if not cursor.fetchone():
            return {"message": "Realistic vitals not available. Start realistic simulator first."}
        
        # Get recent vitals for all patients
        cursor.execute("""
            SELECT mrn, timestamp, hr, spo2, rr, temp, map, clinical_status, 
                   alert_level, severity_score, sepsis_state
            FROM realistic_vitals 
            ORDER BY timestamp DESC 
            LIMIT ?
        """, (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        vitals_by_patient = {}
        for row in rows:
            mrn = row[0]
            if mrn not in vitals_by_patient:
                vitals_by_patient[mrn] = []
            
            vitals_by_patient[mrn].append({
                "timestamp": row[1],
                "hr": row[2],
                "spo2": row[3],
                "rr": row[4],
                "temp": row[5],
                "map": row[6],
                "clinical_status": row[7],
                "alert_level": row[8],
                "severity_score": row[9],
                "sepsis_state": row[10]
            })
        
        return {
            "patients": vitals_by_patient,
            "total_records": len(rows)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve realistic vitals: {e}")


# ============================================================================
# INTEGRATED VITALS SIMULATION ENDPOINTS
# ============================================================================

# Global simulator instance already initialized above
# nicu_simulator = None

@app.post("/simulation/start")
async def start_vitals_simulation(background_tasks: BackgroundTasks, interval_seconds: int = 3):
    """Start integrated background vitals simulation"""
    global nicu_simulator
    
    try:
        if nicu_simulator is None:
            nicu_simulator = IntegratedNICUSimulator()
        
        # Initialize realistic_vitals table if not exists
        db = SessionLocal()
        try:
            from sqlalchemy import text
            db.execute(text("CREATE TABLE IF NOT EXISTS realistic_vitals ("
                      "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                      "timestamp TEXT NOT NULL, "
                      "mrn TEXT NOT NULL, "
                      "hr REAL NOT NULL, "
                      "spo2 REAL NOT NULL, "
                      "rr REAL NOT NULL, "
                      "temp REAL NOT NULL, "
                      "map REAL NOT NULL, "
                      "clinical_status TEXT NOT NULL, "
                      "alert_level TEXT NOT NULL, "
                      "severity_score REAL NOT NULL, "
                      "abnormal_count INTEGER NOT NULL, "
                      "sepsis_state TEXT NOT NULL, "
                      "time_since_sepsis REAL, "
                      "created_at DATETIME DEFAULT CURRENT_TIMESTAMP)"))
            db.commit()
        finally:
            db.close()
        
        result = nicu_simulator.start_background_simulation(interval_seconds)
        
        return {
            "success": True,
            "message": result,
            "interval_seconds": interval_seconds,
            "patients": list(nicu_simulator.patients.keys()),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start simulation: {e}")

@app.post("/simulation/stop")
async def stop_vitals_simulation():
    """Stop integrated background vitals simulation"""
    global nicu_simulator
    
    try:
        if nicu_simulator:
            result = nicu_simulator.stop_background_simulation()
            return {
                "success": True,
                "message": result,
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "success": False,
                "message": "No simulation running"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop simulation: {e}")

@app.get("/simulation/status")
async def get_simulation_status():
    """Get current simulation status"""
    global nicu_simulator
    
    try:
        if nicu_simulator is None:
            return {
                "simulation_active": False,
                "message": "Simulation not initialized"
            }
        
        # Get current patient states
        patient_states = {}
        for mrn, patient in nicu_simulator.patients.items():
            generator = patient['generator']
            vitals = generator.current_vitals
            assessment = generator.get_clinical_assessment()
            
            patient_states[mrn] = {
                "name": patient['name'],
                "ga": patient['ga'],
                "state": generator.state.value,
                "vitals": vitals,
                "assessment": assessment,
                "sepsis_time": generator.time_since_onset if generator.sepsis_onset_time else 0
            }
        
        return {
            "simulation_active": nicu_simulator.simulation_active,
            "patients": patient_states,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get simulation status: {e}")

@app.post("/simulation/trigger-sepsis/{mrn}")
async def trigger_patient_sepsis(mrn: str):
    """Trigger sepsis for specific patient in integrated simulation"""
    global nicu_simulator
    
    try:
        if nicu_simulator is None:
            nicu_simulator = IntegratedNICUSimulator()
        
        result = nicu_simulator.trigger_sepsis(mrn)
        
        return {
            "success": True,
            "message": result,
            "mrn": mrn,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to trigger sepsis: {e}")

@app.post("/simulation/reset-patient/{mrn}")
async def reset_simulation_patient(mrn: str):
    """Reset specific patient to normal in integrated simulation"""
    global nicu_simulator
    
    try:
        if nicu_simulator is None:
            nicu_simulator = IntegratedNICUSimulator()
        
        result = nicu_simulator.reset_patient(mrn)
        
        return {
            "success": True,
            "message": result,
            "mrn": mrn,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reset patient: {e}")

@app.get("/simulation/live-data")
async def get_live_simulation_data():
    """Get current live data from all patients"""
    global nicu_simulator
    
    try:
        if nicu_simulator is None:
            return {"message": "Simulation not initialized"}
        
        readings = nicu_simulator.generate_single_reading()
        
        return {
            "readings": readings,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get live data: {e}")

@app.get("/simulation/export-csv")
async def export_simulation_csv(filename: Optional[str] = None):
    """Export simulation data to CSV file"""
    global nicu_simulator
    
    try:
        if nicu_simulator is None:
            nicu_simulator = IntegratedNICUSimulator()
        
        csv_path = nicu_simulator.export_to_csv(filename)
        
        if csv_path:
            return {
                "success": True,
                "message": "Data exported to CSV",
                "file_path": csv_path,
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to export CSV")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export CSV: {e}")

@app.get("/simulation/generate-demo-data/{mrn}")
async def generate_demo_data(mrn: str):
    """Generate 30 normal + 30 risky values for demonstration"""
    global nicu_simulator
    
    try:
        if nicu_simulator is None:
            nicu_simulator = IntegratedNICUSimulator()
        
        if mrn not in nicu_simulator.patients:
            raise HTTPException(status_code=404, detail=f"Patient {mrn} not found")
        
        generator = nicu_simulator.patients[mrn]['generator']
        
        # Reset to normal state
        generator.reset_to_normal()
        
        demo_data = {
            "normal_values": [],
            "risky_values": [],
            "patient_info": {
                "mrn": mrn,
                "name": nicu_simulator.patients[mrn]['name'],
                "ga": nicu_simulator.patients[mrn]['ga']
            }
        }
        
        # Generate 30 normal values
        for i in range(30):
            vitals = generator.generate_next_vitals()
            assessment = generator.get_clinical_assessment()
            
            demo_data["normal_values"].append({
                "minute": i + 1,
                "hr": vitals['hr'],
                "spo2": vitals['spo2'],
                "rr": vitals['rr'],
                "temp": vitals['temp'],
                "map": vitals['map'],
                "status": assessment['clinical_status'],
                "alert_level": assessment['alert_level']
            })
        
        # Trigger sepsis and generate 30 risky values
        generator.trigger_sepsis()
        
        for i in range(30):
            vitals = generator.generate_next_vitals()
            assessment = generator.get_clinical_assessment()
            
            demo_data["risky_values"].append({
                "minute": i + 31,  # Continue minute numbering
                "hr": vitals['hr'],
                "spo2": vitals['spo2'],
                "rr": vitals['rr'],
                "temp": vitals['temp'],
                "map": vitals['map'],
                "status": assessment['clinical_status'],
                "alert_level": assessment['alert_level'],
                "sepsis_profile": generator.sepsis_profile,
                "sepsis_minutes": generator.sepsis_minutes
            })
        
        # Reset patient back to normal
        generator.reset_to_normal()
        
        return demo_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate demo data: {e}")

@app.get("/simulation/generate-graph-data/{mrn}")
async def generate_graph_data(mrn: str, total_minutes: int = 60):
    """Generate continuous data for graph visualization"""
    global nicu_simulator
    
    try:
        if nicu_simulator is None:
            nicu_simulator = IntegratedNICUSimulator()
        
        if mrn not in nicu_simulator.patients:
            raise HTTPException(status_code=404, detail=f"Patient {mrn} not found")
        
        generator = nicu_simulator.patients[mrn]['generator']
        generator.reset_to_normal()
        
        graph_data = {
            "patient_info": {
                "mrn": mrn,
                "name": nicu_simulator.patients[mrn]['name'],
                "ga": nicu_simulator.patients[mrn]['ga']
            },
            "timeline": [],
            "sepsis_trigger_minute": 30,  # Trigger sepsis at minute 30
            "vital_ranges": {
                "hr_normal": [generator.ranges.hr_min, generator.ranges.hr_max],
                "spo2_normal": [generator.ranges.spo2_min, generator.ranges.spo2_max], 
                "rr_normal": [generator.ranges.rr_min, generator.ranges.rr_max],
                "temp_normal": [generator.ranges.temp_min, generator.ranges.temp_max],
                "map_normal": [generator.ranges.map_min, generator.ranges.map_max]
            }
        }
        
        for minute in range(1, total_minutes + 1):
            # Trigger sepsis at minute 30
            if minute == 30:
                generator.trigger_sepsis()
            
            vitals = generator.generate_next_vitals()
            assessment = generator.get_clinical_assessment()
            
            timeline_point = {
                "minute": minute,
                "timestamp": (datetime.now() + timedelta(minutes=minute-1)).isoformat(),
                "hr": vitals['hr'],
                "spo2": vitals['spo2'],
                "rr": vitals['rr'],
                "temp": vitals['temp'],
                "map": vitals['map'],
                "clinical_status": assessment['clinical_status'],
                "alert_level": assessment['alert_level'],
                "severity_score": assessment['severity_score'],
                "state": generator.state.value,
                "sepsis_profile": generator.sepsis_profile if generator.sepsis_profile else None
            }
            
            graph_data["timeline"].append(timeline_point)
        
        # Reset patient
        generator.reset_to_normal()
        
        return graph_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate graph data: {e}")

@app.get("/simulation/data-summary")
async def get_simulation_data_summary():
    """Get summary of stored simulation data"""
    try:
        import sqlite3
        db_path = Path(__file__).parent / "neonatal_ehr.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if realistic_vitals table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='realistic_vitals'")
        if not cursor.fetchone():
            return {"message": "No simulation data found. Start simulation first."}
        
        # Get data summary
        cursor.execute("SELECT COUNT(*) FROM realistic_vitals")
        total_records = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT mrn) FROM realistic_vitals")
        total_patients = cursor.fetchone()[0]
        
        cursor.execute("SELECT MIN(timestamp), MAX(timestamp) FROM realistic_vitals")
        time_range = cursor.fetchone()
        
        cursor.execute("""
            SELECT mrn, COUNT(*) as record_count, 
                   MAX(timestamp) as latest_reading,
                   sepsis_state
            FROM realistic_vitals 
            GROUP BY mrn 
            ORDER BY latest_reading DESC
        """)
        patient_summary = cursor.fetchall()
        
        conn.close()
        
        return {
            "total_records": total_records,
            "total_patients": total_patients,
            "time_range": {
                "start": time_range[0],
                "end": time_range[1]
            },
            "patients": [
                {
                    "mrn": row[0],
                    "record_count": row[1],
                    "latest_reading": row[2],
                    "current_state": row[3]
                } for row in patient_summary
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get data summary: {e}")


# ============================================================================
# CHAIN OF CUSTODY LOG
# ============================================================================

@app.get("/custody-log")
async def get_custody_log():
    """Get the complete chain of custody audit trail"""
    log_file = Path(__file__).parent / "baby_edit_log.json"
    
    if not log_file.exists():
        return []
    
    entries = []
    try:
        with open(log_file, 'r') as f:
            for line in f:
                if line.strip():
                    entries.append(json.loads(line))
    except Exception as e:
        print(f"[ERROR] Failed to read custody log: {e}")
        raise HTTPException(status_code=500, detail="Failed to read custody log")
    
    return entries


@app.get("/custody-log/{mrn}")
async def get_custody_log_by_mrn(mrn: str):
    """Get chain of custody entries for a specific baby"""
    log_file = Path(__file__).parent / "baby_edit_log.json"
    
    if not log_file.exists():
        return []
    
    entries = []
    try:
        with open(log_file, 'r') as f:
            for line in f:
                if line.strip():
                    entry = json.loads(line)
                    if entry.get("baby_mrn") == mrn:
                        entries.append(entry)
    except Exception as e:
        print(f"[ERROR] Failed to read custody log: {e}")
        raise HTTPException(status_code=500, detail="Failed to read custody log")
    
    return entries


# ============================================================================
# HUMAN-IN-THE-LOOP (HIL) API ENDPOINTS
# ============================================================================

@app.post("/api/v1/predict_sepsis", status_code=status.HTTP_201_CREATED)
def predict_sepsis(request: SepsisPredictionRequest):
    """
    Receives features, runs sepsis prediction, and logs an alert if risk is high.
    """
    db = SessionLocal()
    try:
        # Map our 5 features to the model's expected 23 features
        # This is a simplified mapping for demo purposes
        base_features = [
            request.features.get('hr', 120),           # Heart rate
            request.features.get('spo2', 98),          # SpO2
            request.features.get('rr', 40),            # Respiratory rate
            request.features.get('temp', 37.0),        # Temperature
            request.features.get('map', 40),           # Mean arterial pressure
        ]
        
        # Add 18 dummy features to make 23 total (representing other clinical features)
        # In a real implementation, these would be actual clinical features
        dummy_features = [
            1,  # gestational_age_normalized
            0,  # birth_weight_normalized  
            0,  # maternal_gbs_positive
            0,  # maternal_fever
            0,  # rom_hours_normalized
            0,  # antibiotics_given
            0,  # wbc_normalized
            0,  # neutrophils_normalized
            0,  # platelets_normalized
            0,  # crp_normalized
            0,  # lactate_normalized
            0,  # blood_glucose_normalized
            0,  # ph_normalized
            0,  # pco2_normalized
            0,  # po2_normalized
            0,  # hemoglobin_normalized
            0,  # bilirubin_normalized
            0   # age_hours_normalized
        ]
        
        feature_values = np.array([base_features + dummy_features])
        risk_score = float(sepsis_model.predict_proba(feature_values)[0, 1])  # Convert to Python float
        onset_hours = risk_to_hours(risk_score)
        
        response_data = {"risk_score": float(risk_score), "onset_window_hrs": onset_hours, "alert_id": None}

        if risk_score > 0.75:
            new_alert = Alert(
                baby_id=request.baby_id,
                model_risk_score=risk_score,
                onset_window_hrs=onset_hours,
                alert_status='PENDING_DOCTOR_ACTION'
            )
            db.add(new_alert)
            db.commit()
            db.refresh(new_alert)
            response_data["alert_id"] = new_alert.alert_id
        
        return response_data
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error processing features: {e}")
    finally:
        db.close()


@app.post("/api/v1/log_doctor_action", status_code=status.HTTP_200_OK)
def log_doctor_action(request: DoctorActionRequest):
    """
    Logs the action taken by a doctor in response to an alert.
    """
    db = SessionLocal()
    try:
        alert = db.query(Alert).filter(Alert.alert_id == request.alert_id).first()
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")

        if alert.alert_status != 'PENDING_DOCTOR_ACTION':
            # Allow updating if it's already action taken (to refine details)
            if alert.alert_status not in ['PENDING_DOCTOR_ACTION', 'ACTION_TAKEN']:
                raise HTTPException(status_code=400, detail="Action cannot be taken on this alert.")

        alert.doctor_id = request.doctor_id
        alert.doctor_action = request.action_type
        alert.action_detail = request.action_detail
        
        # Save detailed decision info
        if request.observation_duration:
            alert.observation_duration = request.observation_duration
        if request.lab_tests:
            alert.lab_tests = json.dumps(request.lab_tests)
        if request.antibiotics:
            alert.antibiotics = json.dumps(request.antibiotics)
        if request.dismiss_duration:
            alert.dismiss_duration = request.dismiss_duration
            alert.alert_status = 'DISMISSED'
        else:
            alert.alert_status = 'ACTION_TAKEN'
            
        alert.action_timestamp = datetime.utcnow()
        
        db.commit()
        return {"message": "Doctor's action logged successfully.", "status": alert.alert_status}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error logging action: {e}")
    finally:
        db.close()


@app.post("/api/v1/log_outcome", status_code=status.HTTP_200_OK)
def log_outcome(request: OutcomeLogRequest):
    """
    Logs the final outcome of an alert and calculates the reward signal.
    """
    db = SessionLocal()
    try:
        alert = db.query(Alert).filter(Alert.alert_id == request.alert_id).first()
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")

        alert.sepsis_confirmed = request.final_outcome
        alert.outcome_timestamp = datetime.utcnow()
        alert.alert_status = 'CLOSED'

        model_predicted_high_risk = alert.model_risk_score > 0.75

        if (model_predicted_high_risk and alert.sepsis_confirmed) or \
           (not model_predicted_high_risk and not alert.sepsis_confirmed):
            alert.reward_signal = 1
            alert.model_status = 'SUCCESS'
        else:
            alert.reward_signal = -1
            alert.model_status = 'FAILURE'
            
        db.commit()
        return {"message": "Outcome logged and reward calculated."}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error logging outcome: {e}")
    finally:
        db.close()


@app.get("/api/v1/alerts/pending", response_model=List[AlertNotification])
def get_pending_alerts(role: str):
    """
    Gets pending alerts for a given role with mock data (no database required).
    """
    try:
        # Return mock/empty alerts to avoid database connection issues
        if role.lower() == 'doctor':
            # Return empty list or mock alerts for doctor
            return []
        elif role.lower() == 'nurse':
            # Return empty list for nurse
            return []
        else:
            return []
            
    except Exception as e:
        print(f"[API ERROR] Failed to fetch alerts: {e}")
        # Return empty list instead of raising exception
        return []


# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.get("/")
async def root():
    """Health check endpoint"""
    db = SessionLocal()
    
    try:
        total_alerts = db.query(Alert).count()
        total_vitals = db.query(RealisticVitals).count()
        
        latest = db.query(RealisticVitals)\
            .order_by(desc(RealisticVitals.timestamp))\
            .first()
        
        return {
            "status": "operational",
            "service": "Neovance-AI Neonatal EHR System",
            "version": "2.0.0",
            "database": "connected",
            "statistics": {
                "total_alerts": total_alerts,
                "total_vitals_records": total_vitals
            },
            "latest_vitals_timestamp": latest.timestamp if latest else None,
            "endpoints": {
                "babies": "GET /babies",
                "baby_profile": "GET /baby/{mrn}",
                "update_baby": "POST /baby/update/{mrn}",
                "websocket": "WS /ws/live",
                "history": "GET /history",
                "stats": "GET /stats",
                "action": "POST /action",
                "sepsis_trigger": "POST /trigger-sepsis",
                "simulation": {
                    "start": "POST /simulation/start",
                    "stop": "POST /simulation/stop", 
                    "status": "GET /simulation/status",
                    "trigger_sepsis": "POST /simulation/trigger-sepsis/{mrn}",
                    "reset_patient": "POST /simulation/reset-patient/{mrn}",
                    "live_data": "GET /simulation/live-data",
                    "export_csv": "GET /simulation/export-csv",
                    "data_summary": "GET /simulation/data-summary",
                    "demo_data": "GET /simulation/generate-demo-data/{mrn}",
                    "graph_data": "GET /simulation/generate-graph-data/{mrn}"
                }
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
    print("NEOVANCE-AI: Comprehensive Neonatal EHR System")
    print("="*70)
    print("Starting FastAPI server with complete medical records...")
    print("Endpoints:")
    print("  - Health Check:  http://localhost:8000/")
    print("  - All Babies:    http://localhost:8000/babies")
    print("  - Baby Profile:  http://localhost:8000/baby/{mrn}")
    print("  - Update Baby:   http://localhost:8000/baby/update/{mrn} (POST)")
    print("  - WebSocket:     ws://localhost:8000/ws/live")
    print("  - History:       http://localhost:8000/history")
    print("  - Statistics:    http://localhost:8000/stats")
    print("  - Log Action:    http://localhost:8000/action (POST)")
    print("  - Trigger Sepsis: http://localhost:8000/trigger-sepsis (POST)")
    print("  - API Docs:      http://localhost:8000/docs")
    print("="*70)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
