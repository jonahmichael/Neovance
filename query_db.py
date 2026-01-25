#!/usr/bin/env python
"""Query the SQLite database to view stored patient data."""

import sqlite3
import sys
from pathlib import Path

DB_PATH = Path("data/neovance.db")

def query_all():
    """Execute SELECT * FROM risk_monitor."""
    if not DB_PATH.exists():
        print(f"ERROR: Database not found: {DB_PATH}")
        print("Run the pipeline first to create it.")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get total count
    cursor.execute("SELECT COUNT(*) FROM risk_monitor")
    total = cursor.fetchone()[0]
    
    if total == 0:
        print("Database is empty. Start the simulator and ETL pipeline.")
        conn.close()
        return
    
    print(f"\nTotal Records: {total}")
    print("\n" + "=" * 120)
    print(f"{'TIMESTAMP':<28} {'PATIENT':<10} {'HR':<5} {'SPO2':<5} {'RR':<5} {'TEMP':<6} {'MAP':<5} {'RISK':<6} {'STATUS':<8}")
    print("=" * 120)
    
    # SELECT * FROM risk_monitor
    cursor.execute("""
        SELECT timestamp, patient_id, hr, spo2, rr, temp, map, risk_score, status
        FROM risk_monitor
        ORDER BY timestamp DESC
    """)
    
    for row in cursor.fetchall():
        ts, pid, hr, spo2, rr, temp, map_val, risk, status = row
        print(f"{ts:<28} {pid:<10} {hr:<5.0f} {spo2:<5.0f} {rr:<5.0f} {temp:<6.1f} {map_val:<5.0f} {risk:<6.1f} {status:<8}")
    
    print("=" * 120)
    
    # Statistics
    cursor.execute("""
        SELECT 
            MIN(risk_score) as min_risk,
            MAX(risk_score) as max_risk,
            AVG(risk_score) as avg_risk,
            MIN(timestamp) as first_record,
            MAX(timestamp) as last_record
        FROM risk_monitor
    """)
    
    min_r, max_r, avg_r, first, last = cursor.fetchone()
    print(f"\nStatistics:")
    print(f"  Risk Score: Min={min_r:.1f}, Max={max_r:.1f}, Avg={avg_r:.1f}")
    print(f"  Time Range: {first} → {last}")
    print(f"  Total Records: {total}\n")
    
    conn.close()


def query_latest(n=10):
    """Show latest N records."""
    if not DB_PATH.exists():
        print(f"ERROR: Database not found: {DB_PATH}")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print(f"\nLatest {n} Records:")
    print("-" * 120)
    
    cursor.execute("""
        SELECT timestamp, patient_id, hr, spo2, rr, temp, map, risk_score, status
        FROM risk_monitor
        ORDER BY timestamp DESC
        LIMIT ?
    """, (n,))
    
    for row in cursor.fetchall():
        ts, pid, hr, spo2, rr, temp, map_val, risk, status = row
        print(f"{ts} | {pid} | HR:{hr:.0f} SpO2:{spo2:.0f}% RR:{rr:.0f} "
              f"Temp:{temp:.1f}°C MAP:{map_val:.0f} | Risk:{risk:.1f} [{status}]")
    
    conn.close()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "latest":
            n = int(sys.argv[2]) if len(sys.argv) > 2 else 10
            query_latest(n)
        else:
            print("Usage: python query_db.py [latest [N]]")
    else:
        query_all()
