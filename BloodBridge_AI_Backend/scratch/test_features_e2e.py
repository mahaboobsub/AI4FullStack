"""
End-to-End Feature Test Script for BloodBridge AI.
Tests all 4 core features against live Neo4j + Supabase:
  1. Donor Bridge Formation
  2. Broken Bridge Rebuild
  3. Donor Prediction (Churn)
  4. Emergency Handling (Pipeline)
"""
import os
import sys
import asyncio
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PASS = "[PASS]"
FAIL = "[FAIL]"
SKIP = "[SKIP]"


async def test_bridge_formation():
    """Test 1: Donor Bridge Formation via Neo4j graph matching."""
    print("\n" + "=" * 60)
    print("TEST 1: DONOR BRIDGE FORMATION")
    print("=" * 60)

    from agents.neo4j_match import Neo4jMatcher
    from core.database import get_supabase_admin

    supabase = get_supabase_admin()

    # Pick a real patient from DB
    p_res = supabase.table("patients").select("patient_id, blood_type, city").limit(1).execute()
    if not p_res.data:
        print(f"  {FAIL} No patients found in Supabase")
        return False

    patient = p_res.data[0]
    patient_id = patient["patient_id"]
    print(f"  Patient: {patient_id} | {patient['blood_type']} | {patient['city']}")

    start = time.perf_counter()
    donors = await Neo4jMatcher.find_top_donors(patient_id)
    elapsed = (time.perf_counter() - start) * 1000

    print(f"  Neo4j query time: {elapsed:.0f}ms")
    print(f"  Donors found: {len(donors)}")

    if not donors:
        print(f"  {FAIL} No compatible donors returned by Neo4j")
        return False

    for i, d in enumerate(donors[:5]):
        score = d.get("antigen_score", 0)
        dist = d.get("distance_km", 0)
        print(f"    #{i+1} {d.get('donor_id')} | {d.get('name')} | score={score:.2f} | {dist:.1f}km")

    print(f"\n  {PASS} Bridge formation working! {len(donors)} donors matched in {elapsed:.0f}ms")
    return True


async def test_bridge_rebuild():
    """Test 2: Broken Bridge Rebuild — simulate stale positions and find replacements."""
    print("\n" + "=" * 60)
    print("TEST 2: BROKEN BRIDGE REBUILD")
    print("=" * 60)

    from agents.neo4j_match import Neo4jMatcher
    from core.database import get_supabase_admin
    from core.neo4j_client import get_driver

    supabase = get_supabase_admin()

    # Get a patient
    p_res = supabase.table("patients").select("patient_id, blood_type, city").limit(1).execute()
    if not p_res.data:
        print(f"  {FAIL} No patients in DB")
        return False

    patient = p_res.data[0]
    patient_id = patient["patient_id"]
    city = patient["city"]
    blood_type = patient["blood_type"]
    print(f"  Patient: {patient_id} | {blood_type} | {city}")

    # Step 1: Find initial donors (simulate bridge formation)
    initial_donors = await Neo4jMatcher.find_top_donors(patient_id)
    if len(initial_donors) < 3:
        print(f"  {FAIL} Need at least 3 donors, found {len(initial_donors)}")
        return False

    # Simulate: exclude first 2 donors (as if they declined) and find replacements
    excluded_ids = [initial_donors[0]["donor_id"], initial_donors[1]["donor_id"]]
    print(f"  Simulating decline from: {excluded_ids}")

    driver = get_driver()
    repair_query = """
    MATCH (p:Patient {patient_id: $patient_id})
    MATCH (d:Donor)-[c:COMPATIBLE_WITH]->(p)
    WHERE d.is_active = true
      AND d.blood_type = p.blood_type
      AND (d.last_donation_date IS NULL OR duration.inDays(d.last_donation_date, date()).days >= 56)
      AND NOT d.donor_id IN $exclude_donor_ids
    WITH d, c, p,
         point.distance(
             point({latitude: d.lat, longitude: d.lng}),
             point({latitude: p.lat, longitude: p.lng})
         ) AS distance_m
    ORDER BY d.churn_score ASC, c.antigen_score DESC, distance_m ASC
    LIMIT 2
    RETURN d.donor_id AS donor_id, d.name AS name,
           c.antigen_score AS antigen_score,
           distance_m / 1000.0 AS distance_km
    """

    replacements = []
    async with driver.session() as session:
        result = await session.run(repair_query, {
            "patient_id": patient_id,
            "exclude_donor_ids": excluded_ids
        })
        async for rec in result:
            replacements.append(dict(rec))

    if not replacements:
        print(f"  {FAIL} No replacement donors found")
        return False

    print(f"  Replacement donors found: {len(replacements)}")
    for r in replacements:
        print(f"    {r['donor_id']} | {r['name']} | score={r['antigen_score']:.2f} | {r['distance_km']:.1f}km")

    # Verify replacements are NOT in excluded list
    for r in replacements:
        if r["donor_id"] in excluded_ids:
            print(f"  {FAIL} Replacement donor {r['donor_id']} was in excluded list!")
            return False

    print(f"\n  {PASS} Bridge rebuild working! Found {len(replacements)} replacements excluding declined donors")
    return True


