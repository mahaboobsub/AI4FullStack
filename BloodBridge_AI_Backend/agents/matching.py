"""
Matching and Urgency Scoring Agents for BloodBridge AI.
Includes antigen compatibility scoring and XGBoost clinical urgency evaluation.
"""
import time
import logging
import httpx
from models.state import AgentState
from core.config import get_settings
from core.database import get_supabase_admin
from ml.antigen_scorer import compute_antigen_score, get_eligibility_flags
from ml.urgency_scorer import get_urgency_scorer

logger = logging.getLogger(__name__)

async def send_ntfy_alert(patient_id: str, blood_type: str, hospital: str, score: float):
    """Dispatch an instant mobile push notification via ntfy.sh for CRITICAL patients."""
    settings = get_settings()
    if not settings.NTFY_TOPIC:
        return
        
    url = f"https://ntfy.sh/{settings.NTFY_TOPIC}"
    title = f"🔴 CRITICAL BLOOD REQUEST - {blood_type}"
    message = f"Patient {patient_id} at {hospital} needs {blood_type} immediately. Urgency score: {score:.1f}/10."
    
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                url,
                content=message.encode("utf-8"),
                headers={
                    "Title": title,
                    "Priority": "5",  # max priority (creates noise / vibration)
                    "Tags": "rotating_light,blood,critical"
                },
                timeout=3.0
            )
            logger.info(f"Broadcasted critical alert to ntfy.sh topic: {settings.NTFY_TOPIC}")
    except Exception as e:
        logger.warning(f"Could not send ntfy notification: {e}")

async def antigen_scoring_agent(state: AgentState) -> dict:
    """
    Antigen Scoring Node.
    Runs minor antigen scoring (kell, duffy, kidd, rh, mns) for all eligible donors.
    """
    start_time = time.perf_counter()
    logger.info(f"[{state['trace_id']}] AntigenScoringAgent started...")
    
    patient_profile = state["patient"]
    eligible_donors = state.get("eligible_donors", [])
    
    if not patient_profile:
        return {"errors": state.get("errors", []) + ["No patient profile to score antigens."]}
        
    scored_donors = []
    
    for donor in eligible_donors:
        donor_copy = donor.copy()
        # Compute compatibility score
        score = compute_antigen_score(donor, patient_profile)
        donor_copy["antigen_score"] = score
        donor_copy["antigen_flags"] = get_eligibility_flags(donor)
        scored_donors.append(donor_copy)
        
    # Sort donors by antigen_score DESC (perfect matches first)
    scored_donors.sort(key=lambda d: d.get("antigen_score", 0.0), reverse=True)
    
    duration = (time.perf_counter() - start_time) * 1000.0
    timings = state.get("node_timings", {}).copy()
    timings["antigen_scoring_node"] = round(duration, 2)
    
    logger.info(f"AntigenScoringAgent: Scored {len(scored_donors)} donors.")
    return {
        "scored_donors": scored_donors,
        "node_timings": timings
    }

async def urgency_scoring_agent(state: AgentState) -> dict:
    """
    Urgency Scoring Node.
    Runs XGBoost regressor model on patient parameters to calculate clinical urgency.
    """
    start_time = time.perf_counter()
    logger.info(f"[{state['trace_id']}] UrgencyScoringAgent started...")
    
    patient_profile = state["patient"]
    if not patient_profile:
        return {"errors": state.get("errors", []) + ["No patient profile to score urgency."]}
        
    try:
        # 1. Run XGBoost or rule-based scorer
        scorer = get_urgency_scorer()
        score_res = scorer.score(patient_profile)
        
        urgency_score = score_res["urgency_score"]
        priority = score_res["priority"]
        
        if state.get("request_mode") == "proactive":
            urgency_score = min(urgency_score, 4.0)
            priority = "ROUTINE"
            score_res["urgency_score"] = urgency_score
            score_res["priority"] = priority
        
        # 2. Update Supabase emergency_requests table
        supabase = get_supabase_admin()
        supabase.table("emergency_requests")\
            .update({
                "urgency_score": urgency_score,
                "priority": priority
            })\
            .eq("request_id", state["request_id"])\
            .execute()
            
        # 3. Update Patient Status
        # Patient status is CHECK(status IN ('CRITICAL','STABLE','OVERDUE'))
        patient_status = "CRITICAL" if priority == "CRITICAL" else patient_profile.get("status", "STABLE")
        supabase.table("patients")\
            .update({
                "status": patient_status
            })\
            .eq("patient_id", state["patient_id"])\
            .execute()
            
        # 4. Critical Escalation: Dispatch immediate ntfy alert if CRITICAL
        if priority == "CRITICAL":
            await send_ntfy_alert(
                patient_id=state["patient_id"],
                blood_type=state["blood_type"],
                hospital=state["hospital_name"],
                score=urgency_score
            )
            
        duration = (time.perf_counter() - start_time) * 1000.0
        timings = state.get("node_timings", {}).copy()
        timings["urgency_scoring_node"] = round(duration, 2)
        
        return {
            "urgency_result": score_res,
            "node_timings": timings
        }
        
    except Exception as e:
        err_msg = f"Urgency scoring agent error: {e}"
        logger.error(err_msg, exc_info=True)
        return {
            "errors": state.get("errors", []) + [err_msg],
            "outcome": "FAILED"
        }
