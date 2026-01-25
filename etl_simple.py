"""
Neovance-AI: Simple Streaming ETL (No Pathway)
Processes CSV every minute, calculates risk scores using live statistics from SQL,
and writes to SQLite database.
"""

import sqlite3
import csv
import time
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta


# Clinical Parameters for 28-week Premature Infant
RISK_PARAMS = {
    'hr': {'mu': 145.0, 'weight': 1.0, 'power': 2},
    'spo2': {'mu': 95.0, 'weight': 3.0, 'power': 4},
    'rr': {'mu': 50.0, 'weight': 1.5, 'power': 2},
    'temp': {'mu': 37.0, 'weight': 1.0, 'power': 3},
    'map': {'mu': 35.0, 'weight': 2.0, 'power': 2}
}

DB_PATH = Path("data/neovance.db")
CSV_PATH = Path("data/stream.csv")
ROLLING_WINDOW_MINUTES = 60


def init_database():
    """Initialize SQLite database and create table if not exists."""
    DB_PATH.parent.mkdir(exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
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


def get_live_statistics(patient_id="Baby_A", window_minutes=60):
    """
    Calculate standard deviations from live data in SQL table.
    Uses rolling window of last N minutes.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cutoff_time = (datetime.now() - timedelta(minutes=window_minutes)).isoformat()
        
        cursor.execute("""
            SELECT hr, spo2, rr, temp, map 
            FROM risk_monitor 
            WHERE patient_id = ? AND created_at >= ?
            ORDER BY created_at DESC
        """, (patient_id, cutoff_time))
        
        rows = cursor.fetchall()
        conn.close()
        
        if len(rows) < 2:
            # Return default SDs if insufficient data
            return {
                'hr': 15.0,
                'spo2': 2.5,
                'rr': 10.0,
                'temp': 0.5,
                'map': 5.0
            }
        
        data = np.array(rows)
        
        return {
            'hr': float(np.std(data[:, 0])) or 15.0,
            'spo2': float(np.std(data[:, 1])) or 2.5,
            'rr': float(np.std(data[:, 2])) or 10.0,
            'temp': float(np.std(data[:, 3])) or 0.5,
            'map': float(np.std(data[:, 4])) or 5.0
        }
        
    except Exception as e:
        print(f"[STATS ERROR] {e}")
        return {
            'hr': 15.0, 'spo2': 2.5, 'rr': 10.0, 'temp': 0.5, 'map': 5.0
        }


def calculate_risk_score(hr, spo2, rr, temp, map_val, patient_id="Baby_A"):
    """
    Calculate weighted deviation-based risk score using live statistics.
    
    Formula: Risk = Σ W_i · (|X_i - μ_i| / σ_i)^P_i
    """
    live_sd = get_live_statistics(patient_id, ROLLING_WINDOW_MINUTES)
    
    risk_total = 0.0
    
    vitals = {
        'hr': hr,
        'spo2': spo2,
        'rr': rr,
        'temp': temp,
        'map': map_val
    }
    
    for vital_name, vital_value in vitals.items():
        params = RISK_PARAMS[vital_name]
        
        deviation = abs(vital_value - params['mu'])
        normalized = deviation / live_sd[vital_name]
        powered = normalized ** params['power']
        component = params['weight'] * powered
        
        risk_total += component
    
    return round(risk_total, 2)


def process_csv_line(row_data):
    """Process a single CSV row and write to database."""
    try:
        timestamp = row_data['timestamp']
        patient_id = row_data['patient_id']
        hr = float(row_data['hr'])
        spo2 = float(row_data['spo2'])
        rr = float(row_data['rr'])
        temp = float(row_data['temp'])
        map_val = float(row_data['map'])
        
        # Calculate risk score
        risk_score = calculate_risk_score(hr, spo2, rr, temp, map_val, patient_id)
        
        # Determine status
        if risk_score > 20:
            status = "CRITICAL"
        elif risk_score > 10:
            status = "WARNING"
        else:
            status = "OK"
        
        # Write to database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR IGNORE INTO risk_monitor 
            (timestamp, patient_id, hr, spo2, rr, temp, map, risk_score, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (timestamp, patient_id, hr, spo2, rr, temp, map_val, risk_score, status))
        
        if cursor.rowcount > 0:
            print(f"[DB WRITE] {timestamp} | {patient_id} | "
                  f"HR:{hr:.0f} SpO2:{spo2:.0f}% RR:{rr:.0f} Temp:{temp:.1f} MAP:{map_val:.0f} | "
                  f"Risk:{risk_score:.2f} | {status}", flush=True)
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        print(f"[ERROR] Failed to process row: {e}")


def run_streaming_etl():
    """
    Main ETL loop: reads CSV every minute, calculates risk scores using
    live statistics from SQL, and writes to database.
    """
    init_database()
    
    print("="*70)
    print("NEOVANCE-AI: Simple Streaming ETL")
    print("="*70)
    print("Status: Reading data/stream.csv every minute...")
    print(f"Database: {DB_PATH}")
    print("Risk Formula: Weighted Deviation-Based (Live Stats from SQL)")
    print("Press Ctrl+C to stop")
    print("="*70 + "\n")
    
    last_row_count = 0
    
    while True:
        try:
            if not CSV_PATH.exists():
                print("[WAITING] CSV file not found yet...")
                time.sleep(5)
                continue
            
            with open(CSV_PATH, 'r') as f:
                # CSV has no header row, define field names manually
                reader = csv.DictReader(f, fieldnames=['timestamp', 'patient_id', 'hr', 'spo2', 'rr', 'temp', 'map'])
                rows = list(reader)
                
                # Process only new rows
                new_rows = rows[last_row_count:]
                
                if new_rows:
                    print(f"\n[PROCESSING] {len(new_rows)} new rows...")
                    for row in new_rows:
                        process_csv_line(row)
                    
                    last_row_count = len(rows)
                
            time.sleep(60)  # Check every minute
            
        except KeyboardInterrupt:
            print("\n\n[INFO] ETL stopped by user")
            break
        except Exception as e:
            print(f"[ERROR] ETL error: {e}")
            time.sleep(5)


if __name__ == "__main__":
    run_streaming_etl()
