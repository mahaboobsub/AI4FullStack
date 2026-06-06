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
        
        # Detect image MIME type from magic bytes
        if image_bytes[:4] == b'\x89PNG':
            mime_type = "image/png"
        elif image_bytes[:2] == b'\xff\xd8':
            mime_type = "image/jpeg"
        elif image_bytes[:4] == b'RIFF' and image_bytes[8:12] == b'WEBP':
            mime_type = "image/webp"
        elif image_bytes[:3] == b'GIF':
            mime_type = "image/gif"
        else:
            mime_type = "image/jpeg"
        
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
                    "image_url": {"url": f"data:{mime_type};base64,{base64_data}"},
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


async def call_vision_llm_antigens(image_bytes: bytes) -> dict:
    """Vision LLM fallback for antigen panel extraction from blood card."""
    try:
        from core.llm_provider import get_reasoning_llm
        from langchain_core.messages import HumanMessage
        import json as _json

        base64_data = base64.b64encode(image_bytes).decode('utf-8')
        
        # Detect image MIME type from magic bytes
        if image_bytes[:4] == b'\x89PNG':
            mime_type = "image/png"
        elif image_bytes[:2] == b'\xff\xd8':
            mime_type = "image/jpeg"
        elif image_bytes[:4] == b'RIFF' and image_bytes[8:12] == b'WEBP':
            mime_type = "image/webp"
        elif image_bytes[:3] == b'GIF':
            mime_type = "image/gif"
        else:
            mime_type = "image/jpeg"
        
        llm = get_reasoning_llm()

        message = HumanMessage(
            content=[
                {"type": "text", "text": (
                    "You are looking at a blood group card / antigen report. "
                    "Extract the antigen panel results. For each antigen below, state if it is Positive or Negative. "
                    "Antigens to look for: D (Rh), C (Rh), c (Rh), E (Rh), e (Rh), K (Kell), Fy-a (Duffy), Fy-b (Duffy), Jk-a (Kidd), Jk-b (Kidd), M (MNS), N (MNS), S (MNS). "
                    "Reply ONLY with a JSON object like: "
                    '{"D":"Positive","C":"Negative","c":"Positive","E":"Negative","e":"Positive",'
                    '"K":"Negative","Fya":"Positive","Fyb":"Negative","Jka":"Positive","Jkb":"Negative",'
                    '"M":"Positive","N":"Negative","S":"Negative"} '
                    "Only include antigens you can clearly see on the card. If you cannot find any antigen data, reply with: {}"
                )},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{mime_type};base64,{base64_data}"},
                },
            ]
        )

        resp = await llm.ainvoke([message])
        res_text = resp.content.strip() if isinstance(resp.content, str) else str(resp.content).strip()
        logger.info(f"Vision LLM antigen raw output: {res_text[:300]}")

        # Parse JSON from response
        json_match = re.search(r'\{[^}]+\}', res_text)
        if json_match:
            data = _json.loads(json_match.group(0))
            return data
    except Exception as e:
        logger.error(f"Vision LLM antigen extraction failed: {e}", exc_info=True)
    return {}


