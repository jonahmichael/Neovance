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

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, String, Float, DateTime, Integer, Date, Boolean, ForeignKey, Text, desc
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from pydantic import BaseModel


# ============================================================================
# DATABASE SETUP
# ============================================================================

DATABASE_URL = "sqlite:///./neonatal_ehr.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ============================================================================
# DATABASE MODELS
# ============================================================================

class User(Base):
    """Medical staff user model"""
    __tablename__ = "users"
    
    user_id = Column(String, primary_key=True)
    full_name = Column(String, nullable=False)
    role = Column(String, nullable=False)  # 'Doctor' or 'Nurse'
    password = Column(String, nullable=False)


class Staff(Base):
    """Staff directory - doctors and nurses"""
    __tablename__ = "staff"
    
    staff_id = Column(String, primary_key=True)  # DR001, NS001, etc.
    name = Column(String, nullable=False)
    role = Column(String, nullable=False)  # Doctor, Nurse
    specialization = Column(String, nullable=True)
    contact = Column(String, nullable=True)
    shift = Column(String, nullable=True)  # Day, Night, Rotating


class BabyProfile(Base):
    """Comprehensive neonatal profile"""
    __tablename__ = "baby_profiles"
    
    # ===================== IDENTIFIER DATA =====================
    mrn = Column(String, primary_key=True)  # Medical Record Number (B00x)
    full_name = Column(String, nullable=False)  # Or "Baby of [Mother's Name]"
    sex = Column(String, nullable=False)
    dob = Column(Date, nullable=False)
    time_of_birth = Column(String, nullable=False)
    place_of_birth = Column(String, nullable=False)  # hospital/ward/room
    birth_order = Column(String, nullable=False)  # singleton, twin, triplet
    hospital_id_band = Column(String, default="-")  # ID band number
    footprints_taken = Column(Boolean, default=False)
    
    # ===================== GESTATIONAL & BIRTH DATA =====================
    gestational_age = Column(String, nullable=False)  # weeks + days
    apgar_1min = Column(Integer, nullable=False)
    apgar_5min = Column(Integer, nullable=False)
    apgar_10min = Column(Integer, nullable=True)
    
    # ===================== PARENT INFORMATION =====================
    mother_name = Column(String, nullable=False)
    father_name = Column(String, nullable=False)
    parent_contact = Column(String, nullable=False)  # phone
    parent_address = Column(String, nullable=False)
    mother_age = Column(Integer, nullable=False)
    mother_blood_type = Column(String, nullable=False)  # with Rh factor
    mother_id = Column(String, default="-")  # hospital/national ID
    father_id = Column(String, default="-")  # hospital/national ID
    emergency_contact = Column(String, default="-")
    
    # ===================== BIRTH MEASUREMENTS =====================
    birth_weight = Column(Float, nullable=False)  # kg
    length = Column(Float, nullable=False)  # cm
    head_circumference = Column(Float, nullable=False)  # cm
    chest_circumference = Column(Float, nullable=True)  # cm
    bmi = Column(Float, nullable=True)  # calculated
    weight_percentile = Column(String, default="-")
    length_percentile = Column(String, default="-")
    head_percentile = Column(String, default="-")
    
    # ===================== PHYSICAL EXAMINATION =====================
    muscle_tone = Column(String, default="-")  # Normal/Hypotonic/Hypertonic
    reflexes = Column(String, default="-")  # Moro, rooting, sucking, grasp, stepping
    moro_reflex = Column(String, default="-")
    rooting_reflex = Column(String, default="-")
    sucking_reflex = Column(String, default="-")
    grasp_reflex = Column(String, default="-")
    stepping_reflex = Column(String, default="-")
    alertness_level = Column(String, default="-")  # Alert/Drowsy/Lethargic
    cry_strength = Column(String, default="-")  # Strong/Weak/Absent
    skin_condition = Column(String, default="-")  # Normal/Jaundice/Cyanotic/Pale
    birthmarks = Column(String, default="-")
    bruising = Column(String, default="-")
    fontanelle_status = Column(String, default="-")  # Flat/Bulging/Sunken
    eye_exam = Column(String, default="-")
    ear_exam = Column(String, default="-")
    nose_throat_exam = Column(String, default="-")
    genital_exam = Column(String, default="-")
    anus_patency = Column(String, default="-")  # Patent/Imperforate
    limb_movement = Column(String, default="-")  # Symmetric/Asymmetric
    spine_check = Column(String, default="-")
    hip_check = Column(String, default="-")  # Hip dysplasia screening
    
    # ===================== SENSORY SCREENING =====================
    hearing_screening = Column(String, default="-")  # Pass/Refer/Not Done
    hearing_screening_date = Column(Date, nullable=True)
    vision_screening = Column(String, default="-")  # Red reflex test
    red_reflex_right = Column(String, default="-")
    red_reflex_left = Column(String, default="-")
    response_to_stimuli = Column(String, default="-")
    
    # ===================== CARDIORESPIRATORY SCREENING =====================
    pulse_oximetry = Column(String, default="-")  # For CHD screening
    pulse_ox_right_hand = Column(Float, nullable=True)
    pulse_ox_foot = Column(Float, nullable=True)
    breathing_pattern = Column(String, default="-")  # Regular/Irregular/Apneic
    lung_sounds = Column(String, default="-")  # Clear/Crackles/Wheezing
    heart_sounds = Column(String, default="-")  # Normal/Murmur detected
    heart_murmur_grade = Column(String, default="-")
    
    # ===================== BLOOD & LAB SCREENING =====================
    metabolic_screening = Column(String, default="-")  # Overall status
    metabolic_screening_date = Column(Date, nullable=True)
    pku_result = Column(String, default="-")  # Phenylketonuria
    msud_result = Column(String, default="-")  # Maple Syrup Urine Disease
    galactosemia_result = Column(String, default="-")
    hypothyroidism_result = Column(String, default="-")  # Congenital hypothyroidism
    cah_result = Column(String, default="-")  # Congenital adrenal hyperplasia
    sickle_cell_result = Column(String, default="-")
    thalassemia_result = Column(String, default="-")
    cystic_fibrosis_result = Column(String, default="-")
    scid_result = Column(String, default="-")  # Severe combined immunodeficiency
    biotinidase_result = Column(String, default="-")
    genetic_screening_panel = Column(String, default="-")
    blood_glucose = Column(String, default="-")
    bilirubin_level = Column(String, default="-")
    bilirubin_date = Column(Date, nullable=True)
    blood_type = Column(String, default="-")  # Baby's blood type
    rh_factor = Column(String, default="-")
    coombs_test = Column(String, default="-")  # Direct Coombs
    
    # ===================== IMMUNIZATIONS & PROPHYLAXIS =====================
    vitamin_k_given = Column(Boolean, default=False)
    vitamin_k_date = Column(Date, nullable=True)
    hep_b_vaccine = Column(Boolean, default=False)
    hep_b_date = Column(Date, nullable=True)
    eye_prophylaxis = Column(Boolean, default=False)  # Antibiotic ointment
    eye_prophylaxis_date = Column(Date, nullable=True)
    other_vaccines = Column(String, default="-")
    
    # ===================== FEEDING & ELIMINATION =====================
    feeding_method = Column(String, default="-")  # Breastfeeding/Formula/Mixed/NPO
    feeding_tolerance = Column(String, default="-")  # Good/Poor/Vomiting
    feeds_per_day = Column(Integer, nullable=True)
    urine_output = Column(String, default="-")  # Normal/Decreased/Absent
    first_void_time = Column(String, default="-")
    stool_output = Column(String, default="-")  # Meconium/Transitional/Normal
    meconium_passage_time = Column(String, default="-")
    vomiting = Column(String, default="-")  # None/Occasional/Frequent
    reflux = Column(String, default="-")
    
    # ===================== CLINICAL COURSE =====================
    bed_assignment = Column(String, default="-")  # Incubator/Crib/Warmer
    nicu_admission = Column(Boolean, default=False)
    nicu_admission_reason = Column(String, default="-")
    oxygen_support = Column(String, default="-")  # None/Nasal cannula/CPAP/Ventilator
    fio2 = Column(Float, nullable=True)  # Fraction of inspired oxygen
    iv_fluids = Column(String, default="-")
    medications = Column(Text, default="-")
    antibiotics = Column(String, default="-")
    procedures = Column(Text, default="-")  # Surgeries, procedures
    monitoring_events = Column(Text, default="-")  # Alarms, events
    infection_screening = Column(String, default="-")
    
    # ===================== RISK & HISTORY =====================
    maternal_infections = Column(String, default="-")  # HIV, HepB, GBS, syphilis
    gbs_status = Column(String, default="-")  # Group B Strep
    maternal_hiv = Column(String, default="-")
    maternal_hep_b = Column(String, default="-")
    maternal_syphilis = Column(String, default="-")
    drug_exposure = Column(String, default="-")  # Drug/medication exposure in pregnancy
    delivery_method = Column(String, nullable=False)  # Vaginal/C-section/Assisted
    delivery_complications = Column(String, default="-")
    birth_complications = Column(String, default="-")
    resuscitation_needed = Column(Boolean, default=False)
    resuscitation_details = Column(String, default="-")
    family_genetic_history = Column(Text, default="-")
    prenatal_history = Column(Text, nullable=True)
    prenatal_care = Column(String, default="-")  # Adequate/Inadequate/None
    
    # ===================== DISCHARGE DATA =====================
    discharge_date = Column(Date, nullable=True)
    discharge_weight = Column(Float, nullable=True)
    discharge_diagnosis = Column(Text, nullable=True)
    follow_up_appointments = Column(Text, nullable=True)
    parent_education = Column(Text, nullable=True)
    home_care_instructions = Column(Text, nullable=True)
    screening_results_summary = Column(Text, nullable=True)
    
    # ===================== CARE TEAM =====================
    primary_care_pediatrician = Column(String, nullable=False)
    attending_physician = Column(String, default="-")
    primary_nurse = Column(String, default="-")
    
    # ===================== NOTES =====================
    notes = Column(Text, nullable=True)
    
    # ===================== TIMESTAMPS =====================
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    vitals = relationship("LiveVitals", back_populates="baby")


