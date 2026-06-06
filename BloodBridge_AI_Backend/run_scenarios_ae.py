"""
Run Scenarios A–E from IMPLEMENTATION_PLAN.md and print a pass/fail summary.

Usage:
    cd BloodBridge_AI_Backend
    python run_scenarios_ae.py
"""
import asyncio
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

_SUBPROC_ENV = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"}


def run_script(name: str, script: str) -> bool:
    print(f"\n{'=' * 70}\nRunning {name}...\n{'=' * 70}")
    result = subprocess.run(
        [sys.executable, str(ROOT / script)],
        cwd=str(ROOT),
        capture_output=False,
        env=_SUBPROC_ENV,
    )
    ok = result.returncode == 0
    print(f"\n>>> {name}: {'PASS' if ok else 'FAIL'} (exit {result.returncode})")
    return ok


async def run_pipeline_smoke() -> bool:
    """Quick async smoke: LangGraph pipeline completes without fatal errors."""
    print(f"\n{'=' * 70}\nRunning Scenario B (pipeline smoke)...\n{'=' * 70}")
    try:
        from agents.graph import run_emergency_pipeline
        result = await run_emergency_pipeline({
            "request_id": "REQ-SCENARIO-B-SMOKE",
            "patient_id": "P-10000",
            "blood_type": "B+",
            "city": "Hyderabad",
            "hospital_name": "KIMS Secunderabad",
            "ward": "Thalassemia",
            "triggered_by": "scenario_runner",
        })
        outcome = result.get("outcome")
        chain_len = len(result.get("chain", []))
        errors = result.get("errors", [])
        print(f"  Outcome: {outcome}")
        print(f"  Chain length: {chain_len}")
        print(f"  Errors: {len(errors)}")
        ok = chain_len > 0 and outcome in ("SUCCESS", "ESCALATED", "IN_PROGRESS", None)
        print(f"\n>>> Scenario B pipeline smoke: {'PASS' if ok else 'FAIL'}")
        return ok
    except Exception as e:
        print(f"  Pipeline failed: {e}")
        print("\n>>> Scenario B pipeline smoke: FAIL")
        return False


def run_scenario_e() -> bool:
    print(f"\n{'=' * 70}\nRunning Scenario E (Hungarian optimizer)...\n{'=' * 70}")
    try:
        from core.database import get_supabase_admin
        from services.matching_engine import rank_donors
        from services.assignment_optimizer import optimize_assignments

        sb = get_supabase_admin()
        active = sb.table("emergency_requests").select("patient_id").eq("status", "IN_PROGRESS").limit(5).execute()
        patient_ids = list({r["patient_id"] for r in (active.data or []) if r.get("patient_id")})

        # If no active requests, use two demo patients for disjoint-assignment test
        if len(patient_ids) < 2:
            fallback = sb.table("patients").select("patient_id").eq("city", "Hyderabad").limit(2).execute()
            patient_ids = [p["patient_id"] for p in (fallback.data or [])][:2]

        if len(patient_ids) < 1:
            print("  No patients available for optimizer test.")
            return False

        pools = {}
        for pid in patient_ids:
            ranked = rank_donors(pid, target=8)
            candidates = ranked.get("primary", []) + ranked.get("wide_net", [])
            if candidates:
                pools[pid] = candidates

        if not pools:
            print("  No donor pools — cannot optimize.")
            return False

        assignments = optimize_assignments(pools)
        assigned_donors = []
        for pid, donors in assignments.items():
            for d in donors:
                did = d.get("donor_id")
                if did in assigned_donors:
                    print(f"  FAIL: Donor {did} double-booked across patients.")
                    return False
                assigned_donors.append(did)

        print(f"  Patients optimized: {len(assignments)}")
        print(f"  Total donor slots: {len(assigned_donors)}")
        print(f"  No double-booking detected.")
        print("\n>>> Scenario E: PASS")
        return True
    except Exception as e:
        print(f"  Optimizer failed: {e}")
        print("\n>>> Scenario E: FAIL")
        return False


def check_demo_mode() -> bool:
    print(f"\n{'=' * 70}\nDEMO_MOCK_MODE decision check...\n{'=' * 70}")
    from core.config import get_settings
    s = get_settings()
    mode = s.DEMO_MOCK_MODE
    env = s.APP_ENV
    if env == "production" and mode:
        print("  FAIL: DEMO_MOCK_MODE=true in production (blocked by main.py lifespan).")
        return False
    recommendation = (
        "DEMO_MOCK_MODE=true  -> local demos (simulated voice, synthetic Neo4j fallback)"
        if mode
        else "DEMO_MOCK_MODE=false -> live Bolna/Telegram (requires API keys + ngrok)"
    )
    print(f"  APP_ENV={env}")
    print(f"  DEMO_MOCK_MODE={mode}")
    print(f"  Decision: {recommendation}")
    print("\n>>> DEMO_MOCK_MODE: DOCUMENTED")
    return True


async def main() -> None:
    results = {}

    results["A — Smart Matching"] = run_script("Scenario A", "test_scenario_a.py")
    results["B — Pipeline smoke"] = await run_pipeline_smoke()
    results["B — Component test"] = run_script("Scenario B (components)", "test_scenario_b_simple.py")
    results["C/D — Engagement & Bot"] = run_script("Scenarios C & D", "test_scenarios_cd.py")
    results["E — Hungarian optimizer"] = run_scenario_e()
    results["DEMO_MOCK_MODE"] = check_demo_mode()

    print(f"\n{'=' * 70}")
    print("SCENARIOS A–E SUMMARY")
    print("=" * 70)
    for name, ok in results.items():
        print(f"  {'PASS' if ok else 'FAIL'}  {name}")

    failed = [k for k, v in results.items() if not v]
    if failed:
        print(f"\n{len(failed)} check(s) failed: {', '.join(failed)}")
        sys.exit(1)
    print("\nAll scenario checks passed.")
    sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
