#!/usr/bin/env python3
"""
Human-in-the-Loop Outcome Logging and Continuous Learning
Handles the complete HIL feedback loop: State → Action → Outcome → Retrain

This manages the continuous learning cycle for sepsis prediction.
"""

import psycopg2
import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
import logging
import sys
import os

# Add paths for model training
sys.path.append('.')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
DB_CONFIG = {
    "host": "localhost",
    "database": "neovance_hil", 
    "user": "postgres",
    "password": "password",
    "port": 5432
}

class HILOutcomeLogger:
    """Manages outcome logging for HIL learning"""
    
    def __init__(self):
        self.conn = None
        self.connect_db()
    
    def connect_db(self):
        """Connect to HIL database"""
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            logger.info("✅ Connected to HIL database")
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            self.conn = None
    
    def log_sepsis_outcome(self, alert_id: int, sepsis_confirmed: bool, 
                          lab_result: str = "", patient_status_6hr: str = ""):
        """Log the outcome of a sepsis case for HIL learning"""
        try:
            if not self.conn:
                self.connect_db()
                
            cursor = self.conn.cursor()
            
            insert_query = """
                INSERT INTO outcomes (
                    alert_id, outcome_time, sepsis_confirmed, 
                    lab_result, patient_status_6hr
                )
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id;
            """
            
            cursor.execute(insert_query, (
                alert_id,
                datetime.now(),
                sepsis_confirmed,
                lab_result,
                patient_status_6hr
            ))
            
            outcome_id = cursor.fetchone()[0]
            self.conn.commit()
            cursor.close()
            
            logger.info(f"✅ Outcome logged: Alert {alert_id} → Sepsis: {sepsis_confirmed}")
            return outcome_id
            
        except Exception as e:
            logger.error(f"❌ Failed to log outcome: {e}")
            return None
    
    def get_hil_training_data(self, days_back: int = 30) -> pd.DataFrame:
        """Retrieve HIL training data for model retraining"""
        try:
            if not self.conn:
                self.connect_db()
            
            # Get HIL data with outcomes
            query = """
                SELECT 
                    a.id as alert_id,
                    a.timestamp,
                    a.mrn,
                    a.risk_score as ml_prediction,
                    a.features_json,
                    a.doctor_id,
                    a.doctor_action,
                    a.action_detail,
                    o.sepsis_confirmed,
                    o.patient_status_6hr,
                    CASE 
                        WHEN o.sepsis_confirmed IS TRUE THEN 1
                        WHEN o.sepsis_confirmed IS FALSE THEN 0
                        ELSE NULL 
                    END as outcome_label
                FROM alerts a
                LEFT JOIN outcomes o ON a.id = o.alert_id
                WHERE a.timestamp >= %s
                AND a.doctor_action IS NOT NULL
                ORDER BY a.timestamp DESC;
            """
            
            cutoff_date = datetime.now() - timedelta(days=days_back)
            
            df = pd.read_sql(query, self.conn, params=[cutoff_date])
            
            logger.info(f"📊 Retrieved {len(df)} HIL records from last {days_back} days")
            logger.info(f"   • With outcomes: {df['outcome_label'].notna().sum()}")
            logger.info(f"   • Positive outcomes: {df['outcome_label'].sum()}")
            
            return df
            
        except Exception as e:
            logger.error(f"❌ Failed to retrieve HIL data: {e}")
            return pd.DataFrame()
    
    def get_doctor_performance_metrics(self) -> pd.DataFrame:
        """Analyze doctor performance for HIL insights"""
        try:
            if not self.conn:
                self.connect_db()
            
            query = """
                SELECT 
                    a.doctor_id,
                    a.doctor_action,
                    COUNT(*) as total_actions,
                    AVG(a.risk_score) as avg_ml_risk,
                    COUNT(o.sepsis_confirmed) as outcomes_available,
                    SUM(CASE WHEN o.sepsis_confirmed THEN 1 ELSE 0 END) as sepsis_confirmed,
                    SUM(CASE WHEN o.sepsis_confirmed IS FALSE THEN 1 ELSE 0 END) as sepsis_ruled_out,
                    ROUND(
                        SUM(CASE WHEN o.sepsis_confirmed THEN 1 ELSE 0 END)::float / 
                        NULLIF(COUNT(o.sepsis_confirmed), 0) * 100, 1
                    ) as positive_rate_percent
                FROM alerts a
                LEFT JOIN outcomes o ON a.id = o.alert_id
                WHERE a.doctor_action IS NOT NULL
                GROUP BY a.doctor_id, a.doctor_action
                ORDER BY a.doctor_id, total_actions DESC;
            """
            
            df = pd.read_sql(query, self.conn)
            
            logger.info(f"📈 Doctor performance analysis: {len(df)} doctor-action combinations")
            return df
            
        except Exception as e:
            logger.error(f"❌ Failed to analyze doctor performance: {e}")
            return pd.DataFrame()
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()