class LiveVitals(Base):
    """Real-time vital signs monitoring"""
    __tablename__ = "live_vitals"
    
    timestamp = Column(String, primary_key=True)
    mrn = Column(String, ForeignKey("baby_profiles.mrn"), nullable=False)
    hr = Column(Float, nullable=False)
    spo2 = Column(Float, nullable=False)
    rr = Column(Float, nullable=False)
    temp = Column(Float, nullable=False)
    map = Column(Float, nullable=False)
    risk_score = Column(Float, nullable=False)
    status = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    baby = relationship("BabyProfile", back_populates="vitals")


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
        
        # Create Users
        users = [
            User(user_id="DR001", full_name="Dr. Rajesh Kumar", role="Doctor", password="1234"),
            User(user_id="DR002", full_name="Dr. Priya Sharma", role="Doctor", password="1234"),
            User(user_id="NS001", full_name="Nurse Anjali Patel", role="Nurse", password="1234"),
            User(user_id="NS002", full_name="Nurse Deepika Singh", role="Nurse", password="1234"),
        ]
        
        for user in users:
            db.add(user)
        
        # Create Staff Directory
        staff_members = [
            Staff(staff_id="DR001", name="Dr. Rajesh Kumar", role="Doctor", specialization="Neonatology", contact="+91-9876500001", shift="Day"),
            Staff(staff_id="DR002", name="Dr. Priya Sharma", role="Doctor", specialization="Pediatric Cardiology", contact="+91-9876500002", shift="Night"),
            Staff(staff_id="NS001", name="Anjali Patel", role="Nurse", specialization="NICU Care", contact="+91-9876500003", shift="Day"),
            Staff(staff_id="NS002", name="Deepika Singh", role="Nurse", specialization="Critical Care", contact="+91-9876500004", shift="Rotating"),
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
    print("[STARTUP] Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("[STARTUP] Database tables created")
    
    populate_initial_data()
    
    print("[STARTUP] Backend ready - waiting for Pathway stream data")
    print("[STARTUP] Make sure pathway_simulator.py and pathway_etl.py are running!")


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
            raise HTTPException(status_code=404, detail="Baby not found")
        return baby
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
            db = SessionLocal()
            
            latest_record = db.query(LiveVitals)\
                .order_by(desc(LiveVitals.timestamp))\
                .first()
            
            if latest_record:
                data = {
                    "timestamp": latest_record.timestamp,
                    "patient_id": latest_record.mrn,
                    "hr": latest_record.hr,
                    "spo2": latest_record.spo2,
                    "rr": latest_record.rr,
                    "temp": latest_record.temp,
                    "map": latest_record.map,
                    "risk_score": latest_record.risk_score,
                    "status": latest_record.status,
                    "created_at": latest_record.created_at.isoformat()
                }
                
                await websocket.send_json(data)
            
            db.close()
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
        
        records = db.query(LiveVitals)\
            .filter(LiveVitals.created_at >= cutoff_time)\
            .order_by(desc(LiveVitals.timestamp))\
            .all()
        
        print(f"[HISTORY] Returning {len(records)} records from last 30 minutes")
        
        return records
        
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
async def trigger_sepsis():
    """Trigger a controlled sepsis simulation spike in Pathway simulator"""
    global global_sepsis_triggered
    
    global_sepsis_triggered = True
    
    # Write trigger signal to a file that pathway_simulator.py can monitor
    trigger_file = Path(__file__).parent.parent / "data" / "sepsis_trigger.txt"
    trigger_file.parent.mkdir(exist_ok=True)
    
    with open(trigger_file, 'w') as f:
        f.write(datetime.now().isoformat())
    
    print("[SEPSIS TRIGGER] Signal written - Pathway simulator will respond")
    
    return {
        "success": True,
        "message": "Sepsis spike signal sent to Pathway simulator",
        "duration": "15 seconds (5 steps)",
        "effects": "HR increases, SpO2 decreases, RR increases",
        "note": "Requires pathway_simulator.py to be running"
    }


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
# HEALTH CHECK
# ============================================================================

@app.get("/")
async def root():
    """Health check endpoint"""
    db = SessionLocal()
    
    try:
        total_babies = db.query(BabyProfile).count()
        total_vitals = db.query(LiveVitals).count()
        total_users = db.query(User).count()
        
        latest = db.query(LiveVitals)\
            .order_by(desc(LiveVitals.timestamp))\
            .first()
        
        return {
            "status": "operational",
            "service": "Neovance-AI Neonatal EHR System",
            "version": "2.0.0",
            "database": "connected",
            "statistics": {
                "total_babies": total_babies,
                "total_users": total_users,
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
                "sepsis_trigger": "POST /trigger-sepsis"
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
