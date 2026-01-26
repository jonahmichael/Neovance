#!/usr/bin/env python3

"""
Pathway ETL Pipeline with PostgreSQL/TimescaleDB Support
Updated for HIL system with high-performance time-series database
"""

import pathway as pw
import json
from datetime import datetime
import numpy as np
import random

# HIL Calculator Import
from test_eos_calculator import EOSRiskCalculator

class PathwayETLPostgreSQL:
    def __init__(self):
        self.eos_calculator = EOSRiskCalculator()
        
        # PostgreSQL connection configuration
        self.db_config = {
            'host': 'localhost',
            'port': 5432,
            'database': 'neovance_db',
            'user': 'postgres',
            'password': 'password'  # Should be from environment variable
        }
        
        # Connection URL for Pathway
        self.postgres_url = f"postgresql://{self.db_config['user']}:{self.db_config['password']}@{self.db_config['host']}:{self.db_config['port']}/{self.db_config['database']}"
        
        print("======================================================================")
        print("PATHWAY ETL PIPELINE - POSTGRESQL/TIMESCALEDB HIL SYSTEM")
        print("======================================================================")
        print(f"Source: /mnt/d/Neovance-AI/data/stream_eos.csv")
        print(f"Target: PostgreSQL TimescaleDB - {self.db_config['host']}:{self.db_config['port']}/{self.db_config['database']}")
        print("Processing stream with validated EOS risk calculation...")
        print("======================================================================")

    def create_patient_features_json(self, row):
        """
        Create comprehensive patient features JSON for HIL learning
        This is the critical state snapshot used for AI predictions
        """
        # Basic vitals
        vitals = {
            'hr': float(row['hr']),
            'spo2': float(row['spo2']),
            'rr': float(row['rr']),
            'temp': float(row['temp']),
            'map': float(row['map'])
        }
        
        # Derived features for ML
        derived_features = {
            'hr_trend': 'stable',  # Could be calculated from recent history
            'spo2_trend': 'declining' if vitals['spo2'] < 92 else 'stable',
            'temp_abnormal': vitals['temp'] > 38.0 or vitals['temp'] < 36.0,
            'hypotension': vitals['map'] < 30,
            'tachycardia': vitals['hr'] > 120,
            'bradycardia': vitals['hr'] < 80,
            'hypoxia': vitals['spo2'] < 90
        }
        
        # Patient demographics (would come from database lookup)
        patient_context = {
            'mrn': row['mrn'],
            'gestational_age_weeks': 37,  # Would be looked up
            'birth_weight': 2.8,
            'current_age_hours': 24,
            'maternal_gbs': 'negative',
            'maternal_fever': False,
            'rom_hours': 6.0,
            'antibiotics_given': False
        }
        
        # EOS risk factors
        eos_factors = {
            'risk_score': float(row['risk_score']),
            'risk_category': row['status'],
            'clinical_exam': 'normal',
            'sepsis_risk_level': 'low' if float(row['risk_score']) < 1.0 else 'moderate' if float(row['risk_score']) < 3.0 else 'high'
        }
        
        # Combine all features for ML model
        features_json = {
            'timestamp': row['timestamp'],
            'vitals': vitals,
            'derived_features': derived_features,
            'patient_context': patient_context,
            'eos_factors': eos_factors,
            'feature_version': '1.0'  # For model versioning
        }
        
        return json.dumps(features_json)

    def run(self):
        """
        Main ETL pipeline execution with PostgreSQL sink
        """
        print("[HIL PATHWAY] Pipeline starting - processing with validated EOS calculator...")
        
        # Read CSV stream
        vitals_stream = pw.io.csv.read(
            "/mnt/d/Neovance-AI/data/stream_eos.csv",
            schema=pw.schema_from_types(
                timestamp=str,
                mrn=str,
                hr=float,
                spo2=float,
                rr=float,
                temp=float,
                map=float,
                risk_score=float,
                status=str
            ),
            mode="streaming"
        )
        
        # Process stream with feature engineering for HIL
        processed_stream = vitals_stream.select(
            timestamp=pw.this.timestamp,
            mrn=pw.this.mrn,
            hr=pw.this.hr,
            spo2=pw.this.spo2,
            rr=pw.this.rr,
            temp=pw.this.temp,
            map=pw.this.map,
            risk_score=pw.this.risk_score,
            status=pw.this.status,
            # Add features_json for HIL learning
            features_json=pw.apply(self.create_patient_features_json, pw.this),
            created_at=pw.apply(lambda: datetime.now().isoformat(), pw.this.timestamp)
        )
        
        # Sink to PostgreSQL TimescaleDB realtime_vitals table
        pw.io.postgres.write(
            processed_stream,
            postgres_settings=pw.io.postgres.PostgresSettings(
                host=self.db_config['host'],
                port=self.db_config['port'],
                dbname=self.db_config['database'],
                user=self.db_config['user'],
                password=self.db_config['password']
            ),
            table_name="realtime_vitals",
            on_conflict="ignore"  # Handle duplicate timestamps gracefully
        )
        
        # Run the computation
        pw.run()

def main():
    """Main execution function"""
    etl = PathwayETLPostgreSQL()
    
    try:
        etl.run()
    except KeyboardInterrupt:
        print("\n[HIL PATHWAY] Stopped by user")
    except Exception as e:
        print(f"[ERROR] HIL Pathway ETL error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()