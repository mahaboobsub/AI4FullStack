"""
BloodBridge AI — 3-Phone Demo Seed (UPDATED)

Phone assignment:
  7075899966 → Donor 1  / D-THREE-001 (B+, Kell-negative, ring-1 ~0.3km)
  9642273274 → Donor 2  / D-THREE-002 (O+, universal, Kell-neg, ring-1 ~0.5km)
  6305589656 → Patient  / P-THREE-001 (B+, antibody_kell=True → needs Kell-neg)

Also seeds 6 background donors (D-BGND-001..006) with varied antigens for
Hungarian optimizer and leaderboard showcase.

Bot: @ummedrakho_bot
City: Hyderabad · Hospital: KIMS Secunderabad (17.4480, 78.4982)

Usage:
    cd BloodBridge_AI_Backend
    python -m data.seed_three_phones

Set THREE_PHONE_DEMO_MODE=true in .env after seeding.
"""
import asyncio
from datetime import datetime, date, timezone, timedelta

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
    is_valid_telegram_chat_id,
)

# ── Patient ────────────────────────────────────────────────────────────────────
# Phone 3 (6305589656) is the patient.
# B+ with anti-Kell antibody → the system MUST find Kell-negative donors.
DEMO_PATIENT = {
    "patient_id":           DEMO_PATIENT_ID,   # P-THREE-001
    "name":                 "Ravi Kumar (Patient)",
    "phone":                DEMO_PATIENT_PHONE, # +916305589656
    "age":                  14,
    "blood_type":           DEMO_BLOOD_TYPE,    # B+
    "hospital":             DEMO_HOSPITAL,
    "ward":                 "Thalassemia Day Care",
    "city":                 DEMO_CITY,
    "lat":                  DEMO_LAT,           # 17.4480
    "lng":                  DEMO_LNG,           # 78.4982
    "hemoglobin":           7.5,
    "transfusion_count":    22,
    "next_transfusion_due": (date.today() + timedelta(days=3)).isoformat(),
    "status":               "CRITICAL",
    "is_active":            True,
    # Antigen antibody flags — patient developed anti-Kell from previous transfusions
    "antibody_kell":        True,   # MUST have Kell-neg donors
    "antibody_duffy":       False,
    "antibody_kidd":        False,
    "antibody_rh_e":        False,
    "antibody_rh_c":        False,
    "antibody_mns":         False,
    "kell_negative":        True,   # Patient is Kell-antigen negative (sensitized)
}

# ── Demo donors (real phones) ──────────────────────────────────────────────────
# Donor 1 (7075899966): B+, Kell-negative → PERFECT match for anti-Kell patient
# Donor 2 (9642273274): O+, Kell-negative → universal donor, also safe
DEMO_DONORS = [
    {
        "donor_id":            DEMO_DONOR_IDS[0],  # D-THREE-001
        "name":                "Sheik Bhai",
        "phone":               DEMO_DONOR_PHONES[0],  # +917075899966
        "blood_type":          "B+",
        "city":                DEMO_CITY,
        "lat":                 DEMO_LAT + 0.003,   # ~0.3km north — Ring 1
        "lng":                 DEMO_LNG + 0.002,
        # Full antigen panel — Kell-negative is the critical flag
        "kell_negative":       True,   # Safe for anti-Kell patient ✓
        "duffy_negative":      True,
        "kidd_negative":       False,
        "rh_e_negative":       True,
        "rh_c_negative":       False,
        "mns_negative":        False,
        "hemoglobin":          14.2,
        "donation_count":      12,
        "lives_saved":         12,
        "response_rate":       0.95,
        "churn_score":         0.08,
        "churn_risk":          "LOW",
        "is_active":           True,
        "consent_outreach":    True,
        "consent_data_storage": True,
        "preferred_language":  "hi",
        "last_donation_date":  (date.today() - timedelta(days=90)).isoformat(),
    },
    {
        "donor_id":            DEMO_DONOR_IDS[1],  # D-THREE-002
        "name":                "Arjun Singh",
        "phone":               DEMO_DONOR_PHONES[1],  # +919642273274
        "blood_type":          "O+",   # Universal donor
        "city":                DEMO_CITY,
        "lat":                 DEMO_LAT - 0.005,   # ~0.5km south — Ring 1
        "lng":                 DEMO_LNG + 0.003,
        # Full antigen panel
        "kell_negative":       True,   # Safe for anti-Kell patient ✓
        "duffy_negative":      False,
        "kidd_negative":       True,
        "rh_e_negative":       False,
        "rh_c_negative":       True,
        "mns_negative":        True,
        "hemoglobin":          13.8,
        "donation_count":      8,
        "lives_saved":         8,
        "response_rate":       0.88,
        "churn_score":         0.12,
        "churn_risk":          "LOW",
        "is_active":           True,
        "consent_outreach":    True,
        "consent_data_storage": True,
        "preferred_language":  "en",
        "last_donation_date":  (date.today() - timedelta(days=70)).isoformat(),
    },
]