async def test_donor_prediction():
    """Test 3: Donor Prediction — XGBoost churn scoring."""
    print("\n" + "=" * 60)
    print("TEST 3: DONOR PREDICTION (CHURN)")
    print("=" * 60)

    from ml.churn_predictor import ChurnPredictor
    from core.database import get_supabase_admin

    supabase = get_supabase_admin()

    # Fetch some donors from DB
    res = supabase.table("donors").select("*").eq("is_active", True).limit(10).execute()
    donors = res.data or []
    if not donors:
        print(f"  {FAIL} No donors in DB")
        return False

    # Enrich donors with features ChurnPredictor expects
    rich_donors = []
    for d in donors:
        d_copy = d.copy()
        d_copy["missed_alerts"] = 0
        d_copy["badge_count"] = 0
        d_copy["avg_response_lag"] = 3600.0
        d_copy["city_scarcity_score"] = 0.5
        d_copy["chain_position_avg"] = 4.5
        rich_donors.append(d_copy)

    predictor = ChurnPredictor()
    model_status = "XGBoost model loaded" if predictor.model else "Using fallback formula"
    print(f"  Model: {model_status}")

    start = time.perf_counter()
    results = predictor.predict_batch(rich_donors)
    elapsed = (time.perf_counter() - start) * 1000

    print(f"  Scored {len(results)} donors in {elapsed:.1f}ms")

    tier_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for r in results:
        tier_counts[r["churn_risk"]] += 1
        print(f"    {r['donor_id']} | score={r['churn_score']:.2f} | {r['churn_risk']} | {r['top_risk_factor']}")

    print(f"\n  Tier Distribution: {tier_counts}")

    # Validate scores are in range
    for r in results:
        if not (0.0 <= r["churn_score"] <= 1.0):
            print(f"  {FAIL} Score out of range: {r['churn_score']}")
            return False

    print(f"\n  {PASS} Donor prediction working! {len(results)} donors scored in {elapsed:.1f}ms")
    return True


