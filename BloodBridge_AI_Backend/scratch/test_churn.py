import sys
import unittest
from unittest.mock import patch, MagicMock

# Add backend root to path
backend_path = r"c:\Users\Lenovo\Downloads\BloodBridge-AI (1)\BloodBridge_AI_Backend"
sys.path.append(backend_path)

from ml.churn_predictor import ChurnPredictor

class TestChurnPredictor(unittest.TestCase):
    
    def test_fallback_score(self):
        predictor = ChurnPredictor()
        
        # Test case: active donor who recently donated and missed no alerts
        donor_good = {
            "donor_id": "D-11111",
            "last_donation_date": "2026-06-01",
            "response_rate": 0.9,
            "missed_alerts": 0,
            "avg_response_lag": 120.0,
            "kell_negative": False,
            "city_scarcity_score": 0.5,
            "badge_count": 5,
            "chain_position_avg": 2.0
        }
        res_good = predictor.predict_churn(donor_good)
        self.assertLess(res_good["churn_score"], 0.25)
        self.assertEqual(res_good["churn_risk"], "LOW")
        
        # Test case: inactive donor who hasn't donated for a year and missed multiple alerts
        donor_bad = {
            "donor_id": "D-22222",
            "last_donation_date": "2025-06-01",
            "response_rate": 0.1,
            "missed_alerts": 4,
            "avg_response_lag": 7200.0,
            "kell_negative": False,
            "city_scarcity_score": 0.5,
            "badge_count": 0,
            "chain_position_avg": 7.0
        }
        res_bad = predictor.predict_churn(donor_bad)
        self.assertGreater(res_bad["churn_score"], 0.75)
        self.assertEqual(res_bad["churn_risk"], "CRITICAL")
        self.assertEqual(res_bad["top_risk_factor"], "Multiple missed alert opportunities")

    def test_predict_batch(self):
        predictor = ChurnPredictor()
        donors = [
            {
                "donor_id": "D-1",
                "last_donation_date": "2026-06-01",
                "missed_alerts": 0
            },
            {
                "donor_id": "D-2",
                "last_donation_date": "2025-06-01",
                "missed_alerts": 4
            }
        ]
        res = predictor.predict_batch(donors)
        self.assertEqual(len(res), 2)
        self.assertEqual(res[0]["donor_id"], "D-1")
        self.assertEqual(res[1]["donor_id"], "D-2")
        self.assertEqual(res[0]["churn_risk"], "LOW")
        self.assertEqual(res[1]["churn_risk"], "CRITICAL")

if __name__ == '__main__':
    unittest.main()