class HILContinuousLearning:
    """Manages continuous learning and model retraining"""
    
    def __init__(self):
        self.outcome_logger = HILOutcomeLogger()
    
    def create_hil_training_dataset(self) -> pd.DataFrame:
        """Create enhanced training dataset using HIL feedback"""
        logger.info("🔄 Creating HIL-enhanced training dataset...")
        
        # Get original training data
        try:
            original_df = pd.read_csv('data/neonatal_sepsis_training.csv')
            logger.info(f"📊 Loaded {len(original_df)} original training samples")
        except:
            logger.warning("⚠️ Original training data not found")
            original_df = pd.DataFrame()
        
        # Get HIL feedback data
        hil_df = self.outcome_logger.get_hil_training_data(days_back=90)
        
        if len(hil_df) == 0:
            logger.warning("⚠️ No HIL data available, using original dataset only")
            return original_df
        
        # Convert HIL data to training format
        hil_training_samples = []
        
        for _, row in hil_df.iterrows():
            if pd.notna(row['outcome_label']):  # Only use samples with confirmed outcomes
                try:
                    # Extract features from stored JSON
                    features_json = row['features_json']
                    if isinstance(features_json, str):
                        features_data = json.loads(features_json)
                    else:
                        features_data = features_json
                    
                    # Extract patient data
                    patient_data = features_data.get('patient_data', {})
                    
                    # Create training sample
                    training_sample = {
                        'mrn': f"HIL_{row['alert_id']}",
                        'gestational_age_at_birth_weeks': patient_data.get('gestational_age_at_birth_weeks', 39),
                        'birth_weight_kg': patient_data.get('birth_weight_kg', 3.0),
                        'sex': patient_data.get('sex', 'unknown'),
                        'race': patient_data.get('race', 'unknown'),
                        'ga_weeks': patient_data.get('ga_weeks', 39),
                        'ga_days': patient_data.get('ga_days', 0),
                        'maternal_temp_celsius': patient_data.get('maternal_temp_celsius', 37.0),
                        'rom_hours': patient_data.get('rom_hours', 8.0),
                        'gbs_status': patient_data.get('gbs_status', 'negative'),
                        'antibiotic_type': patient_data.get('antibiotic_type', 'none'),
                        'clinical_exam': patient_data.get('clinical_exam', 'normal'),
                        'hr': patient_data.get('hr', 120),
                        'spo2': patient_data.get('spo2', 97),
                        'rr': patient_data.get('rr', 25),
                        'temp_celsius': patient_data.get('temp_celsius', 37.0),
                        'map': patient_data.get('map', 40),
                        'comorbidities': patient_data.get('comorbidities', 'no'),
                        'central_venous_line': patient_data.get('central_venous_line', 'no'),
                        'intubated_at_time_of_sepsis_evaluation': patient_data.get('intubated_at_time_of_sepsis_evaluation', 'no'),
                        'inotrope_at_time_of_sepsis_eval': patient_data.get('inotrope_at_time_of_sepsis_eval', 'no'),
                        'ecmo': patient_data.get('ecmo', 'no'),
                        'stat_abx': patient_data.get('stat_abx', 'no'),
                        'time_to_antibiotics': patient_data.get('time_to_antibiotics', None),
                        
                        # HIL-specific fields
                        'sepsis_group': 1 if row['outcome_label'] == 1 else 2,  # 1=sepsis, 2=no sepsis
                        'has_sepsis': int(row['outcome_label']),
                        'timestamp': row['timestamp'],
                        'doctor_action': row['doctor_action'],
                        'doctor_id': row['doctor_id'],
                        'ml_prediction': row['ml_prediction'],
                        'is_hil_sample': True
                    }
                    
                    hil_training_samples.append(training_sample)
                    
                except Exception as e:
                    logger.warning(f"Failed to process HIL sample {row['alert_id']}: {e}")
        
        # Convert HIL samples to DataFrame
        if hil_training_samples:
            hil_df_processed = pd.DataFrame(hil_training_samples)
            logger.info(f"✅ Processed {len(hil_df_processed)} HIL training samples")
            
            # Mark original samples
            original_df['is_hil_sample'] = False
            
            # Combine datasets
            combined_df = pd.concat([original_df, hil_df_processed], ignore_index=True)
            logger.info(f"📊 Combined dataset: {len(combined_df)} samples ({len(hil_df_processed)} from HIL)")
            
        else:
            logger.warning("⚠️ No valid HIL samples processed, using original dataset")
            combined_df = original_df
            combined_df['is_hil_sample'] = False
        
        return combined_df
    
    def retrain_model(self):
        """Retrain the sepsis prediction model with HIL feedback"""
        logger.info("🤖 Starting HIL-enhanced model retraining...")
        
        try:
            # Create enhanced dataset
            enhanced_df = self.create_hil_training_dataset()
            
            if len(enhanced_df) == 0:
                logger.error("❌ No training data available")
                return False
            
            # Save enhanced dataset
            enhanced_df.to_csv('data/neonatal_sepsis_hil_enhanced.csv', index=False)
            logger.info(f"💾 Saved enhanced dataset: {len(enhanced_df)} samples")
            
            # Import and run the training script with enhanced data
            os.environ['HIL_ENHANCED_DATA'] = 'data/neonatal_sepsis_hil_enhanced.csv'
            
            # Run training script
            import subprocess
            result = subprocess.run(
                ['python', 'train_sepsis_model.py'],
                env={**os.environ, 'DATA_FILE': 'data/neonatal_sepsis_hil_enhanced.csv'},
                capture_output=True,
                text=True,
                cwd='.'
            )
            
            if result.returncode == 0:
                logger.info("✅ Model retraining completed successfully")
                logger.info(f"Training output: {result.stdout[-500:]}")  # Last 500 chars
                
                # Log retraining event
                self._log_retraining_event(len(enhanced_df), 
                                         enhanced_df['is_hil_sample'].sum(),
                                         True, "")
                return True
            else:
                logger.error(f"❌ Model retraining failed: {result.stderr}")
                self._log_retraining_event(len(enhanced_df), 
                                         enhanced_df['is_hil_sample'].sum(),
                                         False, result.stderr[:500])
                return False
                
        except Exception as e:
            logger.error(f"❌ Retraining process failed: {e}")
            return False
    
    def _log_retraining_event(self, total_samples: int, hil_samples: int, 
                            success: bool, error_message: str):
        """Log retraining events for monitoring"""
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()
            
            # Create retraining log table if it doesn't exist
            create_table_query = """
                CREATE TABLE IF NOT EXISTS model_retraining_log (
                    id BIGSERIAL PRIMARY KEY,
                    timestamp TIMESTAMPTZ DEFAULT NOW(),
                    total_samples INTEGER,
                    hil_samples INTEGER,
                    success BOOLEAN,
                    error_message TEXT
                );
            """
            
            cursor.execute(create_table_query)
            
            insert_query = """
                INSERT INTO model_retraining_log 
                (total_samples, hil_samples, success, error_message)
                VALUES (%s, %s, %s, %s);
            """
            
            cursor.execute(insert_query, (total_samples, hil_samples, success, error_message))
            conn.commit()
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to log retraining event: {e}")


