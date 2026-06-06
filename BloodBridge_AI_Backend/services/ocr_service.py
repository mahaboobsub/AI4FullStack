"""
Tesseract OCR and Gemini Vision blood card extractor for BloodBridge AI.
"""
import re
import base64
import logging
from io import BytesIO
from datetime import datetime
from PIL import Image, ImageEnhance, ImageFilter
from core.database import get_supabase_admin
from core.config import get_settings

logger = logging.getLogger(__name__)

TESSERACT_LANG = 'eng+hin+tel+tam+kan+mal+mar+ben+guj+pan'
KNOWN_BLOOD_TYPES = {"A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"}

def preprocess_image(image_bytes: bytes) -> Image.Image:
    """Preprocess image: grayscale -> contrast enhance -> thresholding."""
    img = Image.open(BytesIO(image_bytes))
    # Convert to grayscale
    img = img.convert('L')
    # Enhance contrast
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(2.0)
    # Apply filter for noise reduction
    img = img.filter(ImageFilter.SHARPEN)
    return img

async def call_gemini_vision(image_bytes: bytes) -> str:
    """Fallback to Gemini Vision for blood group extraction if local Tesseract fails."""
    try:
        from core.llm_provider import get_reasoning_llm
        from langchain_core.messages import HumanMessage
        
        base64_data = base64.b64encode(image_bytes).decode('utf-8')
        
        llm = get_reasoning_llm()
        
        message = HumanMessage(
            content=[
                {"type": "text", "text": "What is the blood group shown in this card image? Reply ONLY with the blood type (A+, B-, O+, etc.). If not found, reply 'UNKNOWN'."},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{base64_data}"},
                },
            ]
        )
        
        resp = await llm.ainvoke([message])
        res_text = resp.content.strip().upper()
        # Clean any markdown or spaces
        clean_match = re.search(r'\b(A|B|AB|O)[+-]\b', res_text)
        if clean_match:
            return clean_match.group(0)
    except Exception as e:
        logger.error(f"Gemini Vision call failed: {e}", exc_info=True)
    return ""

async def extract_blood_type_from_image(image_bytes: bytes, donor_id: str = None) -> dict:
    """
    Extracts blood type from a blood group card photo.
    Returns: {blood_type, confidence, raw_text, method, kell_negative}
    """
    raw_text = ""
    blood_type = None
    confidence = 0.0
    method = "tesseract"
    
    # 1. Attempt Tesseract OCR if available
    try:
        import pytesseract
        preprocessed = preprocess_image(image_bytes)
        raw_text = pytesseract.image_to_string(preprocessed, lang=TESSERACT_LANG)
    except Exception as e:
        logger.warning(f"Local Pytesseract extraction failed or not installed: {e}. Falling back directly to Gemini Vision.")
        method = "gemini_vision"
        
    if raw_text:
        # Regex search patterns (English + Indian languages)
        patterns = [
            r'\b(A|B|AB|O)[+-](?!\w)',
            r'\b(A|B|AB|O)\s*(positive|negative|pos|neg)\b',
            r'Blood\s*Grp\s*[:\-]?\s*(A|B|AB|O)[+-]',
            r'रक्त समूह\s*[:\-]?\s*(A|B|AB|O)[+-]',
            r'రక్త సమూహం\s*[:\-]?\s*(A|B|AB|O)[+-]',
            r'இரத்த வகை\s*[:\-]?\s*(A|B|AB|O)[+-]'
        ]
        
        # 1. Check labeled patterns (indices 2 to 5)
        matched_node = None
        for pattern in patterns[2:]:
            match = re.search(pattern, raw_text, re.IGNORECASE)
            if match:
                matched_node = match
                confidence = 0.85
                break
                
        # 2. Check standard pattern if no labeled match (index 0)
        if not matched_node:
            match = re.search(patterns[0], raw_text, re.IGNORECASE)
            if match:
                matched_node = match
                confidence = 0.95
                
        # 3. Check fuzzy pattern if no standard or labeled match (index 1)
        if not matched_node:
            match = re.search(patterns[1], raw_text, re.IGNORECASE)
            if match:
                matched_node = match
                confidence = 0.65
                
        if matched_node:
            blood_letter = matched_node.group(1).upper()
            
            # Determine sign (+ or -)
            sign = ""
            # If fuzzy, check group 2
            if len(matched_node.groups()) >= 2 and matched_node.group(2):
                sign_word = matched_node.group(2).lower()
                if "pos" in sign_word or "positive" in sign_word:
                    sign = "+"
                elif "neg" in sign_word or "negative" in sign_word:
                    sign = "-"
            else:
                # Standard or Labeled patterns, search '+' or '-' in the matched string
                full_match = matched_node.group(0)
                if "+" in full_match:
                    sign = "+"
                elif "-" in full_match:
                    sign = "-"
                    
            if sign:
                blood_type = f"{blood_letter}{sign}"
                
            if blood_type not in KNOWN_BLOOD_TYPES:
                blood_type = None
                confidence = 0.0

    # 2. Fallback to Gemini Vision if confidence < 0.6
    if confidence < 0.6:
        logger.info("Tesseract confidence low. Invoking Gemini Vision fallback...")
        gemini_res = await call_gemini_vision(image_bytes)
        if gemini_res in KNOWN_BLOOD_TYPES:
            blood_type = gemini_res
            confidence = 0.90
            method = "gemini_vision"

    # Kell extraction attempt
    kell_negative = False
    kell_found = False
    if raw_text:
        kell_patterns = [
            r'Kell\s*(positive|negative|pos|neg)', 
            r'K\s*(pos|neg|\+|-)', 
            r'Kell-negative'
        ]
        for kp in kell_patterns:
            k_match = re.search(kp, raw_text, re.IGNORECASE)
            if k_match:
                k_val = k_match.group(0).lower()
                kell_found = True
                if "negative" in k_val or "-" in k_val or "neg" in k_val:
                    kell_negative = True
                else:
                    kell_negative = False
                break
                
    result_kell = kell_negative if (kell_found and confidence > 0.85) else False
            
    # 3. Audit log in Supabase donor_verifications
    if donor_id and blood_type:
        supabase = get_supabase_admin()
        try:
            # Update donor record if verified
            update_payload = {
                "blood_type": blood_type,
                "updated_at": datetime.utcnow().isoformat() + "Z"
            }
            if kell_found and confidence > 0.85:
                update_payload["kell_negative"] = kell_negative
                
            supabase.table("donors")\
                .update(update_payload)\
                .eq("donor_id", donor_id)\
                .execute()
                
            # Insert verification record
            supabase.table("donor_verifications").insert({
                "donor_id": donor_id,
                "antigen_flag": "blood_type_confirmed",
                "flag_value": True,
                "verification_type": "ocr_card",
                "confidence": confidence,
                "notes": raw_text[:100] if raw_text else f"Extracted via {method}"
            }).execute()
        except Exception as e:
            logger.error(f"Failed to save donor verification audit for {donor_id}: {e}")
            
    return {
        "blood_type": blood_type,
        "confidence": confidence,
        "raw_text": raw_text,
        "method": method,
        "kell_negative": result_kell
    }
