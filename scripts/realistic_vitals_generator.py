#!/usr/bin/env python3
"""
Realistic NICU Vital Signs Generator
Creates authentic clinical patterns for newborn monitoring with realistic:
- Normal variation and noise
- Correlated vital sign changes  
- Gradual sepsis progression
- Biologically plausible patterns
"""

import numpy as np
import pandas as pd
import json
import time
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Tuple
from enum import Enum
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.animation import FuncAnimation
import threading
import argparse

class ClinicalState(Enum):
    STABLE = "stable"
    DETERIORATING = "deteriorating"
    SEPTIC = "septic"
    RECOVERING = "recovering"

@dataclass
class VitalRanges:
    """Normal ranges for newborn vitals by gestational age"""
    hr_min: float
    hr_max: float
    spo2_min: float
    spo2_max: float
    rr_min: float
    rr_max: float
    temp_min: float
    temp_max: float
    map_min: float
    map_max: float

class RealisticVitalGenerator:
    """Generates biologically realistic vital signs for NICU babies"""
    
    def __init__(self, gestational_age_weeks: float = 36.0):
        self.ga = gestational_age_weeks
        self.state = ClinicalState.STABLE
        self.sepsis_onset_time = None
        self.time_since_onset = 0
        
        # Set age-appropriate ranges
        self.ranges = self._get_vital_ranges(gestational_age_weeks)
        
        # Initialize current vitals to normal baseline
        self.current_vitals = {
            'hr': np.random.uniform(self.ranges.hr_min + 10, self.ranges.hr_max - 10),
            'spo2': np.random.uniform(self.ranges.spo2_min + 2, self.ranges.spo2_max),
            'rr': np.random.uniform(self.ranges.rr_min + 5, self.ranges.rr_max - 5),
            'temp': np.random.uniform(self.ranges.temp_min + 0.2, self.ranges.temp_max - 0.2),
            'map': np.random.uniform(self.ranges.map_min + 3, self.ranges.map_max - 3)
        }
        
        # Noise parameters for realistic variation
        self.noise_params = {
            'hr': {'std': 3.0, 'drift': 0.95},      # Heart rate varies ±3 bpm
            'spo2': {'std': 1.5, 'drift': 0.98},    # SpO2 varies ±1.5%
            'rr': {'std': 2.0, 'drift': 0.96},      # Respiratory rate varies ±2/min
            'temp': {'std': 0.1, 'drift': 0.999},   # Temperature varies ±0.1°C
            'map': {'std': 1.5, 'drift': 0.97}      # MAP varies ±1.5 mmHg
        }
    
    def _get_vital_ranges(self, ga_weeks: float) -> VitalRanges:
        """Get age-appropriate vital sign ranges"""
        if ga_weeks < 32:  # Very preterm
            return VitalRanges(
                hr_min=120, hr_max=170,
                spo2_min=90, spo2_max=98,
                rr_min=40, rr_max=70,
                temp_min=36.0, temp_max=37.0,
                map_min=25, map_max=40
            )
        elif ga_weeks < 37:  # Preterm
            return VitalRanges(
                hr_min=115, hr_max=165,
                spo2_min=92, spo2_max=99,
                rr_min=35, rr_max=65,
                temp_min=36.2, temp_max=37.2,
                map_min=30, map_max=45
            )
        else:  # Term
            return VitalRanges(
                hr_min=110, hr_max=160,
                spo2_min=95, spo2_max=100,
                rr_min=30, rr_max=60,
                temp_min=36.5, temp_max=37.5,
                map_min=35, map_max=50
            )
    
    def trigger_sepsis(self):
        """Trigger gradual sepsis progression"""
        self.state = ClinicalState.DETERIORATING
        self.sepsis_onset_time = datetime.now()
        self.time_since_onset = 0
        print(f"🚨 SEPSIS TRIGGERED at {self.sepsis_onset_time.strftime('%H:%M:%S')}")
    
    def reset_to_normal(self):
        """Reset to stable baseline"""
        self.state = ClinicalState.STABLE
        self.sepsis_onset_time = None
        self.time_since_onset = 0
        # Gradually return to normal ranges
        self.current_vitals = {
            'hr': np.random.uniform(self.ranges.hr_min + 10, self.ranges.hr_max - 10),
            'spo2': np.random.uniform(self.ranges.spo2_min + 2, self.ranges.spo2_max),
            'rr': np.random.uniform(self.ranges.rr_min + 5, self.ranges.rr_max - 5),
            'temp': np.random.uniform(self.ranges.temp_min + 0.2, self.ranges.temp_max - 0.2),
            'map': np.random.uniform(self.ranges.map_min + 3, self.ranges.map_max - 3)
        }
        print("✅ RESET TO NORMAL BASELINE")
    
    def _apply_sepsis_progression(self, minutes_since_onset: float) -> Dict[str, float]:
        """Apply realistic sepsis progression over time"""
        # Sepsis progression phases
        if minutes_since_onset < 5:
            # Phase 1: Subtle early changes (0-5 minutes)
            progression = minutes_since_onset / 5.0 * 0.2  # 20% progression
        elif minutes_since_onset < 15:
            # Phase 2: Noticeable deterioration (5-15 minutes)
            progression = 0.2 + (minutes_since_onset - 5) / 10.0 * 0.4  # 20-60%
        elif minutes_since_onset < 30:
            # Phase 3: Severe deterioration (15-30 minutes)
            progression = 0.6 + (minutes_since_onset - 15) / 15.0 * 0.3  # 60-90%
        else:
            # Phase 4: Critical state (30+ minutes)
            progression = min(0.9 + (minutes_since_onset - 30) / 30.0 * 0.1, 1.0)  # 90-100%
        
        # Apply correlated sepsis changes
        sepsis_targets = {
            'hr': self.ranges.hr_max + 20 + (progression * 40),  # Tachycardia
            'spo2': max(self.ranges.spo2_min - 10 - (progression * 15), 75),  # Hypoxemia
            'rr': self.ranges.rr_max + 10 + (progression * 30),  # Tachypnea
            'temp': np.random.choice([
                self.ranges.temp_max + 1.5 + progression,  # Fever
                self.ranges.temp_min - 1.0 - progression   # Hypothermia (50/50)
            ]),
            'map': max(self.ranges.map_min - 5 - (progression * 15), 15)  # Hypotension
        }
        
        return sepsis_targets
    
    def generate_next_vitals(self) -> Dict[str, float]:
        """Generate next realistic vital signs measurement"""
        
        # Update time since sepsis onset if applicable
        if self.sepsis_onset_time:
            self.time_since_onset = (datetime.now() - self.sepsis_onset_time).total_seconds() / 60.0
            
            if self.time_since_onset > 45:  # Transition to septic state after 45 min
                self.state = ClinicalState.SEPTIC
        
        # Apply state-specific changes
        if self.state == ClinicalState.STABLE:
            targets = {
                'hr': np.random.uniform(self.ranges.hr_min + 10, self.ranges.hr_max - 10),
                'spo2': np.random.uniform(self.ranges.spo2_min + 2, self.ranges.spo2_max),
                'rr': np.random.uniform(self.ranges.rr_min + 5, self.ranges.rr_max - 5),
                'temp': np.random.uniform(self.ranges.temp_min + 0.2, self.ranges.temp_max - 0.2),
                'map': np.random.uniform(self.ranges.map_min + 3, self.ranges.map_max - 3)
            }
        
        elif self.state in [ClinicalState.DETERIORATING, ClinicalState.SEPTIC]:
            targets = self._apply_sepsis_progression(self.time_since_onset)
        
        else:  # RECOVERING
            # Gradual improvement toward normal
            targets = {
                'hr': self.ranges.hr_min + 20,
                'spo2': self.ranges.spo2_max - 2,
                'rr': self.ranges.rr_min + 10,
                'temp': (self.ranges.temp_min + self.ranges.temp_max) / 2,
                'map': (self.ranges.map_min + self.ranges.map_max) / 2
            }
        
        # Apply realistic movement toward targets with noise
        new_vitals = {}
        for vital, target in targets.items():
            # Drift toward target with momentum
            drift_factor = self.noise_params[vital]['drift']
            noise_std = self.noise_params[vital]['std']
            
            # Apply momentum and drift
            movement_toward_target = (target - self.current_vitals[vital]) * (1 - drift_factor)
            random_noise = np.random.normal(0, noise_std)
            
            # Update with realistic constraints
            new_value = self.current_vitals[vital] * drift_factor + movement_toward_target + random_noise
            
            # Apply physiological limits
            if vital == 'hr':
                new_value = np.clip(new_value, 60, 220)
            elif vital == 'spo2':
                new_value = np.clip(new_value, 70, 100)
            elif vital == 'rr':
                new_value = np.clip(new_value, 10, 100)
            elif vital == 'temp':
                new_value = np.clip(new_value, 34.0, 42.0)
            elif vital == 'map':
                new_value = np.clip(new_value, 10, 80)
            
            new_vitals[vital] = round(new_value, 1)
        
        # Update current state
        self.current_vitals = new_vitals
        
        return new_vitals
    
    def get_clinical_assessment(self) -> Dict[str, any]:
        """Get clinical interpretation of current vitals"""
        vitals = self.current_vitals
        
        # Score abnormalities
        abnormal_count = 0
        severity_score = 0
        
        # Heart rate assessment
        if vitals['hr'] > self.ranges.hr_max + 10:
            abnormal_count += 1
            severity_score += (vitals['hr'] - self.ranges.hr_max) / 10
        elif vitals['hr'] < self.ranges.hr_min - 10:
            abnormal_count += 1
            severity_score += (self.ranges.hr_min - vitals['hr']) / 10
        
        # SpO2 assessment
        if vitals['spo2'] < self.ranges.spo2_min:
            abnormal_count += 1
            severity_score += (self.ranges.spo2_min - vitals['spo2']) / 5
        
        # Respiratory rate assessment
        if vitals['rr'] > self.ranges.rr_max + 10:
            abnormal_count += 1
            severity_score += (vitals['rr'] - self.ranges.rr_max) / 15
        
        # Temperature assessment
        if vitals['temp'] > self.ranges.temp_max + 0.5 or vitals['temp'] < self.ranges.temp_min - 0.5:
            abnormal_count += 1
            severity_score += abs(vitals['temp'] - (self.ranges.temp_min + self.ranges.temp_max)/2) * 2
        
        # MAP assessment
        if vitals['map'] < self.ranges.map_min - 5:
            abnormal_count += 1
            severity_score += (self.ranges.map_min - vitals['map']) / 5
        
        # Determine clinical status
        if severity_score < 2 and abnormal_count < 2:
            clinical_status = "STABLE"
            alert_level = "🟢"
        elif severity_score < 5 and abnormal_count < 3:
            clinical_status = "MONITOR"
            alert_level = "🟡"
        elif severity_score < 10:
            clinical_status = "CONCERNING"
            alert_level = "🟠"
        else:
            clinical_status = "CRITICAL"
            alert_level = "🔴"
        
        return {
            'clinical_status': clinical_status,
            'alert_level': alert_level,
            'abnormal_count': abnormal_count,
            'severity_score': round(severity_score, 1),
            'time_since_sepsis': self.time_since_onset if self.sepsis_onset_time else 0,
            'state': self.state.value
        }