def simulate_outcome_logging():
    """Simulate some outcome logging for testing"""
    logger.info("🧪 Simulating outcome logging for testing...")
    
    outcome_logger = HILOutcomeLogger()
    
    # Get recent alerts without outcomes
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        query = """
            SELECT a.id, a.mrn, a.risk_score 
            FROM alerts a
            LEFT JOIN outcomes o ON a.id = o.alert_id
            WHERE o.id IS NULL 
            AND a.timestamp >= %s
            ORDER BY a.timestamp DESC
            LIMIT 5;
        """
        
        cutoff = datetime.now() - timedelta(hours=24)
        cursor.execute(query, [cutoff])
        alerts = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # Simulate outcomes
        for alert_id, mrn, risk_score in alerts:
            # Simulate realistic outcomes based on risk score
            sepsis_confirmed = np.random.random() < min(risk_score * 2, 0.8)  # Higher risk → higher chance
            
            status_options = ["Improved", "Stable", "Worsened"] if sepsis_confirmed else ["Improved", "Stable"]
            patient_status = np.random.choice(status_options)
            
            lab_result = "Blood culture positive, CRP elevated" if sepsis_confirmed else "Negative blood culture, normal labs"
            
            outcome_id = outcome_logger.log_sepsis_outcome(
                alert_id, sepsis_confirmed, lab_result, patient_status
            )
            
            if outcome_id:
                logger.info(f"🎯 Simulated outcome: Alert {alert_id} → Sepsis: {sepsis_confirmed}")
    
    except Exception as e:
        logger.error(f"Simulation failed: {e}")
    
    outcome_logger.close()


