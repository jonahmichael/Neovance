"""
Neovance-AI: Real-time NICU Bedside Monitor Simulator
Generates synthetic physiological data for a premature baby with NORMAL/SEPSIS modes.
"""

import csv
import os
import time
from datetime import datetime
from pathlib import Path
import random
import keyboard
import threading


class NICUSimulator:
    """Simulates a bedside monitor for Baby_A with state-based physiological data."""
    
    # Patient configuration
    PATIENT_ID = "Baby_A"
    
    # Baseline vitals (NORMAL state)
    BASELINE_HR = 145
    BASELINE_SPO2 = 98
    BASELINE_RR = 50
    BASELINE_TEMP = 37.0
    BASELINE_MAP = 35
    
    # Safety limits
    MIN_SPO2 = 40
    MAX_HR = 220
    
    def __init__(self):
        self.state = "NORMAL"  # Current state: NORMAL or SEPSIS
        
        # Sepsis drift accumulators (reset when entering sepsis mode)
        self.sepsis_hr_drift = 0
        self.sepsis_spo2_drift = 0
        self.sepsis_temp_drift = 0
        
        # File setup
        self.data_dir = Path("data")
        self.csv_path = self.data_dir / "stream.csv"
        self._initialize_csv()
        
        # Keyboard listener
        self._setup_keyboard_listener()
        
    def _initialize_csv(self):
        """Create data directory and CSV file with headers if needed."""
        self.data_dir.mkdir(exist_ok=True)
        
        if not self.csv_path.exists():
            with open(self.csv_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['timestamp', 'patient_id', 'hr', 'spo2', 'rr', 'temp', 'map'])
                f.flush()
            print(f"[INFO] Created {self.csv_path}")
        else:
            print(f"[INFO] Appending to existing {self.csv_path}")
    
    def _setup_keyboard_listener(self):
        """Setup non-blocking keyboard listener for mode switching."""
        keyboard.on_press_key('s', lambda _: self._switch_to_sepsis())
        keyboard.on_press_key('n', lambda _: self._switch_to_normal())
    
    def _switch_to_sepsis(self):
        """Switch to SEPSIS mode and reset drift accumulators."""
        if self.state != "SEPSIS":
            self.state = "SEPSIS"
            self.sepsis_hr_drift = 0
            self.sepsis_spo2_drift = 0
            self.sepsis_temp_drift = 0
            print("\n[ALERT] SWITCHED TO SEPSIS MODE")
    
    def _switch_to_normal(self):
        """Switch to NORMAL mode."""
        if self.state != "NORMAL":
            self.state = "NORMAL"
            print("\n[INFO] SWITCHED TO NORMAL MODE")
    
    def _generate_normal_vitals(self):
        """Generate stable vitals with Gaussian noise around baselines."""
        hr = max(130, min(160, random.gauss(self.BASELINE_HR, 5)))
        spo2 = max(95, min(100, random.gauss(self.BASELINE_SPO2, 1)))
        rr = max(40, min(60, random.gauss(self.BASELINE_RR, 3)))
        temp = max(36.5, min(37.5, random.gauss(self.BASELINE_TEMP, 0.2)))
        map_val = max(30, min(40, random.gauss(self.BASELINE_MAP, 2)))
        
        return hr, spo2, rr, temp, map_val
    
    def _generate_sepsis_vitals(self):
        """Generate deteriorating vitals with continuous drift + noise."""
        # Update drift accumulators (per iteration, ~1 second)
        self.sepsis_hr_drift += 1.0  # +1 bpm per second
        self.sepsis_spo2_drift -= 0.5  # -0.5% per second
        self.sepsis_temp_drift -= 0.02  # Slow hypothermia
        
        # Apply drift + noise
        hr = self.BASELINE_HR + self.sepsis_hr_drift + random.gauss(0, 3)
        spo2 = self.BASELINE_SPO2 + self.sepsis_spo2_drift + random.gauss(0, 2)
        temp = self.BASELINE_TEMP + self.sepsis_temp_drift + random.gauss(0, 0.1)
        
        # Respiratory distress: increased variability
        rr = self.BASELINE_RR + random.gauss(10, 8)
        
        # MAP: slight decrease
        map_val = self.BASELINE_MAP + random.gauss(-3, 2)
        
        # Apply safety limits
        hr = min(hr, self.MAX_HR)
        spo2 = max(spo2, self.MIN_SPO2)
        temp = max(temp, 35.0)  # Prevent extreme hypothermia
        rr = max(20, min(80, rr))
        map_val = max(20, min(45, map_val))
        
        return hr, spo2, rr, temp, map_val
    
    def _get_vitals(self):
        """Get vitals based on current state."""
        if self.state == "NORMAL":
            return self._generate_normal_vitals()
        else:
            return self._generate_sepsis_vitals()
    
    def _write_data_point(self, vitals):
        """Write a single data point to CSV with immediate flush."""
        timestamp = datetime.now().isoformat()
        hr, spo2, rr, temp, map_val = vitals
        
        with open(self.csv_path, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                timestamp,
                self.PATIENT_ID,
                round(hr, 1),
                round(spo2, 1),
                round(rr, 1),
                round(temp, 2),
                round(map_val, 1)
            ])
            f.flush()  # CRITICAL: Force immediate write to disk
    
    def _print_status(self, vitals):
        """Print formatted console status."""
        hr, spo2, rr, temp, map_val = vitals
        
        if self.state == "NORMAL":
            status = f"[NORMAL] HR: {hr:.0f} | SpO2: {spo2:.0f}% | RR: {rr:.0f} | Temp: {temp:.1f}°C | MAP: {map_val:.0f}"
        else:
            status = f"[SEPSIS] HR: {hr:.0f} | SpO2: {spo2:.0f}% | RR: {rr:.0f} | Temp: {temp:.1f}°C | MAP: {map_val:.0f}"
        
        print(status)
    
    def run(self):
        """Main simulation loop: generate data every 1 second."""
        print("\n" + "="*70)
        print("NEOVANCE-AI: NICU Monitor Simulator")
        print("="*70)
        print("Controls:")
        print("  Press 's' → Switch to SEPSIS mode")
        print("  Press 'n' → Switch to NORMAL mode")
        print("  Press Ctrl+C → Stop simulation")
        print("="*70 + "\n")
        
        try:
            while True:
                vitals = self._get_vitals()
                self._write_data_point(vitals)
                self._print_status(vitals)
                time.sleep(1.0)  # 1 second interval
                
        except KeyboardInterrupt:
            print("\n\n[INFO] Simulation stopped. Data saved to", self.csv_path)


if __name__ == "__main__":
    simulator = NICUSimulator()
    simulator.run()
