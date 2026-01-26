# Neovance AI HIL System Setup Guide

## PostgreSQL/TimescaleDB Installation

### Option 1: Docker (Recommended)
```bash
# Start PostgreSQL with TimescaleDB
docker run -d --name neovance-db \
  -e POSTGRES_DB=neovance_db \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=password \
  -p 5432:5432 \
  timescale/timescaledb:latest-pg15
```

### Option 2: Native Installation
1. Install PostgreSQL 12+
2. Install TimescaleDB extension
3. Create database: `createdb neovance_db`

## Setup Instructions

### 1. Install HIL Requirements
```bash
cd /mnt/d/Neovance-AI
source venv/bin/activate
pip install -r requirements_hil.txt
```

### 2. Set Environment Variables
```bash
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=neovance_db
export DB_USER=postgres
export DB_PASSWORD=password
```

### 3. Initialize Database
```bash
python backend/setup_database.py
```

Expected output:
```
🏥 NEOVANCE AI - HIL SYSTEM DATABASE SETUP
==========================================
=== Step 1: Database Creation ===
✓ Database 'neovance_db' created successfully

=== Step 2: TimescaleDB Setup ===
✓ TimescaleDB extension enabled

=== Step 3: Schema Creation ===
✓ Database schema created successfully

=== Step 4: Hypertable Creation ===
✓ Created hypertable: alerts
✓ Created hypertable: realtime_vitals

=== Verifying Database Setup ===
✓ Database connection successful
✓ TimescaleDB extension enabled
✓ Table 'alerts' created
✓ Table 'outcomes' created
✓ Table 'realtime_vitals' created
✓ Table 'babies' created
✓ Hypertable 'alerts' created
✓ Hypertable 'realtime_vitals' created

🎉 HIL Database Setup Complete!
```

### 4. Start HIL Backend
```bash
python backend/main_hil.py
```

### 5. Start PostgreSQL ETL Pipeline
```bash
python backend/pathway_etl_postgresql.py
```

## HIL System Architecture

### Core Tables

1. **alerts** (TimescaleDB Hypertable)
   - Core HIL table storing AI predictions + doctor actions
   - `features_json`: Complete patient state snapshot for ML
   - Partitioned by timestamp for high performance

2. **outcomes** (Standard Table)
   - Delayed reward signals (sepsis confirmed/not confirmed)
   - Links back to alerts for supervised learning

3. **realtime_vitals** (TimescaleDB Hypertable)
   - High-frequency time-series vitals from Pathway
   - Real-time monitoring data

4. **babies** (Standard Table)
   - Patient demographics and clinical context

### HIL Workflow

1. **Real-time Monitoring**: Pathway ETL streams vitals to `realtime_vitals`
2. **AI Prediction**: System calculates EOS risk scores
3. **Doctor Action**: Doctor takes action via UI
4. **HIL Logging**: Action + patient state → `alerts` table
5. **Outcome Collection**: Lab results → `outcomes` table
6. **Supervised Learning**: Train models on `alerts` + `outcomes`

## API Endpoints

- **POST /hil/doctor_action**: Log doctor decisions with patient state
- **POST /hil/outcome**: Log delayed outcomes for learning
- **GET /hil/training_data**: Retrieve HIL dataset for ML
- **GET /hil/analytics/doctor_performance**: Performance metrics
- **GET /hil/health**: System health check

## Testing HIL System

### 1. Log a Doctor Action
```bash
curl -X POST "http://localhost:8000/hil/doctor_action" \
  -H "Content-Type: application/json" \
  -d '{
    "timestamp": "2026-01-26T08:00:00Z",
    "mrn": "B001",
    "risk_score": 2.5,
    "features_json": {},
    "doctor_id": "DR001",
    "doctor_action": "Treat",
    "action_detail": "Ampicillin + Gentamicin"
  }'
```

### 2. Log Outcome
```bash
curl -X POST "http://localhost:8000/hil/outcome" \
  -H "Content-Type: application/json" \
  -d '{
    "alert_id": 1,
    "outcome_time": "2026-01-26T14:00:00Z",
    "sepsis_confirmed": false,
    "lab_result": "Blood culture negative",
    "patient_status_6hr": "Improved"
  }'
```

### 3. Get Training Data
```bash
curl "http://localhost:8000/hil/training_data?limit=10"
```

## Migration from SQLite

The system maintains backward compatibility. To migrate:

1. Run HIL setup (above steps)
2. Export data from SQLite: `python migrate_to_postgresql.py`
3. Update frontend to use new endpoints
4. Switch to HIL backend: `python backend/main_hil.py`

## Production Considerations

1. **Security**: Use environment variables for database credentials
2. **Performance**: Configure PostgreSQL connection pooling
3. **Monitoring**: Set up TimescaleDB monitoring and retention policies
4. **Backup**: Implement automated PostgreSQL backups
5. **Scaling**: Use read replicas for analytics queries