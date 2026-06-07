"""Fix all demo data for 3-phone test."""
import sys
sys.path.insert(0, '.')

from core.database import get_supabase_admin

s = get_supabase_admin()

print("=== Fixing test donors ===")
donors_to_fix = [
    ("D-72485", "O+", "6352238849", "+917075899966", "Sheik Bhai"),
    ("D-50013", "B+", None,         "+916305589656", "Ravi Kumar"),
    ("D-33512", "A+", None,         "+919642273274", "Arjun Singh"),
]
for d_id, bt, tg_id, phone, name in donors_to_fix:
    upd = {
        "blood_type": bt,
        "is_active": True,
        "phone": phone,
        "name": name,
        "city": "Hyderabad",
        "donation_count": 5,
        "lives_saved": 3,
        "response_rate": 0.9,
    }
    if tg_id:
        upd["telegram_chat_id"] = tg_id
    s.table("donors").update(upd).eq("donor_id", d_id).execute()
    r = s.table("donors").select("donor_id,blood_type,telegram_chat_id,is_active,phone").eq("donor_id", d_id).execute()
    if r.data:
        d = r.data[0]
        print(f"  {d_id} ({name}): blood={d['blood_type']}, tg={d['telegram_chat_id']}, phone={d['phone']}, active={d['is_active']}")
    else:
        print(f"  {d_id} NOT FOUND - creating")
        s.table("donors").insert({**upd, "donor_id": d_id}).execute()

print()
print("=== Setting up P-10099 (B+) ===")
p_exists = s.table("patients").select("patient_id,blood_type").eq("patient_id", "P-10099").execute()
if p_exists.data:
    s.table("patients").update({
        "blood_type": "B+",
        "hospital": "KIMS Secunderabad",
        "ward": "Thalassemia Day Care",
        "city": "Hyderabad",
        "is_active": True,
        "hemoglobin": 8.0,
        "transfusion_count": 10,
        "status": "CRITICAL",
        "name": "Demo Patient B+",
    }).eq("patient_id", "P-10099").execute()
    print("  Updated P-10099 -> B+")
else:
    s.table("patients").insert({
        "patient_id": "P-10099",
        "name": "Demo Patient B+",
        "blood_type": "B+",
        "hospital": "KIMS Secunderabad",
        "ward": "Thalassemia Day Care",
        "city": "Hyderabad",
        "is_active": True,
        "hemoglobin": 8.0,
        "transfusion_count": 10,
        "status": "CRITICAL",
    }).execute()
    print("  Created P-10099 -> B+")

print()
print("=== Ensuring donor_memory records ===")
for d_id, _, _, _, name in donors_to_fix:
    mem = s.table("donor_memory").select("donor_id").eq("donor_id", d_id).execute()
    if not mem.data:
        s.table("donor_memory").insert({
            "donor_id": d_id,
            "badges": ["life_saver"],
            "streak_days": 5,
        }).execute()
        print(f"  Created memory for {d_id}")
    else:
        print(f"  Memory OK for {d_id}")

print()
print("=== Seeding consent for test donors ===")
import asyncio
from services.consent_service import ConsentService

async def seed_consent():
    for d_id, _, _, _, _ in donors_to_fix:
        try:
            await ConsentService.grant_consent(
                d_id,
                ["data_storage", "outreach_telegram", "outreach_voice"],
                channel="demo_seed",
                language="en",
            )
            print(f"  Consent OK for {d_id}")
        except Exception as e:
            print(f"  Consent skip {d_id}: {e}")

asyncio.run(seed_consent())

print()
print("=== Leaderboard seeding ===")
for i, (d_id, _, _, _, name) in enumerate(donors_to_fix):
    try:
        s.table("leaderboard_cache").upsert({
            "donor_id": d_id,
            "city": "Hyderabad",
            "month_year": "2026-06",
            "rank": i + 1,
            "lives_saved": 3 - i,
        }, on_conflict="donor_id,month_year").execute()
        print(f"  Leaderboard rank {i+1} for {name}")
    except Exception as e:
        print(f"  Leaderboard skip {d_id}: {e}")

print()
print("=" * 50)
print("SETUP COMPLETE!")
print()
print("Now go to http://localhost:5173/dashboard/emergency")
print("Click 'New Emergency' and fill in:")
print("  Patient ID: P-10099")
print("  Blood Type: B+")
print("  City: Hyderabad")
print("  Ward: Thalassemia Day Care")
print("  Hospital: KIMS Secunderabad")
print()
print("Expected flow:")
print("  1. Sheik Bhai (+917075899966) receives Telegram alert")
print("  2. If no reply in 1min -> Bolna voice call to Sheik")
print("  3. If declined -> Ravi Kumar (+916305589656) gets alerted")
