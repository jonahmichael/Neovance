# Neovance-AI: NICU Real-Time Monitoring System

AI-Powered Sepsis Detection for Premature Infants

A production-ready real-time monitoring system for Neonatal Intensive Care Units (NICU), featuring live vital signs tracking, comprehensive EHR management, and WebSocket streaming capabilities.

---

## Project Structure

```
Neovance-AI/
├── backend/
│   ├── main.py                     # FastAPI server with comprehensive EHR + WebSocket streaming
│   ├── baby_edit_log.json          # Chain of custody audit trail
│   └── neonatal_ehr.db             # SQLite database (BabyProfile, User, LiveVitals)
│
├── frontend/
│   └── dashboard/                  # Next.js medical dashboard
│       ├── app/
│       │   └── page.tsx            # Main application with routing
│       ├── components/
│       │   ├── BabyList.tsx        # Patient list view
│       │   ├── BabyDetail.tsx      # Patient detail view
│       │   ├── RealTimeChart.tsx   # Live vitals chart
│       │   ├── PatientHistory.tsx  # Historical data table
│       │   ├── ActionPanel.tsx     # Clinical actions + sepsis trigger
│       │   ├── ActionLog.tsx       # Action timeline
│       │   ├── Sidebar.tsx         # Navigation
│       │   └── ui/                 # Reusable UI components
│       └── lib/
│           └── utils.ts            # Utility functions
│
├── data/
│   └── stream.csv                  # Live data stream
│
├── requirements.txt                # Python dependencies
└── README.md                       # This file
```

---

## Quick Start

### Prerequisites
- Python 3.12+
- Node.js 18+
- Virtual environment

### Installation

```bash
# Navigate to project
cd /mnt/d/Neovance-AI

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Install frontend dependencies
cd frontend/dashboard
npm install
```

### Running the System

**Option 1: Complete Pathway Streaming Pipeline (Recommended)**

Start all services at once:
```bash
cd /mnt/d/Neovance-AI
./start_streaming.sh
```

This starts:
1. Pathway Simulator (generates vitals -> CSV stream)
2. Pathway ETL Pipeline (CSV stream -> SQLite database)
3. FastAPI Backend (serves data via REST API + WebSocket)

**Option 2: Manual Start (for development)**

Terminal 1 - Pathway Simulator:
```bash
cd /mnt/d/Neovance-AI/backend
python pathway_simulator.py
```

Terminal 2 - Pathway ETL:
```bash
cd /mnt/d/Neovance-AI/backend
python pathway_etl.py
```

Terminal 3 - FastAPI Backend:
```bash
cd /mnt/d/Neovance-AI
/mnt/d/Neovance-AI/venv/bin/python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Terminal 4 - Frontend:
```bash
cd /mnt/d/Neovance-AI/frontend/dashboard
npm run dev
```

Open **http://localhost:3000** in your browser.

---

## Features

### 1. Pathway Real-Time Streaming Pipeline
- **pathway_simulator.py**: Generates realistic NICU vitals data
- **pathway_etl.py**: Processes CSV stream in real-time
- Writes to SQLite database with streaming processing
- Supports sepsis trigger via file-based signaling
- 3-second data generation interval

### 2. Comprehensive Neonatal EHR System
- 50+ medical record fields per patient
- Patient identification, birth information, measurements
- Physical examinations, lab results, immunizations
- Feeding data, clinical course, discharge planning
- Care team tracking and clinical notes

### 3. Real-Time Vital Signs Monitoring
- Heart Rate (HR), SpO2, Respiratory Rate (RR)
- Temperature, Mean Arterial Pressure (MAP)
- WebSocket streaming for live updates
- Smooth data transitions (no random jumps)

### 4. Chain of Custody Audit Trail
- Blockchain-style immutable logging (SHA256 hashing)
- Tracks all patient record modifications
- Records user ID, timestamp, changes made
- JSON format for easy querying and compliance

### 5. Multi-Patient Management
- 5 pre-loaded patient profiles with Indian names
- Clean card-based list view
- Click to view comprehensive patient details
- Status indicators (NICU/Ward)

### 6. User Authentication
- Doctor and Nurse roles
- Password-based authentication
- Authenticated updates logged to audit trail
- 4 pre-loaded staff users (2 doctors, 2 nurses)

### 7. Sepsis Trigger System
- Controlled 15-second demonstration spike
- Shows realistic vital signs deterioration
- For training and demonstration purposes

---

## API Endpoints

### Patient Records
```
GET  /babies              # List all baby profiles
GET  /baby/{mrn}          # Get specific baby profile
POST /baby/update/{mrn}   # Update baby profile (authenticated)
```

### Vital Signs
```
WS   /ws/live            # WebSocket live stream
GET  /history            # Last 30 minutes
GET  /stats              # Statistics
POST /trigger-sepsis     # Demo sepsis spike
```

### Audit Trail
```
GET  /custody-log        # Complete chain of custody
GET  /custody-log/{mrn}  # Custody log for specific patient
```

### System
```
GET  /                   # Health check
POST /action             # Log clinical action
GET  /docs               # API documentation (FastAPI auto-generated)
```

---

## Dashboard Views

### 1. Real-Time Monitor
- Live Chart.js visualization of vital signs
- 4 statistics cards
- Clinical action logging
- Sepsis trigger button for demonstrations

### 2. All Patients
- Clean card grid of all patient profiles
- Shows MRN, name, DOB, gestational age, birth weight
- Color-coded status badges (NICU/Ward)
- Click any card to view full details

### 3. Patient Details
- Comprehensive 50+ field medical record
- Organized in 14 sections (Identification, Birth Info, Labs, etc.)
- Professional medical record layout
- Back button to return to list

### 4. Vitals History
- Table of last 30 minutes of vital signs
- Auto-refresh every 10 seconds
- Timestamp, vitals, risk score, status

### 5. Action Log
- Clinical intervention timeline
- Categorized events with timestamps

---

## Technology Stack

**Backend:**
- FastAPI 0.104.0
- SQLAlchemy 2.0
- Uvicorn ASGI server
- WebSockets for real-time streaming
- SQLite database

**Frontend:**
- Next.js 16 (App Router)
- TypeScript
- Tailwind CSS (dark mode)
- Chart.js + react-chartjs-2
- axios for HTTP
- lucide-react icons

---

## Sample Data

### Pre-loaded Patients
- 5 baby profiles with Indian names
- Mix of healthy and NICU cases
- Twins included (B003, B004)
- Realistic gestational ages (34-37 weeks)

### Pre-loaded Staff
- DR001: Dr. Rajesh Kumar (Doctor)
- DR002: Dr. Priya Sharma (Doctor)
- NS001: Nurse Anjali Patel (Nurse)
- NS002: Nurse Deepika Singh (Nurse)

All users have password "1234" for testing.

---

## API Usage Examples

### cURL Examples

```bash
# Health check
curl http://localhost:8000/

