import sys
import unittest
from unittest.mock import patch, MagicMock
from datetime import date

# Add backend root to path
backend_path = r"c:\Users\Lenovo\Downloads\BloodBridge-AI (1)\BloodBridge_AI_Backend"
sys.path.append(backend_path)

from services.donor_memory import build_memory_context_for_llm

class TestDonorMemory(unittest.IsolatedAsyncioTestCase):
    
    @patch('services.donor_memory.get_memory')
    @patch('services.donor_memory.get_supabase_admin')
    async def test_build_memory_context_for_llm(self, mock_get_supabase, mock_get_memory):
        # Setup mock for Supabase select
        mock_supabase = MagicMock()
        mock_get_supabase.return_value = mock_supabase
        
        mock_execute = MagicMock()
        mock_execute.execute.return_value = MagicMock(data=[{
            "name": "Rahul Kumar",
            "preferred_language": "Hindi",
            "donation_count": 13,
            "response_rate": 0.87,
            "last_donation_date": "2026-04-20"  # This will depend on date.today(), so let's mock/control it or calculate expected delta
        }])
        mock_supabase.table.return_value.select.return_value.eq.return_value = mock_execute
        
        # Setup mock for get_memory
        mock_get_memory.return_value = {
            "tone_profile": "warm",
            "emotional_anchors": ["saved child"],
            "streak_days": 210
        }
        
        res = await build_memory_context_for_llm("fake_donor_id")
        
        # Calculate expected days_ago
        delta = (date.today() - date.fromisoformat("2026-04-20")).days
        expected = (
            f"Donor: Rahul Kumar | Language: Hindi | Tone: warm | Anchors: [saved child]\n"
            f"13 donations, 87% response rate, {delta} days ago | Streak: 7 months"
        )
        self.assertEqual(res, expected)

if __name__ == '__main__':
    unittest.main()
