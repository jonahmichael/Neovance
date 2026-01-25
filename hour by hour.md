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
numpy>=1.24.0
click>=8.1
beartype>=0.14.0
diskcache>=5.2.1
typing-extensions>=4.8.0
opentelemetry-api>=1.22.0
opentelemetry-sdk>=1.22.0
opentelemetry-exporter-otlp-proto-grpc>=1.22.0
# Note: SQLite is built into Python, no additional packages needed
```

#### Next Steps Planned:
- ~~Test simulator with Pathway data pipeline~~ ✓ COMPLETED
- ~~Monitor CSV file growth and performance~~ ✓ COMPLETED
- ~~Validate real-time data streaming~~ ✓ COMPLETED
- ~~Implement weighted deviation risk formula~~ ✓ COMPLETED
- ~~Calculate live statistics from SQL~~ ✓ COMPLETED
- Implement ML model for sepsis prediction (replace formula-based scoring)
- Add real-time alerting system based on risk thresholds
- Consider adding more patient profiles (Baby_B, Baby_C)
- Build data visualization dashboard
- Add multi-patient support
- Implement alert notification system
- Add historical trend analysis and pattern detection

---

### Hour 5-9: Pathway Streaming & The Math (The "Brain")
**Time:** [Current Session]  
**Status:** COMPLETED

*Goal: Implement the Continuous Deviation Risk Formula with Real-Time Statistics*

#### Hour 5-6: Pathway File Setup & SQLite Integration

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

3. **Initial Risk Score (Placeholder)**
   - Simple formula: `risk_score = (HR + SpO2) / 2`
   - Baseline metric for proof-of-concept
   - **Replaced in Hour 6-9 with sophisticated formula**

#### Hour 6-9: Implementing the Weighted Deviation Risk Formula

**The Formula:**
```
Risk = W_hr · (|HR - 145| / σ_hr)^P_hr + W_spo2 · (|SpO2 - 95| / σ_spo2)^P_spo2 + ...
```

Where:
- **μ (mu)** = Ideal Baseline for 28-week premature infant
- **σ (sigma)** = Standard Deviation from **live SQL data** (60-minute rolling window)
- **W** = Weight (relative importance of vital)
- **P** = Power (sensitivity: linear vs exponential penalty)

**Clinical Parameters Configured:**

| Vital | Ideal (μ) | Weight (W) | Power (P) | Reasoning |
|-------|-----------|------------|-----------|-----------|
| **HR** | 145 bpm | 1.0 | 2 | Bradycardia = #1 sign of apnea |
| **SpO2** | 95% | **3.0** | **4** | **THE KILLER METRIC** - Exponential penalty for desaturation |
| **RR** | 50 bpm | 1.5 | 2 | High variability precedes critical events |
| **Temp** | 37.0°C | 1.0 | 3 | Hypothermia = silent killer in preemies |
| **MAP** | 35 mmHg | 2.0 | 2 | Perfusion pressure ≈ Gestational Age |

**Live Statistics from SQL:**
- Function: `get_live_statistics(patient_id, window_minutes=60)`
- Queries last 60 minutes of patient data from `risk_monitor` table
- Calculates real standard deviations (σ) for each vital sign
- Dynamic normalization adapts to patient-specific variability
- Falls back to default clinical σ values if insufficient data (<2 records)

**Default Standard Deviations (Clinical):**
- HR: ±15 bpm (120-170 range)
- SpO2: ±2.5% (90-97.5 range)
- RR: ±10 bpm (40-60 range)
- Temp: ±0.5°C (36.5-37.5 range)
- MAP: ±5 mmHg (30-40 range)

**Risk Thresholds:**
- **OK**: Risk ≤ 10
- **WARNING**: 10 < Risk ≤ 20
- **CRITICAL**: Risk > 20

**Implementation Details:**
- Created `calculate_risk_score()` with live SQL statistics
- Added numpy for statistical calculations
- Updated `etl_simple.py` for lightweight processing (Pathway was slow to load)
- Processes CSV every minute instead of real-time streaming
- Formula validated with `test_risk_formula.py`

**Neonatal Sepsis Clinical Criteria (Monitored):**
- **Temperature instability**: >38°C (fever) or <36°C (hypothermia)
- **Tachycardia**: >160-180 bpm
- **Bradycardia**: <100 bpm (critical)
- **Respiratory distress**: Apnea, tachypnea (>80/min), low RR (<20/min)
- **Critical SpO2**: <85% (severe desaturation)

#### Files Created/Modified:
- `etl.py` (Pathway streaming pipeline - original version)
- `etl_simple.py` (Lightweight ETL with risk formula - **ACTIVE VERSION**)
- `test_risk_formula.py` (Formula validation and testing)
- `query_db.py` (Database query utility)
- `quick_check.py` (Fast database inspection)
- `.gitignore` (Patient data protection)
- `requirements.txt` (Added numpy for statistics)
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
    risk_score REAL NOT NULL,  -- Weighted deviation-based score
    status TEXT NOT NULL,       -- OK / WARNING / CRITICAL
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Complete Data Flow:
```
┌─────────────────┐
│  simulator.py   │  Generates vitals every 1 sec
│   (Baby_A)      │  HR, SpO2, RR, Temp, MAP
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ data/stream.csv │  Live CSV stream (gitignored)
└────────┬────────┘
         │ (Reads every 60 seconds)
         ▼
