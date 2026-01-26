# Neovance-AI: Complete Startup Guide

This guide provides step-by-step instructions for running the complete Neovance-AI system with Human-in-the-Loop (HIL) integration.

## System Requirements

- **OS**: Linux (Ubuntu 20.04+), macOS, or WSL2 on Windows
- **PostgreSQL**: 13 or higher
- **Python**: 3.10 or higher
- **Node.js**: 18 or higher
- **RAM**: Minimum 4GB
- **Disk Space**: Minimum 2GB

## Pre-Flight Checklist

Before starting, verify:

```bash
# Check PostgreSQL
psql --version  # Should be 13+

# Check Python
python3 --version  # Should be 3.10+

# Check Node.js
node --version  # Should be v18+

# Check if PostgreSQL is running
sudo systemctl status postgresql  # Linux
# or
brew services list | grep postgresql  # macOS
```

## Step 1: Database Setup

### 1.1 Create Database

```bash
# Connect as postgres user
sudo -u postgres psql

# Create database
CREATE DATABASE neovance;

# Set password (if not already set)
ALTER USER postgres PASSWORD 'password';

# Exit
\q
```

### 1.2 Verify Connection

```bash
# Test connection
export DATABASE_URL="postgresql://postgres:password@localhost/neovance"
psql $DATABASE_URL -c "SELECT NOW();"
```

Expected output:
```
              now              
-------------------------------
 2026-01-26 12:00:00.000000+00
```

### 1.3 Apply Database Schema

```bash
# Navigate to backend directory
cd /mnt/d/Neovance-AI/backend

# Apply schema
psql $DATABASE_URL -f schema.sql
```

Expected output:
```
DROP TABLE
DROP TABLE
CREATE TABLE
CREATE TABLE
```

### 1.4 Verify Tables

```bash
psql $DATABASE_URL -c "\dt"
```

Expected output:
```
              List of relations
 Schema |       Name       | Type  |  Owner   
--------+------------------+-------+----------
 public | alerts           | table | postgres
 public | realistic_vitals | table | postgres
```

## Step 2: Backend Setup

### 2.1 Create Virtual Environment

```bash
# Navigate to project root
cd /mnt/d/Neovance-AI

# Create venv
python3 -m venv venv

# Activate venv
source venv/bin/activate

# Verify activation
which python  # Should show /mnt/d/Neovance-AI/venv/bin/python
```

### 2.2 Install Python Dependencies

```bash
# Install requirements
pip install --upgrade pip
pip install -r requirements.txt

# Verify key packages
pip list | grep -E "fastapi|uvicorn|sqlalchemy|psycopg2|scikit-learn|joblib"
```

Expected output:
```
fastapi              0.128.0
uvicorn              0.34.0
sqlalchemy           2.0.46
psycopg2-binary      2.9.10
scikit-learn         1.3.2
joblib               1.3.2
```

### 2.3 Verify ML Model

```bash
# Check if model exists
ls -lh trained_models/sepsis_random_forest.pkl
```

Expected output:
```
-rw-r--r-- 1 user user 12K Jan 26 12:00 trained_models/sepsis_random_forest.pkl
```

If model doesn't exist, train it:
```bash
python train_sepsis_model.py
```

### 2.4 Start FastAPI Backend

```bash
# Navigate to backend
cd backend

# Start server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Expected output:
```
INFO:     Will watch for changes in these directories: ['/mnt/d/Neovance-AI/backend']
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using WatchFiles
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
INFO:     ML model loaded successfully: LogisticRegression
INFO:     Application startup complete.
```

### 2.5 Verify Backend Endpoints

Open a **new terminal** and run:

```bash
# Test health endpoint
curl http://localhost:8000/

# Expected: "Neovance Backend is Running"

# Test API docs
curl http://localhost:8000/docs
# Should return HTML page

# Test prediction endpoint
curl -X POST http://localhost:8000/api/v1/predict_sepsis \
  -H "Content-Type: application/json" \
  -d '{
    "baby_id": "TEST001",
    "features": {
      "hr": 160,
      "spo2": 92,
      "rr": 55,
      "temp": 38.2,
      "map": 35
    }
  }'
```

Expected response:
```json
{
  "risk_score": 1.0,
  "onset_window_hrs": 6,
  "alert_id": 1
}
```

## Step 3: Frontend Setup

### 3.1 Install Node Dependencies

Open a **new terminal**:

```bash
# Navigate to frontend
cd /mnt/d/Neovance-AI/frontend/dashboard

# Install dependencies
npm install
```

Expected output:
```
added 320 packages in 45s
```

### 3.2 Configure Environment

```bash
# Create .env.local file
cat > .env.local << EOF
NEXT_PUBLIC_API_URL=http://localhost:8000
EOF
```

### 3.3 Start Next.js Development Server

```bash
# Start dev server
npm run dev
```

Expected output:
```
▲ Next.js 15.1.6
- Local:        http://localhost:3000
- Network:      http://192.168.1.100:3000

