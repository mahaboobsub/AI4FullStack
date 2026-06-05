"""
Demo Seed Script for BloodBridge AI.
Idempotent — safe to run multiple times. Inserts demo scenario data:
- 1 patient (B-, kell_negative)
- 8 donors (mixed types)
- 1 staff user
- 1 transfusion schedule entry 6 days out
- Neo4j COMPATIBLE_WITH edges

Usage:
    python -m data.seed_demo
"""
import asyncio
import random
import logging
from datetime import date, timedelta

logger = logging.getLogger(__name__)

DEMO_PATIENT = {
    "patient_id": "P-DEMO-001",
    "name": "Aarav Sharma",
    "age": 7,
    "blood_type": "B-",
    "hospital": "KIMS Secunderabad",
    "ward": "Thalassemia Day Care",
    "city": "Hyderabad",
    "kell_negative": True,
    "antibody_kell": True,
    "transfusion_count": 42,
    "hemoglobin": 7.2,
    "status": "CRITICAL",
    "next_transfusion_due": (date.today() + timedelta(days=6)).isoformat()
}

DEMO_DONORS = [
    {"donor_id": "D-DEMO-001", "name": "Rahul Verma", "blood_type": "B-", "city": "Hyderabad", "kell_negative": True, "donation_count": 14, "lives_saved": 14, "churn_score": 0.12, "churn_risk": "LOW", "response_rate": 0.95, "is_active": True, "consent_outreach": True, "telegram_chat_id": "demo_chat_001", "preferred_language": "hi"},
    {"donor_id": "D-DEMO-002", "name": "Priya Reddy", "blood_type": "B-", "city": "Hyderabad", "kell_negative": True, "donation_count": 8, "lives_saved": 8, "churn_score": 0.22, "churn_risk": "LOW", "response_rate": 0.88, "is_active": True, "consent_outreach": True, "telegram_chat_id": "demo_chat_002", "preferred_language": "te"},
    {"donor_id": "D-DEMO-003", "name": "Suresh Kumar", "blood_type": "B+", "city": "Hyderabad", "kell_negative": False, "donation_count": 6, "lives_saved": 5, "churn_score": 0.35, "churn_risk": "MEDIUM", "response_rate": 0.75, "is_active": True, "consent_outreach": True, "telegram_chat_id": "demo_chat_003", "preferred_language": "hi"},
    {"donor_id": "D-DEMO-004", "name": "Lakshmi Devi", "blood_type": "O-", "city": "Hyderabad", "kell_negative": True, "donation_count": 20, "lives_saved": 20, "churn_score": 0.08, "churn_risk": "LOW", "response_rate": 0.97, "is_active": True, "consent_outreach": True, "telegram_chat_id": "demo_chat_004", "preferred_language": "te"},
    {"donor_id": "D-DEMO-005", "name": "Amit Shah", "blood_type": "B-", "city": "Hyderabad", "kell_negative": False, "donation_count": 3, "lives_saved": 2, "churn_score": 0.55, "churn_risk": "MEDIUM", "response_rate": 0.60, "is_active": True, "consent_outreach": True, "telegram_chat_id": "demo_chat_005", "preferred_language": "en"},
    {"donor_id": "D-DEMO-006", "name": "Fatima Begum", "blood_type": "B-", "city": "Hyderabad", "kell_negative": True, "donation_count": 11, "lives_saved": 11, "churn_score": 0.15, "churn_risk": "LOW", "response_rate": 0.92, "is_active": True, "consent_outreach": True, "telegram_chat_id": "demo_chat_006", "preferred_language": "hi"},
    {"donor_id": "D-DEMO-007", "name": "Ravi Teja", "blood_type": "AB-", "city": "Hyderabad", "kell_negative": False, "donation_count": 1, "lives_saved": 1, "churn_score": 0.72, "churn_risk": "HIGH", "response_rate": 0.50, "is_active": True, "consent_outreach": True, "telegram_chat_id": "demo_chat_007", "preferred_language": "te"},
    {"donor_id": "D-DEMO-008", "name": "Ananya Iyer", "blood_type": "O+", "city": "Hyderabad", "kell_negative": False, "donation_count": 5, "lives_saved": 4, "churn_score": 0.40, "churn_risk": "MEDIUM", "response_rate": 0.70, "is_active": True, "consent_outreach": True, "telegram_chat_id": "demo_chat_008", "preferred_language": "en"},
]

