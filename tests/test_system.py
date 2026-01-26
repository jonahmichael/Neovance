"""
Test suite for Neovance-AI system
"""

import unittest
import requests
import json
from datetime import datetime

class TestNeovanceAI(unittest.TestCase):
    """Test cases for the Neovance-AI system"""
    
    def setUp(self):
        """Set up test configuration"""
        self.api_base_url = "http://localhost:8000"
        self.test_baby_id = "B001"
        self.test_vitals = {
            "baby_id": self.test_baby_id,
            "hr": 150,
            "spo2": 92,
            "rr": 45,
            "temp": 37.2,
            "map": 35,
            "timestamp": datetime.now().isoformat()
        }
    
    def test_api_health(self):
        """Test API health endpoint"""
        try:
            response = requests.get(f"{self.api_base_url}/health")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["status"], "healthy")
        except requests.exceptions.RequestException as e:
            self.fail(f"API health check failed: {e}")
    
    def test_sepsis_prediction(self):
        """Test sepsis prediction endpoint"""
        try:
            response = requests.post(
                f"{self.api_base_url}/predict_sepsis",
                json=self.test_vitals
            )
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertIn("risk_score", data)
            self.assertIn("prediction", data)
            self.assertTrue(0 <= data["risk_score"] <= 1)
        except requests.exceptions.RequestException as e:
            self.fail(f"Sepsis prediction test failed: {e}")
    
    def test_baby_data(self):
        """Test baby data retrieval"""
        try:
            response = requests.get(f"{self.api_base_url}/babies/{self.test_baby_id}")
            if response.status_code == 200:
                data = response.json()
                self.assertEqual(data["baby_id"], self.test_baby_id)
            elif response.status_code == 404:
                # Baby not found - acceptable for test
                pass
            else:
                self.fail(f"Unexpected status code: {response.status_code}")
        except requests.exceptions.RequestException as e:
            self.fail(f"Baby data test failed: {e}")

if __name__ == '__main__':
    unittest.main()