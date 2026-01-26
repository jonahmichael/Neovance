# Neovance-AI: Neonatal Sepsis Early Warning System

A real-time predictive analytics platform for early detection of neonatal sepsis using machine learning and a human-in-the-loop (HIL) feedback framework.

## Overview

Neovance-AI combines:
- **Real-time Data Streaming** via Pathway ETL
- **Machine Learning Risk Prediction** using vital sign patterns
- **Human-in-the-Loop Clinical Validation** for continuous improvement
- **Role-Based UI** for doctors and nurses
- **Full Audit Trail** of all predictions, actions, and outcomes

## Key Features

- ✅ Real-time vital signs monitoring and trend analysis
- ✅ ML-powered sepsis risk prediction (0-100% risk score)
- ✅ Early onset sepsis (EOS) calculator integration
- ✅ Doctor action logging with 4 clinical decision options
- ✅ Nurse notification system for care coordination
- ✅ Outcome tracking and reward signal calculation
- ✅ PostgreSQL persistence with TimescaleDB support
- ✅ Next.js dashboard with role-based views
- ✅ Offline model retraining pipeline

## Architecture

```
┌─────────────────┐
│  Live Vital     │
│  Signs Monitor  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Pathway ETL    │  ← Real-time aggregation
│  (streaming)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  FastAPI Server │  ← ML inference + HIL orchestration
│  Port 8000      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  PostgreSQL DB  │  ← Alerts, actions, outcomes
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Next.js UI     │  ← Doctor/Nurse dashboards
│  Port 3000      │
└─────────────────┘
```

## Quick Start

### 1. Prerequisites
```bash
# Install PostgreSQL 13+
sudo apt install postgresql postgresql-contrib

# Install Python 3.10+
python3 --version

# Install Node.js 18+
node --version
```

### 2. Database Setup
```bash
# Create database
createdb -U postgres -h localhost neovance

# Set password (if needed)
psql -U postgres
ALTER USER postgres PASSWORD 'password';
\q

# Apply schema
export DATABASE_URL="postgresql://postgres:password@localhost/neovance"
psql $DATABASE_URL -f backend/schema.sql
```

### 3. Backend Setup
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Verify model exists
ls -lh trained_models/sepsis_random_forest.pkl

