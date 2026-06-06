"""
Seed exactly 3 real phone numbers for demo:
  Patient  7075899966  → P-THREE-001  (triggers emergency via Telegram)
  Donor 1  9642273274  → D-THREE-001  (gets alert + voice call)
  Donor 2  6305589656  → D-THREE-002  (gets alert + voice call)

All share blood type B+, city Hyderabad, compatible antigen profile.

Usage:
    python -m data.seed_three_phones

Set THREE_PHONE_DEMO_MODE=true in .env after seeding.
"""
import asyncio
from datetime import datetime, timezone

from services.demo_phones import (
    DEMO_PATIENT_PHONE,
    DEMO_DONOR_PHONES,
    DEMO_PATIENT_ID,
    DEMO_DONOR_IDS,
    DEMO_BLOOD_TYPE,
    DEMO_CITY,
    DEMO_HOSPITAL,
    DEMO_LAT,
    DEMO_LNG,
    normalize_phone,
)

DEMO_PATIENT = {
    "patient_id": DEMO_PATIENT_ID,
    "name": "Demo Patient",
    "phone": DEMO_PATIENT_PHONE,
    "age": 12,
    "blood_type": DEMO_BLOOD_TYPE,
    "hospital": DEMO_HOSPITAL,
    "ward": "Thalassemia Day Care",
    "city": DEMO_CITY,
    "lat": DEMO_LAT,
    "lng": DEMO_LNG,
    "hemoglobin": 8.0,
    "transfusion_count": 10,
    "status": "CRITICAL",
    "is_active": True,
    "antibody_kell": False,
    "antibody_duffy": False,
    "antibody_kidd": False,
    "kell_negative": False,
}

DEMO_DONORS = [
    {
        "donor_id": DEMO_DONOR_IDS[0],
        "name": "Demo Donor One",
        "phone": DEMO_DONOR_PHONES[0],
        "blood_type": DEMO_BLOOD_TYPE,
        "city": DEMO_CITY,
        "lat": DEMO_LAT + 0.002,
        "lng": DEMO_LNG + 0.002,
        "kell_negative": False,
        "duffy_negative": False,
        "kidd_negative": False,
        "donation_count": 5,
        "lives_saved": 5,
        "response_rate": 0.9,
        "churn_score": 0.15,
        "churn_risk": "LOW",
        "is_active": True,
        "consent_outreach": True,
        "consent_data_storage": True,
        "preferred_language": "en",
        "last_donation_date": None,
    },
    {
        "donor_id": DEMO_DONOR_IDS[1],
        "name": "Demo Donor Two",
        "phone": DEMO_DONOR_PHONES[1],
        "blood_type": DEMO_BLOOD_TYPE,
        "city": DEMO_CITY,
        "lat": DEMO_LAT - 0.001,
        "lng": DEMO_LNG - 0.001,
        "kell_negative": False,
        "duffy_negative": False,
        "kidd_negative": False,
        "donation_count": 3,
        "lives_saved": 3,
        "response_rate": 0.85,
        "churn_score": 0.2,
        "churn_risk": "LOW",
        "is_active": True,
        "consent_outreach": True,
        "consent_data_storage": True,
        "preferred_language": "hi",
        "last_donation_date": None,
    },
]


def _clear_telegram_conflict(supabase, chat_id: str, keep_donor_id: str):
    """Remove telegram_chat_id from other donors so it can be assigned to demo donor."""
    if not chat_id:
        return
    conflicts = supabase.table("donors").select("donor_id").eq("telegram_chat_id", str(chat_id)).execute()
    for row in conflicts.data or []:
        if row["donor_id"] != keep_donor_id:
            supabase.table("donors").update({"telegram_chat_id": None}).eq("donor_id", row["donor_id"]).execute()


def _find_telegram_chat_id(supabase, phone: str) -> str | None:
    """Reuse telegram_chat_id from any existing row with this phone."""
    norm = normalize_phone(phone)
    for table in ("donors", "patients"):
        try:
            res = supabase.table(table).select("telegram_chat_id").eq("phone", norm).execute()
            for row in res.data or []:
                if row.get("telegram_chat_id"):
                    return str(row["telegram_chat_id"])
            alt = norm.replace("+91", "")
            res2 = supabase.table(table).select("telegram_chat_id").like("phone", f"%{alt}").execute()
            for row in res2.data or []:
                if row.get("telegram_chat_id"):
                    return str(row["telegram_chat_id"])
        except Exception:
            pass
    return None


