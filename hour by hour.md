# Neovance-AI: Hour-by-Hour Development Timeline

This document tracks the detailed progress of the Neovance-AI NICU monitoring system development, providing a comprehensive timeline beyond git commit history.

---

## Project Overview
**Project Name:** Neovance-AI  
**Purpose:** Real-time NICU monitoring system for premature babies  
**Start Date:** January 25, 2026  

---

## Development Timeline

### Hour 1: Initial Setup and Core Simulator Development
**Time:** [Current Session Start]  
**Status:** COMPLETED

#### Tasks Completed:
1. **Project Initialization**
   - Created project structure at `d:\Neovance-AI`
   - Established README.md foundation

2. **Simulator Script Development (`simulator.py`)**
   - Implemented `NICUSimulator` class with state machine architecture
   - Created two operational modes:
     - **NORMAL Mode:** Stable vitals with Gaussian noise
     - **SEPSIS Mode:** Deteriorating vitals with continuous drift logic
   
3. **Core Features Implemented:**
   - Real-time data generation (1-second intervals)
   - CSV file output to `data/stream.csv`
   - Automatic header creation on first run
   - File buffer flushing after every write (critical for real-time pipeline)
   - Keyboard-based mode switching:
     - Press 's' → SEPSIS mode
     - Press 'n' → NORMAL mode
   
4. **Patient Configuration:**
   - Patient ID: "Baby_A"
   - Baseline vitals configured:
     - HR (Heart Rate): 145 bpm
     - SpO2 (Oxygen Saturation): 98%
     - RR (Respiratory Rate): 50 breaths/min
     - Temp (Temperature): 37.0°C
     - MAP (Mean Arterial Pressure): 35 mmHg

5. **Safety Mechanisms:**
   - SpO2 floor limit: 40% (prevents death scenario)
   - HR ceiling limit: 220 bpm (prevents unrealistic values)
   - Temperature floor: 35.0°C (hypothermia protection)

6. **Sepsis Drift Logic:**
   - HR increases: +1 bpm per second
   - SpO2 decreases: -0.5% per second
   - Temperature decreases: -0.02°C per second
   - RR variability increased (respiratory distress simulation)

7. **Code Refinement:**
   - Removed all emoji characters for professional output
   - Implemented clean logging with prefixes: `[INFO]`, `[ALERT]`, `[NORMAL]`, `[SEPSIS]`
   - Added comprehensive docstrings and comments

#### Technical Decisions:
- **Library Choice:** Used `keyboard` library for non-blocking input
- **Data Format:** CSV with ISO timestamp format
- **File I/O:** Append mode with immediate flush for real-time visibility
- **State Management:** Object-oriented approach with drift accumulators

#### Files Created:
- `simulator.py` (Main data generation script)
- `hour by hour.md` (This timeline document)

#### Dependencies Required:
```
pandas>=2.0.0
click>=8.1
beartype>=0.14.0
diskcache>=5.2.1
typing-extensions>=4.8.0
opentelemetry-api>=1.22.0
opentelemetry-sdk>=1.22.0
opentelemetry-exporter-otlp-proto-grpc>=1.22.0
# Note: SQLite is built into Python
```

#### Next Steps Planned:
- ~~Test simulator with Pathway data pipeline~~ ✓ COMPLETED
- ~~Monitor CSV file growth and performance~~ ✓ COMPLETED
- ~~Validate real-time data streaming~~ ✓ COMPLETED
- Implement ML model for sepsis prediction (replace simple risk_score)
- Add real-time alerting system based on risk thresholds
- Consider adding more patient profiles (Baby_B, Baby_C)
- Build data visualization dashboard
- Add multi-patient support
- Implement alert notification system

---

## Notes and Observations

### Hour 5-6: Pathway ETL Pipeline with SQLite Integration
**Time:** [Current Session]  
**Status:** COMPLETED

