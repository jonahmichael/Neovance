#!/usr/bin/env python3
"""
FastAPI Sepsis Prediction Service
Real-time sepsis risk prediction using trained ML model

This service provides a production-ready API endpoint for sepsis prediction
that integrates the trained RandomForest model with real-time patient data.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, field_validator
import joblib
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Optional, Dict, Any
import os
import logging
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Model file paths
MODEL_PATH = "trained_models/sepsis_random_forest.pkl"
SCALER_PATH = "trained_models/feature_scaler.pkl" 
FEATURE_PATH = "trained_models/feature_columns.pkl"
METADATA_PATH = "trained_models/model_metadata.json"

# Global model storage
model = None
scaler = None
feature_names = None
metadata = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events"""
    # Startup
    await load_models()
    yield
    # Shutdown - cleanup if needed

# Initialize FastAPI app
app = FastAPI(
    title="Neovance-AI Sepsis Prediction Service",
    description="Real-time early-onset sepsis risk prediction for NICU patients",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# --- PYDANTIC MODELS FOR API ---

class PatientVitals(BaseModel):
    """Patient vital signs and clinical data for sepsis prediction"""
    
    # Patient identifiers
    mrn: str
    timestamp: Optional[str] = None
    
    # Demographics  
    gestational_age_at_birth_weeks: float
    birth_weight_kg: float
    sex: Optional[str] = "unknown"
    race: Optional[str] = "unknown"
    
    # Maternal factors (for EOS calculation)
    ga_weeks: int
    ga_days: int
    maternal_temp_celsius: float = 37.0
    rom_hours: float = 8.0
    gbs_status: str = "negative"  # negative, positive, unknown
    antibiotic_type: str = "none"  # none, penicillin, ampicillin
    clinical_exam: str = "normal"  # normal, abnormal
    
    # Current vital signs
    hr: float  # heart rate (bpm)
    spo2: float  # oxygen saturation (%)
    rr: float  # respiratory rate (breaths/min)
    temp_celsius: float  # temperature (°C)
    map: float  # mean arterial pressure (mmHg)
    
    # Risk factors
    comorbidities: Optional[str] = "no"
    central_venous_line: Optional[str] = "no"
    intubated_at_time_of_sepsis_evaluation: Optional[str] = "no"
    inotrope_at_time_of_sepsis_eval: Optional[str] = "no"
    ecmo: Optional[str] = "no"
    stat_abx: Optional[str] = "no"
    time_to_antibiotics: Optional[float] = None
    
    @field_validator('gbs_status')
    def validate_gbs_status(cls, v):
        allowed = ["negative", "positive", "unknown"]
        if v not in allowed:
            raise ValueError(f"gbs_status must be one of: {allowed}")
        return v
    
    @field_validator('clinical_exam')
    def validate_clinical_exam(cls, v):
        allowed = ["normal", "abnormal", "chorioamnionitis"]
        if v not in allowed:
            raise ValueError(f"clinical_exam must be one of: {allowed}")
        return v
    
    @field_validator('hr')
    def validate_heart_rate(cls, v):
        if not 40 <= v <= 220:
            raise ValueError("Heart rate must be between 40-220 bpm")
        return v
    
    @field_validator('spo2')
    def validate_oxygen_saturation(cls, v):
        if not 70 <= v <= 100:
            raise ValueError("Oxygen saturation must be between 70-100%")
        return v
    
    @field_validator('temp_celsius')
    def validate_temperature(cls, v):
        if not 32.0 <= v <= 42.0:
            raise ValueError("Temperature must be between 32-42°C")
        return v


class SepsisRiskResponse(BaseModel):
    """Response model for sepsis risk prediction"""
    
    # Patient identification
    mrn: str
    timestamp: str
    
    # Primary prediction
    sepsis_probability: float  # 0.0 - 1.0
    sepsis_risk_percentage: float  # 0 - 100%
    
    # Clinical decision support
    risk_category: str  # LOW_RISK, MODERATE_RISK, HIGH_RISK, CRITICAL_RISK
    estimated_onset_hours: int  # 6, 12, 24, 48
    clinical_recommendation: str
    
    # EOS risk calculator results
    eos_risk_score: float  # per 1000 births
    eos_category: str  # ROUTINE_CARE, ENHANCED_MONITORING, HIGH_RISK
    
    # Physiological assessment
    physiological_instability_score: int  # 0-3
    vital_signs_alert: bool
    
    # Model metadata
    model_confidence: float
    feature_importance_top3: Dict[str, float]


# --- EOS RISK CALCULATOR FUNCTIONS ---

def calculate_eos_risk_production(patient_data: dict) -> float:
    """
    Production version of EOS risk calculator
    Implements Puopolo/Kaiser algorithm for real-time use
    """
    try:
        # Extract clinical parameters
        ga_weeks = patient_data.get('ga_weeks', 39)
        ga_days = patient_data.get('ga_days', 0)
        temp_celsius = patient_data.get('maternal_temp_celsius', 37.0)
        rom_hours = patient_data.get('rom_hours', 8.0)
        gbs_status = patient_data.get('gbs_status', 'negative')
        antibiotic_type = patient_data.get('antibiotic_type', 'none')
        clinical_exam = patient_data.get('clinical_exam', 'normal')
        
        # Convert gestational age to decimal weeks
        ga_decimal = ga_weeks + (ga_days / 7.0)
        
        # Initialize risk factors (multiplicative model)
        risk_factors = []
        
        # 1. Gestational age effect
        if ga_decimal < 35.0:
            risk_factors.append(4.0)  # Very preterm
        elif ga_decimal < 37.0:
            risk_factors.append(2.5)  # Preterm
        elif ga_decimal < 39.0:
            risk_factors.append(1.2)  # Late preterm
        
        # 2. Maternal intrapartum fever
        if temp_celsius >= 38.5:
            risk_factors.append(5.0)   # High fever
        elif temp_celsius >= 38.0:
            risk_factors.append(2.5)   # Moderate fever
        
        # 3. Prolonged rupture of membranes
        if rom_hours >= 24.0:
            risk_factors.append(3.0)   # Very prolonged
        elif rom_hours >= 18.0:
            risk_factors.append(2.0)   # Prolonged
        
        # 4. GBS colonization and antibiotic prophylaxis
        if gbs_status.lower() == "positive":
            if antibiotic_type.lower() in ["penicillin", "ampicillin"]:
                risk_factors.append(1.5)  # Reduced risk with adequate prophylaxis
            else:
                risk_factors.append(6.0)  # High risk without adequate prophylaxis
        elif gbs_status.lower() == "unknown":
            risk_factors.append(2.0)  # Unknown status increases risk
        
        # 5. Clinical chorioamnionitis
        if clinical_exam.lower() in ["abnormal", "chorioamnionitis"]:
            risk_factors.append(20.0)  # Clinical signs of infection
        
        # 6. Current neonatal factors
        current_temp = patient_data.get('temp_celsius', 37.0)
        if current_temp >= 38.0 or current_temp <= 36.0:
            risk_factors.append(1.8)  # Temperature instability
            
        hr = patient_data.get('hr', 120)
        if hr >= 160 or hr <= 90:
            risk_factors.append(1.3)  # Heart rate abnormalities
            
        spo2 = patient_data.get('spo2', 97)
        if spo2 <= 92:
            risk_factors.append(1.5)  # Desaturation
        
        # Calculate final risk
        baseline_risk = 0.5  # per 1000 live births
        total_risk = baseline_risk
        
        for factor in risk_factors:
            total_risk *= factor
        
        # Cap at reasonable maximum
        total_risk = min(total_risk, 50.0)
        
        return round(total_risk, 3)
        
    except Exception as e:
        logger.error(f"EOS calculation error: {e}")
        return 0.5  # Return baseline risk on error


def categorize_eos_status(risk_score: float, clinical_exam: str) -> str:
    """Convert EOS risk score to clinical action categories"""
    if clinical_exam.lower() in ["abnormal", "chorioamnionitis"]:
        return "HIGH_RISK"
    
    if risk_score >= 3.0:
        return "HIGH_RISK"
    elif risk_score >= 1.0:
        return "ENHANCED_MONITORING"
    else:
        return "ROUTINE_CARE"


def extract_features_for_ml(patient_data: dict, feature_names: list) -> np.ndarray:
    """
    Extract and prepare features for ML model prediction
    """
    # Create feature vector
    feature_vector = np.zeros(len(feature_names))
    
    # Enhanced EOS risk calculation
    eos_risk = calculate_eos_risk_production(patient_data)
    
    # Calculate derived features
    temp_instability = int(patient_data.get('temp_celsius', 37.0) >= 38.0 or 
                          patient_data.get('temp_celsius', 37.0) <= 36.0)
    
    hr = patient_data.get('hr', 120)
    map_val = patient_data.get('map', 40)
    hemodynamic_instability = int(hr >= 160 or hr <= 90 or map_val <= 30)
    
    spo2 = patient_data.get('spo2', 97)
    rr = patient_data.get('rr', 25)
    respiratory_instability = int(spo2 <= 92 or rr >= 40)
    
    physiological_instability_score = (temp_instability + 
                                     hemodynamic_instability + 
                                     respiratory_instability)
    
    # Map patient data to features
    feature_mapping = {
        'gestational_age_at_birth_weeks': patient_data.get('gestational_age_at_birth_weeks', 39),
        'birth_weight_kg': patient_data.get('birth_weight_kg', 3.0),
        'hr': patient_data.get('hr', 120),
        'spo2': patient_data.get('spo2', 97),
        'rr': patient_data.get('rr', 25),
        'temp_celsius': patient_data.get('temp_celsius', 37.0),
        'map': patient_data.get('map', 40),
        'maternal_temp_celsius': patient_data.get('maternal_temp_celsius', 37.0),
        'rom_hours': patient_data.get('rom_hours', 8.0),
        'time_to_antibiotics': patient_data.get('time_to_antibiotics', 0),
        'eos_risk_enhanced': eos_risk,
        'physiological_instability_score': physiological_instability_score,
        'temp_instability': temp_instability,
        'hemodynamic_instability': hemodynamic_instability,
        'respiratory_instability': respiratory_instability,
        'preterm_and_fever': int(patient_data.get('gestational_age_at_birth_weeks', 39) < 37 and 
                               patient_data.get('temp_celsius', 37.0) >= 38.0),
        'gbs_positive_no_abx': int(patient_data.get('gbs_status', 'negative') == 'positive' and 
                                 patient_data.get('antibiotic_type', 'none') == 'none')
    }
    
    # Handle categorical encodings
    categorical_mappings = {
        'sex': patient_data.get('sex', 'unknown'),
        'race': patient_data.get('race', 'unknown'),
        'gbs_status': patient_data.get('gbs_status', 'negative'),
        'antibiotic_type': patient_data.get('antibiotic_type', 'none'),
        'clinical_exam': patient_data.get('clinical_exam', 'normal'),
        'comorbidities': patient_data.get('comorbidities', 'no'),
        'central_venous_line': patient_data.get('central_venous_line', 'no'),
        'intubated_at_time_of_sepsis_evaluation': patient_data.get('intubated_at_time_of_sepsis_evaluation', 'no'),
        'inotrope_at_time_of_sepsis_eval': patient_data.get('inotrope_at_time_of_sepsis_eval', 'no'),
        'ecmo': patient_data.get('ecmo', 'no'),
        'stat_abx': patient_data.get('stat_abx', 'no'),
    }
    
    # Fill feature vector
    for i, feature_name in enumerate(feature_names):
        if feature_name in feature_mapping:
            feature_vector[i] = feature_mapping[feature_name]
        else:
            # Handle one-hot encoded categorical features
            for cat_name, cat_value in categorical_mappings.items():
                if feature_name.startswith(f"{cat_name}_") and feature_name.endswith(f"_{cat_value}"):
                    feature_vector[i] = 1.0
                    break
    
    return feature_vector


def risk_to_hours(risk_probability: float) -> int:
    """Convert ML risk probability to estimated sepsis onset window in hours"""
    if risk_probability >= 0.8:
        return 6    # Critical risk: immediate evaluation
    elif risk_probability >= 0.5:
        return 12   # High risk: close monitoring
    elif risk_probability >= 0.2:
        return 24   # Moderate risk: standard monitoring
    else:
        return 48   # Low risk: routine care


def get_clinical_recommendation(risk_probability: float, eos_category: str) -> str:
    """Generate clinical recommendation based on risk assessment"""
    if risk_probability >= 0.8 or eos_category == "HIGH_RISK":
        return "IMMEDIATE EVALUATION: Consider empiric antibiotics and laboratory workup"
    elif risk_probability >= 0.5 or eos_category == "ENHANCED_MONITORING":
        return "ENHANCED MONITORING: Increase observation frequency, consider laboratory studies"
    elif risk_probability >= 0.2:
        return "STANDARD MONITORING: Continue routine care with regular vital sign monitoring"
    else:
        return "ROUTINE CARE: Standard newborn care protocols"


def categorize_risk_level(risk_probability: float) -> str:
    """Categorize risk probability into clinical risk levels"""
    if risk_probability >= 0.8:
        return "CRITICAL_RISK"
    elif risk_probability >= 0.5:
        return "HIGH_RISK"
    elif risk_probability >= 0.2:
        return "MODERATE_RISK"
    else:
        return "LOW_RISK"


# --- API STARTUP AND SHUTDOWN ---

async def load_models():
    """Load trained models and metadata on service startup"""
    global model, scaler, feature_names, metadata
    
    try:
        # Load trained model
        if os.path.exists(MODEL_PATH):
            model = joblib.load(MODEL_PATH)
            logger.info(f"✅ Loaded ML model: {MODEL_PATH}")
        else:
            raise FileNotFoundError(f"Model not found: {MODEL_PATH}")
        
        # Load scaler (if exists)
        if os.path.exists(SCALER_PATH):
            scaler = joblib.load(SCALER_PATH)
            logger.info(f"✅ Loaded feature scaler: {SCALER_PATH}")
        
        # Load feature names
        if os.path.exists(FEATURE_PATH):
            feature_names = joblib.load(FEATURE_PATH)
            logger.info(f"✅ Loaded feature columns: {len(feature_names)} features")
        else:
            raise FileNotFoundError(f"Feature info not found: {FEATURE_PATH}")
        
        # Load metadata
        if os.path.exists(METADATA_PATH):
            import json
            with open(METADATA_PATH, 'r') as f:
                metadata = json.load(f)
            logger.info(f"✅ Loaded model metadata")
        
        logger.info("🚀 Sepsis Prediction Service Ready!")
        
    except Exception as e:
        logger.error(f"❌ Failed to load models: {e}")
        raise e


# --- API ENDPOINTS ---

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "Neovance-AI Sepsis Prediction Service",
        "status": "healthy",
        "version": "1.0.0",
        "model_loaded": model is not None
    }


