"""
AWS Textract OCR and Gemini Vision blood card extractor for BloodBridge AI.
Replaces pytesseract with AWS Textract analyze_document(FORMS + LINES).
"""
import re
import base64
import logging
from datetime import datetime
import boto3
from core.database import get_supabase_admin
from core.config import get_settings

logger = logging.getLogger(__name__)

KNOWN_BLOOD_TYPES = {"A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"}

async def call_vision_llm(image_bytes: bytes) -> str:
    """Fallback to Vision LLM for blood group extraction if Textract fails."""
    try:
        from core.llm_provider import get_reasoning_llm
        from langchain_core.messages import HumanMessage
        
        base64_data = base64.b64encode(image_bytes).decode('utf-8')
        
        llm = get_reasoning_llm()
        
        message = HumanMessage(
            content=[
                {"type": "text", "text": (
                    "You are looking at a photo. Find the blood type / blood group on this image. "
                    "It will look like one of: A+, A-, B+, B-, AB+, AB-, O+, O-. "
                    "It may also be written as 'A POSITIVE', 'B NEG', 'O Positive', etc. "
                    "It might be on a blood donation card, ID card, hospital report, or any document. "
                    "Reply with ONLY the blood type in standard format (e.g. 'B+'). "
                    "If you cannot find any blood type, reply ONLY with 'UNKNOWN'."
                )},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{base64_data}"},
                },
            ]
        )
        
        resp = await llm.ainvoke([message])
        res_text = resp.content.strip().upper() if isinstance(resp.content, str) else str(resp.content).strip().upper()
        logger.info(f"Vision LLM raw output: {res_text[:200]}")
        # Match exact pattern: A+, A-, B+, B-, AB+, AB-, O+, O-
        clean_match = re.search(r'\b(AB|A|B|O)[+-]\b', res_text)
        if clean_match:
            return clean_match.group(0)
        # Match "A POSITIVE" / "B NEG" patterns
        pos_match = re.search(r'\b(AB|A|B|O)\s*(POSITIVE|POS|NEGATIVE|NEG)\b', res_text)
        if pos_match:
            letter = pos_match.group(1)
            sign = "+" if pos_match.group(2).startswith("POS") else "-"
            return f"{letter}{sign}"
    except Exception as e:
        logger.error(f"Vision LLM call failed: {e}", exc_info=True)
    return ""

async def extract_blood_type_from_image(image_bytes: bytes, donor_id: str | None = None) -> dict:
    """
    Extracts blood type and donor name from a blood group card photo using AWS Textract.
    Returns: {blood_group, name, raw_text}
    """
    settings = get_settings()
    raw_text = ""
    blood_group = None
    donor_name = None
    
    try:
        client = boto3.client(
            'textract',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        
        response = client.analyze_document(
            Document={'Bytes': image_bytes},
            FeatureTypes=["FORMS"]
        )
        
        blocks = response.get('Blocks', [])
        
        lines = []
        key_map = {}
        value_map = {}
        block_map = {}
        
        for block in blocks:
            block_map[block['Id']] = block
            if block['BlockType'] == 'LINE':
                lines.append(block['Text'])
            elif block['BlockType'] == 'KEY_VALUE_SET':
                if 'KEY' in block.get('EntityTypes', []):
                    key_map[block['Id']] = block
                else:
                    value_map[block['Id']] = block

        raw_text = " ".join(lines)
        
        # Helper to get text from a block
        def get_text(node):
            text = ""
            if 'Relationships' in node:
                for relationship in node['Relationships']:
                    if relationship['Type'] == 'CHILD':
                        for child_id in relationship['Ids']:
                            child = block_map.get(child_id)
                            if child and child['BlockType'] == 'WORD':
                                text += child['Text'] + " "
            return text.strip()

        # Parse forms for Name and Blood Group
        for block_id, key_block in key_map.items():
            key_text = get_text(key_block).lower()
            val_text = ""
            if 'Relationships' in key_block:
                for relationship in key_block['Relationships']:
                    if relationship['Type'] == 'VALUE':
                        for val_id in relationship['Ids']:
                            val_block = value_map.get(val_id)
                            if val_block:
                                val_text = get_text(val_block)
            
            if "name" in key_text and not donor_name:
                donor_name = val_text
            
            if ("blood" in key_text or "group" in key_text) and not blood_group:
                bg_clean = val_text.strip().upper()
                bg_clean = bg_clean.replace("POSITIVE", "+").replace("POS", "+").replace("NEGATIVE", "-").replace("NEG", "-")
                match = re.search(r'\b(A|B|AB|O)[+-]\b', bg_clean)
                if match:
                    blood_group = match.group(0)

        # Fallback to scanning lines for blood group
        if not blood_group:
            patterns = [
                r'\b(AB|A|B|O)[+-](?!\w)',
                r'\b(AB|A|B|O)\s*(positive|negative|pos|neg)\b',
                r'Blood\s*Grp\s*[:\-]?\s*(AB|A|B|O)[+-]',
                r'Blood\s*Group\s*[:\-]?\s*(AB|A|B|O)[+-]',
                r'रक्त समूह\s*[:\-]?\s*(AB|A|B|O)[+-]',
                r'రక్త సమూహం\s*[:\-]?\s*(AB|A|B|O)[+-]',
                r'இரத்த வகை\s*[:\-]?\s*(AB|A|B|O)[+-]'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, raw_text, re.IGNORECASE)
                if match:
                    bg_letter = match.group(1).upper()
                    sign = "+" if "+" in match.group(0) or "pos" in match.group(0).lower() else "-"
                    blood_group = f"{bg_letter}{sign}"
                    break

        logger.info(f"Textract result: blood_group={blood_group}, name={donor_name}, raw_text_len={len(raw_text)}, sample='{raw_text[:200]}'")
                    
    except Exception as e:
        logger.warning(f"AWS Textract failed: {e}. Falling back to Vision LLM.")
        
    if blood_group not in KNOWN_BLOOD_TYPES:
        blood_group = None

    if not blood_group:
        vision_res = await call_vision_llm(image_bytes)
        if vision_res in KNOWN_BLOOD_TYPES:
            blood_group = vision_res

    # Audit log in Supabase
    if donor_id and blood_group:
        supabase = get_supabase_admin()
        try:
            update_payload = {
                "blood_type": blood_group,
                "updated_at": datetime.utcnow().isoformat() + "Z"
            }
            if donor_name:
                update_payload["name"] = donor_name
                
            supabase.table("donors").update(update_payload).eq("donor_id", donor_id).execute()
                
            supabase.table("donor_verifications").insert({
                "donor_id": donor_id,
                "antigen_flag": "ocr_card",
                "flag_value": True,
                "verification_type": "ocr_card",
                "confidence": 0.95 if blood_group else 0.5,
                "notes": raw_text[:100] if raw_text else "Extracted via Textract/Gemini"
            }).execute()
        except Exception as e:
            logger.error(f"Failed to save donor verification audit for {donor_id}: {e}")
            
    return {
        "blood_group": blood_group,
        "name": donor_name,
        "raw_text": raw_text
    }
