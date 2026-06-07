"""
Seed the 3-phone E2E test actors from the test plan:

  7075899966 → Sheik Bhai  (D-72485, O+) — first in chain (ALERTED)
  9642273274 → Arjun Singh (D-33512, A+) — pending
  6305589656 → Ravi Kumar  (D-50013, B+) — pending

Patient: P-10026 (B- @ Apollo Banjara Hills)
Active request: REQ-TEST-B001

Usage:
    python -m data.seed_e2e_three_phones

Set THREE_PHONE_DEMO_MODE=false in .env (matching uses full donor pool + E2E IDs).
"""
import asyncio
from datetime import datetime, timezone

from core.database import get_supabase_admin
from core.time_utils import utc_now_iso
from services.consent_service import ConsentService
from services.demo_phones import (
    E2E_PHONE_SHEIK,
    E2E_PHONE_ARJUN,
    E2E_PHONE_RAVI,
    E2E_DONOR_IDS,
    E2E_PATIENT_ID,
    E2E_REQUEST_ID,
    normalize_phone,
    is_valid_telegram_chat_id,
)

# Legacy demo IDs that share the same phones — must be deactivated for E2E
LEGACY_DEMO_DONOR_IDS = ["D-THREE-001", "D-THREE-002"]

APOLLO_LAT, APOLLO_LNG = 17.4126, 78.4482

E2E_PATIENT = {
    "patient_id": E2E_PATIENT_ID,
    "name": "E2E Thalassemia Patient",
    "phone": E2E_PHONE_SHEIK,
    "age": 14,
    "blood_type": "B-",
    "hospital": "Apollo Banjara Hills",
    "ward": "Thalassemia Day Care",
    "city": "Hyderabad",
    "lat": APOLLO_LAT,
    "lng": APOLLO_LNG,
    "hemoglobin": 7.2,
    "transfusion_count": 24,
    "status": "CRITICAL",
    "is_active": True,
    "antibody_kell": False,
    "antibody_duffy": False,
    "antibody_kidd": False,
    "kell_negative": False,
}

E2E_DONORS = [
    {
        "donor_id": E2E_DONOR_IDS[0],
        "name": "Sheik Bhai",
        "phone": E2E_PHONE_SHEIK,
        "blood_type": "O+",
        "city": "Hyderabad",
        "lat": APOLLO_LAT + 0.003,
        "lng": APOLLO_LNG + 0.003,
        "donation_count": 12,
        "lives_saved": 12,
        "response_rate": 0.95,
        "churn_score": 0.1,
        "churn_risk": "LOW",
        "is_active": True,
        "consent_outreach": True,
        "consent_data_storage": True,
        "preferred_language": "en",
    },
    {
        "donor_id": E2E_DONOR_IDS[1],
        "name": "Arjun Singh",
        "phone": E2E_PHONE_ARJUN,
        "blood_type": "A+",
        "city": "Hyderabad",
        "lat": APOLLO_LAT + 0.008,
        "lng": APOLLO_LNG + 0.005,
        "donation_count": 6,
        "lives_saved": 6,
        "response_rate": 0.88,
        "churn_score": 0.2,
        "churn_risk": "LOW",
        "is_active": True,
        "consent_outreach": True,
        "consent_data_storage": True,
        "preferred_language": "en",
    },
    {
        "donor_id": E2E_DONOR_IDS[2],
        "name": "Ravi Kumar",
        "phone": E2E_PHONE_RAVI,
        "blood_type": "B+",
        "city": "Hyderabad",
        "lat": APOLLO_LAT - 0.004,
        "lng": APOLLO_LNG - 0.002,
        "donation_count": 8,
        "lives_saved": 8,
        "response_rate": 0.9,
        "churn_score": 0.15,
        "churn_risk": "LOW",
        "is_active": True,
        "consent_outreach": True,
        "consent_data_storage": True,
        "preferred_language": "hi",
    },
]


def _clear_telegram_conflict(supabase, chat_id: str, keep_donor_id: str):
    if not chat_id:
        return
    conflicts = supabase.table("donors").select("donor_id").eq("telegram_chat_id", str(chat_id)).execute()
    for row in conflicts.data or []:
        if row["donor_id"] != keep_donor_id:
            supabase.table("donors").update({"telegram_chat_id": None}).eq("donor_id", row["donor_id"]).execute()


def _find_telegram_chat_id(supabase, phone: str) -> str | None:
    norm = normalize_phone(phone)
    for table in ("donors", "patients", "staff"):
        try:
            res = supabase.table(table).select("telegram_chat_id").eq("phone", norm).execute()
            for row in (res.data or []):
                cid = row.get("telegram_chat_id")
                if is_valid_telegram_chat_id(cid):
                    return str(cid)
            alt = norm.replace("+91", "")
            res2 = supabase.table(table).select("telegram_chat_id").like("phone", f"%{alt}").execute()
            for row in (res2.data or []):
                cid = row.get("telegram_chat_id")
                if is_valid_telegram_chat_id(cid):
                    return str(cid)
        except Exception:
            pass
    return None