✓ Starting...
✓ Ready in 2.5s
```

### 3.4 Verify Frontend

Open browser and navigate to:
- [http://localhost:3000](http://localhost:3000)

You should see the Neovance dashboard login page.

## Step 4: End-to-End HIL Workflow Test

### 4.1 Create High-Risk Alert

In a terminal:

```bash
curl -X POST http://localhost:8000/api/v1/predict_sepsis \
  -H "Content-Type: application/json" \
  -d '{
    "baby_id": "B001",
    "features": {
      "hr": 165,
      "spo2": 90,
      "rr": 60,
      "temp": 38.5,
      "map": 33
    }
  }'
```

Expected response:
```json
{
  "risk_score": 0.95,
  "onset_window_hrs": 6,
  "alert_id": 2
}
```

### 4.2 Check Doctor Pending Alerts

```bash
curl http://localhost:8000/api/v1/alerts/pending?role=doctor
```

Expected response (array with the alert):
```json
[
  {
    "alert_id": 2,
    "baby_id": "B001",
    "timestamp": "2026-01-26T12:05:00.000000+00:00",
    "model_risk_score": 0.95,
    "onset_window_hrs": 6,
    "alert_status": "PENDING_DOCTOR_ACTION",
    "doctor_id": null,
    "doctor_action": null,
    "action_detail": null
  }
]
```

### 4.3 Log Doctor Action

```bash
curl -X POST http://localhost:8000/api/v1/log_doctor_action \
  -H "Content-Type: application/json" \
  -d '{
    "alert_id": 2,
    "doctor_id": "DR_SMITH",
    "action_type": "TREAT",
    "action_detail": "Initiated ampicillin 100mg/kg + gentamicin 5mg/kg due to high risk score and clinical deterioration"
  }'
```

Expected response:
```json
{
  "message": "Doctor's action logged successfully."
}
```

### 4.4 Check Nurse Notifications

```bash
curl http://localhost:8000/api/v1/alerts/pending?role=nurse
```

Expected response:
```json
[
  {
    "alert_id": 2,
    "baby_id": "B001",
    "timestamp": "2026-01-26T12:05:00.000000+00:00",
    "model_risk_score": 0.95,
    "onset_window_hrs": 6,
    "alert_status": "ACTION_TAKEN",
    "doctor_id": "DR_SMITH",
    "doctor_action": "TREAT",
    "action_detail": "Initiated ampicillin 100mg/kg + gentamicin 5mg/kg due to high risk score and clinical deterioration",
    "action_timestamp": "2026-01-26T12:06:00.000000+00:00"
  }
]
```

### 4.5 Log Final Outcome

After 24-48 hours, when the outcome is known:

```bash
curl -X POST http://localhost:8000/api/v1/log_outcome \
  -H "Content-Type: application/json" \
  -d '{
    "alert_id": 2,
    "final_outcome": true
  }'
```

Expected response:
```json
{
  "message": "Outcome logged and reward calculated.",
  "reward_signal": 1
}
```

Note: `reward_signal: 1` means the model correctly predicted sepsis (SUCCESS).

### 4.6 Verify Complete Workflow in Database

```bash
psql $DATABASE_URL -c "SELECT alert_id, baby_id, model_risk_score, alert_status, doctor_action, sepsis_confirmed, reward_signal FROM alerts WHERE alert_id = 2;"
```

Expected output:
```
 alert_id | baby_id | model_risk_score |  alert_status  | doctor_action | sepsis_confirmed | reward_signal 
----------+---------+------------------+----------------+---------------+------------------+---------------
        2 | B001    |             0.95 | OUTCOME_LOGGED | TREAT         | t                |             1
```

## Step 5: Frontend HIL Integration Test

### 5.1 Login as Doctor

1. Open [http://localhost:3000](http://localhost:3000)
2. Login with role: **Doctor**
3. Navigate to **Critical Alerts** section

### 5.2 Review Pending Alert

You should see:
- Patient B001 with risk score 95%
- Onset window: 6 hours
- Four action buttons: OBSERVE, TREAT, LAB TEST, DISMISS

### 5.3 Take Action

1. Click **TREAT** button
2. Enter action detail in text area
3. Click **Submit Action**
4. Alert should disappear from doctor's view

### 5.4 Login as Nurse

1. Logout and login with role: **Nurse**
2. Navigate to **Doctor Instructions** section

### 5.5 View Doctor Instructions

You should see:
- Patient B001
- Doctor action: TREAT (green badge)
- Full action details from doctor
- Timestamp of action

## Common Issues & Solutions

### Issue 1: Backend won't start - "ModuleNotFoundError"

**Solution:**
```bash
# Ensure venv is activated
source venv/bin/activate

