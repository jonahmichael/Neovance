"""
Neovance-AI: Real-time NICU Data Pipeline
Streaming ETL pipeline using Pathway framework to ingest live patient vitals
and write to SQLite database.
"""

import pathway as pw
import sqlite3
from pathlib import Path


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
    
    # Calculate risk score and add status column
    # Risk score: simple metric (HR + SpO2) / 2
    # In production, this would be a trained ML model
    table = table.with_columns(
        risk_score=(pw.this.hr + pw.this.spo2) / 2,
        status="OK"
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
