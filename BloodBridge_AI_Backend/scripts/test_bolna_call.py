#!/usr/bin/env python3
"""Place test Bolna calls to all 3 E2E donor phones."""
import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env", override=True)

from core.config import get_settings
from services.voice_service import make_bolna_call

DONORS = [
    {"donor_id": "D-72485", "name": "Sheik Bhai", "phone": "+917075899966", "preferred_language": "en"},
    {"donor_id": "D-33512", "name": "Arjun Singh", "phone": "+919642273274", "preferred_language": "en"},
    {"donor_id": "D-50013", "name": "Ravi Kumar", "phone": "+916305589656", "preferred_language": "hi"},
]

EMERGENCY = {
    "blood_type": "B-",
    "hospital_name": "Apollo Banjara Hills",
    "city": "Hyderabad",
    "urgency_level": "CRITICAL",
}


async def main():
    target = sys.argv[1] if len(sys.argv) > 1 else "all"
    s = get_settings()
    print(f"DEMO_MOCK_MODE={s.DEMO_MOCK_MODE}  BOLNA configured={bool(s.BOLNA_API_KEY)}")

    donors = DONORS
    if target != "all":
        donors = [d for d in DONORS if d["donor_id"] == target or d["phone"].endswith(target)]
        if not donors:
            print(f"Unknown donor: {target}. Use D-50013, D-72485, D-33512, or all")
            sys.exit(1)

    failed = False
    for donor in donors:
        print(f"\nCalling {donor['name']} ({donor['phone']}) ...")
        result = await make_bolna_call(
            phone=donor["phone"],
            donor=donor,
            emergency=EMERGENCY,
            request_id="REQ-TEST-B001",
        )
        print("  Result:", result)
        if result.get("status") != "INITIATED":
            failed = True

    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    asyncio.run(main())