def _migrate_phone_record(supabase, phone: str, target_donor_id: str) -> str | None:
    """Assign phone exclusively to target donor; steal valid Telegram from duplicates."""
    norm = normalize_phone(phone)
    existing = supabase.table("donors").select("donor_id, telegram_chat_id").eq("phone", norm).execute()
    chat_id = None
    for row in existing.data or []:
        cid = row.get("telegram_chat_id")
        if is_valid_telegram_chat_id(cid):
            chat_id = str(cid)
        if row["donor_id"] != target_donor_id:
            supabase.table("donors").update({
                "is_active": False,
                "telegram_chat_id": None,
                "phone": None,
            }).eq("donor_id", row["donor_id"]).execute()
    if not chat_id:
        chat_id = _find_telegram_chat_id(supabase, phone)
    if chat_id:
        _clear_telegram_conflict(supabase, chat_id, target_donor_id)
    return chat_id


async def seed_e2e():
    supabase = get_supabase_admin()
    now = utc_now_iso()

    print("BloodBridge — E2E 3-Phone Seed")
    print("=" * 50)

    # Deactivate legacy demo donors that share the same phone numbers
    for legacy_id in LEGACY_DEMO_DONOR_IDS:
        supabase.table("donors").update({"is_active": False, "telegram_chat_id": None}).eq("donor_id", legacy_id).execute()
    print("  Deactivated legacy D-THREE-* demo donors (phone conflict)")

    # Patient — avoid phone unique constraint clash with donor/patient rows
    existing = supabase.table("patients").select("patient_id, phone").eq("patient_id", E2E_PATIENT_ID).execute()
    chat = _find_telegram_chat_id(supabase, E2E_PHONE_SHEIK)
    patient_row = {**E2E_PATIENT, "updated_at": now}
    if chat:
        patient_row["password"] = f"tg:{chat}"
    # Only set phone if no other patient owns it
    phone_owner = supabase.table("patients").select("patient_id").eq("phone", E2E_PHONE_SHEIK).execute()
    if phone_owner.data and phone_owner.data[0]["patient_id"] != E2E_PATIENT_ID:
        patient_row.pop("phone", None)
    if existing.data:
        supabase.table("patients").update(patient_row).eq("patient_id", E2E_PATIENT_ID).execute()
        print(f"  Updated patient {E2E_PATIENT_ID}")
    else:
        if phone_owner.data:
            patient_row.pop("phone", None)
        supabase.table("patients").insert(patient_row).execute()
        print(f"  Created patient {E2E_PATIENT_ID}")

    # Donors + consent — each phone owned exclusively by one E2E donor
    for donor in E2E_DONORS:
        tg = _migrate_phone_record(supabase, donor["phone"], donor["donor_id"])
        row = {**donor, "consent_granted_at": now, "kell_negative": False,
               "duffy_negative": False, "kidd_negative": False, "last_donation_date": None,
               "is_active": True, "phone": normalize_phone(donor["phone"])}
        if tg:
            row["telegram_chat_id"] = tg
            print(f"  {donor['donor_id']} -> Telegram {tg}")
        else:
            row["telegram_chat_id"] = None
            print(f"  {donor['donor_id']} -> no Telegram (voice calls will be used)")
        ex = supabase.table("donors").select("donor_id").eq("donor_id", donor["donor_id"]).execute()
        if ex.data:
            supabase.table("donors").update(row).eq("donor_id", donor["donor_id"]).execute()
        else:
            supabase.table("donors").insert(row).execute()
        print(f"  OK {donor['donor_id']} ({donor['name']}) {donor['phone']}")

        await ConsentService.grant_consent(
            donor["donor_id"],
            ["data_storage", "outreach_telegram", "outreach_voice"],
            channel="seed_e2e",
            language=donor.get("preferred_language", "en"),
        )

        supabase.table("donor_memory").upsert({
            "donor_id": donor["donor_id"],
            "preferred_language": donor.get("preferred_language", "en"),
            "badges": ["life_saver"],
            "streak_days": 14,
            "total_interactions": donor.get("donation_count", 0),
        }).execute()

    # Emergency request REQ-TEST-B001
    req_ex = supabase.table("emergency_requests").select("request_id").eq("request_id", E2E_REQUEST_ID).execute()
    req_row = {
        "request_id": E2E_REQUEST_ID,
        "patient_id": E2E_PATIENT_ID,
        "blood_type": "B-",
        "city": "Hyderabad",
        "hospital_name": "Apollo Banjara Hills",
        "ward": "Thalassemia Day Care",
        "status": "IN_PROGRESS",
        "priority": "CRITICAL",
        "request_mode": "emergency",
        "triggered_by": "e2e_seed",
        "updated_at": now,
    }
    if req_ex.data:
        supabase.table("emergency_requests").update(req_row).eq("request_id", E2E_REQUEST_ID).execute()
    else:
        req_row["created_at"] = now
        supabase.table("emergency_requests").insert(req_row).execute()
    print(f"  OK emergency {E2E_REQUEST_ID} IN_PROGRESS")

    # Blood chain: Sheik ALERTED, others PENDING
    supabase.table("blood_chains").delete().eq("request_id", E2E_REQUEST_ID).execute()
    chain = [
        {"request_id": E2E_REQUEST_ID, "donor_id": E2E_DONOR_IDS[0], "donor_name": "Sheik Bhai",
         "chain_position": 1, "status": "ALERTED", "antigen_score": 0.92,
         "alerted_at": now, "ring": 1, "match_score": 0.95},
        {"request_id": E2E_REQUEST_ID, "donor_id": E2E_DONOR_IDS[1], "donor_name": "Arjun Singh",
         "chain_position": 2, "status": "PENDING", "antigen_score": 0.75, "ring": 1, "match_score": 0.80},
        {"request_id": E2E_REQUEST_ID, "donor_id": E2E_DONOR_IDS[2], "donor_name": "Ravi Kumar",
         "chain_position": 3, "status": "PENDING", "antigen_score": 0.88, "ring": 1, "match_score": 0.90},
    ]
    supabase.table("blood_chains").insert(chain).execute()
    print(f"  OK blood chain: 1 ALERTED + 2 PENDING")

    # Neo4j edges (best effort)
    try:
        from core.neo4j_client import get_driver
        driver = get_driver()
        if driver:
            async with driver.session() as session:
                await session.run(
                    "MERGE (p:Patient {patient_id: $pid}) "
                    "SET p.name = $pname, p.blood_type = $bt, p.city = $city, p.lat = $lat, p.lng = $lng, "
                    "p.antibody_kell = false, p.antibody_duffy = false, p.antibody_kidd = false",
                    pid=E2E_PATIENT_ID, pname="Patient P-10026", bt="B-", city="Hyderabad",
                    lat=APOLLO_LAT, lng=APOLLO_LNG,
                )
                for d in E2E_DONORS:
                    await session.run(
                        "MERGE (d:Donor {donor_id: $did}) "
                        "SET d.name = $name, d.blood_type = $bt, d.phone = $phone, d.is_active = true, "
                        "d.lat = $lat, d.lng = $lng",
                        did=d["donor_id"], name=d["name"], bt=d["blood_type"],
                        phone=d["phone"], lat=d["lat"], lng=d["lng"],
                    )
                    await session.run(
                        "MATCH (d:Donor {donor_id: $did}), (p:Patient {patient_id: $pid}) "
                        "MERGE (d)-[r:COMPATIBLE_WITH]->(p) "
                        "SET r.antigen_score = 0.9, r.kell_safe = true",
                        did=d["donor_id"], pid=E2E_PATIENT_ID,
                    )
                # Clear stale IN_CHAIN edges for this request before re-seeding
                await session.run(
                    "MATCH ()-[r:IN_CHAIN {request_id: $rid}]->() DELETE r",
                    rid=E2E_REQUEST_ID,
                )
                # IN_CHAIN edges for admin graph search (REQ-TEST-B001)
                for i, d in enumerate(E2E_DONORS):
                    status = "ALERTED" if i == 0 else "PENDING"
                    await session.run(
                        """
                        MATCH (d:Donor {donor_id: $did}), (p:Patient {patient_id: $pid})
                        MERGE (d)-[r:IN_CHAIN {request_id: $rid}]->(p)
                        SET r.status = $status, r.chain_position = $pos,
                            r.antigen_score = $score, r.alerted_at = CASE WHEN $status = 'ALERTED' THEN datetime() ELSE null END
                        """,
                        did=d["donor_id"], pid=E2E_PATIENT_ID, rid=E2E_REQUEST_ID,
                        status=status, pos=i + 1, score=0.9 - (i * 0.05),
                    )
            print("  OK Neo4j COMPATIBLE_WITH + IN_CHAIN edges")
    except Exception as e:
        print(f"  WARN Neo4j skipped: {e}")

    print("\nDone! Test voice call:")
    print("  curl -X POST http://localhost:8000/api/donors/D-72485/voice")
    print("Track chain: /status P-10026 in Telegram")


if __name__ == "__main__":
    asyncio.run(seed_e2e())
