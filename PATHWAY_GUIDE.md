# Quick Start Guide - Pathway Streaming Integration

## Architecture

```
pathway_simulator.py  →  data/stream.csv  →  pathway_etl.py  →  SQLite  →  FastAPI  →  WebSocket  →  Frontend
     (Generate)            (CSV Stream)        (Process)        (Store)    (Serve)     (Stream)      (Display)
```

## Installation

1. **Install Pathway and dependencies:**
```bash
cd /mnt/d/Neovance-AI
pip install pathway pandas numpy fastapi uvicorn sqlalchemy
```

2. **Install frontend dependencies:**
```bash
cd frontend/dashboard
npm install
```

## Running the Complete System

### Option 1: One Command (Recommended)

```bash
cd /mnt/d/Neovance-AI
./start_streaming.sh
```

This starts all 3 backend services:
- Pathway Simulator (generates data)
- Pathway ETL (processes stream)
- FastAPI Backend (serves API)

Then in a separate terminal, start the frontend:
```bash
cd /mnt/d/Neovance-AI/frontend/dashboard
npm run dev
```

### Option 2: Manual (for debugging)

**Terminal 1 - Pathway Simulator:**
```bash
cd /mnt/d/Neovance-AI/backend
python pathway_simulator.py
```
Output: Generates vitals every 3 seconds to `data/stream.csv`

**Terminal 2 - Pathway ETL:**
```bash
cd /mnt/d/Neovance-AI/backend
python pathway_etl.py
```
Output: Processes CSV stream and writes to database

**Terminal 3 - FastAPI Backend:**
```bash
cd /mnt/d/Neovance-AI
/mnt/d/Neovance-AI/venv/bin/python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```
Output: API server on port 8000

**Terminal 4 - Frontend:**
```bash
cd /mnt/d/Neovance-AI/frontend/dashboard
npm run dev
```
Output: Next.js on port 3000

## Verify It's Working

1. **Check Pathway Simulator:**
```bash
tail -f simulator.log
```
Should show: `[2026-01-26...] MRN:B001 HR:80.5 SpO2:98.2% Risk:0.65 OK`

2. **Check Pathway ETL:**
```bash
tail -f pathway.log
```
Should show: `[PATHWAY] Processed: MRN:B001 HR:80.5 SpO2:98.2% Status:OK`

3. **Check Backend API:**
```bash
curl http://localhost:8000/
```
Should return JSON with status "operational"

4. **Check Frontend:**
Open browser to http://localhost:3000

## Data Flow

1. **pathway_simulator.py** generates realistic vitals with smooth transitions
2. Writes to **data/stream.csv** (append mode, one row per 3 seconds)
3. **pathway_etl.py** reads CSV in streaming mode using Pathway
4. Pathway processes each row and writes to **SQLite database** (live_vitals table)
5. **FastAPI backend** reads from database and serves via:
   - REST API endpoints (GET /history, GET /stats)
   - WebSocket endpoint (WS /ws/live) - pushes latest data every second
6. **Next.js frontend** displays:
   - Live chart from WebSocket
   - Patient profiles from REST API
   - Chain of custody audit trail

## Sepsis Trigger

Click "Trigger Sepsis" button in UI or:
```bash
curl -X POST http://localhost:8000/trigger-sepsis
```

This creates `data/sepsis_trigger.txt` file which pathway_simulator.py monitors.
Simulator then increases HR, decreases SpO2, increases RR for 15 seconds (5 cycles).

## Stopping Services

If started with `./start_streaming.sh`, find PIDs:
```bash
ps aux | grep -E "(pathway_simulator|pathway_etl|uvicorn)"
```

Kill all:
```bash
pkill -f pathway_simulator
pkill -f pathway_etl
pkill -f "uvicorn backend.main"
```

Or use the PIDs shown when you started:
```bash
kill <SIM_PID> <ETL_PID> <API_PID>
```

## Troubleshooting

**No data appearing:**
- Check if pathway_simulator.py is running: `ps aux | grep pathway_simulator`
- Check if CSV is being written: `tail data/stream.csv`
- Check if Pathway ETL is processing: `tail pathway.log`

**Pathway import error:**
```bash
pip install pathway
```

**Database locked error:**
- Stop all services
- Delete `backend/neonatal_ehr.db`
- Restart services

**CSV not found:**
- Make sure to run from /mnt/d/Neovance-AI directory
- Data directory is created automatically

## Key Features of Pathway Integration

1. **Real Streaming:** Uses Pathway's `mode="streaming"` for continuous CSV monitoring
2. **Scalable:** Can handle high-frequency data (currently 3-second intervals)
3. **Processing:** Pathway can do transformations, aggregations, joins in real-time
4. **Persistence:** Writes directly to SQLite via `pw.io.sqlite.write()`
5. **Observable:** Subscribe to changes with `pw.io.subscribe()` for monitoring
