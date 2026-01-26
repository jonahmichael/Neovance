#!/usr/bin/env python3
"""
Generate synthetic neonatal sepsis training dataset
Based on clinical patterns and validated EOS risk factors

This creates a labeled dataset for training sepsis prediction models
with realistic clinical scenarios and proper target labels.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

# Import the existing EOS calculator for feature engineering
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

try:
    from test_eos_calculator import calculate_eos_risk, categorize_eos_status
except ImportError:
    # Fallback implementation if import fails
    def calculate_eos_risk(ga_weeks, ga_days, temp_celsius, rom_hours, gbs_status, antibiotic_type, clinical_exam):
        """Simplified EOS risk calculation"""
        risk = 0.5  # baseline
        if ga_weeks < 37: risk *= 2.0
        if temp_celsius >= 38.0: risk *= 3.0
        if rom_hours > 18: risk *= 2.0
        if gbs_status.lower() == "positive": risk *= 4.0
        if clinical_exam.lower() == "abnormal": risk *= 15.0
        return min(risk, 50.0)
    
    def categorize_eos_status(risk_score, clinical_exam):
        if clinical_exam.lower() == "abnormal": return "HIGH_RISK"
        if risk_score >= 3.0: return "HIGH_RISK"
        elif risk_score >= 1.0: return "ENHANCED_MONITORING"
        else: return "ROUTINE_CARE"


def generate_clinical_scenario():
    """Generate a realistic clinical scenario with proper sepsis correlation"""
    
    # Basic demographics
    ga_weeks = np.random.choice([34, 35, 36, 37, 38, 39, 40, 41], 
                                p=[0.05, 0.1, 0.1, 0.15, 0.25, 0.25, 0.08, 0.02])
    ga_days = random.randint(0, 6)
    birth_weight = np.random.normal(3.2, 0.5)  # kg
    birth_weight = max(1.5, min(5.0, birth_weight))
    
    sex = random.choice(['M', 'F'])
    race = random.choice(['white', 'black', 'hispanic', 'asian', 'other'])
    
    # Maternal risk factors
    gbs_status = np.random.choice(['negative', 'positive', 'unknown'], p=[0.75, 0.15, 0.10])
    rom_hours = np.random.exponential(8.0)  # Most short ROM, some very long
    rom_hours = min(72, max(0.5, rom_hours))
    
    # Temperature varies by risk
    if random.random() < 0.15:  # 15% chance of maternal fever
        temp_celsius = np.random.normal(38.5, 0.5)
        temp_celsius = max(38.0, min(40.0, temp_celsius))
    else:
        temp_celsius = np.random.normal(37.0, 0.3)
        temp_celsius = max(36.0, min(37.8, temp_celsius))
    
    # Antibiotics based on GBS status and risk
    if gbs_status == "positive" or temp_celsius >= 38.0:
        antibiotic_type = random.choice(['penicillin', 'ampicillin', 'none'])
    else:
        antibiotic_type = 'none'
    
    # Clinical exam (rarely abnormal)
    clinical_exam = 'abnormal' if random.random() < 0.05 else 'normal'
    
    # Calculate EOS risk
    eos_risk = calculate_eos_risk(ga_weeks, ga_days, temp_celsius, rom_hours, 
                                  gbs_status, antibiotic_type, clinical_exam)
    eos_category = categorize_eos_status(eos_risk, clinical_exam)
    
    # Generate vital signs based on condition
    # Sepsis tends to cause: tachycardia, desaturation, tachypnea, instability
    
    # Determine if this case has sepsis (higher probability with higher EOS risk)
    sepsis_probability = 0.001  # baseline 1/1000
    if eos_category == "HIGH_RISK":
        sepsis_probability = 0.15  # 15% for high risk
    elif eos_category == "ENHANCED_MONITORING":
        sepsis_probability = 0.05  # 5% for moderate risk
    
    has_sepsis = random.random() < sepsis_probability
    
    # Sepsis groups: 1=culture proven, 2=no sepsis, 3=clinical sepsis
    if has_sepsis:
        sepsis_group = random.choice([1, 3])  # Either culture proven or clinical
    else:
        sepsis_group = 2  # No sepsis
    
    # Generate vitals influenced by sepsis status
    if has_sepsis:
        # Sepsis causes physiological stress
        hr_base = np.random.normal(140, 20)  # Tachycardia
        spo2_base = np.random.normal(91, 5)  # Desaturation
        rr_base = np.random.normal(35, 8)    # Tachypnea
        map_base = np.random.normal(32, 8)   # Hypotension
        current_temp = np.random.normal(38.2, 1.0)  # Fever or hypothermia
    else:
        # Normal vitals
        hr_base = np.random.normal(120, 15)
        spo2_base = np.random.normal(97, 3)
        rr_base = np.random.normal(25, 5)
        map_base = np.random.normal(42, 8)
        current_temp = np.random.normal(37.1, 0.4)
    
    # Ensure realistic ranges
    hr = max(60, min(180, hr_base))
    spo2 = max(85, min(100, spo2_base))
    rr = max(15, min(60, rr_base))
    map_val = max(20, min(70, map_base))
    temp = max(35.0, min(41.0, current_temp))
    
    # Additional risk factors
    comorbidities = 'yes' if random.random() < 0.2 else 'no'
    central_venous_line = 'yes' if random.random() < 0.3 else 'no'
    intubated = 'yes' if random.random() < 0.1 else 'no'
    inotropes = 'yes' if random.random() < 0.15 else 'no'
    ecmo = 'yes' if random.random() < 0.02 else 'no'
    
    # Antibiotic timing
    if antibiotic_type != 'none':
        time_to_antibiotics = np.random.exponential(2.0)  # hours
        stat_abx = 'yes' if time_to_antibiotics < 1.0 else 'no'
    else:
        time_to_antibiotics = np.nan
        stat_abx = 'no'
    
    return {
        # Demographics
        'mrn': f"B{random.randint(1000, 9999)}",
        'gestational_age_at_birth_weeks': ga_weeks + (ga_days / 7.0),
        'birth_weight_kg': round(birth_weight, 2),
        'sex': sex,
        'race': race,
        
        # Maternal factors
        'ga_weeks': ga_weeks,
        'ga_days': ga_days, 
        'maternal_temp_celsius': round(temp_celsius, 1),
        'rom_hours': round(rom_hours, 1),
        'gbs_status': gbs_status,
        'antibiotic_type': antibiotic_type,
        'clinical_exam': clinical_exam,
        
        # Current vitals
        'hr': round(hr, 1),
        'spo2': round(spo2, 1),
        'rr': round(rr, 1),
        'temp_celsius': round(temp, 1),
        'map': round(map_val, 1),
        
        # Risk factors
        'comorbidities': comorbidities,
        'central_venous_line': central_venous_line,
        'intubated_at_time_of_sepsis_evaluation': intubated,
        'inotrope_at_time_of_sepsis_eval': inotropes,
        'ecmo': ecmo,
        'stat_abx': stat_abx,
        'time_to_antibiotics': round(time_to_antibiotics, 2) if not np.isnan(time_to_antibiotics) else None,
        
        # EOS calculation results
        'eos_risk_score': round(eos_risk, 2),
        'eos_category': eos_category,
        
        # Target variable
        'sepsis_group': sepsis_group,
        'has_sepsis': 1 if has_sepsis else 0,
        
        # Timestamp
        'timestamp': datetime.now() - timedelta(days=random.randint(0, 365))
    }


def generate_dataset(n_samples=5000):
    """Generate a complete training dataset"""
    print(f"Generating {n_samples} clinical scenarios...")
    
    data = []
    for i in range(n_samples):
        if i % 1000 == 0:
            print(f"Generated {i} samples...")
        
        scenario = generate_clinical_scenario()
        data.append(scenario)
    
    df = pd.DataFrame(data)
    
    # Print dataset statistics
    print(f"\nDataset Statistics:")
    print(f"Total samples: {len(df)}")
    print(f"Sepsis cases: {df['has_sepsis'].sum()} ({df['has_sepsis'].mean()*100:.2f}%)")
    print(f"Culture-proven sepsis: {sum(df['sepsis_group'] == 1)}")
    print(f"Clinical sepsis: {sum(df['sepsis_group'] == 3)}")
    print(f"No sepsis: {sum(df['sepsis_group'] == 2)}")
    
    print(f"\nEOS Risk Categories:")
    print(df['eos_category'].value_counts())
    
    print(f"\nGestational Age Distribution:")
    print(f"Preterm (<37 weeks): {sum(df['gestational_age_at_birth_weeks'] < 37)} ({sum(df['gestational_age_at_birth_weeks'] < 37)/len(df)*100:.1f}%)")
    
    return df


if __name__ == "__main__":
    # Generate the training dataset
    np.random.seed(42)  # For reproducibility
    random.seed(42)
    
    # Generate 5000 samples
    df = generate_dataset(5000)
    
    # Save the dataset
    output_file = "data/neonatal_sepsis_training.csv"
    os.makedirs("data", exist_ok=True)
    df.to_csv(output_file, index=False)
    
    print(f"\n✅ Dataset saved to: {output_file}")
    print(f"Ready for training with train_sepsis_model.py!")