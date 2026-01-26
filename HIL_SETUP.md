# Neovance-AI: Human-in-the-Loop Predictive Workflow

This document outlines the architecture and workflow of the Neovance-AI system, which integrates a machine learning model with a human-in-the-loop (HIL) framework for early sepsis detection in neonates.

## System Architecture

### Components

1. **Pathway ETL** - Real-time vital signs data aggregation and trend analysis
2. **FastAPI Service** - ML model inference and HIL workflow orchestration  
3. **PostgreSQL Database** - Persistent storage for alerts, actions, and outcomes
4. **Next.js Frontend** - Role-based user interface for doctors and nurses
5. **Offline ML Training** - Continuous model improvement using HIL feedback

### Data Flow Diagram

```
Live Vitals → Pathway ETL → FastAPI (/predict_sepsis) → PostgreSQL (alerts table)
                                ↓
                          Alert Created (risk > 0.75)
                                ↓
                          Frontend (Doctor View)
                                ↓
                    Doctor Takes Action (TREAT/OBSERVE/LAB/DISMISS)
                                ↓
                    FastAPI (/log_doctor_action) → PostgreSQL (update alert)
                                ↓
                          Frontend (Nurse View)
                                ↓
                    Nurse Executes Doctor's Instructions
                                ↓
                          Patient Outcome Observed
                                ↓
                    FastAPI (/log_outcome) → PostgreSQL (reward calculation)
                                ↓
                    Offline Training (model improvement)
```

## The Human-in-the-Loop (HIL) Learning Framework

The Neovance-AI system employs a two-stage risk assessment strategy to enhance safety and accuracy.

### Stage 1: EOS Calculator (Medical Feature)
An initial risk assessment based on established clinical guidelines provides a baseline risk score using:
- Maternal risk factors (GBS status, fever, ROM duration)
- Neonatal risk factors (gestational age, birth weight, vital signs)

### Stage 2: ML Model (Outcome Predictor)
A machine learning model trained on historical data provides a secondary risk score based on:
- Real-time vital sign patterns and trends
- Historical outcomes and clinical correlations
- Temporal feature engineering

### The HIL Learning Loop

**AI Prediction → Human Action → System Validation → Model Reward**

This continuous cycle ensures:
1. **Patient Safety** - Doctors maintain full clinical authority
2. **Model Improvement** - System learns from expert decisions
3. **Audit Trail** - Complete logging of all predictions and actions
4. **Feedback Signal** - Clear reward mechanism for model retraining

## Doctor Actions and Reward Logic

When the ML model flags a high-risk patient (risk_score > 0.75), a doctor is prompted to take one of four actions:

### 1. **OBSERVE** (Close Monitoring)
- **Description**: Monitor patient closely without immediate intervention
- **Reward Logic**: Neutral - contributes to model understanding of borderline cases
- **Nursing Action**: Increase vital sign monitoring frequency

### 2. **TREAT** (Start Treatment)
- **Description**: Initiate antibiotic therapy for sepsis
- **Reward Logic**: 
  - If sepsis confirmed: **+1 (SUCCESS)** - Model correctly identified high risk
  - If sepsis not confirmed: **-1 (FAILURE)** - False positive
- **Nursing Action**: Administer prescribed antibiotics, monitor response

### 3. **LAB_TEST** (Order Laboratory Tests)
- **Description**: Order blood culture, CBC, CRP to confirm/rule out sepsis
- **Reward Logic**: Based on lab results confirming or refuting prediction
- **Nursing Action**: Collect samples, expedite lab processing

### 4. **DISMISS** (Dismiss Alert)
- **Description**: Doctor believes this is a false positive
- **Reward Logic**:
  - If sepsis later develops: **-1 (FAILURE)** - Critical miss, high-value feedback
  - If no sepsis: **+1 (SUCCESS)** - Correct dismissal
- **Nursing Action**: Resume standard monitoring protocols

### Reward Calculation Formula

```python
model_predicted_high_risk = risk_score > 0.75

if (model_predicted_high_risk AND sepsis_confirmed) OR 
   (NOT model_predicted_high_risk AND NOT sepsis_confirmed):
    reward = +1  # SUCCESS
else:
    reward = -1  # FAILURE
```

## API Endpoints

### 1. Prediction Endpoint
```http
POST /api/v1/predict_sepsis
Content-Type: application/json

{
  "baby_id": "B001",
  "features": {
    "hr": 160,
    "spo2": 92,
    "rr": 55,
    "temp": 38.2,
    "map": 35
  }
}

Response:
{
  "risk_score": 0.89,
  "onset_window_hrs": 6,
  "alert_id": 1
}
```

### 2. Doctor Action Logging
```http
POST /api/v1/log_doctor_action
Content-Type: application/json

{
  "alert_id": 1,
  "doctor_id": "DR001",
  "action_type": "TREAT",
  "action_detail": "Started ampicillin + gentamicin based on high sepsis risk"
}

Response:
{
  "message": "Doctor's action logged successfully."
}
```

### 3. Outcome Logging
```http
POST /api/v1/log_outcome
Content-Type: application/json

{
  "alert_id": 1,
  "final_outcome": true
}

Response:
{
  "message": "Outcome logged and reward calculated."
}
```

