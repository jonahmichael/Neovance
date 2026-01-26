-- PostgreSQL + TimescaleDB Schema for Neovance HIL System
-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Table 1: alerts (HIL State + Action Log - Hypertable)
-- This is the core time-series table for Human-in-the-Loop learning
CREATE TABLE alerts (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    mrn VARCHAR(10) NOT NULL,
    risk_score FLOAT,
    features_json JSONB,  -- Critical: snapshot of all patient features used for AI prediction
    doctor_id VARCHAR(10),
    doctor_action VARCHAR(50),  -- 'Treat', 'Lab', 'Observe', 'Dismiss'
    action_detail TEXT  -- e.g., 'Ampi+Genta', '4 hours'
);

-- Convert alerts table into TimescaleDB hypertable
SELECT create_hypertable('alerts', 'timestamp');

-- Create indexes for efficient querying
CREATE INDEX idx_alerts_mrn ON alerts (mrn);
CREATE INDEX idx_alerts_doctor_id ON alerts (doctor_id);
CREATE INDEX idx_alerts_risk_score ON alerts (risk_score);
CREATE INDEX idx_alerts_features_json ON alerts USING GIN (features_json);

-- Table 2: outcomes (The Reward Signal - Standard Table)
-- Links delayed outcomes back to specific doctor actions
CREATE TABLE outcomes (
    id BIGSERIAL PRIMARY KEY,
    alert_id BIGINT NOT NULL REFERENCES alerts(id),  -- Foreign key to alerts table
    outcome_time TIMESTAMPTZ,  -- When outcome was determined
    sepsis_confirmed BOOLEAN,  -- THE BINARY REWARD: TRUE/FALSE for sepsis
    lab_result TEXT,  -- Detailed lab result
    patient_status_6hr VARCHAR(50),  -- 'Improved', 'Worsened', 'Stable'
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for outcome lookups
CREATE INDEX idx_outcomes_alert_id ON outcomes (alert_id);
CREATE INDEX idx_outcomes_sepsis_confirmed ON outcomes (sepsis_confirmed);

-- Table 3: realtime_vitals (High-frequency vitals from Pathway)
-- This replaces the SQLite live_vitals table
CREATE TABLE realtime_vitals (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    mrn VARCHAR(10) NOT NULL,
    hr FLOAT,  -- Heart rate
    spo2 FLOAT,  -- SpO2 percentage
    rr FLOAT,  -- Respiratory rate
    temp FLOAT,  -- Temperature
    map FLOAT,  -- Mean arterial pressure
    risk_score FLOAT,  -- EOS risk score
    status VARCHAR(20),  -- ROUTINE_CARE, ENHANCED_MONITORING, HIGH_RISK
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Convert realtime_vitals to hypertable for high-frequency data
SELECT create_hypertable('realtime_vitals', 'timestamp');

-- Indexes for realtime vitals
CREATE INDEX idx_realtime_vitals_mrn ON realtime_vitals (mrn);
CREATE INDEX idx_realtime_vitals_status ON realtime_vitals (status);

-- Table 4: babies (Patient information)
-- Migrate from existing baby data
CREATE TABLE babies (
    mrn VARCHAR(10) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    gestational_age_weeks INTEGER,
    birth_weight FLOAT,
    current_weight FLOAT,
    maternal_gbs VARCHAR(20),  -- positive, negative, unknown
    maternal_fever BOOLEAN,
    rom_hours FLOAT,  -- Rupture of membranes duration
    antibiotics_given BOOLEAN,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Sample data for testing
INSERT INTO babies (mrn, name, gestational_age_weeks, birth_weight, current_weight, maternal_gbs, maternal_fever, rom_hours, antibiotics_given) 
VALUES 
('B001', 'Amelia Rodriguez', 37, 2.8, 2.9, 'negative', false, 6.0, false),
('B002', 'Lucas Chen', 35, 2.2, 2.3, 'positive', true, 18.0, true),
('B003', 'Sophie Williams', 39, 3.1, 3.2, 'unknown', false, 4.0, false);

-- HIL Analytics Views
-- View 1: Latest vitals per patient
CREATE VIEW latest_vitals AS
SELECT DISTINCT ON (mrn)
    mrn, timestamp, hr, spo2, rr, temp, map, risk_score, status
FROM realtime_vitals
ORDER BY mrn, timestamp DESC;

-- View 2: Doctor action summary
CREATE VIEW doctor_action_summary AS
SELECT 
    doctor_id,
    doctor_action,
    COUNT(*) as action_count,
    AVG(risk_score) as avg_risk_score,
    DATE_TRUNC('day', timestamp) as action_date
FROM alerts
WHERE doctor_action IS NOT NULL
GROUP BY doctor_id, doctor_action, DATE_TRUNC('day', timestamp)
ORDER BY action_date DESC, action_count DESC;

-- View 3: HIL learning dataset (alerts with outcomes)
CREATE VIEW hil_training_data AS
SELECT 
    a.id as alert_id,
    a.timestamp,
    a.mrn,
    a.risk_score,
    a.features_json,
    a.doctor_action,
    a.action_detail,
    o.sepsis_confirmed,
    o.patient_status_6hr,
    (o.sepsis_confirmed IS TRUE) as positive_outcome
FROM alerts a
LEFT JOIN outcomes o ON a.id = o.alert_id
WHERE a.doctor_action IS NOT NULL;

-- Retention policy for high-frequency data (optional)
-- Keep detailed vitals for 30 days, then downsample
-- SELECT add_retention_policy('realtime_vitals', INTERVAL '30 days');

COMMENT ON TABLE alerts IS 'Core HIL table: AI predictions + doctor actions for supervised learning';
COMMENT ON TABLE outcomes IS 'Delayed reward signals linked to doctor actions';
COMMENT ON TABLE realtime_vitals IS 'High-frequency time-series vitals from Pathway ETL';
COMMENT ON COLUMN alerts.features_json IS 'JSONB snapshot of all patient state used for AI prediction';
COMMENT ON COLUMN outcomes.sepsis_confirmed IS 'Binary reward signal for HIL learning';