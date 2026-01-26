"""
Pathway Data Simulator - Generates live NICU vital signs data
Writes to CSV stream for Pathway ETL consumption
"""

import time
import csv
import random
from datetime import datetime
from pathlib import Path


class VitalsSimulator:
    """Generates realistic NICU vital signs with smooth transitions"""
    
    def __init__(self):
        self.hr_base = 80.0
        self.spo2_base = 98.0
        self.rr_base = 16.0
        self.temp_base = 37.0
        self.map_base = 35.0
        self.sepsis_mode = False
        self.sepsis_counter = 0
        
    def generate_vitals(self):
        """Generate smooth vital signs"""
        if self.sepsis_mode and self.sepsis_counter < 5:
            self.hr_base += random.uniform(8, 12)
            self.spo2_base -= random.uniform(1.5, 3)
            self.rr_base += random.uniform(3, 5)
            self.temp_base += random.uniform(0.3, 0.5)
            self.sepsis_counter += 1
        elif self.sepsis_mode and self.sepsis_counter >= 5:
            self.sepsis_mode = False
            print("[SIMULATOR] Sepsis cycle complete")
        
        hr = self.hr_base + random.uniform(-0.5, 0.5)
        spo2 = self.spo2_base + random.uniform(-0.3, 0.3)
        rr = self.rr_base + random.uniform(-0.4, 0.4)
        temp = self.temp_base + random.uniform(-0.1, 0.1)
        map_val = self.map_base + random.uniform(-0.5, 0.5)
        
        if not self.sepsis_mode:
            self.hr_base += (80.0 - self.hr_base) * 0.05
            self.spo2_base += (98.0 - self.spo2_base) * 0.05
            self.rr_base += (16.0 - self.rr_base) * 0.05
            self.temp_base += (37.0 - self.temp_base) * 0.05
            self.map_base += (35.0 - self.map_base) * 0.05
        
        hr = max(60, min(180, hr))
        spo2 = max(85, min(100, spo2))
        rr = max(10, min(80, rr))
        temp = max(35.5, min(40.0, temp))
        map_val = max(20, min(50, map_val))
        
        risk_score = abs(hr - 80) * 0.5 + abs(spo2 - 98) * 3 + abs(temp - 37) * 10
        
        if risk_score > 20:
            status = "CRITICAL"
        elif risk_score > 10:
            status = "WARNING"
        else:
            status = "OK"
        
        return {
            "timestamp": datetime.now().isoformat(),
            "mrn": "B001",
            "hr": round(hr, 1),
            "spo2": round(spo2, 1),
            "rr": round(rr, 1),
            "temp": round(temp, 2),
            "map": round(map_val, 1),
            "risk_score": round(risk_score, 2),
            "status": status
        }
    
    def trigger_sepsis(self):
        """Trigger sepsis simulation"""
        self.sepsis_mode = True
        self.sepsis_counter = 0
        print("[SIMULATOR] Sepsis spike triggered")


def run_simulator():
    """Main simulator loop - writes to CSV stream"""
    data_dir = Path(__file__).parent.parent / "data"
    data_dir.mkdir(exist_ok=True)
    
    stream_file = data_dir / "stream.csv"
    trigger_file = data_dir / "sepsis_trigger.txt"
    
    # Create CSV with headers if it doesn't exist
    if not stream_file.exists():
        with open(stream_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'timestamp', 'mrn', 'hr', 'spo2', 'rr', 'temp', 'map', 'risk_score', 'status'
            ])
            writer.writeheader()
    
    simulator = VitalsSimulator()
    last_trigger_check = None
    
    print("="*70)
    print("PATHWAY SIMULATOR - NICU Vitals Generator")
    print("="*70)
    print(f"Writing to: {stream_file}")
    print(f"Monitoring: {trigger_file}")
    print("Generating vitals every 3 seconds...")
    print("Press Ctrl+C to stop")
    print("="*70)
    
    try:
        while True:
            # Check for sepsis trigger
            if trigger_file.exists():
                trigger_time = trigger_file.read_text().strip()
                if trigger_time != last_trigger_check:
                    simulator.trigger_sepsis()
                    last_trigger_check = trigger_time
            
            vitals = simulator.generate_vitals()
            
            # Append to CSV stream
            with open(stream_file, 'a', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=vitals.keys())
                writer.writerow(vitals)
            
            print(f"[{vitals['timestamp']}] MRN:{vitals['mrn']} HR:{vitals['hr']} "
                  f"SpO2:{vitals['spo2']}% Risk:{vitals['risk_score']} {vitals['status']}")
            
            time.sleep(3)
            
    except KeyboardInterrupt:
        print("\n[SIMULATOR] Stopped by user")


if __name__ == "__main__":
    run_simulator()