# ── Background donors (no real phones, for rich UI showcase) ──────────────────
# These show up on the Donors list, leaderboard, Hungarian optimizer, and graph.
BACKGROUND_DONORS = [
    {
        "donor_id": "D-BGND-001", "name": "Lakshmi Devi", "phone": None,
        "blood_type": "O-", "city": DEMO_CITY,
        "lat": DEMO_LAT + 0.020, "lng": DEMO_LNG - 0.015,  # Ring 1
        "kell_negative": True, "duffy_negative": True, "kidd_negative": True,
        "rh_e_negative": True, "rh_c_negative": True, "mns_negative": False,
        "hemoglobin": 13.1, "donation_count": 20, "lives_saved": 20,
        "response_rate": 0.97, "churn_score": 0.05, "churn_risk": "LOW",
        "is_active": True, "consent_outreach": True,
        "last_donation_date": (date.today() - timedelta(days=120)).isoformat(),
        "preferred_language": "te",
    },
    {
        "donor_id": "D-BGND-002", "name": "Rahul Verma", "phone": None,
        "blood_type": "B-", "city": DEMO_CITY,
        "lat": DEMO_LAT - 0.012, "lng": DEMO_LNG + 0.018,  # Ring 1
        "kell_negative": True, "duffy_negative": False, "kidd_negative": True,
        "rh_e_negative": False, "rh_c_negative": False, "mns_negative": False,
        "hemoglobin": 14.5, "donation_count": 14, "lives_saved": 14,
        "response_rate": 0.90, "churn_score": 0.15, "churn_risk": "LOW",
        "is_active": True, "consent_outreach": True,
        "last_donation_date": (date.today() - timedelta(days=65)).isoformat(),
        "preferred_language": "hi",
    },
    {
        "donor_id": "D-BGND-003", "name": "Fatima Begum", "phone": None,
        "blood_type": "B+", "city": DEMO_CITY,
        "lat": DEMO_LAT + 0.040, "lng": DEMO_LNG - 0.030,  # Ring 2
        "kell_negative": False, "duffy_negative": True, "kidd_negative": False,
        "rh_e_negative": True, "rh_c_negative": False, "mns_negative": True,
        "hemoglobin": 12.8, "donation_count": 11, "lives_saved": 11,
        "response_rate": 0.92, "churn_score": 0.18, "churn_risk": "LOW",
        "is_active": True, "consent_outreach": True,
        "last_donation_date": (date.today() - timedelta(days=80)).isoformat(),
        "preferred_language": "hi",
    },
    {
        "donor_id": "D-BGND-004", "name": "Suresh Kumar", "phone": None,
        "blood_type": "A+", "city": DEMO_CITY,
        "lat": DEMO_LAT - 0.060, "lng": DEMO_LNG + 0.045,  # Ring 2
        "kell_negative": False, "duffy_negative": False, "kidd_negative": False,
        "rh_e_negative": False, "rh_c_negative": False, "mns_negative": False,
        "hemoglobin": 15.0, "donation_count": 6, "lives_saved": 5,
        "response_rate": 0.75, "churn_score": 0.35, "churn_risk": "MEDIUM",
        "is_active": True, "consent_outreach": True,
        "last_donation_date": (date.today() - timedelta(days=200)).isoformat(),
        "preferred_language": "te",
    },
    {
        "donor_id": "D-BGND-005", "name": "Priya Reddy", "phone": None,
        "blood_type": "AB-", "city": DEMO_CITY,
        "lat": DEMO_LAT + 0.090, "lng": DEMO_LNG + 0.060,  # Ring 2
        "kell_negative": True, "duffy_negative": True, "kidd_negative": True,
        "rh_e_negative": True, "rh_c_negative": True, "mns_negative": True,
        "hemoglobin": 13.4, "donation_count": 3, "lives_saved": 3,
        "response_rate": 0.80, "churn_score": 0.42, "churn_risk": "MEDIUM",
        "is_active": True, "consent_outreach": True,
        "last_donation_date": (date.today() - timedelta(days=60)).isoformat(),
        "preferred_language": "en",
    },
    {
        "donor_id": "D-BGND-006", "name": "Ravi Teja", "phone": None,
        "blood_type": "O+", "city": DEMO_CITY,
        "lat": DEMO_LAT - 0.110, "lng": DEMO_LNG - 0.080,  # Ring 3 (wide net)
        "kell_negative": False, "duffy_negative": False, "kidd_negative": False,
        "rh_e_negative": False, "rh_c_negative": False, "mns_negative": False,
        "hemoglobin": 14.0, "donation_count": 1, "lives_saved": 1,
        "response_rate": 0.50, "churn_score": 0.72, "churn_risk": "HIGH",
        "is_active": True, "consent_outreach": True,
        "last_donation_date": (date.today() - timedelta(days=400)).isoformat(),
        "preferred_language": "te",
    },
]