#### Tasks Completed:
1. **Pathway ETL Pipeline (`etl.py`)**
   - Created streaming ETL using Pathway framework
   - Implemented `pw.io.csv.read()` with `mode="streaming"` to watch `data/stream.csv`
   - Set `autocommit_duration_ms=1000` for 1-second polling
   - Configured `InputSchema` for strict type validation

2. **SQLite Database Integration**
   - Database: `data/neovance.db` (auto-created on first run)
   - Table: `risk_monitor` with patient vitals and calculated metrics
   - Implemented `write_to_sqlite()` function using `pw.io.subscribe()`
   - Added `INSERT OR IGNORE` for duplicate prevention (timestamp as primary key)

3. **Risk Score Calculation**
   - Formula: `risk_score = (HR + SpO2) / 2`
   - Simple baseline metric for proof-of-concept
   - Future: Replace with trained ML model for sepsis prediction

4. **Database Query Utility (`query_db.py`)**
   - Implemented `SELECT *` functionality to view all records
   - Added `latest N` command to show recent records
   - Statistics: Min/Max/Avg risk scores and time ranges
   - Clean output without emojis

5. **Data Security**
   - Created `.gitignore` to protect patient data
   - Excluded: `data/neovance.db`, `data/stream.csv`
   - Ensures sensitive patient data never committed to git

6. **Complete Data Flow:**
   ```
   simulator.py → stream.csv → Pathway → SQLite table → SELECT *
   ```

#### Technical Decisions:
- **SQLite over PostgreSQL:** Simpler setup, file-based, no server required
- **Pathway's `pw.io.subscribe()`:** Cleaner than `ConnectorSubject` classes
- **Minimal Dependencies:** Only core Pathway libs, no heavy cloud/ML extras
- **Real-time Processing:** 1-second latency from data generation to database

#### Files Created/Modified:
- `etl.py` (Pathway streaming pipeline)
- `query_db.py` (Database query utility)
- `.gitignore` (Patient data protection)
- `requirements.txt` (Minimal dependencies)
- `README.md` (Complete documentation)

#### Database Schema:
```sql
CREATE TABLE risk_monitor (
    timestamp TEXT PRIMARY KEY,
    patient_id TEXT NOT NULL,
    hr REAL NOT NULL,
    spo2 REAL NOT NULL,
    rr REAL NOT NULL,
    temp REAL NOT NULL,
    map REAL NOT NULL,
    risk_score REAL NOT NULL,
    status TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Usage:
```bash
# Terminal 1: Start simulator
venv/bin/python simulator.py

# Terminal 2: Start ETL pipeline
venv/bin/python etl.py

# Terminal 3: Query database
venv/bin/python query_db.py
venv/bin/python query_db.py latest 20
```

---

## Notes and Observations

### Design Considerations:
- **Why 1-second intervals?** Balance between real-world simulation and system performance
- **Why CSV format?** Simple, human-readable, compatible with Pathway streaming
- **Why keyboard library?** Enables live mode switching during demonstrations without GUI overhead

### Potential Future Enhancements:
1. Multi-patient simulation (Baby_A, Baby_B, Baby_C)
2. Additional pathological states (apnea, bradycardia)
3. Configuration file for baseline values
4. Web dashboard for real-time visualization
5. Integration with ML model for anomaly detection
6. Alert thresholds with notification system
7. Data replay functionality from historical CSV
8. Synthetic noise patterns based on medical literature

---

## Session Log Format

Each session entry should include:
- **Time:** Hour marker or timestamp
- **Status:** COMPLETED | IN PROGRESS | BLOCKED | PLANNED
- **Tasks Completed:** Bullet list of what was accomplished
- **Technical Decisions:** Key architectural or implementation choices
- **Files Modified/Created:** List of changed files
- **Blockers/Issues:** Any problems encountered
- **Next Steps:** What to work on next

---

*Last Updated: January 25, 2026 - Hour 5-6: SQLite Integration Complete*
