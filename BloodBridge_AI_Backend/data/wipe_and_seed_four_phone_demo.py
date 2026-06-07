"""
Wipe Supabase demo data and re-seed for the 4-phone judges demo.

Keeps ONLY these real phone numbers in the database after wipe:
  +917075899966  Donor 1  (D-THREE-001)
  +919642273274  Donor 2  (D-THREE-002)
  +916305589656  Patient  (P-THREE-001)
  +919494421169  NOT pre-seeded — reserved for live Telegram registration demo

Also seeds 10 background donors (D-BGND-001..010) + P-THREE-002 for UI richness.

Usage:
    cd BloodBridge_AI_Backend
    python -m data.wipe_and_seed_four_phone_demo

Then set THREE_PHONE_DEMO_MODE=true in .env and restart backend.
"""
import asyncio
from datetime import date, timedelta, datetime, timezone

from core.database import get_supabase_admin
from services.demo_phones import (
    DEMO_ALLOWED_PHONES,
    DEMO_DONOR_IDS,
    DEMO_PATIENT_ID,
    normalize_phone,
)
from data.seed_three_phones import (
    seed_three_phones,
    BACKGROUND_DONORS,
    DEMO_DONORS,
    DEMO_PATIENT,
    PATIENT_2,
)

KEEP_DONOR_IDS = set(DEMO_DONOR_IDS + [d["donor_id"] for d in BACKGROUND_DONORS])
KEEP_PATIENT_IDS = {DEMO_PATIENT_ID, "P-THREE-002"}

# Tables cleared before re-seed (child → parent order)
WIPE_TABLES = [
    "blood_chains",
    "agent_traces",
    "emergency_requests",
    "voice_call_attempts",
    "outreach_protocol_stats",
    "bridge_memberships",
    "bridges",
    "transfusion_schedule",
    "donor_verifications",
    "consent_records",
    "gamification",
    "leaderboard_cache",
    "donor_memory",
    "donor_locations",
    "patient_locations",
]


def _delete_all_rows(supabase, table: str) -> int:
    try:
        res = supabase.table(table).delete().neq("created_at", "1970-01-01T00:00:00+00:00").execute()
        return len(res.data or [])
    except Exception:
        try:
            # Fallback: delete by primary key pattern
            rows = supabase.table(table).select("*").limit(5000).execute()
            count = 0
            for row in rows.data or []:
                pk = next(iter(row.keys()))
                supabase.table(table).delete().eq(pk, row[pk]).execute()
                count += 1
            return count
        except Exception as e:
            print(f"      skip {table}: {e}")
            return 0


def _remove_records_with_foreign_phones(supabase):
    """Delete donors/patients whose phone is not one of the 4 allowed demo numbers."""
    allowed = {normalize_phone(p) for p in DEMO_ALLOWED_PHONES}

    donors = supabase.table("donors").select("donor_id, phone").execute()
    removed_d = 0
    for row in donors.data or []:
        if row["donor_id"] in KEEP_DONOR_IDS:
            continue
        phone = normalize_phone(row.get("phone") or "")
        if phone and phone not in allowed:
            supabase.table("donors").delete().eq("donor_id", row["donor_id"]).execute()
            removed_d += 1
        elif row["donor_id"] not in KEEP_DONOR_IDS:
            supabase.table("donors").delete().eq("donor_id", row["donor_id"]).execute()
            removed_d += 1

    patients = supabase.table("patients").select("patient_id, phone").execute()
    removed_p = 0
    for row in patients.data or []:
        if row["patient_id"] in KEEP_PATIENT_IDS:
            continue
        phone = normalize_phone(row.get("phone") or "")
        if phone and phone not in allowed:
            supabase.table("patients").delete().eq("patient_id", row["patient_id"]).execute()
            removed_p += 1
        elif row["patient_id"] not in KEEP_PATIENT_IDS:
            supabase.table("patients").delete().eq("patient_id", row["patient_id"]).execute()
            removed_p += 1

    return removed_d, removed_p


