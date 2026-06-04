import sys
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, date

# Add backend root to path
backend_path = r"c:\Users\Lenovo\Downloads\BloodBridge-AI (1)\BloodBridge_AI_Backend"
sys.path.append(backend_path)

from services.gamification_service import get_next_badge_progress
from ml.challenge_recommender import ChallengeRecommender
from services.impact_story import generate_impact_story
from services.consent_service import ConsentService

class TestPhase5(unittest.IsolatedAsyncioTestCase):

    # 1. Gamification Progress test
    async def test_next_badge_progress(self):
        # 0 donations
        p0 = await get_next_badge_progress({"donation_count": 0})
        self.assertEqual(p0["current_badge"], "None")
        self.assertEqual(p0["next_badge"], "Blood Starter")
        self.assertEqual(p0["remaining"], 1)

        # 3 donations
        p3 = await get_next_badge_progress({"donation_count": 3})
        self.assertEqual(p3["current_badge"], "Blood Starter")
        self.assertEqual(p3["next_badge"], "Life Saver")
        self.assertEqual(p3["remaining"], 2)

        # 8 donations
        p8 = await get_next_badge_progress({"donation_count": 8})
        self.assertEqual(p8["current_badge"], "Life Saver")
        self.assertEqual(p8["next_badge"], "Blood Hero")
        self.assertEqual(p8["remaining"], 2)

        # 12 donations
        p12 = await get_next_badge_progress({"donation_count": 12})
        self.assertEqual(p12["current_badge"], "Blood Hero")
        self.assertEqual(p12["next_badge"], "None")
        self.assertEqual(p12["remaining"], 0)

    # 2. Challenge Recommender test
    @patch('ml.challenge_recommender.get_supabase_admin')
    def test_recommend_challenges(self, mock_get_supabase):
        # Mock cold start profile lookup
        mock_supabase = MagicMock()
        mock_get_supabase.return_value = mock_supabase
        
        mock_execute = MagicMock()
        mock_execute.execute.return_value = MagicMock(data=[{
            "donor_id": "D-99999",
            "kell_negative": True,
            "donation_count": 5,
            "response_rate": 0.9,
            "city": "Hyderabad"
        }])
        mock_supabase.table.return_value.select.return_value.eq.return_value = mock_execute

        recommender = ChallengeRecommender()
        recs = recommender.recommend_challenges("D-99999", top_k=3)
        
        self.assertEqual(len(recs), 3)
        self.assertIn("challenge_id", recs[0])
        self.assertIn("name", recs[0])
        self.assertIn("emoji", recs[0])

    # 3. Impact Story test
    @patch('services.impact_story.get_supabase_admin')
    @patch('services.impact_story.build_memory_context_for_llm')
    async def test_generate_impact_story_fallback(self, mock_memory, mock_get_supabase):
        mock_memory.return_value = "Donor profile memory context"
        mock_supabase = MagicMock()
        mock_get_supabase.return_value = mock_supabase
        
        donor = {"donor_id": "D-1111", "name": "Rahul Kumar"}
        patient = {"name": "Aarav Sharma", "hospital": "KIMS"}
        
        story = await generate_impact_story(donor, patient, "en")
        self.assertIn("Aarav", story)
        self.assertIn("Rahul Kumar", story)
        self.assertIn("KIMS", story)

    # 4. Consent Service test
    @patch('services.consent_service.get_supabase_admin')
    async def test_consent_service_grant_and_revoke(self, mock_get_supabase):
        mock_supabase = MagicMock()
        mock_get_supabase.return_value = mock_supabase
        
        # Mock check_consent queries
        mock_execute = MagicMock()
        mock_execute.execute.return_value = MagicMock(data=[{"action": "granted"}])
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value = mock_execute
        
        res = await ConsentService.check_consent("D-1111", "outreach_sms")
        self.assertTrue(res)
        
        # Test grant_consent
        grant_res = await ConsentService.grant_consent("D-1111", ["outreach_sms"], "telegram", "en")
        self.assertTrue(grant_res)
        
        # Test revoke_consent
        revoke_res = await ConsentService.revoke_consent("D-1111", "outreach_sms")
        self.assertTrue(revoke_res)

    # 5. Right to Erasure checks active request block
    @patch('services.consent_service.get_supabase_admin')
    async def test_erase_donor_data_blocked_by_active_emergency(self, mock_get_supabase):
        mock_supabase = MagicMock()
        mock_get_supabase.return_value = mock_supabase
        
        # Set up mock returns indicating an active chain node in PENDING state
        mock_execute_chains = MagicMock()
        mock_execute_chains.execute.return_value = MagicMock(data=[{"request_id": "REQ-12345", "status": "PENDING"}])
        
        mock_execute_reqs = MagicMock()
        mock_execute_reqs.execute.return_value = MagicMock(data=[{"request_id": "REQ-12345"}])
        
        # Chain query
        mock_supabase.table.return_value.select.return_value.eq.return_value.in_.return_value = mock_execute_chains
        # Request status query
        mock_supabase.table.return_value.select.return_value.in_.return_value.eq.return_value = mock_execute_reqs
        
        res = await ConsentService.erase_donor_data("D-1111", "api_request")
        self.assertFalse(res["success"])
        self.assertIn("Active emergency coordination", res["error"])

if __name__ == '__main__':
    unittest.main()