### 4. Pending Alerts (Role-Based)
```http
GET /api/v1/alerts/pending?role=doctor

Response:
[
  {
    "alert_id": 1,
    "baby_id": "B001",
    "timestamp": "2026-01-26T12:00:00Z",
    "model_risk_score": 0.89,
    "alert_status": "PENDING_DOCTOR_ACTION"
  }
]
```

## Frontend Integration

### Doctor View
- **Critical Action Panel** - Displays when alert_status = 'PENDING_DOCTOR_ACTION'
- **Four Action Buttons** - OBSERVE, TREAT, LAB_TEST, DISMISS
- **Action Detail Form** - Free-text reasoning and clinical notes
- **Real-time Alert Polling** - Checks for new alerts every 5 seconds

### Nurse View
- **Doctor Instructions Card** - Shows recent actions with alert_status = 'ACTION_TAKEN'
- **Action Summary** - Displays doctor's chosen action and reasoning
- **Patient Priority List** - Highlights patients with new instructions
- **Notification Bell** - Real-time alerts when doctor takes action

## Database Schema

### alerts table
```sql
CREATE TABLE alerts (
    alert_id SERIAL PRIMARY KEY,
    baby_id TEXT NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    -- Model Prediction
    model_risk_score FLOAT,
    onset_window_hrs INT,
    alert_status TEXT DEFAULT 'PENDING_DOCTOR_ACTION',
    
    -- Doctor Action
    doctor_id TEXT,
    doctor_action TEXT,
    action_detail TEXT,
    action_timestamp TIMESTAMPTZ,
    
    -- Outcome
    sepsis_confirmed BOOLEAN,
    outcome_timestamp TIMESTAMPTZ,
    reward_signal INT,
    model_status TEXT
);
```

## Safety & Ethics Statement

> **"The system is a clinical decision support tool, never an autonomous decision maker. The Doctor maintains full control and clinical authority at all times."**

Key principles:
1. **Human Authority** - All clinical decisions require doctor approval
2. **Transparency** - Model predictions include confidence scores and reasoning
3. **Audit Trail** - Complete logging of all system interactions
4. **Continuous Improvement** - System learns from expert decisions, not replaces them
5. **Fail-Safe Design** - System defaults to alerting, never dismissing concerns

## Model Retraining Workflow

The HIL feedback loop enables continuous model improvement:

1. **Data Collection** - Weekly export of alerts with outcomes
2. **Feature Engineering** - Extract temporal patterns from vitals history
3. **Training Dataset** - Combine original training data with new HIL data
4. **Model Training** - Retrain with emphasis on high-reward-signal cases
5. **Validation** - Test on held-out data and recent cases
6. **Deployment** - Hot-swap model with zero downtime
7. **Monitoring** - Track reward signal trends and alert accuracy

## Getting Started

### Prerequisites
- PostgreSQL 13+
- Python 3.10+
- Node.js 18+
- FastAPI and dependencies
- Next.js and dependencies

### Backend Setup
```bash
cd backend
source ../venv/bin/activate
pip install -r requirements.txt

# Set database URL
export DATABASE_URL="postgresql://postgres:password@localhost/neovance"

# Run schema
psql $DATABASE_URL -f schema.sql

# Start server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup
```bash
cd frontend/dashboard
npm install
npm run dev
```

### Testing the HIL Workflow
```bash
# 1. Create a high-risk prediction
curl -X POST http://localhost:8000/api/v1/predict_sepsis \
  -H "Content-Type: application/json" \
  -d '{"baby_id": "B001", "features": {"hr": 160, "spo2": 92, "rr": 55, "temp": 38.2, "map": 35}}'

# 2. Check pending alerts (as doctor)
curl http://localhost:8000/api/v1/alerts/pending?role=doctor

# 3. Log doctor action
curl -X POST http://localhost:8000/api/v1/log_doctor_action \
  -H "Content-Type: application/json" \
  -d '{"alert_id": 1, "doctor_id": "DR001", "action_type": "TREAT", "action_detail": "Started antibiotics"}'

# 4. Check nurse notifications
curl http://localhost:8000/api/v1/alerts/pending?role=nurse

# 5. Log final outcome
curl -X POST http://localhost:8000/api/v1/log_outcome \
  -H "Content-Type: application/json" \
  -d '{"alert_id": 1, "final_outcome": true}'
```

## Metrics and Monitoring

Track these key metrics:
- **Alert Rate** - Predictions per hour/day
- **Action Distribution** - Breakdown of TREAT/OBSERVE/LAB/DISMISS
- **Reward Signal** - Average reward over time (target: > 0.7)
- **False Positive Rate** - DISMISS actions confirmed correct
- **False Negative Rate** - Critical misses (sepsis after DISMISS)
- **Response Time** - Time from alert to doctor action

## Future Enhancements

1. **Multi-Model Ensemble** - Combine multiple prediction models
2. **Explainable AI** - SHAP values for feature importance
3. **Mobile Notifications** - Push alerts to doctor/nurse mobile devices
4. **Voice Integration** - Hands-free action logging
5. **Federated Learning** - Train across multiple hospitals without sharing patient data
