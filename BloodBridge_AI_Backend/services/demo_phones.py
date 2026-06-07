"""
Demo / E2E configuration: exactly 3 real phone numbers for hackathon testing.

E2E test actors (REQ-TEST-B001):
  7075899966 → Sheik Bhai  (D-72485, O+)
  9642273274 → Arjun Singh (D-33512, A+)
  6305589656 → Ravi Kumar  (D-50013, B+)
  Patient: P-10026 (B- @ Apollo Banjara Hills)
"""
from core.config import get_settings

# E.164 format (+91...)
E2E_PHONE_SHEIK = "+917075899966"
E2E_PHONE_ARJUN = "+919642273274"
E2E_PHONE_RAVI = "+916305589656"
E2E_TEST_PHONES = [E2E_PHONE_SHEIK, E2E_PHONE_ARJUN, E2E_PHONE_RAVI]

DEMO_PATIENT_PHONE = E2E_PHONE_SHEIK
DEMO_DONOR_PHONES = [E2E_PHONE_ARJUN, E2E_PHONE_RAVI]
DEMO_ALL_PHONES = list(E2E_TEST_PHONES)

DEMO_PATIENT_ID = "P-THREE-001"
DEMO_DONOR_IDS = ["D-THREE-001", "D-THREE-002"]

# Full E2E test plan donor IDs (dashboard + REQ-TEST-B001 chain)
E2E_DONOR_IDS = ["D-72485", "D-33512", "D-50013"]
E2E_PATIENT_ID = "P-10026"
E2E_REQUEST_ID = "REQ-TEST-B001"

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
    """In development, Bolna may only call the 3 E2E test phones (safety guard)."""
    settings = get_settings()
    if settings.APP_ENV == "development" and not getattr(settings, "BOLNA_ALLOW_ANY_PHONE", False):
        allowed = {normalize_phone(p) for p in E2E_TEST_PHONES}
        return normalize_phone(phone) in allowed
    if is_demo_mode():
        return normalize_phone(phone) in {normalize_phone(p) for p in DEMO_ALL_PHONES}
    return True


def is_demo_donor_phone(phone: str) -> bool:
    if not phone:
        return False
    return normalize_phone(phone) in {normalize_phone(p) for p in DEMO_DONOR_PHONES}


def is_demo_donor_record(donor: dict) -> bool:
    if donor.get("donor_id") in DEMO_DONOR_IDS + E2E_DONOR_IDS:
        return True
    phone = donor.get("phone")
    if phone and normalize_phone(phone) in {normalize_phone(p) for p in E2E_TEST_PHONES}:
        return True
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
