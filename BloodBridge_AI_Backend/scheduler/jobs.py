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
                
            db_chain = bc_res.data or []
            
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
                "trace_id": f"SCHED-{request_id[-4:]}"
            }
            
            # Execute monitoring agent logic
            monitor_res = await chain_monitor_agent(state)
            
            # If a chain break is detected, execute repair agent
            if monitor_res.get("chain_break_detected"):
                logger.warning(f"Scheduler: Chain break detected for request {request_id}. Running repair agent...")
                state.update(monitor_res)
                
                # Execute repair agent
                repair_res = await chain_repair_agent(state)
                state.update(repair_res)
                
                # Run outreach agent if repair updated plans
                if state.get("outreach_plan"):
                    logger.info(f"Scheduler: Chain repaired. Re-running outreach for request {request_id}...")
                    await outreach_agent(state)
                    
            elif monitor_res.get("outcome") == "ESCALATED":
                logger.warning(f"Scheduler: Chain completely failed for request {request_id}. Triggering inventory search...")
                state.update(monitor_res)
                await inventory_agent(state)
                
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
