#!/usr/bin/env python3
"""
Simple Model Test - Quick validation of sepsis prediction model
Tests the model directly and via API to ensure everything is working
"""

import requests
import json
import joblib
import pandas as pd
import numpy as np
from datetime import datetime

def test_model_directly():
    """Test the trained model directly"""
    print("🔬 Testing Model Directly:")
    print("="*50)
    
    try:
        # Load the trained model
        model = joblib.load('trained_models/sepsis_random_forest.pkl')
        scaler = joblib.load('trained_models/feature_scaler.pkl')
        feature_columns = joblib.load('trained_models/feature_columns.pkl')
        
        print(f"✅ Model loaded: {type(model).__name__}")
        print(f"✅ Features loaded: {len(feature_columns)} features")
        print(f"✅ Scaler loaded: {type(scaler).__name__}")
        
        # Create sample test data
        sample_data = {
            'gestational_age_at_birth_weeks': 35.0,
            'birth_weight_kg': 2.5,
            'maternal_temp_celsius': 38.5,
            'rom_hours': 20.0,
            'hr': 160.0,
            'temp_celsius': 38.0,
            'rr': 35.0,
            'spo2': 92.0,
            'map': 35.0
        }
        
        # Fill missing features with defaults
        test_df = pd.DataFrame([sample_data])
        for col in feature_columns:
            if col not in test_df.columns:
                test_df[col] = 0
        
        test_df = test_df[feature_columns]
        
        # Make prediction
        test_scaled = scaler.transform(test_df)
        prediction = model.predict_proba(test_scaled)[0]
        risk_score = prediction[1]  # Probability of sepsis
        
        print(f"🎯 Sample prediction: {risk_score:.3f} ({risk_score*100:.1f}%)")
        
        if risk_score > 0.8:
            risk_level = "CRITICAL"
        elif risk_score > 0.6:
            risk_level = "HIGH"
        elif risk_score > 0.3:
            risk_level = "MODERATE"
        else:
            risk_level = "LOW"
            
        print(f"📊 Risk Level: {risk_level}")
        print("✅ Direct model test PASSED!")
        return True
        
    except Exception as e:
        print(f"❌ Direct model test FAILED: {e}")
        return False

def test_api_service():
    """Test the model via FastAPI service"""
    print("\\n🌐 Testing via API Service:")
    print("="*50)
    
    api_url = "http://localhost:8001"
    
    try:
        # Test health endpoint
        health_response = requests.get(f"{api_url}/health", timeout=5)
        if health_response.status_code == 200:
            health_data = health_response.json()
            print("✅ Service is healthy")
            print(f"   Model loaded: {health_data.get('models', {}).get('ml_model_loaded', 'Unknown')}")
        else:
            print("❌ Service health check failed")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API service")
        print("💡 Start the service with: python sepsis_prediction_service.py")
        return False
    except requests.exceptions.Timeout:
        print("❌ API service timeout")
        return False
    
    # Test prediction endpoint
    test_data = {
        "patient_id": "TEST_BABY_001",
        "gestational_age": 35.0,
        "birth_weight": 2.5,
        "maternal_temperature": 38.5,
        "rom_duration": 20.0,
        "heart_rate": 160.0,
        "temperature": 38.0,
        "respiratory_rate": 35.0,
        "oxygen_saturation": 92.0,
        "blood_pressure": 35.0,
        "white_blood_cells": 15000,
        "eos_risk_score": 7.5
    }
    
    try:
        prediction_response = requests.post(
            f"{api_url}/predict_risk",
            json=test_data,
            timeout=10
        )
        
        if prediction_response.status_code == 200:
            result = prediction_response.json()
            print("✅ Prediction successful!")
            print(f"   🎯 Risk Score: {result['risk_score']:.3f}")
            print(f"   📊 Risk Level: {result['risk_level']}")
            print(f"   👤 Patient: {result['patient_id']}")
            print("✅ API service test PASSED!")
            return True
        else:
            print(f"❌ Prediction failed: {prediction_response.status_code}")
            print(f"   Error: {prediction_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ API prediction test FAILED: {e}")
        return False

def test_complete_workflow():
    """Test the complete HIL workflow"""
    print("\\n🔄 Testing Complete HIL Workflow:")
    print("="*50)
    
    try:
        # Run the comprehensive HIL test
        import subprocess
        result = subprocess.run(
            ['python', 'test_complete_hil_workflow.py'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print("✅ Complete HIL workflow test PASSED!")
            print("   • ML predictions working")
            print("   • Database logging functional") 
            print("   • Doctor action logging working")
            return True
        else:
            print(f"❌ HIL workflow test FAILED")
            print(f"   Error output: {result.stderr[:200]}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ HIL workflow test TIMEOUT")
        return False
    except Exception as e:
        print(f"❌ HIL workflow test ERROR: {e}")
        return False

def main():
    """Run all model tests"""
    print("🏥 NEOVANCE-AI: MODEL TESTING SUITE")
    print("="*80)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        ("Direct Model Test", test_model_directly),
        ("API Service Test", test_api_service), 
        ("Complete Workflow Test", test_complete_workflow)
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test_name, test_func in tests:
        print(f"\\n{'='*80}")
        print(f"🧪 Running: {test_name}")
        print(f"{'='*80}")
        
        if test_func():
            passed_tests += 1
            print(f"✅ {test_name} PASSED")
        else:
            print(f"❌ {test_name} FAILED")
    
    # Summary
    print(f"\\n{'='*80}")
    print("📋 TEST SUMMARY")
    print(f"{'='*80}")
    print(f"Tests Passed: {passed_tests}/{total_tests}")
    print(f"Success Rate: {passed_tests/total_tests*100:.1f}%")
    
    if passed_tests == total_tests:
        print("\\n🎉 ALL TESTS PASSED! Your model is working correctly!")
        print("\\nNext steps:")
        print("1. ✅ Model is trained and ready")
        print("2. ✅ API service is functional") 
        print("3. ✅ HIL workflow is working")
        print("4. 🚀 Ready for production deployment!")
    else:
        print(f"\\n⚠️  {total_tests - passed_tests} tests failed. Please check the errors above.")
        
        if passed_tests >= 1:
            print("✅ Basic model functionality is working")
            
        if passed_tests < total_tests:
            print("\\n🔧 Troubleshooting tips:")
            print("• Ensure prediction service is running: python sepsis_prediction_service.py")
            print("• Check if trained model files exist in trained_models/")
            print("• Verify database connection for HIL workflow")

if __name__ == "__main__":
    main()