# Reinstall requirements
pip install -r requirements.txt
```

### Issue 2: Database connection refused

**Solution:**
```bash
# Check if PostgreSQL is running
sudo systemctl status postgresql

# Start if not running
sudo systemctl start postgresql

# Verify connection
psql $DATABASE_URL -c "SELECT 1"
```

### Issue 3: Model file not found

**Solution:**
```bash
# Train the model
python train_sepsis_model.py

# Verify it was created
ls -lh trained_models/sepsis_random_forest.pkl
```

### Issue 4: Frontend can't connect to backend

**Solution:**
```bash
# Check if backend is running
curl http://localhost:8000/

# Check CORS settings in backend/main.py
# Ensure "http://localhost:3000" is in allowed_origins

# Check .env.local in frontend
cat frontend/dashboard/.env.local
```

### Issue 5: "No alerts showing in frontend"

**Solution:**
```bash
# Create a test alert via API
curl -X POST http://localhost:8000/api/v1/predict_sepsis \
  -H "Content-Type: application/json" \
  -d '{"baby_id":"B999","features":{"hr":160,"spo2":90,"rr":55,"temp":38.5,"map":35}}'

# Verify it was created
curl http://localhost:8000/api/v1/alerts/pending?role=doctor
```

## Production Deployment

### Prerequisites
- PostgreSQL with SSL enabled
- Nginx or Apache for reverse proxy
- SSL certificates (Let's Encrypt recommended)
- Systemd service files for auto-restart

### Backend Production Setup

```bash
# Install gunicorn
pip install gunicorn

# Create systemd service
sudo nano /etc/systemd/system/neovance-backend.service
```

Service file content:
```ini
[Unit]
Description=Neovance FastAPI Backend
After=network.target postgresql.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/neovance/backend
Environment="DATABASE_URL=postgresql://user:pass@localhost/neovance"
ExecStart=/opt/neovance/venv/bin/gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:8000
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable neovance-backend
sudo systemctl start neovance-backend
```

### Frontend Production Setup

```bash
# Build production bundle
cd frontend/dashboard
npm run build

# Start production server
npm run start
```

Or use PM2:
```bash
npm install -g pm2
pm2 start npm --name "neovance-frontend" -- start
pm2 save
pm2 startup
```

## Monitoring

### Check System Status

```bash
# Backend status
curl http://localhost:8000/docs

# Database connections
psql $DATABASE_URL -c "SELECT count(*) FROM pg_stat_activity WHERE datname='neovance';"

# Recent alerts
psql $DATABASE_URL -c "SELECT alert_id, baby_id, model_risk_score, alert_status FROM alerts ORDER BY timestamp DESC LIMIT 10;"
```

### Log Files

```bash
# Backend logs (if using systemd)
sudo journalctl -u neovance-backend -f

# Frontend logs (if using PM2)
pm2 logs neovance-frontend

# PostgreSQL logs
sudo tail -f /var/log/postgresql/postgresql-13-main.log
```

## Performance Tuning

### PostgreSQL

```sql
-- Add indexes for faster queries
CREATE INDEX idx_alerts_status ON alerts(alert_status);
CREATE INDEX idx_alerts_baby ON alerts(baby_id);
CREATE INDEX idx_alerts_timestamp ON alerts(timestamp);
```

### Backend

```bash
# Use more workers for production
gunicorn -w 8 -k uvicorn.workers.UvicornWorker main:app
```

## Backup Strategy

### Database Backup

```bash
# Daily backup
pg_dump $DATABASE_URL > /backups/neovance_$(date +%Y%m%d).sql

# Restore from backup
psql $DATABASE_URL < /backups/neovance_20260126.sql
```

### Model Backup

```bash
# Backup trained models
cp -r trained_models /backups/trained_models_$(date +%Y%m%d)
```

## Next Steps

1. **Integrate with Hospital EHR** - Connect to existing patient records
2. **Add Authentication** - Implement OAuth2/JWT for secure access
3. **Enable WebSocket Notifications** - Real-time alerts for nurses
4. **Add Explainable AI** - SHAP values for prediction interpretation
5. **Mobile App** - iOS/Android app for on-the-go access
6. **Multi-Hospital Deployment** - Federated learning across institutions

## Support & Resources

- **Documentation**: [HIL_SETUP.md](HIL_SETUP.md)
- **API Reference**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **GitHub Issues**: Report bugs and feature requests
- **Email Support**: support@neovance.com

---

**System Status Legend:**
- ✅ Running correctly
- ⚠️ Running with warnings
- ❌ Not running / Error
- 🔄 Starting up
- 🛑 Stopped

**Last Updated:** January 26, 2026
