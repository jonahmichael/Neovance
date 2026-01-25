"""
Neovance-AI: Real-time NICU Data Pipeline
Streaming ETL pipeline using Pathway framework to ingest live patient vitals,
calculate weighted deviation-based risk scores using live statistics,
and write to SQLite database.
"""

import pathway as pw
import sqlite3
from pathlib import Path
import numpy as np
from datetime import datetime, timedelta


class InputSchema(pw.Schema):
    """Schema for incoming patient vital signs data."""
    timestamp: str
    patient_id: str
    hr: float
    spo2: float
    rr: float
    temp: float
    map: float


# SQLite database configuration
DB_PATH = Path("data/neovance.db")

# Clinical Parameters for 28-week Premature Infant
# Based on evidence-based neonatal care guidelines
RISK_PARAMS = {
    'hr': {
        'mu': 145.0,      # Ideal baseline (bpm)
        'weight': 1.0,    # Relative importance
        'power': 2,       # Sensitivity (linear penalty)
    },
    'spo2': {
        'mu': 95.0,       # Ideal baseline (%)
        'weight': 3.0,    # THE KILLER METRIC - heavily weighted
        'power': 4,       # Exponential penalty for desaturation
    },
    'rr': {
        'mu': 50.0,       # Ideal baseline (breaths/min)
        'weight': 1.5,    # High variability precedes events
        'power': 2,
    },
    'temp': {
        'mu': 37.0,       # Ideal baseline (°C)
        'weight': 1.0,    # Silent killer in preemies
        'power': 3,       # Hypothermia penalty
    },
    'map': {
        'mu': 35.0,       # Ideal baseline (mmHg) ≈ Gestational Age
        'weight': 2.0,    # Perfusion pressure
        'power': 2,
    }
}

# Rolling window for calculating standard deviations (last N minutes)
ROLLING_WINDOW_MINUTES = 60


def get_live_statistics(patient_id="Baby_A", window_minutes=60):
    """
    Calculate standard deviations from live data collected from SQL table.
    Uses rolling window of last N minutes to get real-time variability.
    
    Args:
        patient_id: Patient identifier
        window_minutes: Time window for statistics (default 60 min)
    
    Returns:
        dict: Standard deviations for each vital sign
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Calculate cutoff time for rolling window
        cutoff_time = (datetime.now() - timedelta(minutes=window_minutes)).isoformat()
        
        # Query recent data within rolling window
        cursor.execute("""
            SELECT hr, spo2, rr, temp, map 
            FROM risk_monitor 
            WHERE patient_id = ? AND created_at >= ?
            ORDER BY created_at DESC
        """, (patient_id, cutoff_time))
        
        rows = cursor.fetchall()
        conn.close()
        
        # Need at least 2 data points to calculate SD
        if len(rows) < 2:
            # Return default SDs if insufficient data
            return {
                'hr': 15.0,      # ±1σ = 15 bpm (120-170 range)
                'spo2': 2.5,     # ±1σ = 2.5% (90-97.5 range)
                'rr': 10.0,      # ±1σ = 10 bpm (40-60 range)
                'temp': 0.5,     # ±1σ = 0.5°C (36.5-37.5 range)
                'map': 5.0       # ±1σ = 5 mmHg (30-40 range)
            }
        
        # Convert to numpy arrays and calculate standard deviations
        data = np.array(rows)
        
        return {
            'hr': float(np.std(data[:, 0])) or 15.0,
            'spo2': float(np.std(data[:, 1])) or 2.5,
            'rr': float(np.std(data[:, 2])) or 10.0,
            'temp': float(np.std(data[:, 3])) or 0.5,
            'map': float(np.std(data[:, 4])) or 5.0
        }
        
    except Exception as e:
        print(f"[STATS ERROR] Failed to calculate live statistics: {e}", flush=True)
        # Return defaults on error
        return {
            'hr': 15.0, 'spo2': 2.5, 'rr': 10.0, 'temp': 0.5, 'map': 5.0
        }


def calculate_risk_score(hr, spo2, rr, temp, map_val, patient_id="Baby_A"):
    """
    Calculate weighted deviation-based risk score using live statistics.
    
    Formula: Risk = Σ W_i · (|X_i - μ_i| / σ_i)^P_i
    
    Where:
        - μ (mu): Ideal baseline for preterm infant
        - σ (sigma): Standard deviation from live data (tolerance)
        - W: Weight (relative importance)
        - P: Power (sensitivity - linear vs exponential penalty)
    
    Args:
        hr: Heart rate (bpm)
        spo2: Oxygen saturation (%)
        rr: Respiratory rate (breaths/min)
        temp: Temperature (°C)
        map_val: Mean arterial pressure (mmHg)
        patient_id: Patient identifier for statistics
    
    Returns:
        float: Weighted risk score
    """
    # Get live standard deviations from recent data
    live_sd = get_live_statistics(patient_id, ROLLING_WINDOW_MINUTES)
    
    risk_total = 0.0
    
    # Process each vital sign
    vitals = {
        'hr': hr,
        'spo2': spo2,
        'rr': rr,
        'temp': temp,
        'map': map_val
    }
    
    for vital_name, vital_value in vitals.items():
        params = RISK_PARAMS[vital_name]
        
        # Calculate normalized deviation (z-score)
        deviation = abs(vital_value - params['mu'])
        normalized = deviation / live_sd[vital_name]
        
        # Apply power function for sensitivity
        powered = normalized ** params['power']
        
        # Apply weight for relative importance
        component = params['weight'] * powered
        risk_total += component
    
    return round(risk_total, 2)


def init_database():
    """Initialize SQLite database and create table if not exists."""
    DB_PATH.parent.mkdir(exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create table with all vitals plus calculated risk score
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS risk_monitor (
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
        )
    """)
    
    # Create indexes for faster queries
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_patient_id 
        ON risk_monitor(patient_id)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_risk_score 
        ON risk_monitor(risk_score)
    """)
    
    conn.commit()
    conn.close()
    print(f"[INFO] Database initialized: {DB_PATH}")


def write_to_sqlite(key, row, time, is_addition):
    """
    Write processed records to SQLite database.
    
    Args:
        key: Pathway internal key
        row: Dictionary containing the processed row data
        time: Pathway processing time
        is_addition: Boolean indicating if this is a new row
    """
    if not is_addition:
        return  # Skip deletions
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Insert with conflict handling (ignore duplicates)
        cursor.execute("""
            INSERT OR IGNORE INTO risk_monitor 
            (timestamp, patient_id, hr, spo2, rr, temp, map, risk_score, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            row["timestamp"],
            row["patient_id"],
            row["hr"],
            row["spo2"],
            row["rr"],
            row["temp"],
            row["map"],
            row["risk_score"],
            row["status"]
        ))
        
        conn.commit()
        conn.close()
        
        # Print successful write
        print(f"[DB WRITE] {row['timestamp']} | Patient: {row['patient_id']} | "
              f"HR: {row['hr']:.0f} | SpO2: {row['spo2']:.0f}% | "
              f"Risk: {row['risk_score']:.1f}", flush=True)
        
    except Exception as e:
        print(f"[DB ERROR] Failed to write row: {e}", flush=True)