# Start FastAPI server
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at [http://localhost:8000](http://localhost:8000)

API docs at [http://localhost:8000/docs](http://localhost:8000/docs)

### 4. Frontend Setup
```bash
# Install dependencies
cd frontend/dashboard
npm install

# Start Next.js dev server
npm run dev
```

Frontend will be available at [http://localhost:3000](http://localhost:3000)

### 5. Test the HIL Workflow

```bash
# Terminal 1: Start backend
cd backend
source ../../venv/bin/activate
uvicorn main:app --reload

# Terminal 2: Test prediction endpoint
curl -X POST http://localhost:8000/api/v1/predict_sepsis \
  -H "Content-Type: application/json" \
  -d '{
    "baby_id": "B001",
    "features": {
      "hr": 160,
      "spo2": 92,
      "rr": 55,
      "temp": 38.2,
      "map": 35
    }
  }'

# Expected response:
# {"risk_score": 0.89, "onset_window_hrs": 6, "alert_id": 1}

# Terminal 3: Check pending alerts (doctor view)
curl http://localhost:8000/api/v1/alerts/pending?role=doctor

# Terminal 4: Log doctor action
curl -X POST http://localhost:8000/api/v1/log_doctor_action \
  -H "Content-Type: application/json" \
  -d '{
    "alert_id": 1,
    "doctor_id": "DR001",
    "action_type": "TREAT",
    "action_detail": "Started ampicillin + gentamicin therapy"
  }'

# Terminal 5: Check nurse notifications
curl http://localhost:8000/api/v1/alerts/pending?role=nurse

# Terminal 6: Log outcome
curl -X POST http://localhost:8000/api/v1/log_outcome \
  -H "Content-Type: application/json" \
  -d '{
    "alert_id": 1,
    "final_outcome": true
  }'
```

## Human-in-the-Loop (HIL) Workflow

### The Learning Loop

```
1. ML Model predicts high sepsis risk (>75%)
   ↓
2. Alert created in database (PENDING_DOCTOR_ACTION)
   ↓
3. Doctor reviews alert and takes action:
   - OBSERVE: Close monitoring
   - TREAT: Start antibiotics
   - LAB_TEST: Order blood culture
   - DISMISS: False positive
   ↓
4. Nurse receives instructions (ACTION_TAKEN)
   ↓
5. Patient outcome observed (sepsis confirmed or not)
   ↓
6. Reward signal calculated (+1 or -1)
   ↓
7. Data used for offline model retraining
```

### Doctor Actions

| Action | Description | Reward Logic |
|--------|-------------|--------------|
| **OBSERVE** | Close monitoring without immediate treatment | Neutral feedback |
| **TREAT** | Initiate antibiotic therapy | +1 if sepsis confirmed, -1 if false positive |
| **LAB_TEST** | Order confirmatory tests | Depends on lab results |
| **DISMISS** | Reject alert as false positive | +1 if correct, -1 if sepsis develops |

### Reward Signal Formula

```python
if (model_predicted_high_risk AND sepsis_confirmed) OR 
   (NOT model_predicted_high_risk AND NOT sepsis_confirmed):
    reward = +1  # Model was correct
else:
    reward = -1  # Model was incorrect
```

## API Reference

### Endpoints

#### POST /api/v1/predict_sepsis
Predict sepsis risk from vital signs.

**Request:**
```json
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
```

**Response:**
```json
{
  "risk_score": 0.89,
  "onset_window_hrs": 6,
  "alert_id": 1
}
```

#### GET /api/v1/alerts/pending?role={doctor|nurse}
Fetch pending alerts based on user role.

**Response:**
```json
[
  {
    "alert_id": 1,
    "baby_id": "B001",
    "timestamp": "2026-01-26T12:00:00Z",
    "model_risk_score": 0.89,
    "onset_window_hrs": 6,
    "alert_status": "PENDING_DOCTOR_ACTION"
  }
]
```

#### POST /api/v1/log_doctor_action
Log doctor's clinical decision.

**Request:**
```json
{
  "alert_id": 1,
  "doctor_id": "DR001",
  "action_type": "TREAT",
  "action_detail": "Started empiric antibiotics due to high risk score and clinical signs"
}
```

#### POST /api/v1/log_outcome
Log final patient outcome and calculate reward.

**Request:**
```json
{
  "alert_id": 1,
  "final_outcome": true
}
```

## Frontend Components

### Doctor View
- **CriticalActionPanel** - Action buttons and clinical notes form
- **AlertList** - Real-time pending alerts with risk scores
- **PatientDetails** - Full vital signs and trends
- **ActionHistory** - Past decisions and outcomes

### Nurse View
- **DoctorInstructions** - Recent doctor actions to execute
- **NotificationBell** - Real-time alerts when doctors take action
- **PriorityPatients** - Patients needing immediate attention
- **VitalsMonitor** - Real-time vital sign tracking

## Database Schema

### alerts table
```sql
CREATE TABLE alerts (
    alert_id SERIAL PRIMARY KEY,
    baby_id TEXT NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    -- ML Prediction
    model_risk_score FLOAT,
    onset_window_hrs INT,
    alert_status TEXT DEFAULT 'PENDING_DOCTOR_ACTION',
    
    -- Doctor Action
    doctor_id TEXT,
    doctor_action TEXT,
    action_detail TEXT,
    action_timestamp TIMESTAMPTZ,
    
    -- Outcome & Reward
    sepsis_confirmed BOOLEAN,
    outcome_timestamp TIMESTAMPTZ,
    reward_signal INT,
    model_status TEXT
);
```

## Model Training

### Training Data Format
```csv
baby_id,hr,spo2,rr,temp,map,sepsis_confirmed
B001,160,92,55,38.2,35,1
B002,140,95,45,36.8,40,0
```

### Training Pipeline
```bash
# Generate synthetic training data
python generate_sepsis_training_data.py

# Train model
python train_sepsis_model.py

# Test model
python test_your_model.py

# Model saved to: trained_models/sepsis_random_forest.pkl
```

### Model Retraining with HIL Data
```bash
# Export HIL feedback data
psql $DATABASE_URL -c "COPY (SELECT * FROM alerts WHERE reward_signal IS NOT NULL) TO '/tmp/hil_data.csv' CSV HEADER"

# Combine with original training data
cat data/neonatal_sepsis_training.csv /tmp/hil_data.csv > data/combined_training.csv

# Retrain model
python train_sepsis_model.py --data data/combined_training.csv

# Deploy new model (hot-swap)
cp trained_models/sepsis_random_forest.pkl trained_models/sepsis_random_forest_v2.pkl
# Update backend to load new model
```

## Monitoring & Metrics

Track these key performance indicators:

- **Alert Rate**: Predictions per hour/day
- **Action Distribution**: TREAT/OBSERVE/LAB/DISMISS breakdown
- **Average Reward Signal**: Model accuracy over time (target: >0.7)
- **False Positive Rate**: Dismissed alerts that were correct
- **False Negative Rate**: Missed sepsis cases (critical metric)
- **Response Time**: Alert creation to doctor action latency

## Deployment

### Production Checklist

- [ ] Set up PostgreSQL with TimescaleDB extension
- [ ] Configure SSL certificates for HTTPS
- [ ] Set environment variables for sensitive credentials
- [ ] Enable CORS for frontend domain
- [ ] Set up log aggregation (e.g., ELK stack)
- [ ] Configure backup strategy for database
- [ ] Set up monitoring (e.g., Prometheus + Grafana)
- [ ] Test disaster recovery procedures
- [ ] Document incident response plan
- [ ] Obtain regulatory approval (if applicable)

### Environment Variables
```bash
# Backend
export DATABASE_URL="postgresql://user:pass@host:port/dbname"
export MODEL_PATH="trained_models/sepsis_random_forest.pkl"
export LOG_LEVEL="INFO"

# Frontend
export NEXT_PUBLIC_API_URL="https://api.neovance.com"
```

## Safety & Ethics

> **CRITICAL**: This system is a **clinical decision support tool**, NOT an autonomous decision-maker. All clinical decisions require doctor review and approval.

### Key Principles
1. **Human Authority**: Doctors have final say on all patient care decisions
2. **Transparency**: All predictions include confidence scores and reasoning
3. **Audit Trail**: Complete logging of predictions, actions, and outcomes
4. **Continuous Improvement**: System learns from expert decisions
5. **Fail-Safe Design**: System defaults to alerting, never auto-dismissing

## Troubleshooting

### Backend won't start
```bash
# Check PostgreSQL connection
psql $DATABASE_URL -c "SELECT 1"

# Check if model file exists
ls -lh trained_models/sepsis_random_forest.pkl

# Check Python dependencies
pip list | grep -E "fastapi|sqlalchemy|psycopg2|scikit-learn"
```

### Frontend can't connect to backend
```bash
# Verify backend is running
curl http://localhost:8000/api/health

# Check CORS configuration in backend/main.py
# Ensure frontend URL is in allowed_origins list
```

### Database connection errors
```bash
# Test connection
psql postgresql://postgres:password@localhost/neovance -c "SELECT NOW()"

# Check if database exists
psql -U postgres -l | grep neovance

# Recreate database if needed
dropdb -U postgres neovance
createdb -U postgres neovance
psql -U postgres neovance -f backend/schema.sql
```

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request with clear description

## License

MIT License - see LICENSE file for details

## Support

For issues or questions:
- GitHub Issues: [github.com/yourorg/neovance-ai/issues](https://github.com/yourorg/neovance-ai/issues)
- Email: support@neovance.com
- Documentation: [docs.neovance.com](https://docs.neovance.com)

## Acknowledgments

- Pathway framework for real-time ETL
- FastAPI for high-performance API
- Next.js and Tailwind CSS for modern UI
- PostgreSQL and TimescaleDB for time-series data

---

**Made with ❤️ for safer neonatal care**