DEMO_STAFF = {
    "staff_id": "STAFF-DEMO-001",
    "telegram_username": "@demo_staff",
    "telegram_chat_id": "demo_staff_001",
    "role": "Coordinator",
    "hospital": "KIMS Secunderabad",
    "is_active": True,
}

async def seed_demo():
    """Idempotent demo data seeding."""
    from core.database import get_supabase_admin
    supabase = get_supabase_admin()

    print("🩸 BloodBridge AI — Demo Seed Script")
    print("=" * 50)

    # 1. Seed patient
    print("\n📌 Seeding demo patient...")
    existing = supabase.table("patients").select("patient_id").eq("patient_id", DEMO_PATIENT["patient_id"]).execute()
    if not existing.data:
        supabase.table("patients").insert(DEMO_PATIENT).execute()
        print(f"  ✅ Created patient: {DEMO_PATIENT['patient_id']} ({DEMO_PATIENT['name']})")
    else:
        supabase.table("patients").update(DEMO_PATIENT).eq("patient_id", DEMO_PATIENT["patient_id"]).execute()
        print(f"  ♻️ Updated existing patient: {DEMO_PATIENT['patient_id']}")

    # 2. Seed donors
    print("\n📌 Seeding 8 demo donors...")
    for donor in DEMO_DONORS:
        existing = supabase.table("donors").select("donor_id").eq("donor_id", donor["donor_id"]).execute()
        if not existing.data:
            supabase.table("donors").insert(donor).execute()
            print(f"  ✅ Created donor: {donor['donor_id']} ({donor['name']}, {donor['blood_type']})")
        else:
            supabase.table("donors").update(donor).eq("donor_id", donor["donor_id"]).execute()
            print(f"  ♻️ Updated donor: {donor['donor_id']}")

    # 3. Seed donor memory
    print("\n📌 Seeding donor memory...")
    for donor in DEMO_DONORS:
        badges = []
        if donor["donation_count"] >= 10:
            badges.append("blood_hero")
        if donor["lives_saved"] >= 3:
            badges.append("life_saver")
        if donor["response_rate"] >= 0.9:
            badges.append("crisis_hero")
        if donor.get("kell_negative"):
            badges.append("rare_guardian")

        mem = {
            "donor_id": donor["donor_id"],
            "preferred_language": donor.get("preferred_language", "en"),
            "badges": badges,
            "streak_days": donor["donation_count"] * 30,
            "total_interactions": donor["donation_count"]
        }
        supabase.table("donor_memory").upsert(mem).execute()
        print(f"  ✅ Memory set for {donor['donor_id']}: {len(badges)} badges")

    # 4. Seed staff
    print("\n📌 Seeding demo staff...")
    existing = supabase.table("staff").select("staff_id").eq("staff_id", DEMO_STAFF["staff_id"]).execute()
    if not existing.data:
        supabase.table("staff").insert(DEMO_STAFF).execute()
        print(f"  ✅ Created staff: {DEMO_STAFF['telegram_username']}")
    else:
        print(f"  ♻️ Staff already exists: {DEMO_STAFF['telegram_username']}")

    # 5. Seed transfusion schedule
    print("\n📌 Seeding transfusion schedule...")
    sched_date = (date.today() + timedelta(days=6)).isoformat()
    existing_sched = supabase.table("transfusion_schedule")\
        .select("schedule_id")\
        .eq("patient_id", DEMO_PATIENT["patient_id"])\
        .eq("status", "PENDING")\
        .execute()
    if not existing_sched.data:
        supabase.table("transfusion_schedule").insert({
            "patient_id": DEMO_PATIENT["patient_id"],
            "scheduled_date": sched_date,
            "hospital": DEMO_PATIENT["hospital"],
            "blood_type": DEMO_PATIENT["blood_type"],
            "status": "PENDING",
            "created_by": "demo_seed"
        }).execute()
        print(f"  ✅ Scheduled transfusion for {sched_date}")
    else:
        print(f"  ♻️ Pending schedule already exists")

    # 6. Seed Neo4j graph (if available)
    print("\n📌 Seeding Neo4j graph...")
    try:
        from core.neo4j_client import get_driver
        driver = get_driver()
        if driver:
            async with driver.session() as session:
                # Create patient node
                await session.run(
                    "MERGE (p:Patient {patient_id: $pid}) "
                    "SET p.name = $name, p.blood_type = $bt, p.hospital = $hospital, p.kell_negative = $kn",
                    pid=DEMO_PATIENT["patient_id"],
                    name=DEMO_PATIENT["name"],
                    bt=DEMO_PATIENT["blood_type"],
                    hospital=DEMO_PATIENT["hospital"],
                    kn=DEMO_PATIENT["kell_negative"]
                )

                # Create donor nodes and COMPATIBLE_WITH edges
                for donor in DEMO_DONORS:
                    await session.run(
                        "MERGE (d:Donor {donor_id: $did}) "
                        "SET d.name = $name, d.blood_type = $bt, d.city = $city, d.kell_negative = $kn",
                        did=donor["donor_id"],
                        name=donor["name"],
                        bt=donor["blood_type"],
                        city=donor["city"],
                        kn=donor.get("kell_negative", False)
                    )

                    # Compute compatibility score
                    score = 0.5
                    if donor["blood_type"] == DEMO_PATIENT["blood_type"]:
                        score = 0.85
                    if donor.get("kell_negative") and DEMO_PATIENT["kell_negative"]:
                        score += 0.10
                    if donor["blood_type"] == "O-":
                        score = 0.75  # Universal donor

                    await session.run(
                        "MATCH (d:Donor {donor_id: $did}), (p:Patient {patient_id: $pid}) "
                        "MERGE (d)-[r:COMPATIBLE_WITH]->(p) "
                        "SET r.antigen_score = $score",
                        did=donor["donor_id"],
                        pid=DEMO_PATIENT["patient_id"],
                        score=min(score, 1.0)
                    )

                print("  ✅ Neo4j graph seeded with patient + 8 donors + COMPATIBLE_WITH edges")
        else:
            print("  ⚠️ Neo4j driver not available — skipping graph seeding")
    except Exception as e:
        print(f"  ⚠️ Neo4j seeding failed (non-critical): {e}")

    # 7. Seed leaderboard cache
    print("\n📌 Seeding leaderboard cache...")
    sorted_donors = sorted(DEMO_DONORS, key=lambda d: d["lives_saved"], reverse=True)
    for idx, donor in enumerate(sorted_donors):
        supabase.table("leaderboard_cache").upsert({
            "donor_id": donor["donor_id"],
            "city": donor["city"],
            "lives_saved": donor["lives_saved"],
            "rank": idx + 1
        }).execute()
    print(f"  ✅ Leaderboard cache seeded for {len(sorted_donors)} donors")

    print("\n" + "=" * 50)
    print("✅ Demo seed complete! Run the backend and try:")
    print("   • POST /api/emergencies with patient_id=P-DEMO-001, blood_type=B-")
    print("   • GET /api/donors/D-DEMO-001/active-request")
    print("   • GET /api/patients/P-DEMO-001/schedule")


if __name__ == "__main__":
    asyncio.run(seed_demo())
