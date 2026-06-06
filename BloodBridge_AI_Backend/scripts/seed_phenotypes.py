"""
Backfill ISBT antigen phenotype columns on donors and antibody flags on patients.
Run when antigen_scores are all 1.0 because phenotype data was never populated.

Usage:
    cd BloodBridge_AI_Backend
    python scripts/seed_phenotypes.py
"""
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.database import get_supabase_admin
from ml.antigen_scorer import compute_antigen_score

# Indian population distributions (approximate)
DONOR_PHENOTYPE_RATES = {
    "kell_negative": 0.92,
    "duffy_negative": 0.68,
    "kidd_negative": 0.74,
    "rh_e_negative": 0.50,
    "rh_c_negative": 0.50,
    "mns_negative": 0.50,
}

PATIENT_ANTIBODY_RATES = {
    "antibody_kell": 0.18,
    "antibody_duffy": 0.10,
    "antibody_kidd": 0.08,
    "antibody_rh_e": 0.06,
    "antibody_rh_c": 0.05,
    "antibody_mns": 0.04,
}


def _roll(flag_rates: dict) -> dict:
    return {k: random.random() < rate for k, rate in flag_rates.items()}


def seed_donor_phenotypes(sb, limit: int = 500) -> int:
    res = sb.table("donors").select("donor_id").limit(limit).execute()
    updated = 0
    for row in res.data or []:
        pheno = _roll(DONOR_PHENOTYPE_RATES)
        sb.table("donors").update(pheno).eq("donor_id", row["donor_id"]).execute()
        updated += 1
    return updated


def seed_patient_antibodies(sb, limit: int = 50) -> int:
    res = sb.table("patients").select("patient_id").limit(limit).execute()
    updated = 0
    for row in res.data or []:
        flags = _roll(PATIENT_ANTIBODY_RATES)
        # Patients with anti-Kell typically require Kell-negative blood
        flags["kell_negative"] = flags["antibody_kell"]
        sb.table("patients").update(flags).eq("patient_id", row["patient_id"]).execute()
        updated += 1
    return updated


def verify_antigen_variance(sb) -> None:
    """Print score distribution for a Kell-positive patient vs mixed donors."""
    patients = sb.table("patients").select("*").eq("antibody_kell", True).limit(1).execute()
    if not patients.data:
        patients = sb.table("patients").select("*").limit(1).execute()
    if not patients.data:
        print("  No patients to verify.")
        return

    patient = patients.data[0]
    donors = sb.table("donors").select("*").eq("city", patient.get("city", "Hyderabad")).limit(30).execute()
    scores = sorted(
        {compute_antigen_score(d, patient) for d in (donors.data or [])},
        reverse=True,
    )
    unique = sorted(set(scores), reverse=True)
    print(f"  Patient {patient['patient_id']} ({patient['blood_type']}) antibody_kell={patient.get('antibody_kell')}")
    print(f"  Antigen score spread (30 local donors): min={min(scores):.2f} max={max(scores):.2f} unique={len(unique)}")
    print(f"  Distinct values: {[round(s, 2) for s in unique[:8]]}{'...' if len(unique) > 8 else ''}")
    if len(unique) <= 1:
        print("  WARNING: All scores identical — re-run seed or check patient antibody flags.")
    else:
        print("  OK: Phenotype scoring is producing variance.")


def main() -> None:
    random.seed(42)
    sb = get_supabase_admin()
    print("Seeding donor ISBT phenotypes...")
    d_count = seed_donor_phenotypes(sb)
    print(f"  Updated {d_count} donors.")

    print("Seeding patient antibody flags...")
    p_count = seed_patient_antibodies(sb)
    print(f"  Updated {p_count} patients.")

    print("Verifying antigen score variance...")
    verify_antigen_variance(sb)
    print("Done.")


if __name__ == "__main__":
    main()
