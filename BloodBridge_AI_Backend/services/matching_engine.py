"""
Matching Engine for BloodBridge AI — Geo radius-tier + weighted scoring.
Replaces the naive Neo4j antigen-based matcher with a pure-Python geo-radius
search and NGO weighted scoring engine (M2).

Used by agents/neo4j_match.py — keeps the agent's outward interface unchanged.
"""

import logging
from datetime import date
from typing import List, Dict, Any
from core.database import get_supabase_admin
from services.geo_service import haversine_km, radius_buckets, neighbors
from ml.antigen_scorer import compute_antigen_score

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# TUNABLE WEIGHTS — adjust these to change ranking behavior
# ═══════════════════════════════════════════════════════════════════════════════
WEIGHTS = {
    "blood_match":          0.20,   # ABO+Rh exact match bonus
    "antigen_safety":       0.15,   # 8-antigen ISBT compatibility (Kell/Duffy/Kidd/Rh/MNS)
    "proximity":            0.25,   # 1 - dist/30
    "engagement":           0.20,   # calls_to_donations_ratio (inverted) + response_rate
    "eligibility_freshness":0.10,   # days since last donation (56d = peak)
    "churn_avoidance":      0.15,   # 1 - churn_score
    "radius_penalty":       0.10,   # subtracted for R3 donors
    "bridge_bonus":         0.20,   # bonus for Bridge Donors committed to THIS patient
}

# ABO+Rh universal compatibility map (donor → eligible recipients)
COMPATIBILITY_MAP = {
    "O-":  ["O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+"],
    "O+":  ["O+", "A+", "B+", "AB+"],
    "A-":  ["A-", "A+", "AB-", "AB+"],
    "A+":  ["A+", "AB+"],
    "B-":  ["B-", "B+", "AB-", "AB+"],
    "B+":  ["B+", "AB+"],
    "AB-": ["AB-", "AB+"],
    "AB+": ["AB+"],
}


def get_compatible_donor_types(patient_blood_type: str) -> List[str]:
    """Return all donor blood types that can safely donate to the given patient type."""
    compatible = []
    for donor_type, recipients in COMPATIBILITY_MAP.items():
        if patient_blood_type in recipients:
            compatible.append(donor_type)
    return compatible


def _engagement_score(donor: dict) -> float:
    """Normalized 0-1 engagement score from real NGO signals."""
    ratio = float(donor.get("calls_to_donations_ratio") or 1.0)
    response_rate = float(donor.get("response_rate") or 0.5)
    donations = int(donor.get("donation_count") or donor.get("donations_till_date") or 0)
    # Lower ratio = better (fewer calls per donation). Cap at 10.
    ratio_score = max(0.0, 1.0 - (ratio - 1.0) / 9.0) if ratio >= 1.0 else 1.0
    # Donations as a signal (cap at 20)
    donation_score = min(donations / 20.0, 1.0)
    return (ratio_score * 0.4) + (response_rate * 0.4) + (donation_score * 0.2)


def _eligibility_freshness(donor: dict) -> float:
    """Normalized 0-1 score. Peak at 56 days post-donation, decays toward 365."""
    last_date = donor.get("last_donation_date")
    if not last_date:
        return 1.0  # Never donated = fully eligible
    try:
        if isinstance(last_date, str):
            ld = date.fromisoformat(last_date[:10])
        else:
            ld = last_date.date() if hasattr(last_date, "date") else last_date
        days_since = (date.today() - ld).days
        if days_since < 56:
            return 0.0  # Ineligible — will be filtered out
        return max(0.0, 1.0 - (days_since - 56) / 309.0)
    except Exception:
        return 0.5


