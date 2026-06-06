"""
Demo configuration: exactly 3 real phone numbers for hackathon / pilot testing.
  - 1 patient (7075899966) triggers emergencies via Telegram
  - 2 donors (9642273274, 6305589656) receive alerts + Bolna voice calls
"""
from core.config import get_settings

# E.164 format (+91...)
DEMO_PATIENT_PHONE = "+917075899966"
DEMO_DONOR_PHONES = ["+919642273274", "+916305589656"]
DEMO_ALL_PHONES = [DEMO_PATIENT_PHONE] + DEMO_DONOR_PHONES

DEMO_PATIENT_ID = "P-THREE-001"
DEMO_DONOR_IDS = ["D-THREE-001", "D-THREE-002"]

# Shared matching profile — all B+ Hyderabad, no rare-antigen constraints
DEMO_BLOOD_TYPE = "B+"
DEMO_CITY = "Hyderabad"
DEMO_HOSPITAL = "KIMS Secunderabad"
DEMO_LAT = 17.4480
DEMO_LNG = 78.4982


def normalize_phone(phone: str) -> str:
    """Normalize Indian mobile to E.164 (+91XXXXXXXXXX)."""
    import re
    digits = re.sub(r"\D", "", phone or "")
    if len(digits) == 10:
        return f"+91{digits}"
    if len(digits) == 12 and digits.startswith("91"):
        return f"+{digits}"
    if digits.startswith("+"):
        return phone
    return f"+{digits}" if digits else ""


def is_demo_mode() -> bool:
    return get_settings().THREE_PHONE_DEMO_MODE


def is_allowed_voice_phone(phone: str) -> bool:
    """Bolna may only call the 3 demo numbers when demo mode is on."""
    if not is_demo_mode():
        return True
    return normalize_phone(phone) in {normalize_phone(p) for p in DEMO_ALL_PHONES}


def is_demo_donor_phone(phone: str) -> bool:
    if not phone:
        return False
    return normalize_phone(phone) in {normalize_phone(p) for p in DEMO_DONOR_PHONES}


def is_demo_donor_record(donor: dict) -> bool:
    if donor.get("donor_id") in DEMO_DONOR_IDS:
        return True
    phone = donor.get("phone")
    return is_demo_donor_phone(phone) if phone else False


def is_valid_telegram_chat_id(chat_id) -> bool:
    """True if chat_id looks like a real Telegram user (not a seed placeholder)."""
    if chat_id is None:
        return False
    s = str(chat_id).strip()
    if not s.isdigit():
        return False
    # Real user IDs are typically 8+ digits; seed placeholders use 100000xxx pattern
    if len(s) < 8:
        return False
    if s.startswith("1000000") and len(s) <= 9:
        return False
    return True