class RealisticNICUSimulator:
    """Simulates realistic NICU patient monitoring"""
    
    def __init__(self):
        self.patients = {}
        self.db_path = Path(__file__).parent / "neonatal_ehr.db"
        self._setup_database()
        self._initialize_patients()
    
    def _setup_database(self):
        """Setup database with realistic vitals table"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS realistic_vitals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                mrn TEXT NOT NULL,
                hr REAL NOT NULL,
                spo2 REAL NOT NULL,
                rr REAL NOT NULL,
                temp REAL NOT NULL,
                map REAL NOT NULL,
                clinical_status TEXT,
                alert_level TEXT,
                severity_score REAL,
                abnormal_count INTEGER,
                sepsis_state TEXT,
                time_since_sepsis REAL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
    
    def _initialize_patients(self):
        """Initialize patients with different gestational ages"""
        patients_config = [
            {'mrn': 'B001', 'ga': 39.0, 'name': 'Baby Verma'},      # Term
            {'mrn': 'B002', 'ga': 34.2, 'name': 'Aarav Kumar'},     # Preterm  
            {'mrn': 'B003', 'ga': 35.8, 'name': 'Baby Girl Reddy'}, # Late preterm
            {'mrn': 'B004', 'ga': 35.8, 'name': 'Twin B Reddy'},    # Late preterm
            {'mrn': 'B005', 'ga': 37.1, 'name': 'Ishaan Mehta'}     # Early term
        ]
        
        for config in patients_config:
            self.patients[config['mrn']] = {
                'generator': RealisticVitalGenerator(config['ga']),
                'name': config['name'],
                'ga': config['ga']
            }
        
        print(f"🏥 Initialized {len(self.patients)} NICU patients with realistic vital generators")
    
    def trigger_sepsis(self, mrn: str = None):
        """Trigger sepsis for specific patient or random patient"""
        if mrn and mrn in self.patients:
            self.patients[mrn]['generator'].trigger_sepsis()
            print(f"🚨 Triggered sepsis for {self.patients[mrn]['name']} ({mrn})")
        else:
            # Trigger for random patient
            random_mrn = np.random.choice(list(self.patients.keys()))
            self.patients[random_mrn]['generator'].trigger_sepsis()
            print(f"🚨 Triggered sepsis for {self.patients[random_mrn]['name']} ({random_mrn})")
    
    def reset_patient(self, mrn: str):
        """Reset patient to normal baseline"""
        if mrn in self.patients:
            self.patients[mrn]['generator'].reset_to_normal()
            print(f"✅ Reset {self.patients[mrn]['name']} ({mrn}) to normal")
    
    def generate_live_data(self, duration_minutes: int = 120, interval_seconds: int = 2, show_graph: bool = False):
        """Generate realistic live data for all patients with optional visualization"""
        print(f"📊 Starting realistic NICU simulation for {duration_minutes} minutes...")
        print(f"📈 Data interval: {interval_seconds} seconds")
        if show_graph:
            print("📱 Real-time graph visualization enabled")
        
        start_time = datetime.now()
        measurement_count = 0
        
        # Initialize data storage for visualization
        if show_graph:
            self.viz_data = {mrn: {'time': [], 'hr': [], 'spo2': [], 'temp': [], 'map': [], 'rr': []} 
                           for mrn in self.patients.keys()}
            
            # Setup matplotlib for real-time plotting
            plt.ion()
            fig, axes = plt.subplots(2, 3, figsize=(15, 10))
            fig.suptitle('NICU Patients - Real-Time Vital Signs Monitor', fontsize=16)
            
            # Configure subplots
            vital_labels = ['Heart Rate (bpm)', 'SpO2 (%)', 'Temperature (°C)', 'MAP (mmHg)', 'Resp Rate (/min)', 'Clinical Status']
            colors = ['red', 'blue', 'green', 'orange', 'purple']
            
            # Flatten axes for easier indexing
            flat_axes = axes.flatten()
            
            for i, label in enumerate(vital_labels[:5]):  # Skip status for now
                flat_axes[i].set_title(label)
                flat_axes[i].set_xlabel('Time')
                flat_axes[i].grid(True, alpha=0.3)
                flat_axes[i].legend([f'{mrn}' for mrn in self.patients.keys()], loc='upper right')
        
        print("Commands during simulation:")
        print("  Ctrl+C to stop")
        print("  In separate terminal: 'curl -X POST http://localhost:8000/trigger-sepsis?mrn=B002'")
        
        try:
            while (datetime.now() - start_time).total_seconds() / 60 < duration_minutes:
                current_time = datetime.now()
                timestamp = current_time.isoformat()
                
                # Generate vitals for all patients
                all_vitals = {}
                for mrn, patient in self.patients.items():
                    generator = patient['generator']
                    vitals = generator.generate_next_vitals()
                    assessment = generator.get_clinical_assessment()
                    
                    all_vitals[mrn] = {**vitals, **assessment}
                    
                    # Store in database
                    self._store_vital_signs(timestamp, mrn, vitals, assessment)
                    
                    # Update visualization data
                    if show_graph:
                        self.viz_data[mrn]['time'].append(current_time)
                        self.viz_data[mrn]['hr'].append(vitals['hr'])
                        self.viz_data[mrn]['spo2'].append(vitals['spo2'])
                        self.viz_data[mrn]['temp'].append(vitals['temp'])
                        self.viz_data[mrn]['map'].append(vitals['map'])
                        self.viz_data[mrn]['rr'].append(vitals['rr'])
                        
                        # Keep only last 100 points for performance
                        for key in self.viz_data[mrn]:
                            if len(self.viz_data[mrn][key]) > 100:
                                self.viz_data[mrn][key] = self.viz_data[mrn][key][-100:]
                    
                    # Display alerts for abnormal cases
                    if assessment['severity_score'] > 3 or assessment['alert_level'] in ['🚨 CRITICAL', '⚠️ WARNING']:
                        print(f"{assessment['alert_level']} {patient['name']} ({mrn}): "
                              f"HR:{vitals['hr']:.0f} SpO2:{vitals['spo2']:.1f}% "
                              f"RR:{vitals['rr']:.0f} T:{vitals['temp']:.1f}°C "
                              f"MAP:{vitals['map']:.0f} - {assessment['clinical_status']}")
                
                # Update graph every 10 measurements
                if show_graph and measurement_count % 10 == 0:
                    self._update_visualization(flat_axes, colors)
                
                measurement_count += 1
                if measurement_count % 50 == 0:  # Show progress every 50 measurements
                    elapsed = (datetime.now() - start_time).total_seconds() / 60
                    remaining = duration_minutes - elapsed
                    print(f"⏱️ {elapsed:.1f}min elapsed, {remaining:.1f}min remaining | {measurement_count * len(self.patients)} measurements")
                
                time.sleep(interval_seconds)
        
        except KeyboardInterrupt:
            print("\n\n🛑 Simulation interrupted by user")
        finally:
            total_measurements = measurement_count * len(self.patients)
            elapsed_time = (datetime.now() - start_time).total_seconds() / 60
            print(f"✅ Simulation complete: {total_measurements} realistic measurements in {elapsed_time:.1f} minutes")
            
            if show_graph:
                plt.ioff()
                plt.show()  # Keep final graph open
    
    def _update_visualization(self, axes, colors):
        """Update real-time visualization"""
        try:
            vitals_keys = ['hr', 'spo2', 'temp', 'map', 'rr']
            
            for i, vital in enumerate(vitals_keys):
                axes[i].clear()
                axes[i].grid(True, alpha=0.3)
                
                for j, (mrn, patient_data) in enumerate(self.viz_data.items()):
                    if len(patient_data['time']) > 1:
                        patient_info = self.patients[mrn]
                        label = f"{mrn} ({patient_info['name']})"
                        
                        # Color coding based on patient state
                        generator = patient_info['generator']
                        if generator.state == ClinicalState.SEPTIC:
                            color = 'red'
                            alpha = 1.0
                        elif generator.state == ClinicalState.DETERIORATING:
                            color = 'orange'
                            alpha = 0.8
                        else:
                            color = colors[j % len(colors)]
                            alpha = 0.6
                        
                        axes[i].plot(patient_data['time'], patient_data[vital], 
                                   color=color, alpha=alpha, linewidth=2, label=label)
                
                # Format axes
                vital_labels = ['Heart Rate (bpm)', 'SpO2 (%)', 'Temperature (°C)', 'MAP (mmHg)', 'Resp Rate (/min)']
                axes[i].set_title(vital_labels[i])
                axes[i].set_xlabel('Time')
                
                # Set y-axis limits based on vital sign type
                if vital == 'hr':
                    axes[i].set_ylim(60, 200)
                elif vital == 'spo2':
                    axes[i].set_ylim(70, 100)
                elif vital == 'temp':
                    axes[i].set_ylim(35, 40)
                elif vital == 'map':
                    axes[i].set_ylim(15, 70)
                elif vital == 'rr':
                    axes[i].set_ylim(20, 80)
                
                # Format time axis
                if len(self.viz_data[list(self.patients.keys())[0]]['time']) > 0:
                    axes[i].xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
                    axes[i].tick_params(axis='x', rotation=45)
                
                # Add legend
                if i == 0:  # Only add legend to first subplot
                    axes[i].legend(loc='upper right', fontsize='small')
            
            plt.tight_layout()
            plt.pause(0.1)  # Small pause to update display
            
        except Exception as e:
            print(f"Visualization update error: {e}")
        
        print("Commands: 'trigger <mrn>' to trigger sepsis, 'reset <mrn>' to reset patient")
        
        start_time = datetime.now()
        measurement_count = 0
        
        while (datetime.now() - start_time).seconds / 60 < duration_minutes:
            timestamp = datetime.now().isoformat()
            
                # Generate vitals for all patients
                for mrn, patient in self.patients.items():
                    generator = patient['generator']
                    vitals = generator.generate_next_vitals()
                    assessment = generator.get_clinical_assessment()
                    
                    # Store in database
                    self._store_vital_signs(timestamp, mrn, vitals, assessment)
                    
                    # Display if abnormal or septic
                    if assessment['severity_score'] > 3:
                        print(f"{assessment['alert_level']} {patient['name']} ({mrn}): "
                              f"HR:{vitals['hr']:.0f} SpO2:{vitals['spo2']:.1f}% "
                              f"RR:{vitals['rr']:.0f} T:{vitals['temp']:.1f}°C "
                              f"MAP:{vitals['map']:.0f} - {assessment['clinical_status']}")
                
                measurement_count += 1
                if measurement_count % 20 == 0:
                    elapsed = (datetime.now() - start_time).seconds / 60
                    print(f"⏱️ {elapsed:.1f} minutes elapsed, {measurement_count * len(self.patients)} measurements recorded")
                
                time.sleep(interval_seconds)
            
            print(f"✅ Simulation complete: {measurement_count * len(self.patients)} realistic measurements generated")
    
    def _store_vital_signs(self, timestamp: str, mrn: str, vitals: Dict, assessment: Dict):
        """Store vital signs in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO realistic_vitals 
            (timestamp, mrn, hr, spo2, rr, temp, map, clinical_status, 
             alert_level, severity_score, abnormal_count, sepsis_state, time_since_sepsis)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            timestamp, mrn,
            vitals['hr'], vitals['spo2'], vitals['rr'], vitals['temp'], vitals['map'],
            assessment['clinical_status'], assessment['alert_level'],
            assessment['severity_score'], assessment['abnormal_count'],
            assessment['state'], assessment['time_since_sepsis']
        ))
        
        conn.commit()
        conn.close()