def parse_antigens_from_text(raw_text: str) -> dict:
    """
    Parse antigen panel from OCR raw text.
    Returns dict with keys: kell_negative, duffy_negative, kidd_negative,
    rh_e_negative, rh_c_negative, mns_negative, and raw antigen_panel dict.

    Typical card text patterns:
      "D (Rh) Positive"
      "C (Rh) Negative"
      "K (Kell) Negative"
      "Fy-a (Duffy) Positive"
      "Jk-a (Kidd) Negative"
    """
    antigen_panel = {}  # raw: {"D": "Positive", "C": "Negative", ...}
    
    # Patterns for antigen extraction from card text
    # Format: "ANTIGEN_NAME ... Positive/Negative"
    antigen_patterns = [
        # Rh system
        (r'D\s*\(?Rh\)?\s*(Positive|Negative|Pos|Neg)', 'D'),
        (r'C\s*\(?Rh\)?\s*(Positive|Negative|Pos|Neg)', 'C'),
        (r'\bc\s*\(?Rh\)?\s*(Positive|Negative|Pos|Neg)', 'c'),
        (r'E\s*\(?Rh\)?\s*(Positive|Negative|Pos|Neg)', 'E'),
        (r'\be\s*\(?Rh\)?\s*(Positive|Negative|Pos|Neg)', 'e'),
        (r'Cw\s*\(?Rh\)?\s*(Positive|Negative|Pos|Neg)', 'Cw'),
        # Kell
        (r'K\s*\(?Kell\)?\s*(Positive|Negative|Pos|Neg)', 'K'),
        (r'Kell\s*(Positive|Negative|Pos|Neg)', 'K'),
        # Duffy
        (r'Fy[\-\s]?a\s*\(?Duffy\)?\s*(Positive|Negative|Pos|Neg)', 'Fya'),
        (r'Fy[\-\s]?b\s*\(?Duffy\)?\s*(Positive|Negative|Pos|Neg)', 'Fyb'),
        (r'Duffy[\-\s]?a\s*(Positive|Negative|Pos|Neg)', 'Fya'),
        (r'Duffy[\-\s]?b\s*(Positive|Negative|Pos|Neg)', 'Fyb'),
        # Kidd
        (r'Jk[\-\s]?a\s*\(?Kidd\)?\s*(Positive|Negative|Pos|Neg)', 'Jka'),
        (r'Jk[\-\s]?b\s*\(?Kidd\)?\s*(Positive|Negative|Pos|Neg)', 'Jkb'),
        (r'Kidd[\-\s]?a\s*(Positive|Negative|Pos|Neg)', 'Jka'),
        (r'Kidd[\-\s]?b\s*(Positive|Negative|Pos|Neg)', 'Jkb'),
        # MNS
        (r'\bM\s*\(?MNS\)?\s*(Positive|Negative|Pos|Neg)', 'M'),
        (r'\bN\s*\(?MNS\)?\s*(Positive|Negative|Pos|Neg)', 'N'),
        (r'\bS\s*\(?MNS\)?\s*(Positive|Negative|Pos|Neg)', 'S'),
    ]

    for pattern, antigen_key in antigen_patterns:
        match = re.search(pattern, raw_text, re.IGNORECASE)
        if match:
            result_str = match.group(1).strip().upper()
            is_positive = result_str.startswith("POS")
            antigen_panel[antigen_key] = "Positive" if is_positive else "Negative"

    # Map to database boolean columns (True = antigen is NEGATIVE, matching schema convention)
    db_flags = {}
    
    # Kell negative
    if 'K' in antigen_panel:
        db_flags['kell_negative'] = (antigen_panel['K'] == 'Negative')
    
    # Duffy negative (both Fya and Fyb negative = duffy null/negative phenotype)
    if 'Fya' in antigen_panel or 'Fyb' in antigen_panel:
        fya_neg = antigen_panel.get('Fya') == 'Negative'
        fyb_neg = antigen_panel.get('Fyb') == 'Negative'
        db_flags['duffy_negative'] = fya_neg and fyb_neg
    
    # Kidd negative (both Jka and Jkb negative)
    if 'Jka' in antigen_panel or 'Jkb' in antigen_panel:
        jka_neg = antigen_panel.get('Jka') == 'Negative'
        jkb_neg = antigen_panel.get('Jkb') == 'Negative'
        db_flags['kidd_negative'] = jka_neg and jkb_neg
    
    # Rh E negative
    if 'E' in antigen_panel:
        db_flags['rh_e_negative'] = (antigen_panel['E'] == 'Negative')
    
    # Rh c negative (little c)
    if 'c' in antigen_panel:
        db_flags['rh_c_negative'] = (antigen_panel['c'] == 'Negative')
    
    # MNS negative
    if 'M' in antigen_panel or 'N' in antigen_panel or 'S' in antigen_panel:
        m_neg = antigen_panel.get('M') == 'Negative'
        s_neg = antigen_panel.get('S') == 'Negative'
        db_flags['mns_negative'] = m_neg and s_neg

    return {
        "antigen_panel": antigen_panel,
        "db_flags": db_flags
    }

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

    # ── Antigen Panel Extraction ──────────────────────────────────────────────
    antigen_result = parse_antigens_from_text(raw_text) if raw_text else {"antigen_panel": {}, "db_flags": {}}
    
    # If Textract didn't find antigens, try Vision LLM fallback
    if not antigen_result["antigen_panel"]:
        vision_antigens = await call_vision_llm_antigens(image_bytes)
        if vision_antigens:
            # Convert vision LLM response to our format
            antigen_panel = {}
            for key, val in vision_antigens.items():
                if isinstance(val, str) and val.upper() in ("POSITIVE", "NEGATIVE", "POS", "NEG"):
                    antigen_panel[key] = "Positive" if val.upper().startswith("POS") else "Negative"
            
            if antigen_panel:
                antigen_result["antigen_panel"] = antigen_panel
                # Recalculate db_flags from vision data
                db_flags = {}
                if 'K' in antigen_panel:
                    db_flags['kell_negative'] = (antigen_panel['K'] == 'Negative')
                if 'Fya' in antigen_panel or 'Fyb' in antigen_panel:
                    db_flags['duffy_negative'] = antigen_panel.get('Fya') == 'Negative' and antigen_panel.get('Fyb') == 'Negative'
                if 'Jka' in antigen_panel or 'Jkb' in antigen_panel:
                    db_flags['kidd_negative'] = antigen_panel.get('Jka') == 'Negative' and antigen_panel.get('Jkb') == 'Negative'
                if 'E' in antigen_panel:
                    db_flags['rh_e_negative'] = (antigen_panel['E'] == 'Negative')
                if 'c' in antigen_panel:
                    db_flags['rh_c_negative'] = (antigen_panel['c'] == 'Negative')
                if 'M' in antigen_panel or 'S' in antigen_panel:
                    db_flags['mns_negative'] = antigen_panel.get('M') == 'Negative' and antigen_panel.get('S') == 'Negative'
                antigen_result["db_flags"] = db_flags

    logger.info(f"Antigen extraction: panel={antigen_result['antigen_panel']}, db_flags={antigen_result['db_flags']}")

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
            
            # Store antigen flags if detected
            if antigen_result["db_flags"]:
                update_payload.update(antigen_result["db_flags"])
                
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
        "raw_text": raw_text,
        "antigen_panel": antigen_result["antigen_panel"],
        "antigen_flags": antigen_result["db_flags"]
    }
