"""
Demo / E2E configuration: 4 real phone numbers for hackathon testing.

Phone assignment:
  7075899966 → Donor 1  (D-THREE-001, B+, Kell-negative)
  9642273274 → Donor 2  (D-THREE-002, O+, universal donor)
  6305589656 → Patient  (P-THREE-001, B+, antibody_kell=True, needs Kell-neg blood)
  9494421169 → Live registration demo only (not pre-seeded; register + delete during judges demo)

Bot: @ummedrakho_bot
City: Hyderabad (KIMS Secunderabad)
"""
from core.config import get_settings

# E.164 format (+91...)
E2E_PHONE_DONOR1 = "+917075899966"   # Phone 1 → Donor 1 (B+)
E2E_PHONE_DONOR2 = "+919642273274"   # Phone 2 → Donor 2 (O+)
E2E_PHONE_PATIENT = "+916305589656"  # Phone 3 → Patient
E2E_PHONE_REGISTRATION = "+919494421169"  # Phone 4 → live Telegram register/delete demo

E2E_TEST_PHONES = [E2E_PHONE_DONOR1, E2E_PHONE_DONOR2, E2E_PHONE_PATIENT]
DEMO_REGISTRATION_PHONES = [E2E_PHONE_REGISTRATION]
DEMO_ALLOWED_PHONES = E2E_TEST_PHONES + DEMO_REGISTRATION_PHONES

DEMO_PATIENT_PHONE = E2E_PHONE_PATIENT
DEMO_DONOR_PHONES = [E2E_PHONE_DONOR1, E2E_PHONE_DONOR2]
DEMO_ALL_PHONES = list(E2E_TEST_PHONES)

DEMO_PATIENT_ID = "P-THREE-001"
DEMO_DONOR_IDS = ["D-THREE-001", "D-THREE-002"]

# Legacy E2E IDs (kept for backward compat)
E2E_DONOR_IDS = ["D-THREE-001", "D-THREE-002"]
E2E_PATIENT_ID = "P-THREE-001"
E2E_REQUEST_ID = "REQ-TEST-B001"

# Patient is B+, needs Kell-negative donors
# Donor 1: B+, Kell-negative (perfect match for Kell-sensitized patient)
# Donor 2: O+, Kell-negative (universal donor, also matches)
DEMO_BLOOD_TYPE = "B+"
DEMO_CITY = "Hyderabad"
DEMO_HOSPITAL = "KIMS Secunderabad"
DEMO_LAT = 17.4480
DEMO_LNG = 78.4982

TELEGRAM_BOT_USERNAME = "ummedrakho_bot"


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
    if phone and normalize_phone(phone) in {normalize_phone(p) for p in DEMO_DONOR_PHONES}:
        return True
    return is_demo_donor_phone(phone) if phone else False


def is_valid_telegram_chat_id(chat_id) -> bool:
    """True if chat_id looks like a real Telegram user (not a seed placeholder)."""
    if chat_id is None:
        return False
    s = str(chat_id).strip()
    if not s.isdigit():
        return False
    if len(s) < 8:
        return False
    if s.startswith("1000000") and len(s) <= 9:
        return False
    return True