def _migrate_phone_record(supabase, phone: str, target_donor_id: str) -> str | None:
    """If a donor already exists with this phone, steal their telegram_chat_id and deactivate them."""
    norm = normalize_phone(phone)
    existing = supabase.table("donors").select("donor_id, telegram_chat_id").eq("phone", norm).execute()
    chat_id = None
    for row in existing.data or []:
        if row.get("telegram_chat_id"):
            chat_id = str(row["telegram_chat_id"])
        if row["donor_id"] != target_donor_id:
            supabase.table("donors").update({"is_active": False, "telegram_chat_id": None}).eq("donor_id", row["donor_id"]).execute()
    if not chat_id:
        chat_id = _find_telegram_chat_id(supabase, phone)
    if chat_id:
        _clear_telegram_conflict(supabase, chat_id, target_donor_id)
    return chat_id


async def seed_three_phones():
    from core.database import get_supabase_admin
    from services.consent_service import ConsentService

    supabase = get_supabase_admin()
    now = datetime.now(timezone.utc).isoformat()

    print("BloodBridge - 3-Phone Demo Seed")
    print("=" * 50)
    print(f"  Patient : {DEMO_PATIENT_PHONE} -> {DEMO_PATIENT_ID}")
    print(f"  Donor 1 : {DEMO_DONOR_PHONES[0]} -> {DEMO_DONOR_IDS[0]}")
    print(f"  Donor 2 : {DEMO_DONOR_PHONES[1]} -> {DEMO_DONOR_IDS[1]}")
    print(f"  Blood   : {DEMO_BLOOD_TYPE} | City: {DEMO_CITY}")
    print()

    # 1. Deactivate every other donor so matching only finds our 2
    print("  -> Deactivating non-demo donors...")
    all_donors = supabase.table("donors").select("donor_id").execute()
    deactivated = 0
    for row in all_donors.data or []:
        if row["donor_id"] not in DEMO_DONOR_IDS:
            supabase.table("donors").update({"is_active": False}).eq("donor_id", row["donor_id"]).execute()
            deactivated += 1
    print(f"  OK Deactivated {deactivated} other donors")

    # 2. Upsert patient
    print("  -> Seeding demo patient...")
    patient_chat = _find_telegram_chat_id(supabase, DEMO_PATIENT_PHONE)
    patient_row = {**DEMO_PATIENT}
    if patient_chat:
        patient_row["password"] = f"tg:{patient_chat}"
        print(f"  Linked patient Telegram chat_id: {patient_chat}")
    existing = supabase.table("patients").select("patient_id").eq("patient_id", DEMO_PATIENT_ID).execute()
    if existing.data:
        supabase.table("patients").update(patient_row).eq("patient_id", DEMO_PATIENT_ID).execute()
        print(f"  Updated {DEMO_PATIENT_ID}")
    else:
        supabase.table("patients").insert(patient_row).execute()
        print(f"  Created {DEMO_PATIENT_ID}")

    # patient_locations (if table exists)
    try:
        supabase.table("patient_locations").upsert({
            "patient_id": DEMO_PATIENT_ID,
            "label": "Hospital",
            "lat": DEMO_LAT,
            "lng": DEMO_LNG,
            "is_primary": True,
            "priority_order": 1,
        }).execute()
    except Exception:
        pass

    # 3. Upsert donors
    print("\n  -> Seeding 2 demo donors...")
    for donor in DEMO_DONORS:
        chat_id = _migrate_phone_record(supabase, donor["phone"], donor["donor_id"])
        row = {**donor, "consent_granted_at": now}
        if chat_id:
            row["telegram_chat_id"] = chat_id
            print(f"  {donor['donor_id']} linked to Telegram {chat_id}")
        existing = supabase.table("donors").select("donor_id").eq("donor_id", donor["donor_id"]).execute()
        if existing.data:
            supabase.table("donors").update(row).eq("donor_id", donor["donor_id"]).execute()
            print(f"  Updated {donor['donor_id']} ({donor['name']})")
        else:
            supabase.table("donors").insert(row).execute()
            print(f"  Created {donor['donor_id']} ({donor['name']})")

        supabase.table("donor_memory").upsert({
            "donor_id": donor["donor_id"],
            "preferred_language": donor.get("preferred_language", "en"),
            "badges": ["life_saver"],
            "streak_days": 30,
            "total_interactions": donor.get("donation_count", 0),
        }).execute()

        await ConsentService.grant_consent(
            donor["donor_id"],
            ["data_storage", "outreach_telegram", "outreach_voice"],
            channel="seed_three_phones",
            language=donor.get("preferred_language", "en"),
        )
        donor["_telegram_chat_id"] = chat_id  # for Neo4j seed below

    # 4. Neo4j graph
    print("\n  -> Seeding Neo4j compatibility edges...")
    try:
        from core.neo4j_client import get_driver
        driver = get_driver()
        if driver:
            async with driver.session() as session:
                await session.run(
                    "MERGE (p:Patient {patient_id: $pid}) "
                    "SET p.name = $name, p.blood_type = $bt, p.city = $city, "
                    "p.lat = $lat, p.lng = $lng, p.kell_negative = false, "
                    "p.antibody_kell = false, p.antibody_duffy = false, p.antibody_kidd = false",
                    pid=DEMO_PATIENT_ID,
                    name=DEMO_PATIENT["name"],
                    bt=DEMO_BLOOD_TYPE,
                    city=DEMO_CITY,
                    lat=DEMO_LAT,
                    lng=DEMO_LNG,
                )
                for donor in DEMO_DONORS:
                    await session.run(
                        "MERGE (d:Donor {donor_id: $did}) "
                        "SET d.name = $name, d.blood_type = $bt, d.city = $city, "
                        "d.lat = $lat, d.lng = $lng, d.is_active = true, "
                        "d.kell_negative = false, d.phone = $phone, "
                        "d.telegram_chat_id = $tg, d.preferred_language = $lang, "
                        "d.churn_score = $churn",
                        did=donor["donor_id"],
                        name=donor["name"],
                        bt=donor["blood_type"],
                        city=donor["city"],
                        lat=donor["lat"],
                        lng=donor["lng"],
                        phone=donor["phone"],
                        tg=donor.get("_telegram_chat_id"),
                        lang=donor.get("preferred_language", "en"),
                        churn=donor.get("churn_score", 0.2),
                    )
                    await session.run(
                        "MATCH (d:Donor {donor_id: $did}), (p:Patient {patient_id: $pid}) "
                        "MERGE (d)-[r:COMPATIBLE_WITH]->(p) "
                        "SET r.antigen_score = 0.95, r.kell_safe = true, "
                        "r.duffy_safe = true, r.kidd_safe = true, r.last_computed = datetime()",
                        did=donor["donor_id"],
                        pid=DEMO_PATIENT_ID,
                    )
            print("  OK Neo4j patient + 2 donors + COMPATIBLE_WITH edges")
        else:
            print("  WARN Neo4j not available - matching uses Supabase geo engine")
    except Exception as e:
        print(f"  WARN Neo4j seed skipped: {e}")

    print("\n" + "=" * 50)
    print("OK 3-phone demo seed complete!\n")
    print("Next steps:")
    print("  1. Set THREE_PHONE_DEMO_MODE=true in .env")
    print("  2. Restart backend")
    print("  3. Patient (7075899966) sends in Telegram:")
    print(f"     Emergency {DEMO_BLOOD_TYPE} blood needed at {DEMO_HOSPITAL} {DEMO_CITY}")
    print("     OR: /emergency B+ P-THREE-001 KIMS Secunderabad  (staff)")
    print("  4. Donors 9642273274 & 6305589656 get Telegram alerts, then Bolna calls if no reply")
    print(f"  5. Track: /status {DEMO_PATIENT_ID}")


if __name__ == "__main__":
    asyncio.run(seed_three_phones())
