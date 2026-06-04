import sys
import unittest
from unittest.mock import patch, MagicMock

# Add backend root to path
backend_path = r"c:\Users\Lenovo\Downloads\BloodBridge-AI (1)\BloodBridge_AI_Backend"
sys.path.append(backend_path)

from services.ocr_service import extract_blood_type_from_image

class TestOCRExtractor(unittest.IsolatedAsyncioTestCase):
    
    @patch('pytesseract.image_to_string')
    @patch('services.ocr_service.preprocess_image')
    @patch('core.database.get_supabase_admin')
    async def test_standard_pattern(self, mock_db, mock_preprocess, mock_ocr):
        mock_ocr.return_value = "This card belongs to John Doe. Blood Group: B-"
        # Standard pattern should match B- directly (index 0) or labeled (index 2: Blood Grp: B-)?
        # Wait, "Blood Group: B-" matches lp r'Blood\s*Grp\s*[:\-]?\s*(A|B|AB|O)[+-]'
        # Let's see what is matched first.
        # "Blood Group: B-" has "Blood Group: B-" or "Blood Grp: B-".
        # Let's test a simple standard pattern: just "O+" in the text.
        mock_ocr.return_value = "Donor name: Rahul\nO+\nDate: 2026"
        res = await extract_blood_type_from_image(b"fake_image_bytes")
        self.assertEqual(res["blood_type"], "O+")
        self.assertEqual(res["confidence"], 0.95)
        self.assertFalse(res["kell_negative"])

    @patch('pytesseract.image_to_string')
    @patch('services.ocr_service.preprocess_image')
    @patch('core.database.get_supabase_admin')
    async def test_labeled_pattern(self, mock_db, mock_preprocess, mock_ocr):
        mock_ocr.return_value = "Name: Rahul Kumar\nBlood Grp: AB-\nCity: Delhi"
        res = await extract_blood_type_from_image(b"fake_image_bytes")
        self.assertEqual(res["blood_type"], "AB-")
        self.assertEqual(res["confidence"], 0.85)
        self.assertFalse(res["kell_negative"])

    @patch('pytesseract.image_to_string')
    @patch('services.ocr_service.preprocess_image')
    @patch('core.database.get_supabase_admin')
    async def test_fuzzy_pattern(self, mock_db, mock_preprocess, mock_ocr):
        mock_ocr.return_value = "Hospital Card. A positive donor."
        res = await extract_blood_type_from_image(b"fake_image_bytes")
        self.assertEqual(res["blood_type"], "A+")
        self.assertEqual(res["confidence"], 0.65)
        self.assertFalse(res["kell_negative"])

    @patch('pytesseract.image_to_string')
    @patch('services.ocr_service.preprocess_image')
    @patch('core.database.get_supabase_admin')
    async def test_kell_negative(self, mock_db, mock_preprocess, mock_ocr):
        # High confidence (standard) + Kell negative
        mock_ocr.return_value = "A-\nKell negative"
        res = await extract_blood_type_from_image(b"fake_image_bytes")
        self.assertEqual(res["blood_type"], "A-")
        self.assertEqual(res["confidence"], 0.95)
        self.assertTrue(res["kell_negative"])

    @patch('pytesseract.image_to_string')
    @patch('services.ocr_service.preprocess_image')
    @patch('core.database.get_supabase_admin')
    async def test_kell_negative_low_confidence(self, mock_db, mock_preprocess, mock_ocr):
        # Low confidence (fuzzy) + Kell negative
        # Standard blood pattern should be missing to trigger fuzzy.
        mock_ocr.return_value = "A positive\nKell negative"
        res = await extract_blood_type_from_image(b"fake_image_bytes")
        self.assertEqual(res["blood_type"], "A+")
        self.assertEqual(res["confidence"], 0.65)
        # Even though Kell negative is in text, confidence is <= 0.85, so it should return False
        self.assertFalse(res["kell_negative"])

if __name__ == '__main__':
    unittest.main()
