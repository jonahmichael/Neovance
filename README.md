# Neovance-AI: NICU Real-Time Monitoring System

AI-Powered Sepsis Detection for Premature Infants

A production-ready real-time monitoring system for Neonatal Intensive Care Units (NICU), featuring live vital signs tracking, weighted deviation-based risk scoring, and WebSocket streaming capabilities.

---

## Project Structure

```
Neovance-AI/
├── backend/                    # Backend Python services
│   ├── main.py                # FastAPI server with WebSocket streaming
│   ├── simulator.py           # NICU vitals data generator
│   ├── etl_simple.py         # Lightweight ETL pipeline
│   └── query_db.py           # Database query utilities
│
├── frontend/                   # Frontend applications
│   └── dashboard/             # Next.js medical dashboard
│       ├── app/               # Next.js app directory
│       ├── components/        # React components
│       └── lib/               # Utility functions
│
├── data/                       # Data storage (gitignored)
│   ├── stream.csv            # Live CSV stream
│   ├── neovance.db           # ETL pipeline database
│   └── realtime_data.db      # FastAPI database
│
├── requirements.txt            # Python dependencies
└── README.md                  # This file
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

**Terminal 1 - Backend:**
```bash
cd backend
python main.py
# Runs on http://localhost:8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend/dashboard
npm run dev
# Runs on http://localhost:3000
```

Open **http://localhost:3000** in your browser.

---

## Core Features

### 1. Real-Time Vital Signs Monitoring
- Heart Rate (HR): Target 80 bpm
- SpO2: Target 98%
- Respiratory Rate (RR): Target 16 breaths/min
- Temperature: Target 37.0°C
- Mean Arterial Pressure (MAP): Target 35 mmHg

### 2. Smooth Data Generation
- Realistic vital signs with gradual transitions
- Base values drift smoothly rather than random jumps
- More accurate simulation of real patient data

### 3. Sepsis Simulation
- Controlled deterioration for demonstrations
- 15-second spike cycle (5 data points)
- Realistic sepsis pattern: HR up, SpO2 down, RR up
- Triggered via button in UI or API endpoint

### 4. Risk Assessment
```
Risk Score = Weighted deviation from normal baseline

Thresholds:
- OK: ≤ 10
- WARNING: 10-20
- CRITICAL: > 20
```

### 5. API Endpoints
```
GET  /                    # Health check
WS   /ws/live            # WebSocket live stream
GET  /history            # Last 30 minutes
GET  /stats              # Statistics
POST /action             # Log clinical action
POST /trigger-sepsis     # Demo sepsis spike
GET  /docs               # API documentation
```

---

## Dashboard Features

### Real-Time Monitor
- Live Chart.js visualization
- 4 statistics cards
- Clinical action logging
- Sepsis trigger button

### Patient History
- 30-minute data table
- Auto-refresh every 10 seconds
- Color-coded status badges

### Action Log
- Clinical intervention timeline
- Categorized events

---

## Sepsis Demonstration

For hackathon demos and training:

1. Click "Trigger Sepsis Spike (15s Demo)" in Action Panel
2. Observe vital deterioration over 15 seconds
3. Risk score rises to CRITICAL
4. System maintains or recovers from critical state

---

## Technology Stack

**Backend:**
- FastAPI 0.104.0+
- SQLAlchemy 2.0+
- Uvicorn
- WebSockets
- SQLite

**Frontend:**
- Next.js 16+
- TypeScript
- Tailwind CSS
- Chart.js
- axios
- lucide-react

---

## API Usage

### cURL Examples

```bash
# Health check
curl http://localhost:8000/

# History
curl http://localhost:8000/history

# Trigger sepsis
curl -X POST http://localhost:8000/trigger-sepsis

# Log action
curl -X POST http://localhost:8000/action \
  -H "Content-Type: application/json" \
  -d '{"patient_id":"Baby_A","action":"Oxygen adjusted"}'
```

### Python Examples

```python
import requests

# Get history
response = requests.get("http://localhost:8000/history")
data = response.json()

# Trigger sepsis
response = requests.post("http://localhost:8000/trigger-sepsis")
print(response.json())
```

---

## Configuration

### Backend
Edit `backend/main.py`:
- Database connection
- CORS settings
- Data generation parameters
- Risk thresholds

### Frontend
Edit `frontend/dashboard/components/`:
- API URLs
- Chart settings
- Theme colors
- Refresh intervals

---

## Troubleshooting

**Backend issues:**
```bash
curl http://localhost:8000/
wscat -c ws://localhost:8000/ws/live
```

**Port conflicts:**
```bash
# Backend: Edit main.py port
# Frontend: Edit package.json dev script
```

**Database reset:**
```bash
rm backend/realtime_data.db
python backend/main.py
```

---

## License

MIT License

---

**Built for NICU medical professionals**
