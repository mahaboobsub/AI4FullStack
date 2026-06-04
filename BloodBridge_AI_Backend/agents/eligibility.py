"""
Eligibility Filter Agent for BloodBridge AI.
Queries potential donors, applies WHO guidelines, and manages donor scarcity.
"""
import time
import logging
from models.state import AgentState
from core.database import get_supabase_admin
from ml.eligibility_filter import filter_eligible_donors

logger = logging.getLogger(__name__)

async def eligibility_agent(state: AgentState) -> dict:
    """
    Eligibility Filter node in LangGraph pipeline.
    Fetches candidate donors and filters them according to medical eligibility criteria.
    """
    start_time = time.perf_counter()
    logger.info(f"[{state['trace_id']}] EligibilityAgent started...")
    
    blood_type = state["blood_type"]
    city = state["city"]
    supabase = get_supabase_admin()
    
    try:
        # 1. Fetch potential active matching donors in patient's city
        res = supabase.table("donors")\
            .select("*")\
            .eq("blood_type", blood_type)\
            .eq("city", city)\
            .eq("is_active", True)\
            .order("last_donation_date")\
            .limit(200)\
            .execute()
            
        donors = res.data or []
        logger.info(f"Retrieved {len(donors)} local potential donors for {blood_type} in {city}")
        
        # 2. Local Scarcity Fallback: if we find fewer than 8 candidate donors, expand search to other cities
        if len(donors) < 8:
            logger.warning(f"Local donor count ({len(donors)}) is below the safety threshold. Fetching from other cities...")
            res_other = supabase.table("donors")\
                .select("*")\
                .eq("blood_type", blood_type)\
                .neq("city", city)\
                .eq("is_active", True)\
                .order("last_donation_date")\
                .limit(50)\
                .execute()
            if res_other.data:
                donors.extend(res_other.data)
                logger.info(f"Expanded donor search: Added {len(res_other.data)} non-local donors.")
                
        # 3. Filter candidates through WHO / NBTC clinical guidelines
        patient_profile = state["patient"]
        if not patient_profile:
            err_msg = "Patient profile is missing in State. Cannot evaluate eligibility."
            logger.error(err_msg)
            return {
                "errors": state.get("errors", []) + [err_msg],
                "outcome": "FAILED"
            }
            
        eligible_donors = filter_eligible_donors(donors, patient_profile)
        
        # 4. Handle Empty Pool Escalation
        outcome = None
        errors = state.get("errors", [])
        if not eligible_donors:
            err_msg = f"Zero eligible donors found for patient {state['patient_id']} ({blood_type}). Escalating to emergency inventory fallback."
            logger.error(err_msg)
            errors.append(err_msg)
            outcome = "ESCALATED" # Escalated state triggers inventory scraper node
            
        duration = (time.perf_counter() - start_time) * 1000.0
        timings = state.get("node_timings", {}).copy()
        timings["eligibility_node"] = round(duration, 2)
        
        return {
            "eligible_donors": eligible_donors,
            "outcome": outcome,
            "errors": errors,
            "node_timings": timings
        }
        
    except Exception as e:
        err_msg = f"Eligibility agent error: {e}"
        logger.error(err_msg, exc_info=True)
        return {
            "errors": state.get("errors", []) + [err_msg],
            "outcome": "FAILED"
        }
