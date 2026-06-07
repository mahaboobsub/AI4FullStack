"""
Blood card OCR for BloodBridge AI.

Pipeline:
  1. AWS Textract — raw text + form fields (fast, cheap)
  2. AWS Bedrock Claude Sonnet (vision) — blood group, name, full antigen panel (primary)
  3. Regex parse Textract text — fallback when Bedrock vision unavailable
"""
import re
import json
import base64
import logging
from typing import Optional

import boto3
from langchain_core.messages import HumanMessage

from core.config import get_settings

logger = logging.getLogger(__name__)

KNOWN_BLOOD_TYPES = {"A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"}

ANTIGEN_KEYS = ("D", "C", "c", "E", "e", "K", "Fya", "Fyb", "Jka", "Jkb", "M", "N", "S")

BEDROCK_CARD_PROMPT = """You are a transfusion-medicine OCR expert analyzing a blood group / antigen card photo.

Extract every field you can read. Return ONLY valid JSON (no markdown fences, no commentary):
{
  "blood_group": "O+",
  "donor_name": "Full Name",
  "antigen_panel": {
    "D": "Positive",
    "K": "Negative"
  },
  "confidence": 0.95
}

Rules:
- blood_group: exactly one of A+, A-, B+, B-, AB+, AB-, O+, O- (or null if not visible)
- donor_name: full name on card (or null)
- antigen_panel: only include antigens clearly printed on the card
  Keys to use: D, C, c, E, e, K, Fya, Fyb, Jka, Jkb, M, N, S
  Each value must be exactly "Positive" or "Negative"
- D = Rh(D), K = Kell, Fya/Fyb = Duffy, Jka/Jkb = Kidd, M/N/S = MNS
- Cards may be in English, Hindi, or Telugu — still extract antigens
- confidence: 0.0-1.0 for overall extraction quality
- If no antigen data visible, return "antigen_panel": {}
- If image is not a blood card, return {"blood_group": null, "donor_name": null, "antigen_panel": {}, "confidence": 0}
"""


def _detect_image_mime(image_bytes: bytes) -> str:
    if image_bytes[:4] == b"\x89PNG":
        return "image/png"
    if image_bytes[:2] == b"\xff\xd8":
        return "image/jpeg"
    if image_bytes[:4] == b"RIFF" and image_bytes[8:12] == b"WEBP":
        return "image/webp"
    if image_bytes[:3] == b"GIF":
        return "image/gif"
    return "image/jpeg"


def _parse_json_from_llm(text: str) -> dict:
    """Extract JSON object from model response."""
    text = (text or "").strip()
    if not text:
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Strip markdown code fences
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fenced:
        try:
            return json.loads(fenced.group(1))
        except json.JSONDecodeError:
            pass
    brace = re.search(r"\{.*\}", text, re.DOTALL)
    if brace:
        try:
            return json.loads(brace.group(0))
        except json.JSONDecodeError:
            pass
    return {}


