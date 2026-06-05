"""
Supabase Database Seeding Script.
Generates synthetic data for hackathon demo (500 donors, 50 patients, memory, consent, badges).
"""
import os
import sys
import uuid
import random
from datetime import datetime, date, timedelta
from faker import Faker

# Add backend root to path to resolve imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import get_settings
from core.database import get_supabase_admin

def check_env():
    """Verify that required environment variables are set."""
    settings = get_settings()
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_KEY:
        print("Error: SUPABASE_URL or SUPABASE_SERVICE_KEY is missing from configuration.")
        print("Please copy .env.example to .env and configure your Supabase credentials.")
        return False
    return True

def get_churn_risk(score: float) -> str:
    """Classify churn score into risk category."""
    if score >= 0.75:
        return "CRITICAL"
    elif score >= 0.50:
        return "HIGH"
    elif score >= 0.25:
        return "MEDIUM"
    else:
        return "LOW"

def get_city_language(city: str) -> str:
    """Correlate language with city based on demographical weightings."""
    roll = random.random()
    if city == "Hyderabad":
        return "Telugu" if roll < 0.60 else "Hindi"
    elif city == "Chennai":
        return "Tamil" if roll < 0.80 else "English"
    elif city == "Bangalore":
        return "Kannada" if roll < 0.60 else "English"
    elif city == "Mumbai":
        if roll < 0.50:
            return "Marathi"
        elif roll < 0.80:
            return "Hindi"
        else:
            return "English"
    else: # Delhi
        return "Hindi" if roll < 0.90 else "English"

