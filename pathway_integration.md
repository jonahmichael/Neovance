# Neovance-AI: Real-time NICU Monitoring System - Implementation Summary

## Project Overview

We built a **real-time neonatal ICU monitoring system** that uses **Pathway** for live data streaming - the core requirement for your hackathon. The system simulates vital signs for NICU patients and streams them through a modern data pipeline to a web dashboard.

---

## Architecture

```
┌─────────────────┐    ┌─────────────┐    ┌──────────────┐    ┌─────────────┐    ┌──────────┐
│ Pathway         │───▶│ CSV Stream  │───▶│ Pathway ETL  │───▶│ SQLite DB   │───▶│ Frontend │
│ Simulator       │    │ (buffer)    │    │ (processing) │    │ (storage)   │    │ (Next.js)│
└─────────────────┘    └─────────────┘    └──────────────┘    └─────────────┘    └──────────┘
     (3s interval)                              ▲                    │
                                                │                    ▼
                                           Pathway              FastAPI + 
                                           Framework            WebSocket
```

---

## Components Implemented

| Component | File | Description |
|-----------|------|-------------|
| **Data Simulator** | `backend/pathway_simulator.py` | Generates realistic NICU vitals (HR, SpO2, RR, Temp, MAP) with smooth transitions every 3 seconds |
| **Pathway ETL** | `backend/pathway_etl.py` | Reads CSV stream using Pathway's `pw.io.csv.read()` in streaming mode, writes to SQLite via `pw.io.subscribe()` |
| **REST API** | `backend/main.py` | FastAPI backend with WebSocket support for real-time updates |
| **Data Stream** | `data/stream.csv` | CSV buffer between simulator and ETL with proper header |
| **Database** | `backend/neonatal_ehr.db` | SQLite with `baby_profiles`, `live_vitals`, `users` tables |
| **Startup Script** | `start_streaming.sh` | Launches all 3 backend services |

---

## Key Pathway Integration

```python
# Pathway streaming pipeline (pathway_etl.py)
vitals_stream = pw.io.csv.read(
    str(self.stream_file),
    schema=VitalsSchema,
    mode="streaming"  # Real-time streaming mode
)

processed = vitals_stream.select(...)
pw.io.subscribe(processed, write_to_db)  # Callback for each new row
pw.run()  # Starts the streaming computation
```

---

## Cleanup Completed

- Removed backup files (`main_old.py`, `main_new.py`, etc.)
- Removed old scripts (`etl_simple.py`, `query_db.py`)
- Removed all emojis from codebase
- Updated `.gitignore` with proper patterns
- Updated `README.md` with Pathway architecture docs

---

## Running the System

```bash
# Terminal 1: Simulator
cd backend && python pathway_simulator.py

# Terminal 2: Pathway ETL
cd backend && python pathway_etl.py

# Terminal 3: FastAPI Backend
cd backend && uvicorn main:app --reload --port 8000

# Terminal 4: Frontend
cd frontend/nicu-dashboard && npm run dev
```

---

## Current Status

| Service | Status | Output |
|---------|--------|--------|
| Simulator | Running | Generating vitals to CSV |
| Pathway ETL | Running | `MRN:B001 HR:80.2 SpO2:98.1%` |
| FastAPI | Running | http://127.0.0.1:8000 |
| Database | Receiving | Live records being inserted |

---

## What Makes This Special for Your Hackathon

1. **Pathway Framework** - Real-time stream processing (your core requirement)
2. **True Streaming** - Not batch processing, actual live data flow
3. **Medical Domain** - NICU vital signs with realistic ranges
4. **Full Stack** - Simulator → ETL → Database → API → WebSocket → Frontend
5. **Sepsis Detection** - Risk scoring and status alerts built-in

The system demonstrates Pathway's power for real-time data processing in a healthcare context.

---

## Technical Details

### Pathway Version
- `pathway==0.29.0`

### Data Schema (VitalsSchema)
```python
class VitalsSchema(pw.Schema):
    timestamp: str
    mrn: str
    hr: float      # Heart Rate (bpm)
    spo2: float    # Oxygen Saturation (%)
    rr: float      # Respiratory Rate (breaths/min)
    temp: float    # Temperature (Celsius)
    map: float     # Mean Arterial Pressure (mmHg)
    risk_score: float
    status: str    # OK, WARNING, CRITICAL
```

### CSV Stream Format
```csv
timestamp,mrn,hr,spo2,rr,temp,map,risk_score,status
2026-01-26T00:51:41.695351,B001,79.5,97.9,16.0,36.96,35.3,0.91,OK
```

### Database Write via Subscribe
```python
def write_to_db(key, row, time, is_addition):
    if is_addition:
        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO live_vitals 
                (timestamp, mrn, hr, spo2, rr, temp, map, risk_score, status, created_at)
                VALUES (...)
            """), {...})
            conn.commit()

pw.io.subscribe(processed, write_to_db)
pw.run()
```

---

## Dependencies

### Backend (Python)
- pathway==0.29.0
- fastapi
- uvicorn
- sqlalchemy
- websockets

### Frontend (Node.js)
- next.js
- typescript
- tailwindcss
- chart.js
