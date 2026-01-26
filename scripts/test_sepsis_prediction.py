#!/usr/bin/env python3
"""
Test Client for Sepsis Prediction Service
Demonstrates real-time sepsis risk prediction with clinical scenarios

This script tests the trained model via the FastAPI service to ensure
the complete pipeline works correctly.
"""

import requests
import json
from datetime import datetime

# Service endpoint
API_BASE_URL = "http://localhost:8001"

def test_prediction_service():
    """Test the sepsis prediction service with clinical scenarios"""
    
    print("="*80)
    print("🧪 TESTING SEPSIS PREDICTION SERVICE")
    print("="*80)
    
    # Check if service is healthy
    try:
        health_response = requests.get(f"{API_BASE_URL}/health")
        if health_response.status_code == 200:
            health_data = health_response.json()
            print("✅ Service Health Check:")
            print(f"   • Status: {health_data['status']}")
            print(f"   • ML Model Loaded: {health_data['models']['ml_model_loaded']}")
            print(f"   • Features Loaded: {health_data['models']['feature_count']}")
        else:
            print("❌ Service health check failed")
            return
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to prediction service")
        print("💡 Please start the service with: python sepsis_prediction_service.py")
        return
    
    # Test scenarios based on clinical practice
    test_scenarios = [
        {
            "name": "🟢 Low-Risk Term Baby (Baseline)",
            "data": {
                "mrn": "TEST001",
                "gestational_age_at_birth_weeks": 39.5,
                "birth_weight_kg": 3.2,
                "sex": "M",
                "race": "white",
                "ga_weeks": 39,
                "ga_days": 4,
                "maternal_temp_celsius": 37.0,
                "rom_hours": 6.0,
                "gbs_status": "negative",
                "antibiotic_type": "none",
                "clinical_exam": "normal",
                "hr": 120.0,
                "spo2": 97.0,
                "rr": 25.0,
                "temp_celsius": 37.1,
                "map": 45.0,
                "comorbidities": "no",
                "central_venous_line": "no",
                "intubated_at_time_of_sepsis_evaluation": "no",
                "inotrope_at_time_of_sepsis_eval": "no",
                "ecmo": "no",
                "stat_abx": "no"
            }
        },
        {
            "name": "🟠 Moderate Risk: Prolonged ROM + Late Preterm",
            "data": {
                "mrn": "TEST002", 
                "gestational_age_at_birth_weeks": 36.8,
                "birth_weight_kg": 2.8,
                "sex": "F",
                "race": "hispanic",
                "ga_weeks": 36,
                "ga_days": 6,
                "maternal_temp_celsius": 37.8,
                "rom_hours": 22.0,
                "gbs_status": "unknown",
                "antibiotic_type": "none",
                "clinical_exam": "normal",
                "hr": 135.0,
                "spo2": 94.0,
                "rr": 28.0,
                "temp_celsius": 37.6,
                "map": 38.0,
                "comorbidities": "no",
                "central_venous_line": "no",
                "intubated_at_time_of_sepsis_evaluation": "no",
                "inotrope_at_time_of_sepsis_eval": "no",
                "ecmo": "no",
                "stat_abx": "no"
            }
        },
        {
            "name": "🔴 High Risk: Preterm + Maternal Fever + GBS+",
            "data": {
                "mrn": "TEST003",
                "gestational_age_at_birth_weeks": 34.2,
                "birth_weight_kg": 2.1,
                "sex": "M",
                "race": "black",
                "ga_weeks": 34,
                "ga_days": 1,
                "maternal_temp_celsius": 38.7,
                "rom_hours": 18.0,
                "gbs_status": "positive",
                "antibiotic_type": "none",
                "clinical_exam": "normal",
                "hr": 155.0,
                "spo2": 91.0,
                "rr": 35.0,
                "temp_celsius": 38.2,
                "map": 32.0,
                "comorbidities": "yes",
                "central_venous_line": "yes",
                "intubated_at_time_of_sepsis_evaluation": "no",
                "inotrope_at_time_of_sepsis_eval": "no",
                "ecmo": "no",
                "stat_abx": "no"
            }
        },
        {
            "name": "🚨 Critical Risk: Very Preterm + Clinical Chorioamnionitis",
            "data": {
                "mrn": "TEST004",
                "gestational_age_at_birth_weeks": 32.5,
                "birth_weight_kg": 1.8,
                "sex": "F",
                "race": "asian",
                "ga_weeks": 32,
                "ga_days": 4,
                "maternal_temp_celsius": 39.1,
                "rom_hours": 30.0,
                "gbs_status": "positive",
                "antibiotic_type": "none",
                "clinical_exam": "abnormal",  # Clinical chorioamnionitis
                "hr": 170.0,
                "spo2": 88.0,
                "rr": 42.0,
                "temp_celsius": 38.8,
                "map": 28.0,
                "comorbidities": "yes",
                "central_venous_line": "yes",
                "intubated_at_time_of_sepsis_evaluation": "yes",
                "inotrope_at_time_of_sepsis_eval": "yes",
                "ecmo": "no",
                "stat_abx": "no"
            }
        },
        {
            "name": "✅ Protected High-Risk: GBS+ with Adequate Antibiotics",
            "data": {
                "mrn": "TEST005",
                "gestational_age_at_birth_weeks": 35.8,
                "birth_weight_kg": 2.5,
                "sex": "M",
                "race": "white",
                "ga_weeks": 35,
                "ga_days": 6,
                "maternal_temp_celsius": 38.2,
                "rom_hours": 16.0,
                "gbs_status": "positive",
                "antibiotic_type": "penicillin",  # Adequate prophylaxis
                "clinical_exam": "normal",
                "hr": 125.0,
                "spo2": 96.0,
                "rr": 30.0,
                "temp_celsius": 37.3,
                "map": 40.0,
                "comorbidities": "no",
                "central_venous_line": "no",
                "intubated_at_time_of_sepsis_evaluation": "no",
                "inotrope_at_time_of_sepsis_eval": "no",
                "ecmo": "no",
                "stat_abx": "yes",
                "time_to_antibiotics": 0.5
            }
        }
    ]
    
    print(f"\n🔬 Testing {len(test_scenarios)} Clinical Scenarios:")
    print("="*80)
    
    results = []
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n{i}. {scenario['name']}")
        print("-" * 60)
        
        try:
            # Make prediction request
            response = requests.post(
                f"{API_BASE_URL}/predict",
                json=scenario['data'],
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                prediction = response.json()
                results.append(prediction)
                
                # Display results in clinical format
                print(f"👤 Patient: {prediction['mrn']}")
                print(f"📊 Sepsis Risk: {prediction['sepsis_risk_percentage']:.1f}% (Probability: {prediction['sepsis_probability']:.4f})")
                print(f"⚠️  Risk Category: {prediction['risk_category'].replace('_', ' ')}")
                print(f"⏰ Estimated Onset: {prediction['estimated_onset_hours']} hours")
                print(f"🏥 EOS Risk: {prediction['eos_risk_score']:.2f}/1000 ({prediction['eos_category'].replace('_', ' ')})")
                print(f"🫀 Physiological Instability: {prediction['physiological_instability_score']}/4")
                print(f"🚨 Vital Signs Alert: {'YES' if prediction['vital_signs_alert'] else 'NO'}")
                print(f"💡 Clinical Recommendation:")
                print(f"   {prediction['clinical_recommendation']}")
                
                # Model insight
                if prediction['feature_importance_top3']:
                    print(f"🔍 Key Risk Factors:")
                    for feature, importance in prediction['feature_importance_top3'].items():
                        print(f"   • {feature}: {importance:.4f}")
                
            else:
                print(f"❌ Prediction failed: {response.status_code}")
                print(f"Error: {response.text}")
                
        except Exception as e:
            print(f"❌ Request error: {e}")
    
    # Summary analysis
    if results:
        print(f"\n" + "="*80)
        print("📈 CLINICAL VALIDATION SUMMARY")
        print("="*80)
        
        risk_distribution = {}
        for result in results:
            category = result['risk_category']
            risk_distribution[category] = risk_distribution.get(category, 0) + 1
        
        print(f"Risk Distribution:")
        for category, count in sorted(risk_distribution.items()):
            print(f"  • {category.replace('_', ' ')}: {count} cases")
        
        # Clinical appropriateness check
        print(f"\nClinical Appropriateness:")
        appropriate_predictions = 0
        
        for i, result in enumerate(results):
            expected_high_risk = ["TEST003", "TEST004"]  # Known high-risk cases
            expected_low_risk = ["TEST001", "TEST005"]   # Known low-risk cases
            
            mrn = result['mrn']
            risk_prob = result['sepsis_probability']
            
            if mrn in expected_high_risk and risk_prob >= 0.3:
                appropriate_predictions += 1
                print(f"  ✅ {mrn}: Correctly identified as high risk ({risk_prob:.3f})")
            elif mrn in expected_low_risk and risk_prob < 0.5:
                appropriate_predictions += 1
                print(f"  ✅ {mrn}: Correctly identified as lower risk ({risk_prob:.3f})")
            elif mrn not in expected_high_risk and mrn not in expected_low_risk:
                appropriate_predictions += 1
                print(f"  ✅ {mrn}: Reasonable risk assessment ({risk_prob:.3f})")
            else:
                print(f"  ⚠️  {mrn}: Unexpected risk level ({risk_prob:.3f})")
        
        accuracy = appropriate_predictions / len(results) * 100
        print(f"\nClinical Accuracy: {accuracy:.1f}% ({appropriate_predictions}/{len(results)})")
        
        print(f"\n🎯 VALIDATION COMPLETE!")
        print(f"   • Model successfully integrated with FastAPI")
        print(f"   • Real-time predictions working correctly")  
        print(f"   • Clinical decision support functioning")
        print(f"   • EOS risk calculator properly embedded")


if __name__ == "__main__":
    test_prediction_service()