┌─────────────────┐
│ etl_simple.py   │  ├─ Queries SQL for last 60min data
│                 │  ├─ Calculates live σ (std dev)
│                 │  ├─ Applies weighted risk formula
│                 │  │   Risk = Σ W·(|X-μ|/σ)^P
│                 │  └─ Assigns status
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ data/neovance.db│  SQLite database (gitignored)
│  risk_monitor   │  ├─ All 5 vitals
│     table       │  ├─ risk_score (0-800+)
└────────┬────────┘  └─ status
         │
         ▼
┌─────────────────┐
│  query_db.py    │  SELECT * queries
│                 │  Statistics & trends
└─────────────────┘
```

#### Live Results (Validated):
**Perfect Vitals:**
- HR:145 SpO2:95 RR:50 Temp:37.0 MAP:35 → Risk: **0.00** ✅

**Normal Range:**
- HR:146 SpO2:96% → Risk: **0.71** (OK) ✅
- HR:145 SpO2:97% → Risk: **0.82** (OK) ✅

**Critical Deviations:**
- HR:144 SpO2:100% → Risk: **48.18** (CRITICAL) ⚠️
- HR:180 SpO2:85% → Risk: **791.36** (CRITICAL) ⚠️⚠️⚠️

*Note: SpO2=100% triggers CRITICAL because it's 5% above ideal (95%). The power-4 exponential penalty catches both high AND low deviations.*

#### Technical Decisions:
- **SQLite over PostgreSQL:** Simpler setup, file-based, no server required
- **Live Statistics:** Calculate σ from actual patient data (60-min window) instead of static values
- **Pathway's `pw.io.subscribe()`:** Cleaner than `ConnectorSubject` classes
- **Lightweight ETL:** Created `etl_simple.py` because Pathway took too long to load (~30+ seconds)
- **Minimal Dependencies:** Only core libs + numpy for statistics
- **Non-linear Penalties:** Power functions (P=2,3,4) to exponentially penalize dangerous deviations
- **SpO2 Priority:** Weight=3.0 and Power=4 because desaturation is the #1 killer metric

#### Usage:
```bash
# Terminal 1: Start simulator
venv/bin/python simulator.py

# Terminal 2: Start ETL pipeline (lightweight version)
venv/bin/python etl_simple.py

# Terminal 3: Query database
venv/bin/python query_db.py
venv/bin/python query_db.py latest 20

# Test formula independently
venv/bin/python test_risk_formula.py
```

#### What Makes This Special:
1. 🎯 **Clinically Grounded** - Based on actual NICU protocols for 28-week preemies
2. 📊 **Dynamic σ** - Standard deviations calculated from live patient data (not hardcoded)
3. 🚨 **Non-Linear** - SpO2 with power of 4 catches critical desaturation exponentially
4. ⚡ **Real-Time** - Updates every minute with streaming data
5. 🔒 **Privacy** - All patient data protected by .gitignore
6. 🪶 **Lightweight** - No heavy ML frameworks, just numpy + SQLite

---

## Notes and Observations

### Design Considerations:
- **Why 1-second intervals?** Balance between real-world simulation and system performance
- **Why CSV format?** Simple, human-readable, compatible with Pathway streaming
- **Why keyboard library initially?** Enables live mode switching during demonstrations without GUI overhead (later replaced with threading + select for Linux compatibility)
- **Why SQLite over PostgreSQL?** File-based, no server setup, perfect for single-machine prototypes
- **Why live σ calculations?** Patient-specific variability is more accurate than population averages
- **Why SpO2 gets Power=4?** Desaturation is non-linear - a 5% drop is far more critical than it appears
- **Why 60-minute window?** Balance between having enough data for statistics and catching recent trends

### Potential Future Enhancements:
1. **Multi-patient simulation** (Baby_A, Baby_B, Baby_C) - Currently only Baby_A
2. **Additional pathological states** (apnea episodes, bradycardia events)
3. **Configuration file** for baseline values and thresholds
4. **Web dashboard** for real-time visualization (plotly/streamlit)
5. **ML model integration** for anomaly detection and sepsis prediction
6. **Alert notification system** (email/SMS/webhook when CRITICAL status)
7. **Data replay functionality** from historical CSV for training/testing
8. **Synthetic noise patterns** based on medical literature
9. **Absolute threshold alerts** (e.g., SpO2 <85%, Temp <36°C regardless of risk score)
10. **Trend analysis** - detect patterns over time (deteriorating vs improving)
11. **Multi-modal alerts** - combine risk score with absolute thresholds for comprehensive monitoring

---

## Last Updated
**Date:** January 25, 2026 - Hour 5-9: Weighted Deviation Risk Formula Complete  
**Status:** Core functionality operational - Real-time monitoring with sophisticated risk scoring active

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
