#!/usr/bin/env python3
"""
Complete HIL Workflow Test Client
Demonstrates the end-to-end Human-in-the-Loop workflow:
Live Data → Critical Threshold → ML Prediction → Doctor Action → Outcome

This simulates the complete workflow for testing and validation.
"""

import requests
import json
import time
import random
from datetime import datetime, timedelta
from typing import Dict, List
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API endpoints
PREDICTION_API = "http://localhost:8001/predict_risk"
HIL_LOGGING_API = "http://localhost:8001/log_doctor_action"
HEALTH_API = "http://localhost:8001/health"

class HILWorkflowTester:
    """Tests complete HIL workflow"""
    
    def __init__(self):
        self.active_alerts = {}
        self.completed_workflows = []
    
    def check_service_health(self) -> bool:
        """Check if prediction service is running"""
        try:
            response = requests.get(HEALTH_API, timeout=5)
            if response.status_code == 200:
                health_data = response.json()
                logger.info("✅ Prediction service is healthy")
                logger.info(f"   • ML Model: {health_data['models']['ml_model_loaded']}")
                logger.info(f"   • Features: {health_data['models']['feature_count']}")
                return True
            else:
                logger.error(f"❌ Service unhealthy: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Cannot connect to prediction service: {e}")
            logger.info("💡 Start with: python sepsis_prediction_service.py")
            return False
    
    def generate_critical_patient_scenario(self, mrn: str) -> Dict:
        """Generate a critical patient scenario that should trigger ML prediction"""
        
        scenarios = [
            {
                "name": "Preterm Tachycardia + Fever",
                "data": {
                    "mrn": mrn,
                    "gestational_age_at_birth_weeks": 34.2,
                    "birth_weight_kg": 2.1,
                    "sex": "M",
                    "race": "hispanic",
                    "ga_weeks": 34,
                    "ga_days": 1,
                    "maternal_temp_celsius": 38.5,
                    "rom_hours": 16.0,
                    "gbs_status": "positive",
                    "antibiotic_type": "none",
                    "clinical_exam": "normal",
                    "hr": 185.0,  # CRITICAL: >180
                    "spo2": 89.0,  # CRITICAL: <90
                    "rr": 35.0,
                    "temp_celsius": 38.3,
                    "map": 32.0,
                    "comorbidities": "yes",
                    "central_venous_line": "yes",
                    "intubated_at_time_of_sepsis_evaluation": "no",
                    "inotrope_at_time_of_sepsis_eval": "yes",
                    "ecmo": "no",
                    "stat_abx": "no"
                }
            },
            {
                "name": "Term Baby Hypotension + Desaturation",
                "data": {
                    "mrn": mrn,
                    "gestational_age_at_birth_weeks": 39.1,
                    "birth_weight_kg": 3.1,
                    "sex": "F",
                    "race": "white",
                    "ga_weeks": 39,
                    "ga_days": 1,
                    "maternal_temp_celsius": 37.2,
                    "rom_hours": 22.0,
                    "gbs_status": "unknown",
                    "antibiotic_type": "none",
                    "clinical_exam": "normal",
                    "hr": 165.0,
                    "spo2": 87.0,  # CRITICAL: <90
                    "rr": 45.0,
                    "temp_celsius": 37.8,
                    "map": 22.0,  # CRITICAL: <25
                    "comorbidities": "no",
                    "central_venous_line": "no",
                    "intubated_at_time_of_sepsis_evaluation": "no",
                    "inotrope_at_time_of_sepsis_eval": "no",
                    "ecmo": "no",
                    "stat_abx": "no"
                }
            },
            {
                "name": "Very Preterm + Clinical Chorioamnionitis",
                "data": {
                    "mrn": mrn,
                    "gestational_age_at_birth_weeks": 32.3,
                    "birth_weight_kg": 1.8,
                    "sex": "F",
                    "race": "black",
                    "ga_weeks": 32,
                    "ga_days": 2,
                    "maternal_temp_celsius": 39.2,
                    "rom_hours": 28.0,
                    "gbs_status": "positive",
                    "antibiotic_type": "none",
                    "clinical_exam": "abnormal",  # Clinical chorioamnionitis
                    "hr": 175.0,
                    "spo2": 91.0,
                    "rr": 48.0,
                    "temp_celsius": 38.9,
                    "map": 25.0,
                    "comorbidities": "yes",
                    "central_venous_line": "yes",
                    "intubated_at_time_of_sepsis_evaluation": "yes",
                    "inotrope_at_time_of_sepsis_eval": "yes",
                    "ecmo": "no",
                    "stat_abx": "no"
                }
            }
        ]
        
        return random.choice(scenarios)
    
    def call_ml_prediction(self, patient_data: Dict) -> Dict:
        """Call ML prediction API"""
        try:
            response = requests.post(
                PREDICTION_API,
                json=patient_data,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                prediction = response.json()
                return prediction
            else:
                logger.error(f"Prediction failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Prediction API error: {e}")
            return None
    
    def simulate_doctor_decision(self, prediction: Dict) -> Dict:
        """Simulate realistic doctor decision based on ML prediction"""
        risk_score = prediction.get('risk_score', 0.0)
        is_critical = prediction.get('is_critical_alert', False)
        mrn = prediction.get('mrn', 'UNKNOWN')
        
        # Simulate different doctors
        doctors = ['DR001', 'DR002', 'DR003']
        doctor_id = random.choice(doctors)
        
        # Doctor decision logic based on risk and clinical guidelines
        if is_critical or risk_score >= 0.8:
            # High risk: likely to treat empirically
            if random.random() < 0.8:  # 80% chance to treat
                action_type = "Treat"
                action_detail = random.choice([
                    "Ampicillin + Gentamicin",
                    "Cefotaxime",
                    "Vancomycin + Gentamicin"
                ])
            else:
                action_type = "Lab"
                action_detail = "CBC, Blood culture, CRP - empiric pending"
        elif risk_score >= 0.5:
            # Moderate-high risk: likely labs first
            if random.random() < 0.6:  # 60% chance for labs
                action_type = "Lab"
                action_detail = "Blood culture, CBC, CRP - observe closely"
            else:
                action_type = "Observe"
                action_detail = "Enhanced monitoring q1h vitals"
        elif risk_score >= 0.2:
            # Moderate risk: enhanced monitoring
            if random.random() < 0.7:  # 70% chance to observe
                action_type = "Observe"
                action_detail = "Monitor closely q2h, repeat assessment in 4h"
            else:
                action_type = "Lab"
                action_detail = "CBC only, continue monitoring"
        else:
            # Low risk: mostly observe or dismiss
            if random.random() < 0.3:  # 30% chance to dismiss (conservative)
                action_type = "Dismiss"
                action_detail = "ML false positive, clinical assessment normal"
            else:
                action_type = "Observe"
                action_detail = "Routine care, no additional intervention"
        
        return {
            'doctor_id': doctor_id,
            'action_type': action_type,
            'action_detail': action_detail,
            'decision_reasoning': f"Risk {risk_score:.1%}, {'Critical' if is_critical else 'Non-critical'} alert"
        }
    
    def log_doctor_action(self, mrn: str, prediction: Dict, doctor_decision: Dict) -> bool:
        """Log doctor action via HIL API"""
        try:
            hil_request = {
                'mrn': mrn,
                'doctor_id': doctor_decision['doctor_id'],
                'action_type': doctor_decision['action_type'],
                'action_detail': doctor_decision['action_detail'],
                'ml_prediction_snapshot': prediction
            }
            
            response = requests.post(
                HIL_LOGGING_API,
                json=hil_request,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                hil_response = response.json()
                alert_id = hil_response.get('alert_id', 0)
                logger.info(f"✅ HIL Action logged: Alert {alert_id}")
                return True
            else:
                logger.error(f"HIL logging failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"HIL logging error: {e}")
            return False
    
    def run_single_hil_workflow(self, mrn: str) -> Dict:
        """Execute a complete HIL workflow for one patient"""
        logger.info(f"\\n🔄 Starting HIL Workflow for MRN: {mrn}")
        logger.info("="*60)
        
        workflow_result = {
            'mrn': mrn,
            'start_time': datetime.now(),
            'steps_completed': [],
            'success': False
        }
        
        try:
            # Step 1: Generate critical patient scenario
            scenario = self.generate_critical_patient_scenario(mrn)
            logger.info(f"1️⃣ Generated scenario: {scenario['name']}")
            workflow_result['steps_completed'].append('scenario_generated')
            workflow_result['scenario'] = scenario
            
            # Step 2: Call ML Prediction (simulates Pathway trigger)
            logger.info("2️⃣ Calling ML prediction service...")
            prediction = self.call_ml_prediction(scenario['data'])
            
            if not prediction:
                logger.error("❌ ML prediction failed")
                return workflow_result
            
            workflow_result['steps_completed'].append('ml_prediction')
            workflow_result['prediction'] = prediction
            
            # Display prediction results
            risk_score = prediction.get('risk_score', 0.0)
            is_critical = prediction.get('is_critical_alert', False)
            alert_reason = prediction.get('alert_reason', 'Unknown')
            
            logger.info(f"   • Risk Score: {risk_score:.1%}")
            logger.info(f"   • Critical Alert: {'🚨 YES' if is_critical else '⚠️ NO'}")
            logger.info(f"   • Alert Reason: {alert_reason}")
            logger.info(f"   • Onset Window: {prediction.get('onset_window_hrs', 'Unknown')} hours")
            
            # Step 3: Simulate Doctor Decision
            logger.info("3️⃣ Simulating doctor decision...")
            doctor_decision = self.simulate_doctor_decision(prediction)
            workflow_result['steps_completed'].append('doctor_decision')
            workflow_result['doctor_decision'] = doctor_decision
            
            logger.info(f"   • Doctor: {doctor_decision['doctor_id']}")
            logger.info(f"   • Action: {doctor_decision['action_type']}")
            logger.info(f"   • Detail: {doctor_decision['action_detail']}")
            logger.info(f"   • Reasoning: {doctor_decision['decision_reasoning']}")
            
            # Step 4: Log HIL Action
            logger.info("4️⃣ Logging HIL action...")
            hil_success = self.log_doctor_action(mrn, prediction, doctor_decision)
            
            if hil_success:
                workflow_result['steps_completed'].append('hil_logged')
                workflow_result['success'] = True
                logger.info("✅ HIL workflow completed successfully!")
            else:
                logger.error("❌ HIL logging failed")
            
            workflow_result['end_time'] = datetime.now()
            workflow_result['duration'] = (workflow_result['end_time'] - workflow_result['start_time']).total_seconds()
            
            return workflow_result
            
        except Exception as e:
            logger.error(f"❌ HIL workflow failed: {e}")
            workflow_result['error'] = str(e)
            return workflow_result
    
    def run_multiple_hil_workflows(self, num_workflows: int = 5):
        """Run multiple HIL workflows for testing"""
        logger.info(f"\\n🚀 Starting {num_workflows} HIL Workflows")
        logger.info("="*80)
        
        results = []
        
        for i in range(num_workflows):
            mrn = f"HIL_TEST_{i+1:03d}"
            
            result = self.run_single_hil_workflow(mrn)
            results.append(result)
            
            # Brief pause between workflows
            if i < num_workflows - 1:
                time.sleep(2)
        
        # Summary analysis
        self.analyze_workflow_results(results)
        
        return results
    
    def analyze_workflow_results(self, results: List[Dict]):
        """Analyze and display HIL workflow results"""
        logger.info(f"\\n📊 HIL WORKFLOW ANALYSIS")
        logger.info("="*50)
        
        total_workflows = len(results)
        successful_workflows = sum(1 for r in results if r.get('success', False))
        
        logger.info(f"Total Workflows: {total_workflows}")
        logger.info(f"Successful: {successful_workflows} ({successful_workflows/total_workflows*100:.1f}%)")
        
        # Step completion analysis
        step_counts = {}
        for result in results:
            for step in result.get('steps_completed', []):
                step_counts[step] = step_counts.get(step, 0) + 1
        
        logger.info(f"\\nStep Completion Rates:")
        for step, count in step_counts.items():
            logger.info(f"  • {step}: {count}/{total_workflows} ({count/total_workflows*100:.1f}%)")
        
        # Risk distribution analysis
        risk_scores = []
        action_types = {}
        
        for result in results:
            if 'prediction' in result:
                risk_score = result['prediction'].get('risk_score', 0.0)
                risk_scores.append(risk_score)
            
            if 'doctor_decision' in result:
                action = result['doctor_decision'].get('action_type', 'Unknown')
                action_types[action] = action_types.get(action, 0) + 1
        
        if risk_scores:
            avg_risk = sum(risk_scores) / len(risk_scores)
            max_risk = max(risk_scores)
            min_risk = min(risk_scores)
            
            logger.info(f"\\nRisk Score Distribution:")
            logger.info(f"  • Average: {avg_risk:.1%}")
            logger.info(f"  • Range: {min_risk:.1%} - {max_risk:.1%}")
        
        if action_types:
            logger.info(f"\\nDoctor Actions:")
            for action, count in sorted(action_types.items()):
                logger.info(f"  • {action}: {count} ({count/total_workflows*100:.1f}%)")
        
        # Performance metrics
        durations = [r.get('duration', 0) for r in results if 'duration' in r]
        if durations:
            avg_duration = sum(durations) / len(durations)
            logger.info(f"\\nPerformance:")
            logger.info(f"  • Average workflow time: {avg_duration:.2f} seconds")


def main():
    """Main HIL workflow testing function"""
    print("="*80)
    print("🧪 HUMAN-IN-THE-LOOP WORKFLOW TESTER")
    print("="*80)
    print("Testing complete workflow: Live Data → ML Prediction → Doctor Action → HIL Log")
    print()
    
    tester = HILWorkflowTester()
    
    # Check service health
    if not tester.check_service_health():
        print("❌ Cannot proceed without prediction service")
        print("💡 Start the service: python sepsis_prediction_service.py")
        return
    
    print("\\n🎯 Test Options:")
    print("1. Single HIL workflow test")
    print("2. Multiple HIL workflows (5 tests)")
    print("3. Stress test (20 workflows)")
    print("4. Exit")
    
    try:
        choice = input("\\nSelect test option (1-4): ").strip()
        
        if choice == "1":
            result = tester.run_single_hil_workflow("SINGLE_TEST_001")
            print(f"\\n✅ Workflow result: {'SUCCESS' if result.get('success') else 'FAILED'}")
            
        elif choice == "2":
            results = tester.run_multiple_hil_workflows(5)
            print(f"\\n✅ Completed {len(results)} workflows")
            
        elif choice == "3":
            print("⚡ Running stress test...")
            results = tester.run_multiple_hil_workflows(20)
            print(f"\\n✅ Stress test completed: {len(results)} workflows")
            
        elif choice == "4":
            print("👋 Exiting HIL tester")
            
        else:
            print("❌ Invalid option")
    
    except KeyboardInterrupt:
        print("\\n⏹️ Testing interrupted by user")
    except Exception as e:
        print(f"\\n❌ Testing failed: {e}")


if __name__ == "__main__":
    main()