"""
Enhanced NICU Vitals Simulator - Generates realistic noisy data with clinical scenarios
Supports sepsis triggering, apnea events, and realistic physiological variations
"""

import time
import csv
import random
import math
from datetime import datetime
from pathlib import Path


class EnhancedNICUSimulator:
    """Generates realistic NICU vital signs with noise, trends, and clinical events"""
    
    def __init__(self):
        # Baseline vitals for a stable neonate
        self.hr_target = 120.0
        self.spo2_target = 95.0
        self.rr_target = 40.0
        self.temp_target = 36.8
        self.map_target = 35.0
        
        # Current values (start with some variation)
        self.hr_current = self.hr_target + random.uniform(-10, 10)
        self.spo2_current = self.spo2_target + random.uniform(-3, 3)
        self.rr_current = self.rr_target + random.uniform(-5, 5)
        self.temp_current = self.temp_target + random.uniform(-0.5, 0.5)
        self.map_current = self.map_target + random.uniform(-5, 5)
        
        # Clinical state management
        self.sepsis_mode = False
        self.sepsis_duration = 0
        self.apnea_mode = False
        self.apnea_duration = 0
        self.bradycardia_mode = False
        self.bradycardia_duration = 0
        
        # Time tracking for natural variations
        self.time_counter = 0
        self.noise_amplitude = 1.0
        
    def add_physiological_noise(self, value, base_noise, frequency_factor=1.0):
        """Add realistic physiological noise with multiple frequency components"""
        # High frequency noise (breathing, movement artifacts)
        high_freq_noise = random.uniform(-base_noise, base_noise)
        
        # Medium frequency variations (sleep cycles, feeding)
        med_freq_noise = math.sin(self.time_counter * 0.05 * frequency_factor) * base_noise * 0.5
        
        # Low frequency trends (circadian rhythms, development)
        low_freq_noise = math.sin(self.time_counter * 0.01 * frequency_factor) * base_noise * 0.3
        
        return value + high_freq_noise + med_freq_noise + low_freq_noise
    
    def simulate_sepsis_physiology(self):
        """Simulate sepsis-induced physiological changes"""
        if self.sepsis_mode:
            self.sepsis_duration += 1
            severity = min(self.sepsis_duration / 10.0, 1.0)  # Gradual worsening
            
            # Sepsis targets: tachycardia, hypoxia, tachypnea, fever/hypothermia, hypotension
            self.hr_target = 120 + (60 * severity)  # Up to 180 bpm
            self.spo2_target = 95 - (15 * severity)  # Down to 80%
            self.rr_target = 40 + (40 * severity)  # Up to 80 bpm
            self.temp_target = 36.8 + random.choice([1, -1]) * (2.0 * severity)  # Fever or hypothermia
            self.map_target = 35 - (15 * severity)  # Down to 20 mmHg
            
            # Increase noise during sepsis (physiological instability)
            self.noise_amplitude = 1.0 + (2.0 * severity)
            
            if self.sepsis_duration > 50:  # Auto-resolve after ~3 minutes
                print("[SIMULATOR] Sepsis episode resolving...")
                self.sepsis_mode = False
                self.sepsis_duration = 0
                self.noise_amplitude = 1.0
    
    def simulate_apnea_event(self):
        """Simulate apnea with bradycardia and desaturation"""
        if random.random() < 0.05:  # 5% chance of spontaneous apnea
            self.apnea_mode = True
            self.apnea_duration = 0
            print("[SIMULATOR] Apnea event started")
        
        if self.apnea_mode:
            self.apnea_duration += 1
            # During apnea: RR drops to near zero, SpO2 falls, HR drops
            self.rr_target = 5.0
            self.spo2_target = max(80, 95 - (self.apnea_duration * 2))
            self.hr_target = max(80, 120 - (self.apnea_duration * 3))
            
            if self.apnea_duration > 8:  # Resolve after ~24 seconds
                print("[SIMULATOR] Apnea resolved")
                self.apnea_mode = False
                self.rr_target = 40.0
                self.spo2_target = 95.0
                self.hr_target = 120.0
    
    def update_vitals_with_momentum(self):
        """Update vitals with realistic momentum/inertia"""
        momentum = 0.8  # How much vitals resist sudden changes
        
        # Move current values toward targets with momentum
        self.hr_current = (self.hr_current * momentum) + (self.hr_target * (1 - momentum))
        self.spo2_current = (self.spo2_current * momentum) + (self.spo2_target * (1 - momentum))
        self.rr_current = (self.rr_current * momentum) + (self.rr_target * (1 - momentum))
        self.temp_current = (self.temp_current * momentum) + (self.temp_target * (1 - momentum))
        self.map_current = (self.map_current * momentum) + (self.map_target * (1 - momentum))
    
    def generate_vitals(self):
        """Generate realistic vital signs with noise and clinical events"""
        self.time_counter += 1
        
        # Run clinical scenario simulations
        self.simulate_sepsis_physiology()
        self.simulate_apnea_event()
        self.update_vitals_with_momentum()
        
        # Add realistic noise to each vital sign
        hr = self.add_physiological_noise(self.hr_current, 3.0 * self.noise_amplitude, 1.2)
        spo2 = self.add_physiological_noise(self.spo2_current, 2.0 * self.noise_amplitude, 0.8)
        rr = self.add_physiological_noise(self.rr_current, 4.0 * self.noise_amplitude, 2.0)
        temp = self.add_physiological_noise(self.temp_current, 0.3 * self.noise_amplitude, 0.1)
        map_val = self.add_physiological_noise(self.map_current, 3.0 * self.noise_amplitude, 0.9)
        
        # Apply physiological limits
        hr = max(60, min(220, hr))
        spo2 = max(75, min(100, spo2))
        rr = max(0, min(100, rr))  # Can go to 0 during apnea
        temp = max(34.0, min(42.0, temp))
        map_val = max(15, min(60, map_val))
        
        # Calculate risk score based on deviations from normal
        hr_risk = abs(hr - 120) / 10.0
        spo2_risk = max(0, 95 - spo2) * 2.0
        rr_risk = abs(rr - 40) / 5.0
        temp_risk = abs(temp - 36.8) * 5.0
        map_risk = max(0, 35 - map_val) * 1.5
        
        total_risk = hr_risk + spo2_risk + rr_risk + temp_risk + map_risk
        
        # Determine clinical status
        if total_risk > 25 or self.sepsis_mode:
            status = "CRITICAL"
        elif total_risk > 12 or self.apnea_mode:
            status = "WARNING"
        elif total_risk > 6:
            status = "UNSTABLE"
        else:
            status = "STABLE"
        
        return {
            "timestamp": datetime.now().isoformat(),
            "mrn": "B001",
            "hr": round(hr, 1),
            "spo2": round(spo2, 1),
            "rr": round(rr, 1),
            "temp": round(temp, 2),
            "map": round(map_val, 1),
            "risk_score": round(total_risk, 2),
            "status": status
        }
    
    def trigger_sepsis(self):
        """Manually trigger sepsis simulation"""
        self.sepsis_mode = True
        self.sepsis_duration = 0
        print("[SIMULATOR] 🚨 SEPSIS EPISODE TRIGGERED - Monitoring physiological deterioration")
    
    def trigger_apnea(self):
        """Manually trigger apnea event"""
        self.apnea_mode = True
        self.apnea_duration = 0
        print("[SIMULATOR] ⚠️ APNEA EVENT TRIGGERED - Respiratory arrest simulation")
    
    def reset_to_stable(self):
        """Reset to stable baseline"""
        self.sepsis_mode = False
        self.apnea_mode = False
        self.hr_target = 120.0
        self.spo2_target = 95.0
        self.rr_target = 40.0
        self.temp_target = 36.8
        self.map_target = 35.0
        self.noise_amplitude = 1.0
        print("[SIMULATOR] 💚 RESET TO STABLE BASELINE")
