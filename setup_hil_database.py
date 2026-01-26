#!/usr/bin/env python3
"""
Neovance-AI: HIL Database Setup
Initialize PostgreSQL database with HIL schema and test data
"""

import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import logging
from datetime import datetime, timedelta
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HILDatabaseSetup:
    """Setup HIL database with all required tables"""
    
    def __init__(self):
        # Database configuration
        self.db_config = {
            'host': 'localhost',
            'port': '5432',
            'user': 'postgres',
            'password': 'postgres123',  # Change as needed
            'database': 'neovance_hil'
        }
        
        self.admin_config = self.db_config.copy()
        self.admin_config['database'] = 'postgres'  # Connect to admin database first
    
    def create_database(self):
        """Create the HIL database if it doesn't exist"""
        logger.info("🗃️ Creating HIL database...")
        
        try:
            # Connect to postgres database to create new database
            conn = psycopg2.connect(**self.admin_config)
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cursor = conn.cursor()
            
            # Check if database exists
            cursor.execute(
                "SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s",
                (self.db_config['database'],)
            )
            
            if cursor.fetchone():
                logger.info(f"✅ Database '{self.db_config['database']}' already exists")
            else:
                # Create database
                cursor.execute(f"CREATE DATABASE {self.db_config['database']}")
                logger.info(f"✅ Created database '{self.db_config['database']}'")
            
            cursor.close()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create database: {e}")
            return False
    
    def create_hil_schema(self):
        """Create HIL tables and indexes"""
        logger.info("📋 Creating HIL schema...")
        
        hil_schema = """
        -- Enable TimescaleDB extension
        CREATE EXTENSION IF NOT EXISTS timescaledb;
        
        -- HIL Predictions Table
        CREATE TABLE IF NOT EXISTS hil_predictions (
            id SERIAL PRIMARY KEY,
            patient_id TEXT NOT NULL,
            prediction_id UUID UNIQUE NOT NULL,
            timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            risk_score FLOAT NOT NULL,
            risk_level TEXT NOT NULL,
            features JSONB NOT NULL,
            model_version TEXT NOT NULL,
            alert_triggered BOOLEAN DEFAULT FALSE,
            threshold_exceeded BOOLEAN DEFAULT FALSE,
            doctor_notified BOOLEAN DEFAULT FALSE
        );
        
        -- HIL Doctor Actions Table
        CREATE TABLE IF NOT EXISTS hil_doctor_actions (
            id SERIAL PRIMARY KEY,
            prediction_id UUID NOT NULL REFERENCES hil_predictions(prediction_id),
            patient_id TEXT NOT NULL,
            timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            doctor_id TEXT NOT NULL,
            action_taken TEXT NOT NULL,
            clinical_reasoning TEXT,
            sepsis_confirmed BOOLEAN,
            confidence_score INTEGER CHECK (confidence_score BETWEEN 1 AND 5),
            additional_tests_ordered TEXT[],
            treatment_initiated BOOLEAN DEFAULT FALSE,
            outcome_notes TEXT
        );
        
        -- HIL Patient Outcomes Table
        CREATE TABLE IF NOT EXISTS hil_patient_outcomes (
            id SERIAL PRIMARY KEY,
            patient_id TEXT NOT NULL,
            prediction_id UUID NOT NULL REFERENCES hil_predictions(prediction_id),
            outcome_timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            actual_sepsis BOOLEAN NOT NULL,
            sepsis_onset_time TIMESTAMPTZ,
            severity_level TEXT,
            time_to_treatment INTERVAL,
            length_of_stay INTERVAL,
            outcome TEXT NOT NULL, -- 'discharged', 'transferred', 'deceased'
            prediction_accuracy BOOLEAN,
            false_positive BOOLEAN DEFAULT FALSE,
            false_negative BOOLEAN DEFAULT FALSE
        );
        
        -- HIL Model Performance Metrics
        CREATE TABLE IF NOT EXISTS hil_model_metrics (
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            model_version TEXT NOT NULL,
            evaluation_period INTERVAL NOT NULL,
            total_predictions INTEGER NOT NULL,
            true_positives INTEGER NOT NULL,
            false_positives INTEGER NOT NULL,
            true_negatives INTEGER NOT NULL,
            false_negatives INTEGER NOT NULL,
            precision FLOAT NOT NULL,
            recall FLOAT NOT NULL,
            f1_score FLOAT NOT NULL,
            auc FLOAT NOT NULL,
            specificity FLOAT NOT NULL
        );
        
        -- Convert to time-series tables
        SELECT create_hypertable('hil_predictions', 'timestamp', if_not_exists => TRUE);
        SELECT create_hypertable('hil_doctor_actions', 'timestamp', if_not_exists => TRUE);
        SELECT create_hypertable('hil_patient_outcomes', 'outcome_timestamp', if_not_exists => TRUE);
        
        -- Create indexes for performance
        CREATE INDEX IF NOT EXISTS idx_hil_predictions_patient_id ON hil_predictions(patient_id);
        CREATE INDEX IF NOT EXISTS idx_hil_predictions_risk_level ON hil_predictions(risk_level);
        CREATE INDEX IF NOT EXISTS idx_hil_predictions_alert ON hil_predictions(alert_triggered);
        
        CREATE INDEX IF NOT EXISTS idx_hil_actions_patient_id ON hil_doctor_actions(patient_id);
        CREATE INDEX IF NOT EXISTS idx_hil_actions_doctor_id ON hil_doctor_actions(doctor_id);
        CREATE INDEX IF NOT EXISTS idx_hil_actions_sepsis_confirmed ON hil_doctor_actions(sepsis_confirmed);
        
        CREATE INDEX IF NOT EXISTS idx_hil_outcomes_patient_id ON hil_patient_outcomes(patient_id);
        CREATE INDEX IF NOT EXISTS idx_hil_outcomes_actual_sepsis ON hil_patient_outcomes(actual_sepsis);
        """
        
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            # Execute schema creation
            cursor.execute(hil_schema)
            conn.commit()
            
            cursor.close()
            conn.close()
            
            logger.info("✅ HIL schema created successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create HIL schema: {e}")
            return False
    
    def create_hil_views(self):
        """Create useful views for HIL analytics"""
        logger.info("👀 Creating HIL analytics views...")
        
        views_sql = """
        -- Real-time HIL Dashboard View
        CREATE OR REPLACE VIEW hil_dashboard AS
        SELECT 
            p.patient_id,
            p.prediction_id,
            p.timestamp as prediction_time,
            p.risk_score,
            p.risk_level,
            p.alert_triggered,
            da.doctor_id,
            da.action_taken,
            da.sepsis_confirmed,
            da.confidence_score,
            po.actual_sepsis,
            po.outcome,
            CASE 
                WHEN po.actual_sepsis = TRUE AND p.risk_level IN ('HIGH', 'CRITICAL') THEN 'TRUE_POSITIVE'
                WHEN po.actual_sepsis = FALSE AND p.risk_level IN ('HIGH', 'CRITICAL') THEN 'FALSE_POSITIVE'
                WHEN po.actual_sepsis = TRUE AND p.risk_level IN ('LOW', 'MODERATE') THEN 'FALSE_NEGATIVE'
                ELSE 'TRUE_NEGATIVE'
            END as prediction_result
        FROM hil_predictions p
        LEFT JOIN hil_doctor_actions da ON p.prediction_id = da.prediction_id
        LEFT JOIN hil_patient_outcomes po ON p.prediction_id = po.prediction_id;
        
        -- HIL Performance Summary View
        CREATE OR REPLACE VIEW hil_performance_summary AS
        SELECT 
            DATE_TRUNC('day', prediction_time) as date,
            COUNT(*) as total_predictions,
            COUNT(CASE WHEN prediction_result = 'TRUE_POSITIVE' THEN 1 END) as true_positives,
            COUNT(CASE WHEN prediction_result = 'FALSE_POSITIVE' THEN 1 END) as false_positives,
            COUNT(CASE WHEN prediction_result = 'FALSE_NEGATIVE' THEN 1 END) as false_negatives,
            COUNT(CASE WHEN prediction_result = 'TRUE_NEGATIVE' THEN 1 END) as true_negatives,
            AVG(risk_score) as avg_risk_score,
            COUNT(CASE WHEN alert_triggered THEN 1 END) as alerts_triggered
        FROM hil_dashboard
        GROUP BY DATE_TRUNC('day', prediction_time)
        ORDER BY date DESC;
        
        -- Doctor Action Summary View
        CREATE OR REPLACE VIEW hil_doctor_summary AS
        SELECT 
            doctor_id,
            COUNT(*) as total_actions,
            COUNT(CASE WHEN sepsis_confirmed = TRUE THEN 1 END) as confirmed_sepsis,
            COUNT(CASE WHEN sepsis_confirmed = FALSE THEN 1 END) as ruled_out_sepsis,
            AVG(confidence_score) as avg_confidence,
            COUNT(CASE WHEN treatment_initiated = TRUE THEN 1 END) as treatments_initiated
        FROM hil_doctor_actions
        GROUP BY doctor_id
        ORDER BY total_actions DESC;
        """
        
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            cursor.execute(views_sql)
            conn.commit()
            
            cursor.close()
            conn.close()
            
            logger.info("✅ HIL views created successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create HIL views: {e}")
            return False
    
    def insert_sample_data(self):
        """Insert sample HIL data for testing"""
        logger.info("📊 Inserting sample HIL data...")
        
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            # Sample prediction data
            sample_predictions = [
                {
                    'patient_id': 'BABY_001',
                    'prediction_id': 'pred-001-001',
                    'risk_score': 0.85,
                    'risk_level': 'HIGH',
                    'features': json.dumps({
                        'heart_rate': 180,
                        'temperature': 38.5,
                        'white_blood_cells': 15000,
                        'eos_risk_score': 8
                    }),
                    'model_version': 'v1.0.0',
                    'alert_triggered': True,
                    'threshold_exceeded': True,
                    'doctor_notified': True
                },
                {
                    'patient_id': 'BABY_002', 
                    'prediction_id': 'pred-002-001',
                    'risk_score': 0.65,
                    'risk_level': 'MODERATE',
                    'features': json.dumps({
                        'heart_rate': 160,
                        'temperature': 37.8,
                        'white_blood_cells': 12000,
                        'eos_risk_score': 5
                    }),
                    'model_version': 'v1.0.0',
                    'alert_triggered': False,
                    'threshold_exceeded': False,
                    'doctor_notified': False
                }
            ]
            
            # Insert predictions
            for pred in sample_predictions:
                cursor.execute("""
                    INSERT INTO hil_predictions 
                    (patient_id, prediction_id, risk_score, risk_level, features, 
                     model_version, alert_triggered, threshold_exceeded, doctor_notified)
                    VALUES (%(patient_id)s, %(prediction_id)s, %(risk_score)s, %(risk_level)s, 
                           %(features)s, %(model_version)s, %(alert_triggered)s, 
                           %(threshold_exceeded)s, %(doctor_notified)s)
                """, pred)
            
            # Sample doctor actions
            cursor.execute("""
                INSERT INTO hil_doctor_actions 
                (prediction_id, patient_id, doctor_id, action_taken, clinical_reasoning,
                 sepsis_confirmed, confidence_score, additional_tests_ordered, treatment_initiated)
                VALUES 
                ('pred-001-001', 'BABY_001', 'DR_SMITH', 'immediate_evaluation', 
                 'High risk score with elevated vital signs warranting immediate assessment',
                 TRUE, 4, ARRAY['blood_culture', 'complete_blood_count'], TRUE),
                ('pred-002-001', 'BABY_002', 'DR_JONES', 'continued_monitoring',
                 'Moderate risk, will monitor closely for 4 hours', 
                 FALSE, 3, ARRAY['repeat_vitals'], FALSE)
            """)
            
            # Sample outcomes
            cursor.execute("""
                INSERT INTO hil_patient_outcomes
                (patient_id, prediction_id, actual_sepsis, severity_level, outcome, prediction_accuracy)
                VALUES 
                ('BABY_001', 'pred-001-001', TRUE, 'severe', 'discharged', TRUE),
                ('BABY_002', 'pred-002-001', FALSE, NULL, 'discharged', TRUE)
            """)
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info("✅ Sample HIL data inserted successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to insert sample data: {e}")
            return False
    
    def test_database_connection(self):
        """Test database connection and basic queries"""
        logger.info("🔍 Testing HIL database connection...")
        
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            # Test basic query
            cursor.execute("SELECT COUNT(*) FROM hil_predictions")
            prediction_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM hil_doctor_actions") 
            action_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM hil_patient_outcomes")
            outcome_count = cursor.fetchone()[0]
            
            cursor.close()
            conn.close()
            
            logger.info(f"✅ Database connection successful")
            logger.info(f"   📊 Predictions: {prediction_count}")
            logger.info(f"   👨‍⚕️ Doctor Actions: {action_count}")
            logger.info(f"   📈 Outcomes: {outcome_count}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            return False
    
    def setup_complete_hil_database(self):
        """Setup complete HIL database"""
        logger.info("🏥 Setting up complete HIL database...")
        
        steps = [
            ('Create Database', self.create_database),
            ('Create Schema', self.create_hil_schema),
            ('Create Views', self.create_hil_views),
            ('Insert Sample Data', self.insert_sample_data),
            ('Test Connection', self.test_database_connection)
        ]
        
        for step_name, step_func in steps:
            logger.info(f"\\n🔄 {step_name}...")
            success = step_func()
            
            if not success:
                logger.error(f"❌ Failed at: {step_name}")
                return False
        
        logger.info("\\n✅ HIL DATABASE SETUP COMPLETE!")
        logger.info("="*50)
        logger.info("Database ready for ML + HIL workflow")
        return True


def main():
    """Main setup function"""
    print("="*60)
    print("🏥 NEOVANCE-AI: HIL DATABASE SETUP")
    print("="*60)
    
    setup = HILDatabaseSetup()
    
    if setup.setup_complete_hil_database():
        print("\\n🎉 Setup completed successfully!")
        print("\\nNext steps:")
        print("1. Run: python run_ml_hil_system.py")
        print("2. Test workflow: python test_complete_hil_workflow.py")
    else:
        print("\\n❌ Setup failed. Please check logs.")


if __name__ == "__main__":
    main()