def _normalize_blood_group(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    cleaned = str(value).strip().upper()
    cleaned = (
        cleaned.replace("POSITIVE", "+")
        .replace("POS", "+")
        .replace("NEGATIVE", "-")
        .replace("NEG", "-")
        .replace(" ", "")
    )
    if cleaned in KNOWN_BLOOD_TYPES:
        return cleaned
    # (?!\w) not trailing \b — "+" is non-word so \b after [+-] fails on "O+"
    match = re.search(r"(AB|A|B|O)[+-](?!\w)", cleaned)
    if match:
        bg = match.group(0)
        return bg if bg in KNOWN_BLOOD_TYPES else None
    return None


def _normalize_antigen_panel(raw_panel: dict) -> dict:
    """Normalize antigen panel to Positive/Negative values."""
    panel = {}
    if not isinstance(raw_panel, dict):
        return panel
    for key, val in raw_panel.items():
        if not isinstance(val, str):
            continue
        norm_key = str(key).strip()
        upper = val.strip().upper()
        if upper.startswith("POS"):
            panel[norm_key] = "Positive"
        elif upper.startswith("NEG"):
            panel[norm_key] = "Negative"
    return panel


def antigen_panel_to_db_flags(antigen_panel: dict) -> dict:
    """Map antigen panel to Supabase boolean columns (True = antigen-negative phenotype)."""
    db_flags = {}
    if "K" in antigen_panel:
        db_flags["kell_negative"] = antigen_panel["K"] == "Negative"
    if "Fya" in antigen_panel or "Fyb" in antigen_panel:
        db_flags["duffy_negative"] = (
            antigen_panel.get("Fya") == "Negative" and antigen_panel.get("Fyb") == "Negative"
        )
    if "Jka" in antigen_panel or "Jkb" in antigen_panel:
        db_flags["kidd_negative"] = (
            antigen_panel.get("Jka") == "Negative" and antigen_panel.get("Jkb") == "Negative"
        )
    if "E" in antigen_panel:
        db_flags["rh_e_negative"] = antigen_panel["E"] == "Negative"
    if "c" in antigen_panel:
        db_flags["rh_c_negative"] = antigen_panel["c"] == "Negative"
    if "M" in antigen_panel or "N" in antigen_panel or "S" in antigen_panel:
        db_flags["mns_negative"] = (
            antigen_panel.get("M") == "Negative" and antigen_panel.get("S") == "Negative"
        )
    return db_flags


async def call_bedrock_vision_card_extraction(image_bytes: bytes) -> dict:
    """
    Primary OCR: AWS Bedrock Claude Sonnet vision.
    Returns {blood_group, donor_name, antigen_panel, confidence, model}.
    """
    settings = get_settings()
    if not settings.AWS_ACCESS_KEY_ID or not settings.AWS_SECRET_ACCESS_KEY:
        logger.warning("Bedrock vision skipped — AWS credentials not configured")
        return {}

    try:
        from core.llm_provider import get_vision_llm

        mime = _detect_image_mime(image_bytes)
        b64 = base64.b64encode(image_bytes).decode("utf-8")
        llm = get_vision_llm()

        message = HumanMessage(
            content=[
                {"type": "text", "text": BEDROCK_CARD_PROMPT},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{mime};base64,{b64}"},
                },
            ]
        )

        resp = await llm.ainvoke([message])
        raw = resp.content.strip() if isinstance(resp.content, str) else str(resp.content).strip()
        logger.info(f"Bedrock vision OCR raw: {raw[:400]}")

        data = _parse_json_from_llm(raw)
        raw_bg = data.get("blood_group")
        blood_group = _normalize_blood_group(raw_bg)
        if not blood_group and isinstance(raw_bg, str) and raw_bg.strip().upper() in KNOWN_BLOOD_TYPES:
            blood_group = raw_bg.strip().upper()
        panel = _normalize_antigen_panel(data.get("antigen_panel") or {})

        return {
            "blood_group": blood_group,
            "donor_name": (data.get("donor_name") or data.get("name") or "").strip() or None,
            "antigen_panel": panel,
            "confidence": float(data.get("confidence") or 0.0),
            "model": "bedrock_vision",
        }
    except Exception as e:
        logger.error(f"Bedrock vision card extraction failed: {e}", exc_info=True)
        return {}


def _textract_extract(image_bytes: bytes) -> dict:
    """AWS Textract FORMS analysis — returns raw_text, blood_group, donor_name."""
    settings = get_settings()
    raw_text = ""
    blood_group = None
    donor_name = None

    client = boto3.client(
        "textract",
        region_name=settings.AWS_REGION,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    )

    response = client.analyze_document(
        Document={"Bytes": image_bytes},
        FeatureTypes=["FORMS"],
    )

    blocks = response.get("Blocks", [])
    lines = []
    key_map = {}
    value_map = {}
    block_map = {}

    for block in blocks:
        block_map[block["Id"]] = block
        if block["BlockType"] == "LINE":
            lines.append(block["Text"])
        elif block["BlockType"] == "KEY_VALUE_SET":
            if "KEY" in block.get("EntityTypes", []):
                key_map[block["Id"]] = block
            else:
                value_map[block["Id"]] = block

    raw_text = " ".join(lines)

    def get_text(node):
        text = ""
        if "Relationships" in node:
            for relationship in node["Relationships"]:
                if relationship["Type"] == "CHILD":
                    for child_id in relationship["Ids"]:
                        child = block_map.get(child_id)
                        if child and child["BlockType"] == "WORD":
                            text += child["Text"] + " "
        return text.strip()

    for _block_id, key_block in key_map.items():
        key_text = get_text(key_block).lower()
        val_text = ""
        if "Relationships" in key_block:
            for relationship in key_block["Relationships"]:
                if relationship["Type"] == "VALUE":
                    for val_id in relationship["Ids"]:
                        val_block = value_map.get(val_id)
                        if val_block:
                            val_text = get_text(val_block)

        if "name" in key_text and not donor_name:
            donor_name = val_text
        if ("blood" in key_text or "group" in key_text) and not blood_group:
            blood_group = _normalize_blood_group(val_text)

    if not blood_group:
        patterns = [
            r"\b(AB|A|B|O)[+-](?!\w)",
            r"\b(AB|A|B|O)\s*(positive|negative|pos|neg)\b",
            r"Blood\s*Grp\s*[:\-]?\s*(AB|A|B|O)[+-]",
            r"Blood\s*Group\s*[:\-]?\s*(AB|A|B|O)[+-]",
        ]
        for pattern in patterns:
            match = re.search(pattern, raw_text, re.IGNORECASE)
            if match:
                bg_letter = match.group(1).upper()
                sign = "+" if "+" in match.group(0) or "pos" in match.group(0).lower() else "-"
                blood_group = f"{bg_letter}{sign}"
                if blood_group in KNOWN_BLOOD_TYPES:
                    break
                blood_group = None

    return {
        "raw_text": raw_text,
        "blood_group": blood_group if blood_group in KNOWN_BLOOD_TYPES else None,
        "donor_name": donor_name,
    }