def run_simulator():
    """Enhanced simulator with trigger monitoring and realistic data"""
    data_dir = Path(__file__).parent.parent / "data"
    data_dir.mkdir(exist_ok=True)
    
    stream_file = data_dir / "stream.csv"
    trigger_file = data_dir / "sepsis_trigger.txt"
    apnea_trigger_file = data_dir / "apnea_trigger.txt"
    reset_trigger_file = data_dir / "reset_trigger.txt"
    
    # Create CSV with headers if it doesn't exist
    if not stream_file.exists():
        with open(stream_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'timestamp', 'mrn', 'hr', 'spo2', 'rr', 'temp', 'map', 'risk_score', 'status'
            ])
            writer.writeheader()
    
    simulator = EnhancedNICUSimulator()
    last_sepsis_trigger = None
    last_apnea_trigger = None
    last_reset_trigger = None
    
    print("="*80)
    print("🏥 ENHANCED NICU VITALS SIMULATOR - Realistic Physiological Data")
    print("="*80)
    print(f"📊 Data Stream: {stream_file}")
    print(f"🚨 Sepsis Trigger: {trigger_file}")
    print(f"⚠️  Apnea Trigger: {apnea_trigger_file}")
    print(f"💚 Reset Trigger: {reset_trigger_file}")
    print("📈 Features:")
    print("   • Realistic physiological noise and variations")
    print("   • Multi-frequency noise (breathing, sleep cycles, circadian rhythms)")
    print("   • Sepsis simulation with progressive deterioration")
    print("   • Spontaneous apnea events with bradycardia")
    print("   • Manual trigger support via trigger files")
    print("   • Momentum-based vital sign changes")
    print("⏱️  Generating vitals every 3 seconds...")
    print("🛑 Press Ctrl+C to stop")
    print("="*80)
    
    try:
        while True:
            # Check for manual triggers
            if trigger_file.exists():
                trigger_time = trigger_file.read_text().strip()
                if trigger_time != last_sepsis_trigger:
                    simulator.trigger_sepsis()
                    last_sepsis_trigger = trigger_time
            
            if apnea_trigger_file.exists():
                trigger_time = apnea_trigger_file.read_text().strip()
                if trigger_time != last_apnea_trigger:
                    simulator.trigger_apnea()
                    last_apnea_trigger = trigger_time
            
            if reset_trigger_file.exists():
                trigger_time = reset_trigger_file.read_text().strip()
                if trigger_time != last_reset_trigger:
                    simulator.reset_to_stable()
                    last_reset_trigger = trigger_time
            
            # Generate realistic vitals
            vitals = simulator.generate_vitals()
            
            # Append to CSV stream
            with open(stream_file, 'a', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=vitals.keys())
                writer.writerow(vitals)
            
            # Enhanced status display
            status_emoji = {
                "STABLE": "💚",
                "UNSTABLE": "💛", 
                "WARNING": "🟠",
                "CRITICAL": "🔴"
            }.get(vitals['status'], "⚪")
            
            clinical_flags = []
            if simulator.sepsis_mode:
                clinical_flags.append("SEPSIS")
            if simulator.apnea_mode:
                clinical_flags.append("APNEA")
            
            flags_str = f" [{', '.join(clinical_flags)}]" if clinical_flags else ""
            
            print(f"{status_emoji} [{vitals['timestamp'][11:19]}] MRN:{vitals['mrn']} "
                  f"HR:{vitals['hr']} SpO2:{vitals['spo2']}% RR:{vitals['rr']} "
                  f"Temp:{vitals['temp']}°C MAP:{vitals['map']} "
                  f"Risk:{vitals['risk_score']} {vitals['status']}{flags_str}")
            
            time.sleep(3)
            
    except KeyboardInterrupt:
        print("\n🛑 [SIMULATOR] Stopped by user")


if __name__ == "__main__":
    run_simulator()