def main():
    """Interactive realistic NICU simulation with enhanced options"""
    parser = argparse.ArgumentParser(description='Realistic NICU Vital Signs Simulator')
    parser.add_argument('--duration', type=int, default=120, 
                       help='Simulation duration in minutes (default: 120)')
    parser.add_argument('--interval', type=int, default=2,
                       help='Data collection interval in seconds (default: 2)')
    parser.add_argument('--graph', action='store_true',
                       help='Show real-time visualization')
    parser.add_argument('--auto-run', action='store_true',
                       help='Start simulation immediately without menu')
    
    args = parser.parse_args()
    
    simulator = RealisticNICUSimulator()
    
    print("\n🏥 REALISTIC NICU VITAL SIGNS SIMULATOR")
    print("=" * 60)
    print("Available patients:")
    for mrn, patient in simulator.patients.items():
        print(f"  {mrn}: {patient['name']} (GA: {patient['ga']} weeks)")
    
    print(f"\nConfiguration:")
    print(f"  📊 Duration: {args.duration} minutes")
    print(f"  ⏱️ Interval: {args.interval} seconds") 
    print(f"  📈 Visualization: {'Enabled' if args.graph else 'Disabled'}")
    
    # Auto-run mode
    if args.auto_run:
        print(f"\n🚀 Starting automatic simulation...")
        simulator.generate_live_data(duration_minutes=args.duration, 
                                   interval_seconds=args.interval, 
                                   show_graph=args.graph)
        return
    
    print("\nCommands:")
    print("  'run' - Start continuous simulation with current settings")
    print("  'run <minutes>' - Start simulation for specific duration")
    print("  'run graph' - Start simulation with real-time visualization")
    print("  'trigger <mrn>' - Trigger gradual sepsis for patient")
    print("  'reset <mrn>' - Reset patient to normal baseline")  
    print("  'status' - Show all patient status")
    print("  'config' - Show current configuration")
    print("  'quit' - Exit")
    
    while True:
        try:
            cmd = input("\n> ").strip().lower()
            
            if cmd == 'quit':
                break
            elif cmd == 'run':
                simulator.generate_live_data(duration_minutes=args.duration, 
                                           interval_seconds=args.interval, 
                                           show_graph=args.graph)
            elif cmd.startswith('run '):
                parts = cmd.split()
                if 'graph' in parts:
                    simulator.generate_live_data(duration_minutes=args.duration, 
                                               interval_seconds=args.interval, 
                                               show_graph=True)
                elif parts[1].isdigit():
                    duration = int(parts[1])
                    simulator.generate_live_data(duration_minutes=duration, 
                                               interval_seconds=args.interval, 
                                               show_graph=args.graph)
            elif cmd == 'config':
                print(f"Current settings: Duration={args.duration}min, Interval={args.interval}s, Graph={args.graph}")
            elif cmd == 'status':
                print("\nPatient Status:")
                for mrn, patient in simulator.patients.items():
                    assessment = patient['generator'].get_clinical_assessment()
                    vitals = patient['generator'].current_vitals
                    state_emoji = "🟢" if patient['generator'].state == ClinicalState.STABLE else ("🟠" if patient['generator'].state == ClinicalState.DETERIORATING else "🔴")
                    print(f"  {state_emoji} {mrn}: {assessment['alert_level']} {assessment['clinical_status']}")
                    print(f"     HR:{vitals['hr']:.0f} SpO2:{vitals['spo2']:.1f}% "
                          f"RR:{vitals['rr']:.0f} T:{vitals['temp']:.1f}°C MAP:{vitals['map']:.0f}")
            elif cmd.startswith('trigger'):
                parts = cmd.split()
                mrn = parts[1].upper() if len(parts) > 1 else None
                simulator.trigger_sepsis(mrn)
            elif cmd.startswith('reset'):
                parts = cmd.split()
                if len(parts) > 1:
                    simulator.reset_patient(parts[1].upper())
            else:
                print("Unknown command. Type 'quit' to exit or 'run' to start simulation.")
                
        except KeyboardInterrupt:
            print("\n\n👋 Simulation stopped")
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()