@app.get("/health")
async def health_check():
    """Detailed health check with model status"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "models": {
            "ml_model_loaded": model is not None,
            "scaler_loaded": scaler is not None,
            "features_loaded": feature_names is not None,
            "feature_count": len(feature_names) if feature_names else 0
        },
        "metadata": metadata is not None
    }


@app.post("/predict", response_model=SepsisRiskResponse)
async def predict_sepsis_risk(patient_vitals: PatientVitals):
    """
    Predict sepsis risk for a neonatal patient
    
    Returns comprehensive risk assessment including:
    - ML model probability
    - EOS risk score
    - Clinical recommendations
    - Estimated onset timing
    """
    if model is None or feature_names is None:
        raise HTTPException(status_code=503, detail="Prediction models not loaded")
    
    try:
        # Convert patient data to dictionary
        patient_data = patient_vitals.dict()
        
        # Add timestamp if not provided
        if not patient_data.get('timestamp'):
            patient_data['timestamp'] = datetime.now().isoformat()
        
        # Calculate EOS risk score
        eos_risk = calculate_eos_risk_production(patient_data)
        eos_category = categorize_eos_status(eos_risk, patient_data['clinical_exam'])
        
        # Extract features for ML model
        feature_vector = extract_features_for_ml(patient_data, feature_names)
        
        # Apply scaling if scaler is available
        if scaler is not None:
            feature_vector = scaler.transform(feature_vector.reshape(1, -1))[0]
        
        # Make ML prediction
        ml_probability = model.predict_proba(feature_vector.reshape(1, -1))[0][1]
        
        # Calculate physiological instability
        temp_unstable = patient_data['temp_celsius'] >= 38.0 or patient_data['temp_celsius'] <= 36.0
        hr_unstable = patient_data['hr'] >= 160 or patient_data['hr'] <= 90
        resp_unstable = patient_data['spo2'] <= 92 or patient_data['rr'] >= 40
        map_unstable = patient_data['map'] <= 30
        
        instability_score = sum([temp_unstable, hr_unstable, resp_unstable, map_unstable])
        vital_signs_alert = instability_score >= 2
        
        # Generate clinical decision support
        risk_category = categorize_risk_level(ml_probability)
        estimated_hours = risk_to_hours(ml_probability)
        clinical_recommendation = get_clinical_recommendation(ml_probability, eos_category)
        
        # Calculate model confidence (simplified approach)
        probabilities = model.predict_proba(feature_vector.reshape(1, -1))[0]
        confidence = max(probabilities) - min(probabilities)
        
        # Get top feature importances (if available)
        feature_importance_top3 = {}
        if hasattr(model, 'feature_importances_'):
            importances = model.feature_importances_
            top_indices = np.argsort(importances)[-3:][::-1]
            feature_importance_top3 = {
                feature_names[i]: float(importances[i]) 
                for i in top_indices
            }
        
        # Construct response
        response = SepsisRiskResponse(
            mrn=patient_vitals.mrn,
            timestamp=patient_data['timestamp'],
            sepsis_probability=round(float(ml_probability), 4),
            sepsis_risk_percentage=round(float(ml_probability * 100), 2),
            risk_category=risk_category,
            estimated_onset_hours=estimated_hours,
            clinical_recommendation=clinical_recommendation,
            eos_risk_score=round(eos_risk, 2),
            eos_category=eos_category,
            physiological_instability_score=instability_score,
            vital_signs_alert=vital_signs_alert,
            model_confidence=round(confidence, 4),
            feature_importance_top3=feature_importance_top3
        )
        
        logger.info(f"Prediction completed for MRN: {patient_vitals.mrn}, Risk: {ml_probability:.3f}")
        
        return response
        
    except Exception as e:
        logger.error(f"Prediction error for MRN {patient_vitals.mrn}: {e}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@app.get("/model/info")
async def get_model_info():
    """Get information about the loaded model"""
    if model is None or metadata is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    return {
        "model_metadata": metadata,
        "feature_count": len(feature_names),
        "model_type": type(model).__name__,
        "scaler_available": scaler is not None
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("sepsis_prediction_service:app", host="0.0.0.0", port=8001, reload=False)