def main():
    """Main HIL management function"""
    print("="*80)
    print("🔄 HUMAN-IN-THE-LOOP OUTCOME LOGGING AND CONTINUOUS LEARNING")
    print("="*80)
    
    # Initialize HIL system
    hil_learning = HILContinuousLearning()
    
    # Show current HIL data status
    hil_data = hil_learning.outcome_logger.get_hil_training_data()
    print(f"📊 Current HIL Data Status:")
    print(f"   • Total alerts with doctor actions: {len(hil_data)}")
    print(f"   • Alerts with outcomes: {hil_data['outcome_label'].notna().sum()}")
    print(f"   • Confirmed sepsis cases: {hil_data['outcome_label'].sum()}")
    
    # Show doctor performance
    doctor_perf = hil_learning.outcome_logger.get_doctor_performance_metrics()
    if len(doctor_perf) > 0:
        print(f"\\n👩‍⚕️ Doctor Performance Summary:")
        print(doctor_perf.to_string(index=False))
    
    # Options for HIL management
    print(f"\\n🎛️ HIL Management Options:")
    print(f"1. Simulate outcome logging (for testing)")
    print(f"2. Retrain model with HIL feedback")
    print(f"3. Show HIL analytics")
    print(f"4. Exit")
    
    try:
        choice = input("\\nSelect option (1-4): ").strip()
        
        if choice == "1":
            simulate_outcome_logging()
        elif choice == "2":
            success = hil_learning.retrain_model()
            if success:
                print("✅ Model retraining completed successfully!")
            else:
                print("❌ Model retraining failed!")
        elif choice == "3":
            print("\\n📈 Detailed HIL Analytics:")
            print(hil_data[['timestamp', 'mrn', 'ml_prediction', 'doctor_action', 'outcome_label']].to_string())
        elif choice == "4":
            print("👋 Exiting HIL management")
        else:
            print("❌ Invalid option")
    
    except KeyboardInterrupt:
        print("\\n⏹️ Interrupted by user")
    
    finally:
        hil_learning.outcome_logger.close()


if __name__ == "__main__":
    main()