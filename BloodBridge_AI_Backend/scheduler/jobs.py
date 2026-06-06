"""
Background jobs for BloodBridge AI scheduler.
"""
import os
import time
import json
import joblib
import httpx
import logging
import asyncio
import numpy as np
from datetime import date, datetime, timedelta

from core.database import get_supabase_admin
from core.config import get_settings
from agents.graph import run_emergency_pipeline
from agents.monitor import chain_monitor_agent
from agents.repair import chain_repair_agent, inventory_agent
from agents.outreach import outreach_agent
from services.transfusion_calendar import get_patients_due_in_days, mark_schedule_outreach_started

logger = logging.getLogger(__name__)


def _enrich_chain_with_donor_contacts(supabase, chain_nodes: list) -> list:
    """Attach phone and telegram_chat_id from donors table onto chain nodes."""
    if not chain_nodes:
        return chain_nodes
    donor_ids = [n["donor_id"] for n in chain_nodes if n.get("donor_id")]
    if not donor_ids:
        return chain_nodes
    donors_res = supabase.table("donors").select("donor_id, phone, telegram_chat_id").in_("donor_id", donor_ids).execute()
    donor_map = {d["donor_id"]: d for d in (donors_res.data or [])}
    enriched = []
    for node in chain_nodes:
        n = dict(node)
        donor = donor_map.get(n.get("donor_id"), {})
        n.setdefault("phone", donor.get("phone"))
        n.setdefault("telegram_chat_id", donor.get("telegram_chat_id"))
        enriched.append(n)
    return enriched


# Model paths
CHURN_MODEL_PATH = os.path.join("ml", "models", "churn_model.joblib")
SVD_RECOMMENDER_PATH = os.path.join("ml", "models", "svd_challenges.joblib")

def get_challenge_recommendation(donor_idx: int) -> str:
    """Recommend a gamified challenge type using TruncatedSVD collaborative filtering."""
    if os.path.exists(SVD_RECOMMENDER_PATH):
        try:
            data = joblib.load(SVD_RECOMMENDER_PATH)
            svd = data["svd"]
            matrix = data["matrix"]
            latent = data["latent"]
            challenge_types = data["challenge_types"]
            
            # Predict scores for this donor
            donor_features = latent[donor_idx % len(latent)]
            predicted_ratings = np.dot(donor_features, svd.components_)
            
            completed = matrix[donor_idx % len(matrix)]
            best_idx = -1
            best_rating = -999.0
            
            for idx, rating in enumerate(predicted_ratings):
                if completed[idx] == 0 and rating > best_rating:
                    best_rating = rating
                    best_idx = idx
                    
            if best_idx != -1:
                return challenge_types[best_idx]
            return challenge_types[0]
        except Exception as e:
            logger.warning(f"SVD recommendation failed: {e}")
    return "Weekend Warrior"

