"""
Pathway ETL Pipeline - Real-time streaming data processing
Reads from CSV stream and writes to SQLite database
"""

import pathway as pw
from datetime import datetime
from pathlib import Path
import sys
from sqlalchemy import create_engine, text


class PathwayETL:
    """Pathway-based ETL pipeline for NICU vitals"""
    
    def __init__(self):
        self.data_dir = Path(__file__).parent.parent / "data"
        self.stream_file = self.data_dir / "stream.csv"
        self.db_path = Path(__file__).parent / "neonatal_ehr.db"
        
    def run(self):
        """Run the Pathway streaming pipeline"""
        print("="*70)
        print("PATHWAY ETL PIPELINE - Real-time Data Processing")
        print("="*70)
        print(f"Source: {self.stream_file}")
        print(f"Target: {self.db_path}")
        print("Processing stream...")
        print("="*70)
        
        # NOTE: SQLAlchemy engine is ONLY needed if you want to set up the schema
        # or read data outside of Pathway. Pathway's SQL sink handles the writes.
        
        # Define input schema
        class VitalsSchema(pw.Schema):
            timestamp: str
            mrn: str
            hr: float
            spo2: float
            rr: float
            temp: float
            map: float
            risk_score: float
            status: str
        
        # Read from CSV stream
        vitals_stream = pw.io.csv.read(
            str(self.stream_file),
            schema=VitalsSchema,
            mode="streaming"
        )
        
        # Process the stream
        # This DTable now has the schema ready for the DB
        processed = vitals_stream.select(
            timestamp=pw.this.timestamp,
            mrn=pw.this.mrn,
            hr=pw.this.hr,
            spo2=pw.this.spo2,
            rr=pw.this.rr,
            temp=pw.this.temp,
            map=pw.this.map,
            risk_score=pw.this.risk_score,
            status=pw.this.status
        )
        
        # -----------------------------------------------------------------
        # Use subscribe with manual write - VERIFIED WORKING APPROACH
        # -----------------------------------------------------------------
        
        # Create SQLAlchemy engine for writing
        engine = create_engine(f'sqlite:///{self.db_path}')
        
        def write_to_db(key, row, time, is_addition):
            """Write each new row to database"""
            if is_addition:
                try:
                    with engine.connect() as conn:
                        conn.execute(text("""
                            INSERT INTO live_vitals 
                            (timestamp, mrn, hr, spo2, rr, temp, map, risk_score, status, created_at)
                            VALUES 
                            (:timestamp, :mrn, :hr, :spo2, :rr, :temp, :map, :risk_score, :status, datetime('now'))
                        """), {
                            'timestamp': str(row['timestamp']),
                            'mrn': str(row['mrn']),
                            'hr': float(row['hr']),
                            'spo2': float(row['spo2']),
                            'rr': float(row['rr']),
                            'temp': float(row['temp']),
                            'map': float(row['map']),
                            'risk_score': float(row['risk_score']),
                            'status': str(row['status'])
                        })
                        conn.commit()
                        print(f"[OK] MRN:{row['mrn']} HR:{row['hr']} SpO2:{row['spo2']}%")
                except Exception as e:
                    print(f"[ERROR] DB write error: {e}")
        
        pw.io.subscribe(processed, write_to_db)
        
        # Run the pipeline
        print("[PATHWAY] Pipeline starting - will process new CSV rows as they arrive...")
        pw.run(monitoring_level=pw.MonitoringLevel.NONE)


def main():
    """Main entry point"""
    try:
        etl = PathwayETL()
        etl.run()
    except KeyboardInterrupt:
        print("\n[PATHWAY] Stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"[ERROR] Pipeline failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