def parse_antigens_from_text(raw_text: str) -> dict:
    """Regex fallback: parse antigen panel from Textract raw text."""
    antigen_panel = {}
    antigen_patterns = [
        (r"D\s*\(?Rh\)?\s*(Positive|Negative|Pos|Neg)", "D"),
        (r"C\s*\(?Rh\)?\s*(Positive|Negative|Pos|Neg)", "C"),
        (r"\bc\s*\(?Rh\)?\s*(Positive|Negative|Pos|Neg)", "c"),
        (r"E\s*\(?Rh\)?\s*(Positive|Negative|Pos|Neg)", "E"),
        (r"\be\s*\(?Rh\)?\s*(Positive|Negative|Pos|Neg)", "e"),
        (r"K\s*\(?Kell\)?\s*(Positive|Negative|Pos|Neg)", "K"),
        (r"Kell\s*(Positive|Negative|Pos|Neg)", "K"),
        (r"Fy[\-\s]?a\s*\(?Duffy\)?\s*(Positive|Negative|Pos|Neg)", "Fya"),
        (r"Fy[\-\s]?b\s*\(?Duffy\)?\s*(Positive|Negative|Pos|Neg)", "Fyb"),
        (r"Jk[\-\s]?a\s*\(?Kidd\)?\s*(Positive|Negative|Pos|Neg)", "Jka"),
        (r"Jk[\-\s]?b\s*\(?Kidd\)?\s*(Positive|Negative|Pos|Neg)", "Jkb"),
        (r"\bM\s*\(?MNS\)?\s*(Positive|Negative|Pos|Neg)", "M"),
        (r"\bN\s*\(?MNS\)?\s*(Positive|Negative|Pos|Neg)", "N"),
        (r"\bS\s*\(?MNS\)?\s*(Positive|Negative|Pos|Neg)", "S"),
    ]

    for pattern, antigen_key in antigen_patterns:
        match = re.search(pattern, raw_text, re.IGNORECASE)
        if match:
            result_str = match.group(1).strip().upper()
            is_positive = result_str.startswith("POS")
            antigen_panel[antigen_key] = "Positive" if is_positive else "Negative"

    return {
        "antigen_panel": antigen_panel,
        "db_flags": antigen_panel_to_db_flags(antigen_panel),
    }


async def extract_blood_type_from_image(image_bytes: bytes, donor_id: str | None = None) -> dict:
    """
    Full blood card extraction for Telegram photo upload and donor portal.

    Priority:
      - Blood group + antigens: Bedrock Claude Sonnet vision (primary)
      - Raw text + name fallback: AWS Textract
      - Antigen regex fallback: Textract text parsing
    """
    raw_text = ""
    blood_group = None
    donor_name = None
    antigen_panel = {}
    db_flags = {}
    ocr_source = []

    # 1. Textract — raw OCR text
    try:
        textract = _textract_extract(image_bytes)
        raw_text = textract.get("raw_text") or ""
        blood_group = textract.get("blood_group")
        donor_name = textract.get("donor_name")
        if raw_text:
            ocr_source.append("textract")
        logger.info(
            f"Textract: blood_group={blood_group}, name={donor_name}, "
            f"raw_text_len={len(raw_text)}, sample='{raw_text[:200]}'"
        )
    except Exception as e:
        logger.warning(f"AWS Textract failed: {e}")

    # 2. Bedrock Claude Sonnet vision — primary for blood group + antigen panel
    vision = await call_bedrock_vision_card_extraction(image_bytes)
    if vision:
        ocr_source.append(vision.get("model", "bedrock_vision"))
        if vision.get("blood_group"):
            blood_group = vision["blood_group"]
        if vision.get("donor_name") and not donor_name:
            donor_name = vision["donor_name"]
        if vision.get("antigen_panel"):
            antigen_panel = vision["antigen_panel"]
            db_flags = antigen_panel_to_db_flags(antigen_panel)
        logger.info(
            f"Bedrock vision: blood_group={blood_group}, antigens={list(antigen_panel.keys())}, "
            f"confidence={vision.get('confidence', 0)}"
        )

    # 3. Textract text regex fallback for antigens if Bedrock found none
    if not antigen_panel and raw_text:
        textract_antigens = parse_antigens_from_text(raw_text)
        if textract_antigens["antigen_panel"]:
            antigen_panel = textract_antigens["antigen_panel"]
            db_flags = textract_antigens["db_flags"]
            ocr_source.append("textract_regex")
            logger.info(f"Textract regex antigens: {antigen_panel}")

    result = {
        "blood_group": blood_group,
        "name": donor_name,
        "raw_text": raw_text,
        "antigen_panel": antigen_panel,
        "antigen_flags": db_flags,
        "ocr_source": ocr_source,
        "vision_confidence": vision.get("confidence", 0.0) if vision else 0.0,
    }

    if donor_id and (blood_group or antigen_panel):
        from services.ocr_persist import persist_ocr_results
        await persist_ocr_results(donor_id, result)

    return result