# ── Second patient for Hungarian optimizer showcase ────────────────────────────
PATIENT_2 = {
    "patient_id":           "P-THREE-002",
    "name":                 "Ananya Iyer (Patient 2)",
    "phone":                None,
    "age":                  9,
    "blood_type":           "O-",
    "hospital":             "Apollo Banjara Hills",
    "ward":                 "Pediatric Hematology",
    "city":                 DEMO_CITY,
    "lat":                  17.4126,
    "lng":                  78.4482,
    "hemoglobin":           6.8,
    "transfusion_count":    45,
    "next_transfusion_due": (date.today() + timedelta(days=7)).isoformat(),
    "status":               "CRITICAL",
    "is_active":            True,
    "antibody_kell":        False,
    "antibody_duffy":       True,   # needs Duffy-negative
    "antibody_kidd":        False,
    "antibody_rh_e":        False,
    "antibody_rh_c":        False,
    "antibody_mns":         False,
    "kell_negative":        False,
}


# ── Helpers ────────────────────────────────────────────────────────────────────

def _clear_telegram_conflict(supabase, chat_id: str, keep_donor_id: str):
    if not chat_id:
        return
    conflicts = supabase.table("donors").select("donor_id").eq("telegram_chat_id", str(chat_id)).execute()
    for row in conflicts.data or []:
        if row["donor_id"] != keep_donor_id:
            supabase.table("donors").update({"telegram_chat_id": None}).eq("donor_id", row["donor_id"]).execute()


def _find_telegram_chat_id(supabase, phone: str):
    norm = normalize_phone(phone)
    for table in ("donors", "patients", "staff"):
        try:
            res = supabase.table(table).select("telegram_chat_id").eq("phone", norm).execute()
            for row in res.data or []:
                cid = row.get("telegram_chat_id")
                if is_valid_telegram_chat_id(cid):
                    return str(cid)
            alt = norm.replace("+91", "")
            res2 = supabase.table(table).select("telegram_chat_id").like("phone", f"%{alt}").execute()
            for row in res2.data or []:
                cid = row.get("telegram_chat_id")
                if is_valid_telegram_chat_id(cid):
                    return str(cid)
        except Exception:
            pass
    return None


def _migrate_phone_to_donor(supabase, phone: str, target_donor_id: str):
    norm = normalize_phone(phone)
    existing = supabase.table("donors").select("donor_id, telegram_chat_id").eq("phone", norm).execute()
    chat_id = None
    for row in existing.data or []:
        cid = row.get("telegram_chat_id")
        if is_valid_telegram_chat_id(cid):
            chat_id = str(cid)
        if row["donor_id"] != target_donor_id:
            supabase.table("donors").update({"is_active": False, "telegram_chat_id": None, "phone": None}).eq("donor_id", row["donor_id"]).execute()
    if not chat_id:
        chat_id = _find_telegram_chat_id(supabase, phone)
    if chat_id:
        _clear_telegram_conflict(supabase, chat_id, target_donor_id)
    return chat_id