def seed_database():
    if not check_env():
        sys.exit(1)

    print("Connecting to Supabase Admin Client...")
    try:
        supabase = get_supabase_admin()
    except Exception as e:
        print(f"Error initializing Supabase client: {e}")
        sys.exit(1)

    # 1. Idempotency Check: check if data already exists
    try:
        res = supabase.table("staff").select("staff_id", count="exact").limit(1).execute()
        if res.count > 0:
            print("Database already contains records. Proceeding with UPSERT to update state.")
            # return
    except Exception as e:
        print(f"Database table check failed (tables might not be created yet): {e}")
        print("Please run data/supabase_schema.sql in your Supabase SQL editor first.")
        sys.exit(1)

    print("Starting database seeding...")
    fake = Faker("en_IN")

    # ━━━ SEED STAFF (3 Members) ━━━
    print("Seeding hospital staff...")
    staff_data = [
        {
            "telegram_username": "staff1",
            "telegram_chat_id": "11111111",
            "email": "staff1@kims.org",
            "password": "staff123",
            "hospital": "KIMS Secunderabad",
            "role": "Coordinator",
            "auth_token": "11111111-1111-1111-1111-111111111111"
        },
        {
            "telegram_username": "staff2",
            "telegram_chat_id": "22222222",
            "email": "staff2@apollo.org",
            "password": "staff123",
            "hospital": "Apollo Banjara Hills",
            "role": "Staff",
            "auth_token": "22222222-2222-2222-2222-222222222222"
        },
        {
            "telegram_username": "staff3",
            "telegram_chat_id": "33333333",
            "email": "staff3@bloodwarriors.org",
            "password": "staff123",
            "hospital": "Blood Warriors HQ",
            "role": "Admin",
            "auth_token": "33333333-3333-3333-3333-333333333333"
        }
    ]
    supabase.table("staff").upsert(staff_data, on_conflict="telegram_username").execute()
    print(f"Inserted {len(staff_data)} staff records.")

    # ━━━ SEED PATIENTS (50 Members) ━━━
    print("Seeding patients...")
    hospitals = [
        ("KIMS Secunderabad", "Secunderabad", 17.4480, 78.4982),
        ("Apollo Banjara Hills", "Banjara Hills", 17.4316, 78.4558),
        ("Yashoda Secunderabad", "Secunderabad", 17.4600, 78.5000),
        ("Nizam's Institute", "Punjagutta", 17.4065, 78.4772),
        ("Care Hospitals", "Gachibowli", 17.4435, 78.3772)
    ]
    blood_types = ["O+", "O-", "A+", "A-", "B+", "B-", "AB+", "AB-"]
    patient_ids = []
    patient_records = []
    transfusion_schedule_records = []

    today = date.today()

    for i in range(50):
        p_id = f"P-{10000 + i}"
        patient_ids.append(p_id)
        
        # Clinical parameters
        tx_count = random.randint(10, 250)
        hgb = round(random.uniform(4.0, 8.5), 1)
        age = random.randint(3, 18)
        
        # Allo-antibodies: if >20 transfusions, 40% probability of minor antigen mismatch sensitization
        kell_neg = False
        duffy_neg = False
        kidd_neg = False
        rh_e = False
        rh_c = False
        mns = False
        
        if tx_count > 20:
            kell_neg = random.random() < 0.40
            duffy_neg = random.random() < 0.40
            kidd_neg = random.random() < 0.40
            rh_e = random.random() < 0.40
            rh_c = random.random() < 0.40
            mns = random.random() < 0.40

        hosp_choice = random.choice(hospitals)
        blood_choice = random.choice(blood_types)
        
        # Urgency classification
        status = "STABLE"
        if hgb < 6.0:
            status = "CRITICAL"
        elif random.random() < 0.3:
            status = "OVERDUE"

        pat = {
            "patient_id": p_id,
            "name": f"patient{i+1}",
            "phone": f"+919{random.randint(100000000, 999999999)}",
            "password": "patient123",
            "age": age,
            "blood_type": blood_choice,
            "hospital": hosp_choice[0],
            "ward": "Thalassemia Day Care",
            "city": "Hyderabad",
            "hemoglobin": hgb,
            "transfusion_count": tx_count,
            "next_transfusion_due": str(today + timedelta(days=random.randint(-5, 10))),
            "antibody_kell": kell_neg,
            "antibody_duffy": duffy_neg,
            "antibody_kidd": kidd_neg,
            "antibody_rh_e": rh_e,
            "antibody_rh_c": rh_c,
            "antibody_mns": mns,
            "kell_negative": kell_neg,
            "status": status,
            "is_active": True,
            "coordinator_id": "11111111-1111-1111-1111-111111111111"
        }
        patient_records.append(pat)

        # Transfusion Schedule (3 upcoming dates: due in 3, 25, and 50 days)
        for offset in [3, 25, 50]:
            transfusion_schedule_records.append({
                "patient_id": p_id,
                "scheduled_date": str(today + timedelta(days=offset)),
                "advance_days": 5,
                "hospital": hosp_choice[0],
                "blood_type": blood_choice,
                "status": "PENDING",
                "created_by": "11111111-1111-1111-1111-111111111111"
            })

    supabase.table("patients").upsert(patient_records).execute()
    supabase.table("transfusion_schedule").upsert(transfusion_schedule_records).execute()
    print(f"Inserted {len(patient_records)} patient records and {len(transfusion_schedule_records)} schedule entries.")

    # ━━━ SEED DONORS (500 Members) ━━━
    print("Seeding 500 donors, memory log, and consent audit logs...")
    cities_weight = [
        ("Hyderabad", 0.40, 17.4065, 78.4772),
        ("Mumbai", 0.20, 19.0760, 72.8777),
        ("Chennai", 0.15, 13.0827, 80.2707),
        ("Bangalore", 0.15, 12.9716, 77.5946),
        ("Delhi", 0.10, 28.6139, 77.2090)
    ]
    
    donors_list = []
    consent_list = []
    memory_list = []
    verifications_list = []
    gamification_list = []

    for d_idx in range(500):
        # Pick city based on weights
        city_roll = random.random()
        cumulative = 0.0
        selected_city = cities_weight[0]
        for cw in cities_weight:
            cumulative += cw[1]
            if city_roll <= cumulative:
                selected_city = cw
                break
        
        city_name, _, base_lat, base_lng = selected_city
        
        # Local offset for coordinates
        lat = base_lat + random.uniform(-0.15, 0.15)
        lng = base_lng + random.uniform(-0.15, 0.15)
        
        # Phenotypes (Indian distribution: 92% Kell-neg, 68% Duffy-neg, 74% Kidd-neg)
        kell_neg = random.random() < 0.92
        duffy_neg = random.random() < 0.68
        kidd_neg = random.random() < 0.74
        
        # Other minor subtypes
        rh_e_neg = random.random() < 0.50
        rh_c_neg = random.random() < 0.50
        mns_neg = random.random() < 0.50

        # Blood types distribution: O+(38%) B+(32%) A+(21%) AB+(9%), negatives at 15% each
        type_roll = random.random()
        if type_roll < 0.38:
            base_type = "O"
        elif type_roll < 0.70:
            base_type = "B"
        elif type_roll < 0.91:
            base_type = "A"
        else:
            base_type = "AB"
            
        rh_factor = "-" if random.random() < 0.15 else "+"
        blood_type = f"{base_type}{rh_factor}"
        
        # Churn score: Beta distribution
        churn_score = round(random.betavariate(2, 5), 2)
        churn_risk = get_churn_risk(churn_score)
        
        lang = get_city_language(city_name)
        
        # Donation stats
        never_donated = random.random() < 0.30
        if never_donated:
            donation_count = 0
            lives_saved = 0
            last_date = None
        else:
            donation_count = random.choices([1,2,3,4,5, 10, 15, 20, 25], weights=[0.2, 0.2, 0.2, 0.15, 0.1, 0.05, 0.04, 0.03, 0.03])[0]
            lives_saved = donation_count
            last_date = str(today - timedelta(days=random.randint(10, 365)))

        d_id = f"D-{50000 + d_idx}"
        phone = f"9{random.randint(100000000, 999999999)}"
        tg_username = f"tg_donor_{d_idx}"
        name = f"donor{d_idx+1}"

        donor = {
            "donor_id": d_id,
            "telegram_chat_id": str(100000000 + d_idx),
            "phone": phone,
            "password": "donor123",
            "name": name,
            "blood_type": blood_type,
            "city": city_name,
            "ward": "Ward No " + str(random.randint(1, 30)),
            "lat": lat,
            "lng": lng,
            "kell_negative": kell_neg,
            "duffy_negative": duffy_neg,
            "kidd_negative": kidd_neg,
            "rh_e_negative": rh_e_neg,
            "rh_c_negative": rh_c_neg,
            "mns_negative": mns_neg,
            "hemoglobin": round(random.uniform(11.5, 16.5), 1),
            "last_donation_date": last_date,
            "medical_hold": False,
            "donation_count": donation_count,
            "lives_saved": lives_saved,
            "response_rate": round(random.uniform(0.4, 0.98), 2),
            "preferred_language": lang,
            "churn_score": churn_score,
            "churn_risk": churn_risk,
            "is_active": True,
            "consent_data_storage": True,
            "consent_outreach": True,
            "consent_granted_at": datetime.now().isoformat()
        }
        donors_list.append(donor)

        # Pre-consented logs (data_storage + outreach_telegram + outreach_sms)
        for consent_type in ["data_storage", "outreach_telegram", "outreach_sms"]:
            consent_list.append({
                "donor_id": d_id,
                "consent_type": consent_type,
                "action": "granted",
                "granted_at": datetime.now().isoformat(),
                "channel": "staff_manual",
                "language": "en",
                "consent_text_hash": hashlib_sha256("demo_seed_pre_consented"),
                "ip_hash": hashlib_sha256("127.0.0.1")
            })

        # Verification record for Kell Negative Donors (70% lab_confirmed, 30% self_reported)
        if kell_neg:
            is_lab = random.random() < 0.70
            verifications_list.append({
                "donor_id": d_id,
                "antigen_flag": "kell_negative",
                "flag_value": True,
                "verification_type": "lab_confirmed" if is_lab else "self_reported",
                "confidence": 0.95 if is_lab else 0.70,
                "source_document": "Lab_Certificate_Kell.pdf" if is_lab else "Self_Declaration",
                "verified_by": "dr_priya_kims" if is_lab else None,
                "notes": "Verified automatically during seeding."
            })

        # Gamification logs for top donors (milestone badges)
        if donation_count >= 1:
            gamification_list.append({
                "donor_id": d_id,
                "badge_name": "Blood Starter",
                "badge_emoji": "🌱",
                "threshold": 1,
                "awarded_at": (datetime.now() - timedelta(days=20)).isoformat(),
                "notified": True
            })
        if donation_count >= 5:
            gamification_list.append({
                "donor_id": d_id,
                "badge_name": "Life Saver",
                "badge_emoji": "❤️",
                "threshold": 5,
                "awarded_at": (datetime.now() - timedelta(days=10)).isoformat(),
                "notified": True
            })
        if donation_count >= 10:
            gamification_list.append({
                "donor_id": d_id,
                "badge_name": "Blood Hero",
                "badge_emoji": "🦸",
                "threshold": 10,
                "awarded_at": (datetime.now() - timedelta(days=2)).isoformat(),
                "notified": True
            })

        # Donor memory entries
        memory_list.append({
            "donor_id": d_id,
            "preferred_language": lang,
            "tone_profile": random.choice(["warm", "motivational", "urgent"]),
            "emotional_anchors": ["saved a child", "frequent donor"] if donation_count > 5 else ["first timer"],
            "last_interaction": datetime.now().isoformat(),
            "total_interactions": donation_count * 2,
            "streak_days": random.randint(0, 15),
            "impact_story": "You helped a Thalassemia child receive their monthly transfusion." if donation_count > 0 else None,
            "last_story_date": last_date
        })

    # Batch insert to avoid rate limits / timeouts (batches of 100)
    batch_size = 100
    for i in range(0, len(donors_list), batch_size):
        supabase.table("donors").upsert(donors_list[i:i+batch_size]).execute()
    print(f"Inserted {len(donors_list)} donor records.")

    for i in range(0, len(consent_list), batch_size * 2):
        supabase.table("consent_records").upsert(consent_list[i:i+(batch_size*2)]).execute()
    print(f"Inserted {len(consent_list)} consent logs.")

    for i in range(0, len(memory_list), batch_size):
        supabase.table("donor_memory").upsert(memory_list[i:i+batch_size]).execute()
    print(f"Inserted {len(memory_list)} donor memory logs.")

    if verifications_list:
        for i in range(0, len(verifications_list), batch_size):
            supabase.table("donor_verifications").upsert(verifications_list[i:i+batch_size]).execute()
        print(f"Inserted {len(verifications_list)} donor verification certificates.")

    if gamification_list:
        for i in range(0, len(gamification_list), batch_size):
            supabase.table("gamification").upsert(gamification_list[i:i+batch_size]).execute()
        print(f"Inserted {len(gamification_list)} badge milestones.")

    print("Database seeding completed successfully.")

def hashlib_sha256(text: str) -> str:
    """Generate simple SHA256 hex string."""
    import hashlib
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

if __name__ == "__main__":
    seed_database()