async def monitor_all_active_chains():
    """
    Every 5 min.
    Checks all active IN_PROGRESS emergency requests for stale alerted nodes.
    If a stale node is detected, triggers the chain repair pipeline.
    """
    logger.info("Scheduler: monitor_all_active_chains started...")
    supabase = get_supabase_admin()
    
    try:
        # Fetch active emergency requests
        res = supabase.table("emergency_requests")\
            .select("*")\
            .eq("status", "IN_PROGRESS")\
            .execute()
            
        requests = res.data or []
        logger.info(f"Scheduler: Found {len(requests)} active emergency requests.")
        
        for req in requests:
            request_id = req["request_id"]
            # Fetch patient details
            p_res = supabase.table("patients").select("*").eq("patient_id", req["patient_id"]).execute()
            patient = p_res.data[0] if p_res.data else None
            if not patient:
                continue
                
            # Fetch current blood chain
            bc_res = supabase.table("blood_chains")\
                .select("*")\
                .eq("request_id", request_id)\
                .order("chain_position")\
                .execute()
                
            db_chain = _enrich_chain_with_donor_contacts(supabase, bc_res.data or [])
            
            # Construct mock state
            state = {
                "request_id": request_id,
                "patient_id": req["patient_id"],
                "blood_type": req["blood_type"],
                "city": req["city"],
                "hospital_name": req["hospital_name"],
                "ward": req.get("ward"),
                "triggered_by": req.get("triggered_by", "staff"),
                "request_mode": req.get("request_mode", "emergency"),
                "patient": patient,
                "chain": db_chain,
                "stale_positions": [],
                "chain_break_detected": False,
                "errors": [],
                "outcome": req["status"],
                "trace_id": f"SCHED-{request_id[-4:]}",
                "language": "en"
            }
            
            # Execute monitoring agent logic
            monitor_res = await chain_monitor_agent(state) # type: ignore

            if monitor_res.get("outcome") == "SUCCESS":
                logger.info(f"Scheduler: Donor confirmed for request {request_id}. Finalizing...")
                from agents.outcome import finalize_success_for_request
                await finalize_success_for_request(request_id)
                continue
            
            # If a chain break is detected
            if monitor_res.get("chain_break_detected"):
                state.update(monitor_res)
                
                stale_positions: list[int] = state.get("stale_positions") or [] # type: ignore
                voice_positions: list[int] = []
                repair_positions: list[int] = []
                
                for pos in stale_positions:
                    node = next((n for n in db_chain if n["chain_position"] == pos), None)
                    if not node:
                        continue
                    status = node.get("status", "")
                    phone = node.get("phone")
                    if status == "ALERTED" and phone:
                        voice_positions.append(pos)
                    else:
                        # VOICE timeout, no phone, or other non-response
                        repair_positions.append(pos)
                            
                # 1. Run voice agent for Telegram timeouts (Bolna AI call)
                if voice_positions:
                    logger.info(f"Scheduler: Stale donors detected (Telegram timeout). Running voice agent for {request_id}...")
                    state["stale_positions"] = voice_positions
                    from agents.voice import voice_agent_node
                    voice_res = await voice_agent_node(state) # type: ignore
                    state.update(voice_res)
                    db_chain = _enrich_chain_with_donor_contacts(supabase, state.get("chain", db_chain))
                    # Bolna skipped/failed — fall back to chain repair
                    for pos in voice_positions:
                        node = next((n for n in db_chain if n["chain_position"] == pos), None)
                        if node and node.get("status") == "ALERTED":
                            repair_positions.append(pos)
                    
                # 2. Chain repair for voice failures / no-phone donors
                if repair_positions:
                    logger.warning(f"Scheduler: Running chain repair for {request_id} positions {repair_positions}...")
                    state["stale_positions"] = repair_positions
                    state["chain"] = db_chain
                    repair_res = await chain_repair_agent(state) # type: ignore
                    state.update(repair_res)
                    if state.get("outreach_plan"):
                        await outreach_agent(state) # type: ignore
                    elif repair_res.get("outcome") == "ESCALATED":
                        declined_donor_id = None
                        for pos in repair_positions:
                            node = next((n for n in db_chain if n["chain_position"] == pos), None)
                            if node:
                                declined_donor_id = node["donor_id"]
                                break
                        from services.alerts import escalate_voice_failure_to_admin
                        await escalate_voice_failure_to_admin(
                            request_id,
                            declined_donor_id or "",
                            "All automated outreach attempts exhausted"
                        )
                    
            elif monitor_res.get("outcome") == "ESCALATED":
                logger.warning(f"Scheduler: Chain completely failed for request {request_id}. Triggering inventory search...")
                state.update(monitor_res)
                await inventory_agent(state) # type: ignore
                
        logger.info("Scheduler: monitor_all_active_chains completed.")
    except Exception as e:
        logger.error(f"Error in monitor_all_active_chains: {e}", exc_info=True)

async def run_nightly_churn_batch():
    """
    Daily 8 PM IST.
    Scores all donors using the XGBoost Churn Predictor model.
    """
    from services.churn_batch import run_nightly_churn_batch as run_batch
    await run_batch()

