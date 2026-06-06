"""
Seed bridges + bridge_memberships so the matcher's bridge_bonus (0.20) fires.

Run AFTER seed_supabase.py and schema_v5_bridges.sql.

Strategy (bridge_id == patient_id):
  - For the first N patients, create a 'bridges' row.
  - Attach 2-3 ABO-compatible, geographically-near donors as ACTIVE bridge members.
  - These donors then receive the bridge_bonus in matching_engine.rank_donors().

Usage:
    python data/seed_bridge_memberships.py
"""
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import get_settings
from core.database import get_supabase_admin
from services.geo_service import haversine_km

# Donor blood type -> recipient patient types (who this donor can give to)
COMPATIBILITY_MAP = {
    "O-": ["O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+"],
    "O+": ["O+", "A+", "B+", "AB+"],
    "A-": ["A-", "A+", "AB-", "AB+"],
    "A+": ["A+", "AB+"],
    "B-": ["B-", "B+", "AB-", "AB+"],
    "B+": ["B+", "AB+"],
    "AB-": ["AB-", "AB+"],
    "AB+": ["AB+"],
}

N_BRIDGE_PATIENTS = 20   # how many patients get a bridge
DONORS_PER_BRIDGE = 3    # bridge donors per patient
MAX_BRIDGE_KM = 30.0     # only attach donors within this radius


def compatible_donor_types(patient_blood_type: str) -> list:
    """Donor blood types that can safely donate to this patient."""
    return [dt for dt, recips in COMPATIBILITY_MAP.items() if patient_blood_type in recips]


def check_env() -> bool:
    settings = get_settings()
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_KEY:
        print("Error: SUPABASE_URL / SUPABASE_SERVICE_KEY missing. Configure .env first.")
        return False
    return True


def seed_bridges():
    if not check_env():
        sys.exit(1)

    supabase = get_supabase_admin()
    print("Fetching patients and donors...")

    patients = (supabase.table("patients").select("*").limit(N_BRIDGE_PATIENTS).execute().data) or []
    if not patients:
        print("No patients found. Run seed_supabase.py first.")
        sys.exit(1)

    all_donors = (supabase.table("donors").select(
        "donor_id, blood_type, lat, lng, is_active").eq("is_active", True).execute().data) or []
    if not all_donors:
        print("No donors found. Run seed_supabase.py first.")
        sys.exit(1)

    bridges_rows = []
    membership_rows = []

    for patient in patients:
        pid = patient["patient_id"]
        p_blood = patient.get("blood_type")
        p_lat, p_lng = patient.get("lat"), patient.get("lng")
        if p_lat is None or p_lng is None:
            continue

        compat = compatible_donor_types(p_blood)

        # Rank compatible donors by distance to the patient
        candidates = []
        for d in all_donors:
            if d.get("blood_type") not in compat:
                continue
            if d.get("lat") is None or d.get("lng") is None:
                continue
            dist = haversine_km(p_lat, p_lng, d["lat"], d["lng"])
            if dist <= MAX_BRIDGE_KM:
                candidates.append((dist, d["donor_id"]))

        candidates.sort(key=lambda x: x[0])
        chosen = candidates[:DONORS_PER_BRIDGE]
        if not chosen:
            continue

        bridges_rows.append({
            "bridge_id": pid,                      # bridge_id == patient_id
            "patient_id": pid,
            "blood_type": p_blood,
            "city": patient.get("city"),
            "next_expected_transfusion": patient.get("next_transfusion_due"),
            "frequency_days": 21,
            "status": "ACTIVE",
        })

        for _, donor_id in chosen:
            membership_rows.append({
                "bridge_id": pid,
                "donor_id": donor_id,
                "role": "BRIDGE_DONOR",
                "status": "ACTIVE",
            })

    if bridges_rows:
        supabase.table("bridges").upsert(bridges_rows, on_conflict="bridge_id").execute()
        print(f"Upserted {len(bridges_rows)} bridges.")

    if membership_rows:
        supabase.table("bridge_memberships").upsert(
            membership_rows, on_conflict="bridge_id,donor_id"
        ).execute()
        print(f"Upserted {len(membership_rows)} bridge memberships "
              f"(~{DONORS_PER_BRIDGE} donors x {len(bridges_rows)} patients).")

    print("Bridge seeding complete.")


if __name__ == "__main__":
    seed_bridges()