# Get all babies
curl http://localhost:8000/babies

# Get specific baby
curl http://localhost:8000/baby/B001

# Update baby (authenticated)
curl -X POST http://localhost:8000/baby/update/B001 \
  -H "Content-Type: application/json" \
  -d '{
    "auth": {"user_id": "DR001", "password": "1234"},
    "updates": {"notes": "Patient improving", "discharge_weight": 2.8}
  }'

# Get custody log
curl http://localhost:8000/custody-log

# Trigger sepsis demo
curl -X POST http://localhost:8000/trigger-sepsis
```

### Python Examples

```python
import requests

# Get all babies
response = requests.get("http://localhost:8000/babies")
babies = response.json()

# Update baby profile
response = requests.post(
    "http://localhost:8000/baby/update/B001",
    json={
        "auth": {"user_id": "DR001", "password": "1234"},
        "updates": {"discharge_weight": 2.8}
    }
)
result = response.json()
```

---

## Database Schema

### BabyProfile Table (50+ fields)
- Identification: mrn, full_name, sex, dob, birth_order
- Gestational: gestational_age, apgar scores
- Parents: mother/father names, contacts, blood type
- Measurements: weights, length, circumferences
- Physical Exam: muscle tone, reflexes, skin, fontanelle
- Sensory: hearing, vision screening
- Cardiorespiratory: pulse ox, breathing, heart sounds
- Labs: metabolic, glucose, bilirubin, blood type
- Immunizations: Vit K, Hep B, eye prophylaxis
- Feeding: type, tolerance, output
- Clinical: NICU status, oxygen, medications, procedures
- Risk: maternal infections, delivery, complications
- Discharge: date, weight, instructions
- Team: pediatrician, attending, nursing staff

### User Table
- user_id (PK), full_name, role, password

### LiveVitals Table
- timestamp (PK), mrn (FK), hr, spo2, rr, temp, map, risk_score, status

---

## Troubleshooting

**Backend not starting:**
```bash
# Check if port 8000 is in use
lsof -i :8000

# Use correct Python from venv
/mnt/d/Neovance-AI/venv/bin/python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend not starting:**
```bash
# Check if port 3000 is in use
lsof -i :3000

# Remove lock file if needed
rm -f frontend/dashboard/.next/dev/lock

# Restart
cd frontend/dashboard && npm run dev
```

**Database issues:**
```bash
# Backend will auto-create on first run
# To reset, delete and restart:
rm backend/neonatal_ehr.db
rm backend/baby_edit_log.json
# Restart backend to repopulate
```

**WebSocket connection:**
```bash
# Test with wscat
wscat -c ws://localhost:8000/ws/live
```

---

## License

MIT License

---

Built for NICU medical professionals - Real-time monitoring and comprehensive EHR management