def _upsert(supabase, table: str, pk_field: str, pk_value: str, row: dict):
    existing = supabase.table(table).select(pk_field).eq(pk_field, pk_value).execute()
    if existing.data:
        supabase.table(table).update(row).eq(pk_field, pk_value).execute()
        return "updated"
    supabase.table(table).insert(row).execute()
    return "created"


# ── Main seed ──────────────────────────────────────────────────────────────────

async def seed_three_phones():
    from core.database import get_supabase_admin
    from services.consent_service import ConsentService

    supabase = get_supabase_admin()
    now = datetime.now(timezone.utc).isoformat()

    print("BloodBridge - 3-Phone Demo Seed (v2)")
    print("=" * 55)
    print(f"  Phone 1 (Donor 1)  : {DEMO_DONOR_PHONES[0]} -> {DEMO_DONOR_IDS[0]} B+ Kell-neg")
    print(f"  Phone 2 (Donor 2)  : {DEMO_DONOR_PHONES[1]} -> {DEMO_DONOR_IDS[1]} O+ Kell-neg")
    print(f"  Phone 3 (Patient)  : {DEMO_PATIENT_PHONE} -> {DEMO_PATIENT_ID}  B+ anti-Kell")
    print(f"  Bot                : @ummedrakho_bot")
    print(f"  City               : {DEMO_CITY} | Hospital: {DEMO_HOSPITAL}")
    print()

    # ── 1. Deactivate non-demo donors (keep background donors active) ──────────
    print("  [1/7] Deactivating old conflicting donors...")
    all_donors = supabase.table("donors").select("donor_id").execute()
    keep_ids = set(DEMO_DONOR_IDS + [d["donor_id"] for d in BACKGROUND_DONORS])
    deactivated = 0
    for row in all_donors.data or []:
        if row["donor_id"] not in keep_ids:
            supabase.table("donors").update({"is_active": False}).eq("donor_id", row["donor_id"]).execute()
            deactivated += 1
    print(f"      Deactivated {deactivated} old donor(s)")

    # ── 2. Upsert patient (phone 3) ────────────────────────────────────────────
    print("  [2/7] Seeding patient (Phone 3 -> P-THREE-001)...")
    patient_chat = _find_telegram_chat_id(supabase, DEMO_PATIENT_PHONE)
    patient_row = {**DEMO_PATIENT}
    if patient_chat:
        patient_row["password"] = f"tg:{patient_chat}"
        print(f"      Linked Telegram chat_id: {patient_chat}")
    action = _upsert(supabase, "patients", "patient_id", DEMO_PATIENT_ID, patient_row)
    print(f"      {action} {DEMO_PATIENT_ID}")

    # patient_location row
    try:
        supabase.table("patient_locations").upsert({
            "patient_id": DEMO_PATIENT_ID,
            "label": "KIMS Secunderabad",
            "lat": DEMO_LAT, "lng": DEMO_LNG,
            "is_primary": True, "priority_order": 1,
        }).execute()
    except Exception:
        pass

    # ── 3. Upsert 2nd patient for Hungarian optimizer ──────────────────────────
    print("  [3/7] Seeding 2nd patient for Hungarian optimizer...")
    _upsert(supabase, "patients", "patient_id", "P-THREE-002", PATIENT_2)
    try:
        supabase.table("patient_locations").upsert({
            "patient_id": "P-THREE-002",
            "label": "Apollo Banjara Hills",
            "lat": 17.4126, "lng": 78.4482,
            "is_primary": True, "priority_order": 1,
        }).execute()
    except Exception:
        pass
    print("      Created P-THREE-002 (O- anti-Duffy @ Apollo Banjara Hills)")

    # ── 4. Upsert 2 real-phone donors ─────────────────────────────────────────
    print("  [4/7] Seeding 2 real-phone donors...")
    for donor in DEMO_DONORS:
        chat_id = _migrate_phone_to_donor(supabase, donor["phone"], donor["donor_id"])
        row = {**donor, "consent_granted_at": now, "is_active": True}
        if chat_id:
            row["telegram_chat_id"] = chat_id
        else:
            row["telegram_chat_id"] = None
        action = _upsert(supabase, "donors", "donor_id", donor["donor_id"], row)
        tg_note = f"Telegram:{chat_id}" if chat_id else "no Telegram yet (will link on /start)"
        print(f"      {action} {donor['donor_id']} ({donor['name']}) [{tg_note}]")

        supabase.table("donor_memory").upsert({
            "donor_id": donor["donor_id"],
            "preferred_language": donor.get("preferred_language", "en"),
            "badges": ["life_saver", "rapid_responder"],
            "streak_days": donor.get("donation_count", 0) * 30,
            "total_interactions": donor.get("donation_count", 0),
            "impact_story": f"{donor['name']} donated and saved {donor['lives_saved']} lives through BloodBridge AI.",
        }).execute()

        await ConsentService.grant_consent(
            donor["donor_id"],
            ["data_storage", "outreach_telegram", "outreach_voice", "outreach_sms"],
            channel="seed_three_phones",
            language=donor.get("preferred_language", "en"),
        )
        donor["_telegram_chat_id"] = chat_id

    # ── 5. Upsert 6 background donors ─────────────────────────────────────────
    print("  [5/7] Seeding 6 background donors for rich UI...")
    for d in BACKGROUND_DONORS:
        row = {**d, "consent_granted_at": now, "consent_data_storage": True}
        action = _upsert(supabase, "donors", "donor_id", d["donor_id"], row)
        supabase.table("donor_memory").upsert({
            "donor_id": d["donor_id"],
            "preferred_language": d.get("preferred_language", "en"),
            "badges": ["life_saver"] if d["donation_count"] >= 5 else [],
            "streak_days": d["donation_count"] * 20,
            "total_interactions": d["donation_count"],
        }).execute()
        await ConsentService.grant_consent(
            d["donor_id"], ["data_storage", "outreach_telegram", "outreach_voice"],
            channel="seed_bg", language=d.get("preferred_language", "en"),
        )
        print(f"      {action} {d['donor_id']} ({d['name']}, {d['blood_type']})")

    # ── 6. Leaderboard cache ───────────────────────────────────────────────────
    print("  [6/7] Building leaderboard cache...")
    all_for_lb = DEMO_DONORS + BACKGROUND_DONORS
    sorted_by_lives = sorted(all_for_lb, key=lambda x: x["lives_saved"], reverse=True)
    for idx, d in enumerate(sorted_by_lives):
        try:
            supabase.table("leaderboard_cache").upsert({
                "donor_id": d["donor_id"],
                "city": d["city"],
                "lives_saved": d["lives_saved"],
                "rank": idx + 1,
                "month_year": datetime.now().strftime("%Y-%m"),
            }).execute()
        except Exception:
            pass
    print(f"      Ranked {len(sorted_by_lives)} donors")

    # ── 7. Neo4j — full antigen edges ──────────────────────────────────────────
    print("  [7/7] Seeding Neo4j with antigen-aware COMPATIBLE_WITH edges...")
    try:
        from core.neo4j_client import get_driver
        from ml.antigen_scorer import compute_antigen_score
        driver = get_driver()
        if driver:
            async with driver.session() as session:
                # Create/update both patients
                for pat in [DEMO_PATIENT, PATIENT_2]:
                    await session.run(
                        """
                        MERGE (p:Patient {patient_id: $pid})
                        SET p.name = $name, p.blood_type = $bt, p.city = $city,
                            p.lat = $lat, p.lng = $lng,
                            p.antibody_kell = $ak, p.antibody_duffy = $ad,
                            p.antibody_kidd = $aki, p.antibody_rh_e = $are,
                            p.antibody_rh_c = $arc, p.antibody_mns = $amns,
                            p.kell_negative = $kn, p.hospital = $hosp
                        """,
                        pid=pat["patient_id"], name=pat["name"], bt=pat["blood_type"],
                        city=pat["city"], lat=pat["lat"], lng=pat["lng"],
                        ak=pat.get("antibody_kell", False),
                        ad=pat.get("antibody_duffy", False),
                        aki=pat.get("antibody_kidd", False),
                        are=pat.get("antibody_rh_e", False),
                        arc=pat.get("antibody_rh_c", False),
                        amns=pat.get("antibody_mns", False),
                        kn=pat.get("kell_negative", False),
                        hosp=pat["hospital"],
                    )

                # Create/update all donors (real phones + background)
                all_donors_neo = DEMO_DONORS + BACKGROUND_DONORS
                for donor in all_donors_neo:
                    await session.run(
                        """
                        MERGE (d:Donor {donor_id: $did})
                        SET d.name = $name, d.blood_type = $bt, d.city = $city,
                            d.lat = $lat, d.lng = $lng, d.is_active = true,
                            d.kell_negative = $kn, d.duffy_negative = $dn,
                            d.kidd_negative = $kin, d.rh_e_negative = $ren,
                            d.rh_c_negative = $rcn, d.mns_negative = $mn,
                            d.phone = $phone, d.churn_score = $churn,
                            d.donation_count = $dc, d.lives_saved = $ls,
                            d.preferred_language = $lang,
                            d.telegram_chat_id = $tg
                        """,
                        did=donor["donor_id"], name=donor["name"],
                        bt=donor["blood_type"], city=donor["city"],
                        lat=donor["lat"], lng=donor["lng"],
                        kn=donor.get("kell_negative", False),
                        dn=donor.get("duffy_negative", False),
                        kin=donor.get("kidd_negative", False),
                        ren=donor.get("rh_e_negative", False),
                        rcn=donor.get("rh_c_negative", False),
                        mn=donor.get("mns_negative", False),
                        phone=donor.get("phone"),
                        churn=donor.get("churn_score", 0.3),
                        dc=donor.get("donation_count", 0),
                        ls=donor.get("lives_saved", 0),
                        lang=donor.get("preferred_language", "en"),
                        tg=donor.get("_telegram_chat_id"),
                    )

                    # Compute real antigen score for BOTH patients
                    for pat in [DEMO_PATIENT, PATIENT_2]:
                        try:
                            score = compute_antigen_score(donor, pat)
                        except Exception:
                            score = 0.8

                        if score > 0.0:
                            await session.run(
                                """
                                MATCH (d:Donor {donor_id: $did}), (p:Patient {patient_id: $pid})
                                MERGE (d)-[r:COMPATIBLE_WITH]->(p)
                                SET r.antigen_score = $score,
                                    r.kell_safe = $kn, r.duffy_safe = $dn,
                                    r.kidd_safe = $kin, r.rh_e_safe = $ren,
                                    r.rh_c_safe = $rcn, r.mns_safe = $mn,
                                    r.last_computed = datetime()
                                """,
                                did=donor["donor_id"], pid=pat["patient_id"],
                                score=score,
                                kn=donor.get("kell_negative", False),
                                dn=donor.get("duffy_negative", False),
                                kin=donor.get("kidd_negative", False),
                                ren=donor.get("rh_e_negative", False),
                                rcn=donor.get("rh_c_negative", False),
                                mn=donor.get("mns_negative", False),
                            )
                            print(f"        COMPATIBLE_WITH {donor['donor_id']} → {pat['patient_id']} score={score:.2f}")

            print("      OK Neo4j antigen-aware edges created")
        else:
            print("      ⚠ Neo4j not reachable — matching falls back to Supabase geo engine")
    except Exception as e:
        print(f"      ⚠ Neo4j seed failed: {e}")

    print()
    print("=" * 55)
    print("OK Seed complete!\n")
    print("Next steps:")
    print("  1. Ensure THREE_PHONE_DEMO_MODE=true in .env")
    print("  2. Restart backend:  uvicorn main:app --reload")
    print()
    print("  Demo flow:")
    print(f"  a. Phone 3 (+916305589656) sends via @ummedrakho_bot:")
    print(f"     'Emergency B+ blood needed at KIMS Secunderabad Hyderabad'")
    print(f"  b. Phones 1 & 2 get Telegram alerts with YES/NO buttons")
    print(f"  c. If no reply in 1min -> Bolna AI calls Phone 1 (+917075899966)")
    print(f"  d. Reply YES -> chain CONFIRMED -> Dashboard updates live")
    print(f"  e. Track: /status {DEMO_PATIENT_ID}")
    print()
    print("  Dashboard URLs:")
    print("  - Emergency:  http://localhost:5173/dashboard/emergency")
    print("  - Graph:      http://localhost:5173/dashboard/graph")
    print("  - Admin:      http://localhost:5173/dashboard/admin")
    print(f"  - Patient:    http://localhost:5173/patient?id={DEMO_PATIENT_ID}")


if __name__ == "__main__":
    asyncio.run(seed_three_phones())