def wipe_supabase_demo():
    supabase = get_supabase_admin()
    print("BloodBridge — Wipe Supabase for 4-Phone Demo")
    print("=" * 55)

    for table in WIPE_TABLES:
        n = _delete_all_rows(supabase, table)
        print(f"  Cleared {table}: {n} row(s)")

    removed_d, removed_p = _remove_records_with_foreign_phones(supabase)
    print(f"  Removed {removed_d} extra donor(s), {removed_p} extra patient(s)")
    print("  OK Wipe complete\n")


async def seed_ui_extras():
    """Seed dashboard-visible extras: bridge, transfusion schedule, completed emergency."""
    supabase = get_supabase_admin()
    now = datetime.now(timezone.utc).isoformat()

    # Bridge: D-THREE-001 + D-THREE-002 committed to P-THREE-001 (Blood Bridge card UI)
    try:
        supabase.table("bridges").upsert({
            "bridge_id": DEMO_PATIENT_ID,
            "patient_id": DEMO_PATIENT_ID,
            "blood_type": DEMO_PATIENT["blood_type"],
            "city": DEMO_PATIENT["city"],
            "next_expected_transfusion": (date.today() + timedelta(days=7)).isoformat(),
            "frequency_days": 21,
            "status": "ACTIVE",
        }).execute()
        for donor in DEMO_DONORS:
            supabase.table("bridge_memberships").upsert({
                "bridge_id": DEMO_PATIENT_ID,
                "donor_id": donor["donor_id"],
                "role": "BRIDGE_DONOR",
                "status": "ACTIVE",
                "joined_at": now,
            }).execute()
        print("  OK Bridge memberships for P-THREE-001")
    except Exception as e:
        print(f"  WARN bridge seed: {e}")

    # Transfusion schedule — status must be PENDING (PatientDashboard filters on PENDING)
    try:
        supabase.table("transfusion_schedule").delete().eq("patient_id", DEMO_PATIENT_ID).execute()
        for i, days in enumerate([7, 21, 35], start=1):
            supabase.table("transfusion_schedule").insert({
                "patient_id": DEMO_PATIENT_ID,
                "scheduled_date": (date.today() + timedelta(days=days)).isoformat(),
                "hospital": DEMO_PATIENT["hospital"],
                "blood_type": DEMO_PATIENT["blood_type"],
                "status": "PENDING",
                "created_by": "seed",
            }).execute()
        print("  OK Transfusion schedule (PENDING) for P-THREE-001")
    except Exception as e:
        print(f"  WARN transfusion schedule: {e}")

    # Patient portal login by phone 6305589656
    try:
        supabase.table("patients").update({
            "password": "demo123",
            "phone": normalize_phone(DEMO_PATIENT["phone"]),
        }).eq("patient_id", DEMO_PATIENT_ID).execute()
        print("  OK Patient login password set (demo123)")
    except Exception as e:
        print(f"  WARN patient password: {e}")

    # 2 COMPLETED emergencies with completed_at — required for AI auto-schedule background task
    try:
        for idx, days_ago in enumerate([42, 21], start=1):
            req_id = f"REQ-DEMO-HIST-00{idx}"
            completed = (datetime.now(timezone.utc) - timedelta(days=days_ago)).isoformat()
            supabase.table("emergency_requests").upsert({
                "request_id": req_id,
                "patient_id": DEMO_PATIENT_ID,
                "blood_type": "B+",
                "city": DEMO_PATIENT["city"],
                "hospital_name": DEMO_PATIENT["hospital"],
                "ward": DEMO_PATIENT["ward"],
                "status": "COMPLETED",
                "priority": "CRITICAL",
                "request_mode": "emergency",
                "triggered_by": "seed",
                "created_at": (datetime.now(timezone.utc) - timedelta(days=days_ago + 1)).isoformat(),
                "completed_at": completed,
                "updated_at": completed,
            }).execute()
            supabase.table("blood_chains").delete().eq("request_id", req_id).execute()
            supabase.table("blood_chains").insert({
                "request_id": req_id,
                "donor_id": DEMO_DONOR_IDS[0],
                "donor_name": DEMO_DONORS[0]["name"],
                "chain_position": 1,
                "status": "COMPLETED",
                "antigen_score": 0.98,
                "match_score": 0.96,
                "ring": 1,
                "confirmed_at": completed,
            }).execute()
        print("  OK 2 COMPLETED emergencies for AI auto-schedule history")
    except Exception as e:
        print(f"  WARN completed emergencies: {e}")

    # Completed emergency for chain history UI (primary display record)
    try:
        req_id = "REQ-DEMO-HIST-001"
        completed = (datetime.now(timezone.utc) - timedelta(days=14)).isoformat()
        supabase.table("emergency_requests").upsert({
            "request_id": req_id,
            "patient_id": DEMO_PATIENT_ID,
            "blood_type": "B+",
            "city": DEMO_PATIENT["city"],
            "hospital_name": DEMO_PATIENT["hospital"],
            "ward": DEMO_PATIENT["ward"],
            "status": "COMPLETED",
            "priority": "CRITICAL",
            "request_mode": "emergency",
            "triggered_by": "seed",
            "created_at": (datetime.now(timezone.utc) - timedelta(days=15)).isoformat(),
            "completed_at": completed,
            "updated_at": completed,
        }).execute()
        supabase.table("blood_chains").delete().eq("request_id", req_id).execute()
        supabase.table("blood_chains").insert([
            {
                "request_id": req_id,
                "donor_id": DEMO_DONOR_IDS[0],
                "donor_name": DEMO_DONORS[0]["name"],
                "chain_position": 1,
                "status": "COMPLETED",
                "antigen_score": 0.98,
                "match_score": 0.96,
                "ring": 1,
                "confirmed_at": now,
            },
            {
                "request_id": req_id,
                "donor_id": DEMO_DONOR_IDS[1],
                "donor_name": DEMO_DONORS[1]["name"],
                "chain_position": 2,
                "status": "DECLINED",
                "antigen_score": 0.91,
                "match_score": 0.88,
                "ring": 1,
            },
        ]).execute()
        print("  OK Historical emergency REQ-DEMO-HIST-001 (COMPLETED)")
    except Exception as e:
        print(f"  WARN history emergency: {e}")

    # Neo4j IN_CHAIN for graph when no active emergency
    try:
        from core.neo4j_client import get_driver
        driver = get_driver()
        if driver:
            async with driver.session() as session:
                await session.run(
                    "MATCH ()-[r:IN_CHAIN {request_id: $rid}]->() DELETE r",
                    rid="REQ-DEMO-HIST-001",
                )
                for i, donor in enumerate(DEMO_DONORS):
                    status = "COMPLETED" if i == 0 else "DECLINED"
                    await session.run(
                        """
                        MATCH (d:Donor {donor_id: $did}), (p:Patient {patient_id: $pid})
                        MERGE (d)-[r:IN_CHAIN {request_id: $rid}]->(p)
                        SET r.status = $status, r.chain_position = $pos, r.antigen_score = $score
                        """,
                        did=donor["donor_id"], pid=DEMO_PATIENT_ID,
                        rid="REQ-DEMO-HIST-001", status=status, pos=i + 1,
                        score=0.95 - i * 0.05,
                    )
            print("  OK Neo4j IN_CHAIN edges for graph history")
    except Exception as e:
        print(f"  WARN Neo4j history: {e}")


async def main():
    wipe_supabase_demo()
    await seed_three_phones()
    print("\n  Seeding UI extras (bridges, schedule, history)...")
    await seed_ui_extras()
    print("\n" + "=" * 55)
    print("OK 4-Phone demo seed complete!")
    print("\nAllowed real phones in DB:")
    for p in DEMO_ALLOWED_PHONES:
        print(f"  {p}")
    print("\nPhone 4 (+919494421169) is NOT pre-seeded — register live via Telegram.")
    print("Set THREE_PHONE_DEMO_MODE=true, restart backend, then run demo plan.")


if __name__ == "__main__":
    asyncio.run(main())