def rank_donors(patient_id: str, target: int = 8) -> dict:
    """
    Geo radius-tier search + weighted multi-criteria scoring.

    Returns:
        dict with 'primary' (top N donors) and 'wide_net' (R3 backups) lists.
        Each donor dict has: donor_id, name, telegram_chat_id, phone,
        preferred_language, churn_score, blood_type, distance_km,
        antigen_score (always 1.0), ring (1/2/3), match_score.
    """
    logger.info(f"MatchingEngine: ranking donors for patient {patient_id}")
    supabase = get_supabase_admin()

    # ── 1. Fetch patient + locations ──────────────────────────────────────────
    p_res = supabase.table("patients").select("*").eq("patient_id", patient_id).execute()
    if not p_res.data:
        logger.error(f"Patient {patient_id} not found")
        return {"primary": [], "wide_net": []}
    patient = p_res.data[0]

    # patient_locations is optional (schema_v4). Degrade gracefully if the table
    # is absent or empty by falling back to the patient's primary lat/lng.
    p_locs = []
    try:
        ploc_res = supabase.table("patient_locations").select("*").eq("patient_id", patient_id).execute()
        p_locs = ploc_res.data or []
    except Exception as e:
        logger.warning(f"patient_locations unavailable ({e}); falling back to patient lat/lng.")

    if not p_locs and patient.get("lat") and patient.get("lng"):
        p_locs = [{"lat": patient["lat"], "lng": patient["lng"],
                    "geohash": patient.get("geohash", "")}]
    if not p_locs:
        logger.error(f"Patient {patient_id} has no geo locations")
        return {"primary": [], "wide_net": []}

    # ── 2. Compatible blood types ─────────────────────────────────────────────
    compat_types = get_compatible_donor_types(patient["blood_type"])

    # ── 3. Fetch eligible donors ──────────────────────────────────────────────
    donors_q = supabase.table("donors")\
        .select("*")\
        .eq("is_active", True)\
        .in_("blood_type", compat_types)
    donors_res = donors_q.execute()
    all_donors = donors_res.data or []

    # Demo mode: only the 2 seeded donor phones participate in matching
    from services.demo_phones import is_demo_mode, is_demo_donor_record
    if is_demo_mode():
        all_donors = [d for d in all_donors if is_demo_donor_record(d)]
        logger.info(f"THREE_PHONE_DEMO_MODE: restricted to {len(all_donors)} demo donor(s)")

    # ── 4. Bridge membership bonus lookup ─────────────────────────────────────
    bridge_donor_ids = set()
    try:
        bm_res = supabase.table("bridge_memberships")\
            .select("donor_id").eq("bridge_id", patient_id).execute()
        bridge_donor_ids = {r["donor_id"] for r in (bm_res.data or [])}
    except Exception as e:
        logger.warning(f"bridge_memberships unavailable ({e}); bridge_bonus disabled.")

    buckets = radius_buckets()  # R1:5, R2:15, R3:30

    # ── 5. Score each donor ───────────────────────────────────────────────────
    scored = []
    for donor in all_donors:
        # 56-day eligibility filter
        last_dt = donor.get("last_donation_date")
        if last_dt:
            try:
                days = (date.today() - date.fromisoformat(str(last_dt)[:10])).days
                if days < 56:
                    continue
            except Exception:
                pass

        # Medical hold filter
        if donor.get("medical_hold"):
            continue

        # Best distance across all patient locations
        d_lat, d_lng = donor.get("lat"), donor.get("lng")
        best_dist = float("inf")
        if d_lat is not None and d_lng is not None:
            for pl in p_locs:
                d = haversine_km(pl["lat"], pl["lng"], d_lat, d_lng)
                if d < best_dist:
                    best_dist = d

        if best_dist > buckets["R3"]:
            continue  # Too far

        # Ring assignment
        if best_dist <= buckets["R1"]:
            ring = 1
        elif best_dist <= buckets["R2"]:
            ring = 2
        else:
            ring = 3

        # Component scores
        blood_match = 1.0 if donor["blood_type"] == patient["blood_type"] else 0.8
        antigen = compute_antigen_score(donor, patient)   # 8-antigen ISBT safety (0.0-1.0)
        prox = max(0.0, 1.0 - best_dist / 30.0)
        eng = _engagement_score(donor)
        elig = _eligibility_freshness(donor)
        churn_avoid = max(0.0, 1.0 - float(donor.get("churn_score") or 0.0))
        rad_pen = 1.0 if ring == 3 else (0.5 if ring == 2 else 0.0)
        bridge = 1.0 if donor["donor_id"] in bridge_donor_ids else 0.0

        # Hard safety gate: a dangerous antigen mismatch (anti-Kell etc.) removes the donor
        if antigen <= 0.0:
            continue

        final = (
            WEIGHTS["blood_match"]           * blood_match
            + WEIGHTS["antigen_safety"]      * antigen
            + WEIGHTS["proximity"]           * prox
            + WEIGHTS["engagement"]          * eng
            + WEIGHTS["eligibility_freshness"] * elig
            + WEIGHTS["churn_avoidance"]     * churn_avoid
            + WEIGHTS["bridge_bonus"]        * bridge
            - WEIGHTS["radius_penalty"]      * rad_pen
        )

        scored.append({
            "donor_id":           donor["donor_id"],
            "name":               donor.get("name", "Unknown"),
            "telegram_chat_id":   donor.get("telegram_chat_id"),
            "phone":              donor.get("phone"),
            "preferred_language": donor.get("preferred_language", "en"),
            "churn_score":        donor.get("churn_score", 0.0),
            "blood_type":         donor["blood_type"],
            "distance_km":        round(best_dist, 2),
            "antigen_score":      antigen,   # real 8-antigen ISBT compatibility score
            "bridge_bonus":       bridge,     # 1.0 if committed bridge donor, else 0.0
            "engagement_score":   eng,        # engagement component
            "ring":               ring,
            "match_score":        round(final, 4),
        })

    scored.sort(key=lambda x: x["match_score"], reverse=True)

    # ── 6. Split primary vs wide-net ──────────────────────────────────────────
    primary, wide_net = [], []
    for c in scored:
        (primary if c["ring"] in (1, 2) else wide_net).append(c)

    # Backfill from wide_net if primary is short
    if len(primary) < target:
        needed = target - len(primary)
        primary.extend(wide_net[:needed])
        wide_net = wide_net[needed:]

    primary = primary[:target]
    logger.info(f"MatchingEngine: {len(primary)} primary, {len(wide_net)} wide-net for {patient_id}")
    return {"primary": primary, "wide_net": wide_net}
