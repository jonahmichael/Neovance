# Neovance-AI: Real-Time NICU Monitoring System

A real-time data streaming system for NICU patient monitoring, featuring:
- Live physiological data simulation (HR, SpO2, RR, Temp, MAP)
- Pathway-based streaming ETL pipeline
- SQLite database for data persistence
- NORMAL/SEPSIS mode switching for testing early detection algorithms

## Architecture

```
[Simulator] → [CSV Stream] → [Pathway ETL] → [SQLite DB]
simulator.py   data/stream.csv    etl.py      data/neovance.db
                                               risk_monitor table
```

**Complete Data Flow:**
1. **simulator.py** → Generates patient vitals every second → **data/stream.csv**
2. **data/stream.csv** → Monitored by **Pathway** (streaming mode, 1-second polling)
3. **Pathway** → Calculates `risk_score = (HR + SpO2) / 2` → **SQLite table**
4. **SQLite table** → Query with `SELECT *` via **query_db.py**

**Note:** Database contains sensitive patient data and is in `.gitignore`

## Quick Start

### 1. Install Dependencies

```bash
# Install Pathway with minimal dependencies
pip install pathway --no-deps
pip install -r requirements.txt
```

**Note:** SQLite is built into Python - no additional database setup needed!

### 2. Run Simulator

```bash
python simulator.py
# or with venv
venv/bin/python simulator.py
```

**Controls:**
- Type `s` + ENTER → Switch to SEPSIS mode
- Type `n` + ENTER → Switch to NORMAL mode  
- Ctrl+C → Stop

### 3. Run Streaming Pipeline

**Terminal 1 - Start Simulator:**
```bash
python simulator.py
```

**Terminal 2 - Start Pathway ETL:**
```bash
python etl.py
```

You should see:
```
[DB WRITE] 2026-01-25T18:30:45.123456 | Patient: Baby_A | HR: 145 | SpO2: 98% | Risk: 121.5
```

### 4. Query Database (SELECT *)

**View all records:**
```bash
python query_db.py
```

**View latest N records:**
```bash
python query_db.py latest 20
```

**Direct SQL:**
```bash
sqlite3 data/neovance.db "SELECT * FROM risk_monitor ORDER BY timestamp DESC LIMIT 10;"
```

**Output shows:**
- Timestamp, Patient ID, HR, SpO2, RR, Temp, MAP
- Calculated Risk Score
- Status and statistics

**Terminal 3 - Monitor Database (Optional):**
```bash
# Check row count
sudo -u postgres psql -d neovance_db -c "SELECT COUNT(*) FROM risk_monitor;"

# View latest records
sudo -u postgres psql -d neovance_db -c "SELECT * FROM risk_monitor ORDER BY timestamp DESC LIMIT 5;"
```

## Data Schema

### CSV Input Schema

| Field | Type | Description |
|-------|------|-------------|
| timestamp | ISO string | Measurement time |
| patient_id | string | Patient identifier (e.g., "Baby_A") |
| hr | float | Heart Rate (bpm) |
| spo2 | float | Oxygen Saturation (%) |
| rr | float | Respiratory Rate (breaths/min) |
| temp | float | Body Temperature (°C) |
| map | float | Mean Arterial Pressure (mmHg) |

### PostgreSQL Output Schema

All input fields plus:
- `risk_score` (float): Calculated as `(HR + SpO2) / 2`
- `status` (string): Currently "OK" (placeholder for alert logic)
- `created_at` (timestamp): Automatic insertion timestamp

## Simulator Modes

### NORMAL Mode
- Stable vitals with small Gaussian noise
- HR: 145 ± 5 bpm
- SpO2: 98 ± 1%
- Temp: 37.0 ± 0.2°C

### SEPSIS Mode
- Progressive deterioration:
  - HR increases by ~1 bpm/sec
  - SpO2 decreases by ~0.5%/sec
  - Temperature drift (hypothermia)
  - Respiratory distress (increased variability)

## Pathway Streaming Configuration

The ETL pipeline uses Pathway's streaming mode with PostgreSQL sink:
- **Input**: `data/stream.csv`
- **Mode**: Streaming (monitors file for changes)
- **Poll Interval**: 1 second (`autocommit_duration_ms=1000`)
- **Schema**: Strictly typed with `InputSchema`
- **Processing**: Calculates `risk_score = (hr + spo2) / 2`
- **Output**: PostgreSQL table `risk_monitor` via custom Python sink
- **Conflict Handling**: `ON CONFLICT (timestamp) DO NOTHING`

## Files with PostgreSQL sink
- `run_streaming.py` - Automated test runner for full pipeline
- `setup_database.sql` - PostgreSQL schema setup
- `setup_database.sh` - Automated database setup script
- `data/stream.csv` - Live data stream (created automatically)
- `requirements.txt` - Minimal Python dependencies
- `POSTGRESQL_SETUP.md` - Detailed PostgreSQL integration guide
- `etl.py` - Pathway streaming ETL pipeline
- `run_streaming.py` - Automated test runner for full pipeline
- `data/stream.csv` - Live data stream (created automatically)

## Troubleshooting

### No Root Required
The simulator **does not require sudo**. It uses a thread-based input listener instead of system keyboard hooks.

### Pathway Not Detecting Changes
- Verify `mode="streaming"` in `etl.py`
- Check `autocommit_duration_ms` setting
- Ensure CSV file is being written with `f.flush()`

- Check for `[DB WRITE]` messages in ETL console
- Query database: `sudo -u postgres psql -d neovance_db -c "SELECT COUNT(*) FROM risk_monitor;"`

###✓ ~~Add PostgreSQL output sink~~ **COMPLETE**
2. Replace simple risk_score with ML model for sepsis prediction
3. Implement real-time alerts based on risk thresholds
4. Add data visualization dashboard (Grafana/custom)
5. Multi-patient support with separate monitoring
6. Add alert notification system (email/SMS)tgresql

# Verify database exists
sudo -u postgres psql -l | grep neovance_db

# Check table exists
sudo -u postgres psql -d neovance_db -c '\d risk_monitor'
```

See [POSTGRESQL_SETUP.md](POSTGRESQL_SETUP.md) for detailed troubleshooting.
### Data Not Appearing
- Check `data/stream.csv` exists and has recent timestamps
- Verify simulator is running in background
- Ensure ETL pipeline shows "watching" message

## Next Steps

1. Add ML model for sepsis prediction
2. Implement real-time alerts/notifications
3. Add data visualization dashboard
4. Multi-patient support
