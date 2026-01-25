# Quick Reference: Complete Data Flow

## The Pipeline

```
simulator.py → stream.csv → Pathway → SQLite table → SELECT *
```

### 1. Start Data Generation
```bash
venv/bin/python simulator.py
```
- Generates vitals every 1 second
- Writes to `data/stream.csv`
- Press `s` + ENTER for SEPSIS mode
- Press `n` + ENTER for NORMAL mode

### 2. Start ETL Processing
```bash
venv/bin/python etl.py
```
- Monitors `data/stream.csv` in real-time
- Calculates risk_score = (HR + SpO2) / 2
- Inserts into `data/neovance.db` → `risk_monitor` table
- Prints: `[DB WRITE] timestamp | Patient | HR | SpO2 | Risk`

### 3. Query Results (SELECT *)
```bash
# All records
venv/bin/python query_db.py

# Latest 20 records  
venv/bin/python query_db.py latest 20

# Direct SQL
sqlite3 data/neovance.db "SELECT * FROM risk_monitor;"
```

## Data Security
- ✅ `data/neovance.db` - In .gitignore (patient data)
- ✅ `data/stream.csv` - In .gitignore (patient data)
- ✅ Database auto-created on first run
- ✅ Duplicate prevention with `INSERT OR IGNORE`

## Schema
```sql
CREATE TABLE risk_monitor (
    timestamp TEXT PRIMARY KEY,
    patient_id TEXT,
    hr REAL,
    spo2 REAL,
    rr REAL,
    temp REAL,
    map REAL,
    risk_score REAL,    -- Calculated: (HR + SpO2) / 2
    status TEXT,         -- Currently: "OK"
    created_at TIMESTAMP
);
```

## Example Output
```
📊 Total Records: 80

TIMESTAMP                    PATIENT    HR    SPO2  RR    TEMP   MAP   RISK   STATUS  
2026-01-25T18:48:55.347027   Baby_A     139   99    52    37.2   38    119.0  OK
2026-01-25T18:48:54.338644   Baby_A     143   98    52    36.5   36    120.6  OK

📈 Statistics:
  Risk Score: Min=116.2, Max=128.4, Avg=122.0
  Time Range: 2026-01-25T18:47:35 → 2026-01-25T18:48:55
```