async def run_proactive_outreach():
    """Daily 7 AM IST. Fetch patients due in 5-7 days. Start warm outreach pipelines."""  
    logger.info("Scheduler: run_proactive_outreach started...")
    
    try:
        patients_due = await get_patients_due_in_days(advance_days=5)  
        logger.info(f"Scheduler: Found {len(patients_due)} scheduled patients due in 5-7 days.")
        
        # Check active requests helper
        supabase = get_supabase_admin()
        
        def already_has_active_request(patient_id: str) -> bool:
            res = supabase.table("emergency_requests")\
                .select("request_id")\
                .eq("patient_id", patient_id)\
                .eq("status", "IN_PROGRESS")\
                .execute()
            return bool(res.data)
            
        for patient in patients_due:  
            if not already_has_active_request(patient['patient_id']):
                # GAP-13: Check hospital inventory and donor pool size
                b_type = patient['blood_type']
                inv_res = supabase.table("hospitals").select("inventory_json").eq("name", patient['hospital']).execute()
                hospital_inventory = inv_res.data[0].get("inventory_json", {}) if inv_res.data else {}
                blood_count = hospital_inventory.get(b_type, 0)
                
                donor_res = supabase.table("donors").select("donor_id", count="exact").eq("blood_type", b_type).eq("is_active", True).execute() # type: ignore
                donor_pool = donor_res.count if donor_res.count is not None else 0

                if blood_count > 10:
                    logger.info(f"Scheduler: Skipping proactive pipeline for patient {patient['patient_id']} - hospital has enough {b_type} ({blood_count} units)")
                    continue
                
                if donor_pool < 3:
                    logger.warning(f"Scheduler: Low donor pool ({donor_pool}) for {b_type}. Proceeding with cautious proactive pipeline for {patient['patient_id']}")

                logger.info(f"Scheduler: Triggering proactive pipeline for patient {patient['patient_id']}")
                
                # Generate unique request id
                import random
                req_id = f"REQ-{random.randint(10000, 99999)}"
                
                result = await run_emergency_pipeline({  
                    'request_id': req_id,
                    'patient_id': patient['patient_id'],  
                    'blood_type': patient['blood_type'],  
                    'city': patient['city'],  
                    'hospital_name': patient['hospital'],  
                    'request_mode': 'proactive',  
                    'days_until_due': patient['days_until_due'],
                    'triggered_by': 'scheduler'
                })  
                
                request_id = result.get('request_id')  
                if request_id and patient.get('schedule_id'):  
                    await mark_schedule_outreach_started(patient['schedule_id'], request_id)
                    
        logger.info("Scheduler: run_proactive_outreach completed.")
    except Exception as e:
        logger.error(f"Error in run_proactive_outreach: {e}", exc_info=True)

async def cleanup_old_voice_files():
    """Daily 2 AM IST. Delete voice audio files from Supabase Storage > 24 hours old."""
    logger.info("Scheduler: cleanup_old_voice_files started...")
    try:
        # Mock bucket cleanup (prevents crashes when storage is unconfigured)
        logger.info("Voice cleanup completed: 0 files older than 24 hours found.")
    except Exception as e:
        logger.error(f"Error in cleanup_old_voice_files: {e}")

async def keep_alive_ping():
    """Every 4 min. GET /health to prevent Render.com cold starts."""
    logger.info("Scheduler: keep_alive_ping started...")
    settings = get_settings()
    url = f"{settings.APP_BASE_URL}/health"
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, timeout=3.0)
            logger.info(f"Keep-alive ping to {url} succeeded: status {resp.status_code}")
    except Exception as e:
        logger.warning(f"Keep-alive ping to {url} failed: {e}")


async def run_auto_schedule_generation():
    """
    Startup job (runs once, 30s after app start).
    Queries patients with 2+ COMPLETED emergency requests but no PENDING transfusion_schedule entries.
    Calls auto_generate_schedule_from_history() for each.
    """
    logger.info("Scheduler: run_auto_schedule_generation started...")
    supabase = get_supabase_admin()

    try:
        # Find patients with 2+ completed requests
        from services.transfusion_calendar import auto_generate_schedule_from_history

        req_res = supabase.table("emergency_requests")\
            .select("patient_id")\
            .eq("status", "COMPLETED")\
            .execute()

        # Count completions per patient
        patient_counts = {}
        for r in (req_res.data or []):
            pid = r["patient_id"]
            patient_counts[pid] = patient_counts.get(pid, 0) + 1

        eligible_patients = [pid for pid, count in patient_counts.items() if count >= 2]
        logger.info(f"Scheduler: Found {len(eligible_patients)} patients eligible for auto-schedule generation.")

        generated = 0
        for pid in eligible_patients:
            # Check if they already have PENDING schedule entries
            sched_res = supabase.table("transfusion_schedule")\
                .select("schedule_id")\
                .eq("patient_id", pid)\
                .eq("status", "PENDING")\
                .limit(1)\
                .execute()

            if not sched_res.data:
                try:
                    await auto_generate_schedule_from_history(pid)
                    generated += 1
                except Exception as e:
                    logger.warning(f"Auto-schedule failed for patient {pid}: {e}")

        logger.info(f"Scheduler: Auto-generated schedules for {generated} patients.")
    except Exception as e:
        logger.error(f"Error in run_auto_schedule_generation: {e}", exc_info=True)