def run_pipeline():
    """
    Initialize and run the streaming data ingestion pipeline.
    Monitors CSV file, calculates risk scores, and writes to SQLite.
    """
    # Initialize database
    init_database()
    
    print("="*70)
    print("NEOVANCE-AI: Pathway Streaming ETL Pipeline")
    print("="*70)
    print("Status: Watching data/stream.csv for incoming data...")
    print(f"Database: {DB_PATH}")
    print("Press Ctrl+C to stop the pipeline")
    print("="*70 + "\n")
    
    # Configure the streaming CSV connector
    table = pw.io.csv.read(
        path="./data/stream.csv",
        schema=InputSchema,
        mode="streaming",  # Watch file for continuous updates
        autocommit_duration_ms=1000,  # Check for new data every 1 second
    )
    
    # Calculate risk score using weighted deviation-based formula
    # Risk = Σ W_i · (|X_i - μ_i| / σ_i)^P_i
    # Uses live statistics from SQL table (rolling 60-minute window)
    table = table.select(
        timestamp=pw.this.timestamp,
        patient_id=pw.this.patient_id,
        hr=pw.this.hr,
        spo2=pw.this.spo2,
        rr=pw.this.rr,
        temp=pw.this.temp,
        map=pw.this.map,
        risk_score=pw.apply(
            calculate_risk_score,
            pw.this.hr,
            pw.this.spo2,
            pw.this.rr,
            pw.this.temp,
            pw.this.map,
            pw.this.patient_id
        ),
        status=pw.apply(
            lambda risk: "CRITICAL" if risk > 20 else "WARNING" if risk > 10 else "OK",
            pw.apply(
                calculate_risk_score,
                pw.this.hr,
                pw.this.spo2,
                pw.this.rr,
                pw.this.temp,
                pw.this.map,
                pw.this.patient_id
            )
        )
    )
    
    # Write processed data to SQLite
    pw.io.subscribe(table, write_to_sqlite)
    
    # Run the Pathway computation graph
    pw.run()


if __name__ == "__main__":
    try:
        run_pipeline()
    except KeyboardInterrupt:
        print("\n\n[INFO] Pipeline stopped by user")
    except Exception as e:
        print(f"\n[ERROR] Pipeline failed: {e}")
        raise
