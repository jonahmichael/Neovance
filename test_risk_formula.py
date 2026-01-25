"""
Test the weighted deviation-based risk scoring formula
"""
import sqlite3
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

# Clinical Parameters for 28-week Premature Infant
RISK_PARAMS = {
    'hr': {'mu': 145.0, 'weight': 1.0, 'power': 2},
    'spo2': {'mu': 95.0, 'weight': 3.0, 'power': 4},
    'rr': {'mu': 50.0, 'weight': 1.5, 'power': 2},
    'temp': {'mu': 37.0, 'weight': 1.0, 'power': 3},
    'map': {'mu': 35.0, 'weight': 2.0, 'power': 2}
}

# Default standard deviations (used when insufficient data)
DEFAULT_SD = {
    'hr': 15.0,      # ±1σ = 15 bpm (120-170 range)
    'spo2': 2.5,     # ±1σ = 2.5% (90-97.5 range)
    'rr': 10.0,      # ±1σ = 10 bpm (40-60 range)
    'temp': 0.5,     # ±1σ = 0.5°C (36.5-37.5 range)
    'map': 5.0       # ±1σ = 5 mmHg (30-40 range)
}


def calculate_risk_score(hr, spo2, rr, temp, map_val, use_sd=None):
    """
    Calculate weighted deviation-based risk score.
    
    Formula: Risk = Σ W_i · (|X_i - μ_i| / σ_i)^P_i
    """
    if use_sd is None:
        use_sd = DEFAULT_SD
    
    risk_total = 0.0
    components = {}
    
    vitals = {
        'hr': hr,
        'spo2': spo2,
        'rr': rr,
        'temp': temp,
        'map': map_val
    }
    
    print("\n" + "="*70)
    print("RISK SCORE CALCULATION")
    print("="*70)
    print(f"Vitals: HR={hr} SpO2={spo2} RR={rr} Temp={temp} MAP={map_val}\n")
    
    for vital_name, vital_value in vitals.items():
        params = RISK_PARAMS[vital_name]
        
        # Calculate normalized deviation (z-score)
        deviation = abs(vital_value - params['mu'])
        normalized = deviation / use_sd[vital_name]
        
        # Apply power function for sensitivity
        powered = normalized ** params['power']
        
        # Apply weight for relative importance
        component = params['weight'] * powered
        
        components[vital_name] = component
        risk_total += component
        
        print(f"{vital_name.upper():5s}: |{vital_value:.1f} - {params['mu']:.1f}| / {use_sd[vital_name]:.2f} = {normalized:.2f}")
        print(f"       Weight={params['weight']:.1f} × (z-score)^{params['power']} = {component:.3f}")
    
    print(f"\n{'='*70}")
    print(f"TOTAL RISK SCORE: {risk_total:.2f}")
    print(f"{'='*70}\n")
    
    # Determine status
    if risk_total > 20:
        status = "CRITICAL ⚠️"
    elif risk_total > 10:
        status = "WARNING ⚡"
    else:
        status = "OK ✓"
    
    print(f"Status: {status}\n")
    
    return round(risk_total, 2)


if __name__ == "__main__":
    print("\n" + "="*70)
    print("TESTING WEIGHTED DEVIATION-BASED RISK FORMULA")
    print("="*70)
    
    # Test Case 1: NORMAL infant (close to ideal)
    print("\n### TEST 1: NORMAL Vitals (Low Risk)")
    risk1 = calculate_risk_score(
        hr=145, spo2=95, rr=50, temp=37.0, map_val=35
    )
    
    # Test Case 2: Mild deviation
    print("\n### TEST 2: Mild Deviation (Moderate Risk)")
    risk2 = calculate_risk_score(
        hr=160, spo2=92, rr=55, temp=37.5, map_val=40
    )
    
    # Test Case 3: SEPSIS - Critical SpO2 drop
    print("\n### TEST 3: SEPSIS - Critical SpO2 Drop (HIGH RISK)")
    risk3 = calculate_risk_score(
        hr=180, spo2=85, rr=70, temp=36.0, map_val=28
    )
    
    # Test Case 4: Using actual data from simulator
    print("\n### TEST 4: Real Simulator Data")
    # Example from your simulator output: HR: 141 | SpO2: 99% | RR: 52 | Temp: 37.0°C | MAP: 34
    risk4 = calculate_risk_score(
        hr=141, spo2=99, rr=52, temp=37.0, map_val=34
    )
    
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"Test 1 (Normal):     Risk = {risk1:.2f}")
    print(f"Test 2 (Mild):       Risk = {risk2:.2f}")
    print(f"Test 3 (Sepsis):     Risk = {risk3:.2f}")
    print(f"Test 4 (Real Data):  Risk = {risk4:.2f}")
    print("="*70 + "\n")