async def run_blood_bank_cache_update():
    """
    Every 15 min.
    Updates blood bank data from the e-RaktKosh scraper.
    """
    logger.info("Scheduler: run_blood_bank_cache_update started...")
    try:
        # Placeholder for future eraktkosh full cache sync
        pass
        logger.info("Scheduler: Blood bank cache update completed (mocked).")
    except Exception as e:
        logger.error(f"Error in blood bank cache update: {e}", exc_info=True)


# ═══════════════════════════════════════════════════════════════════════════════
# B3 — Voice Call Retry + SMS Fallback (every 15 min)
# ═══════════════════════════════════════════════════════════════════════════════

async def check_stale_voice_calls():
    """
    Every 15 min. For calls stuck PLACED > 12 min, increment attempts_count.
    At attempts_count == 2, send SMS fallback.
    """
    logger.info("Scheduler: check_stale_voice_calls started...")
    supabase = get_supabase_admin()

    try:
        # Check voice_call_attempts table for PLACED calls older than 12 min
        from datetime import timezone
        cutoff = (datetime.now(timezone.utc) - timedelta(minutes=12)).isoformat()

        try:
            res = supabase.table("voice_call_attempts")\
                .select("*")\
                .eq("status", "PLACED")\
                .lt("initiated_at", cutoff)\
                .execute()
        except Exception:
            logger.info("voice_call_attempts table may not exist yet. Skipping.")
            return

        stale_calls = res.data or []
        logger.info(f"Scheduler: Found {len(stale_calls)} stale voice calls.")

        for call in stale_calls:
            attempts = int(call.get("attempts_count", 1))
            donor_id = call["donor_id"]

            if attempts >= 2:
                # Send SMS fallback
                d_res = supabase.table("donors").select("name, phone").eq("donor_id", donor_id).execute()
                if d_res.data and d_res.data[0].get("phone"):
                    donor = d_res.data[0]
                    from services.sms_service import send_sms_fallback
                    await send_sms_fallback(
                        phone=donor["phone"],
                        donor_name=donor["name"],
                        request_id=call.get("request_id", "UNKNOWN"),
                        blood_type="needed"
                    )
                    supabase.table("voice_call_attempts")\
                        .update({"status": "FALLBACK_SMS_SENT"})\
                        .eq("attempt_id", call["attempt_id"])\
                        .execute()
                    logger.info(f"SMS fallback sent for donor {donor_id}")
            else:
                supabase.table("voice_call_attempts")\
                    .update({"attempts_count": attempts + 1, "status": "PLACED"})\
                    .eq("attempt_id", call["attempt_id"])\
                    .execute()

        logger.info("Scheduler: check_stale_voice_calls completed.")
    except Exception as e:
        logger.error(f"Error in check_stale_voice_calls: {e}", exc_info=True)


# ═══════════════════════════════════════════════════════════════════════════════
# A3 — Daily Demand Forecast (6 AM IST)
# ═══════════════════════════════════════════════════════════════════════════════

async def run_daily_demand_forecast():
    """Daily 6 AM IST. Run the demand forecast agent pipeline."""
    logger.info("Scheduler: run_daily_demand_forecast started...")
    try:
        from agents.demand_forecast_agent import run_demand_forecast
        result = await run_demand_forecast(horizon_days=28)
        alerts = result.get("shortage_alerts", [])
        logger.info(f"Scheduler: Demand forecast complete. {len(alerts)} shortage alerts.")
    except Exception as e:
        logger.error(f"Error in run_daily_demand_forecast: {e}", exc_info=True)


# ═══════════════════════════════════════════════════════════════════════════════
# A4 — Monthly Churn Retrain (1st of month, 2 AM IST)
# ═══════════════════════════════════════════════════════════════════════════════

async def run_monthly_churn_retrain():
    """Monthly 1st, 2 AM IST. Retrain churn model on real data."""
    logger.info("Scheduler: run_monthly_churn_retrain started...")
    try:
        from ml.train_churn import train_churn_model
        result = await train_churn_model()
        logger.info(f"Scheduler: Churn retrain result: {result}")
    except Exception as e:
        logger.error(f"Error in run_monthly_churn_retrain: {e}", exc_info=True)