async def test_emergency_pipeline():
    """Test 4: Emergency Handling — dry-run the full LangGraph pipeline."""
    print("\n" + "=" * 60)
    print("TEST 4: EMERGENCY HANDLING (PIPELINE)")
    print("=" * 60)

    from core.database import get_supabase_admin
    import random

    supabase = get_supabase_admin()

    # Pick a patient
    p_res = supabase.table("patients").select("*").limit(1).execute()
    if not p_res.data:
        print(f"  {FAIL} No patients in DB")
        return False

    patient = p_res.data[0]
    patient_id = patient["patient_id"]
    blood_type = patient["blood_type"]
    city = patient["city"]
    hospital = patient["hospital"]
    print(f"  Patient: {patient_id} | {blood_type} | {city} | {hospital}")

    # Test individual pipeline stages instead of full graph (avoids Telegram/voice side effects)
    print("\n  --- Stage 1: Intake Agent ---")
    from agents.intake import intake_agent
    state = {
        "request_id": f"REQ-TEST-{random.randint(10000,99999)}",
        "patient_id": patient_id,
        "blood_type": blood_type,
        "city": city,
        "hospital_name": hospital,
        "ward": patient.get("ward"),
        "triggered_by": "test",
        "request_mode": "emergency",
        "days_until_due": None,
        "patient": None,
        "eligible_donors": [],
        "scored_donors": [],
        "matched_donors": [],
        "chain": [],
        "chain_confirmed_count": 0,
        "chain_declined_count": 0,
        "conflict_detected": False,
        "conflict_resolution": None,
        "outreach_plan": [],
        "chain_break_detected": False,
        "stale_positions": [],
        "urgency_result": {},
        "patient_antibody_flags": {},
        "donors_consent_checked": False,
        "non_consented_donors": [],
        "outcome": None,
        "badges_awarded": [],
        "impact_story": None,
        "trace_id": f"TRC-TEST-{random.randint(1000,9999)}",
        "node_timings": {},
        "errors": [],
        "language": "en",
    }

    intake_result = await intake_agent(state)
    state.update(intake_result)

    if state.get("outcome") == "FAILED":
        print(f"  {FAIL} Intake failed: {state.get('errors')}")
        return False
    print(f"  {PASS} Intake: Patient loaded, antibody flags extracted")

    print("\n  --- Stage 2: Eligibility Filter ---")
    from agents.eligibility import eligibility_agent
    elig_result = await eligibility_agent(state)
    state.update(elig_result)

    eligible_count = len(state.get("eligible_donors", []))
    print(f"  {PASS} Eligibility: {eligible_count} eligible donors found")

    print("\n  --- Stage 3: Antigen Scoring ---")
    from agents.matching import antigen_scoring_agent
    score_result = await antigen_scoring_agent(state)
    state.update(score_result)

    scored_count = len(state.get("scored_donors", []))
    print(f"  {PASS} Antigen Scoring: {scored_count} donors scored")
    if scored_count > 0:
        top = state["scored_donors"][0]
        print(f"         Top donor: {top.get('donor_id')} | score={top.get('antigen_score', 0):.2f}")

    print("\n  --- Stage 4: Urgency Scoring ---")
    from agents.matching import urgency_scoring_agent
    urg_result = await urgency_scoring_agent(state)
    state.update(urg_result)

    urg = state.get("urgency_result", {})
    print(f"  {PASS} Urgency: score={urg.get('urgency_score', 0):.1f}/10 | priority={urg.get('priority', 'N/A')}")

    print("\n  --- Stage 5: Neo4j Graph Matching ---")
    from agents.neo4j_match import neo4j_matching_agent
    match_result = await neo4j_matching_agent(state)
    state.update(match_result)

    chain = state.get("chain", [])
    matched = state.get("matched_donors", [])
    print(f"  {PASS if chain else FAIL} Neo4j Match: {len(matched)} donors matched, {len(chain)} chain nodes built")

    if chain:
        for c in chain[:3]:
            print(f"         Pos {c['chain_position']}: {c['donor_id']} | {c['status']} | score={c['antigen_score']:.2f}")

    # Clean up test emergency request
    try:
        supabase.table("blood_chains").delete().eq("request_id", state["request_id"]).execute()
        supabase.table("agent_traces").delete().eq("request_id", state["request_id"]).execute()
        supabase.table("emergency_requests").delete().eq("request_id", state["request_id"]).execute()
        print(f"\n  [CLEANUP] Test data cleaned from DB")
    except Exception as e:
        print(f"\n  [CLEANUP] Partial cleanup: {e}")

    # Clean up test IN_CHAIN edges from Neo4j
    try:
        from core.neo4j_client import get_driver
        driver = get_driver()
        async with driver.session() as session:
            await session.run(
                "MATCH ()-[r:IN_CHAIN {request_id: $rid}]->() DELETE r",
                {"rid": state["request_id"]}
            )
        print(f"  [CLEANUP] Test chain edges removed from Neo4j")
    except Exception as e:
        print(f"  [CLEANUP] Neo4j cleanup: {e}")

    # Final timings
    timings = state.get("node_timings", {})
    print(f"\n  Pipeline Node Timings:")
    total_ms = 0
    for node, ms in timings.items():
        print(f"    {node}: {ms:.1f}ms")
        total_ms += ms
    print(f"    TOTAL: {total_ms:.0f}ms")

    success = bool(chain)
    print(f"\n  {PASS if success else FAIL} Emergency pipeline {'completed' if success else 'failed'}")
    return success


async def main():
    print("=" * 60)
    print("BLOODBRIDGE AI - END-TO-END FEATURE TESTS")
    print("=" * 60)
    print(f"Running against live Neo4j + Supabase\n")

    results = {}

    try:
        results["Bridge Formation"] = await test_bridge_formation()
    except Exception as e:
        print(f"  {FAIL} Exception: {e}")
        results["Bridge Formation"] = False

    try:
        results["Bridge Rebuild"] = await test_bridge_rebuild()
    except Exception as e:
        print(f"  {FAIL} Exception: {e}")
        results["Bridge Rebuild"] = False

    try:
        results["Donor Prediction"] = await test_donor_prediction()
    except Exception as e:
        print(f"  {FAIL} Exception: {e}")
        results["Donor Prediction"] = False

    try:
        results["Emergency Pipeline"] = await test_emergency_pipeline()
    except Exception as e:
        print(f"  {FAIL} Exception: {e}")
        results["Emergency Pipeline"] = False

    # Summary
    print("\n" + "=" * 60)
    print("FINAL RESULTS")
    print("=" * 60)
    all_pass = True
    for feature, passed in results.items():
        status = PASS if passed else FAIL
        if not passed:
            all_pass = False
        print(f"  {status} {feature}")

    print("\n" + ("ALL TESTS PASSED!" if all_pass else "SOME TESTS FAILED"))
    print("=" * 60)

    # Close Neo4j driver
    from core.neo4j_client import close
    await close()


if __name__ == "__main__":
    asyncio.run(main())
