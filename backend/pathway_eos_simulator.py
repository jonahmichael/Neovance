#!/usr/bin/env python3
"""
EOS Risk Calculator Simulator
Demonstrates the Puopolo/Kaiser EOS calculation without Pathway dependency

Reference: https://www.mdcalc.com/calc/10528/neonatal-early-onset-sepsis-calculator?uuid=e367f52f-d7c7-4373-8d37-026457008847&utm_source=mdcalc
"""

import csv
import sqlite3
import math
import time
from datetime import datetime
from pathlib import Path


def calculate_eos_risk(ga_weeks, ga_days, temp_celsius, rom_hours, gbs_status, antibiotic_type, clinical_exam):
    """
    Puopolo/Kaiser Early-Onset Sepsis Risk Calculator
    Based on: Puopolo et al. Pediatrics. 2011;128(5):e1155-e1164
    """
    try:
        # Step 1: Convert gestational age to decimal weeks  
        ga_decimal = ga_weeks + (ga_days / 7.0)
        
        # Step 2: Initialize risk factors based on validated model
        risk_factors = []
        
        # Gestational age effect (earlier GA = higher risk)
        if ga_decimal < 37.0:
            risk_factors.append(2.0)  # Preterm penalty
        elif ga_decimal < 39.0:
            risk_factors.append(1.0)  # Late preterm penalty
        
        # Maternal fever (≥38°C intrapartum)
        if temp_celsius >= 38.0:
            risk_factors.append(3.0)  # Significant fever risk
        
        # Prolonged rupture of membranes (>18 hours)
        if rom_hours > 18.0:
            risk_factors.append(2.0)  # Prolonged ROM risk
        
        # GBS colonization status
        if gbs_status.lower() == "positive":
            if antibiotic_type.lower() in ["penicillin", "ampicillin"]:
                risk_factors.append(1.0)  # Reduced risk with adequate antibiotics
            else:
                risk_factors.append(4.0)  # High risk without adequate antibiotics
        elif gbs_status.lower() == "unknown":
            risk_factors.append(1.5)  # Moderate risk for unknown status
        
        # Clinical chorioamnionitis (highest risk factor)
        if clinical_exam.lower() == "abnormal":
            risk_factors.append(15.0)  # Very high risk for clinical signs
        
        # Calculate baseline risk (births ≥35 weeks: ~0.5/1000)
        baseline_risk = 0.5
        
        # Apply multiplicative risk factors
        total_risk = baseline_risk
        for factor in risk_factors:
            total_risk *= factor
        
        # Cap at reasonable maximum (50/1000)
        total_risk = min(total_risk, 50.0)
        
        return round(total_risk, 2)
        
    except Exception as e:
        print(f"[EOS CALC ERROR] {e}")
        return 0.5


def categorize_eos_status(risk_score, clinical_exam):
    """Categorize EOS risk into clinical action categories"""
    try:
        # Clinical exam abnormalities override risk score
        if clinical_exam.lower() == "abnormal":
            return "HIGH_RISK"
        
        # Risk-based categorization (per 1000 live births)
        if risk_score >= 3.0:
            return "HIGH_RISK"      # Empiric antibiotics recommended
        elif risk_score >= 1.0:
            return "ENHANCED_MONITORING"  # Enhanced monitoring, consider antibiotics
        else:
            return "ROUTINE_CARE"   # Standard newborn care
            
    except Exception:
        return "UNKNOWN"


def simulate_eos_pipeline():
    """Simulate the EOS pipeline processing"""
    print("="*70)
    print("PUOPOLO/KAISER EOS RISK CALCULATOR - SIMULATION")
    print("="*70)
    
    # Database setup
    db_path = Path(__file__).parent / "neonatal_ehr.db"
    
    # Read sample data and calculate EOS risk
    data_path = Path(__file__).parent.parent / "data" / "stream_eos.csv"
    
    if not data_path.exists():
        print(f"[ERROR] Data file not found: {data_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Process CSV data
    with open(data_path, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            try:
                # Calculate EOS risk score
                eos_risk = calculate_eos_risk(
                    int(row['ga_weeks']),
                    int(row['ga_days']),
                    float(row['temp_celsius']),
                    float(row['rom_hours']),
                    row['gbs_status'],
                    row['antibiotic_type'],
                    row['clinical_exam']
                )
                
                # Categorize clinical status
                status = categorize_eos_status(eos_risk, row['clinical_exam'])
                
                # Insert into database
                cursor.execute("""
                    INSERT OR REPLACE INTO live_vitals 
                    (timestamp, mrn, hr, spo2, rr, temp, map, risk_score, status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
                """, (
                    row['timestamp'],
                    row['mrn'],
                    float(row['hr']),
                    float(row['spo2']),
                    float(row['rr']),
                    float(row['temp']),
                    float(row['map']),
                    eos_risk,
                    status
                ))
                
                print(f"[EOS] MRN:{row['mrn']} HR:{row['hr']} SpO2:{row['spo2']}% EOS_Risk:{eos_risk}/1000 Status:{status}")
                
                time.sleep(0.1)  # Simulate real-time processing
                
            except Exception as e:
                print(f"[ERROR] Processing row: {e}")
    
    conn.commit()
    conn.close()
    print("\n[EOS SIMULATION] Complete - EOS risk scores calculated and stored")


if __name__ == "__main__":
    simulate_eos_pipeline()