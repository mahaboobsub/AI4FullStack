"""
Outcome and Escalation Agents for BloodBridge AI.
Closes completed requests or triggers manual staff intervention loops.
"""
import logging
import time
from datetime import datetime
from models.state import AgentState
from core.database import get_supabase_admin
from api.websocket import ws_manager
from services.transfusion_calendar import mark_schedule_completed_by_request

logger = logging.getLogger(__name__)

async def outcome_agent(state: AgentState) -> dict:
    """
    Outcome Agent Node.
    Saves final request results, cleans up donor chain, and handles calendar completions.
    """
    start_time = time.perf_counter()
    logger.info(f"[{state['trace_id']}] OutcomeAgent started...")
    
    request_id = state["request_id"]
    patient_id = state["patient_id"]
    outcome = state.get("outcome", "SUCCESS")
    request_mode = state.get("request_mode", "emergency")
    supabase = get_supabase_admin()
    
    # Map 'SUCCESS' to 'COMPLETED' for database storage
    db_status = "COMPLETED" if outcome == "SUCCESS" else (outcome if outcome in ["COMPLETED", "ESCALATED"] else "CANCELLED")
    
    try:
        # 1. Update emergency_request: status=db_status, completed_at=NOW
        now_str = datetime.utcnow().isoformat() + "Z"
        supabase.table("emergency_requests")\
            .update({"status": db_status, "completed_at": now_str, "updated_at": now_str})\
            .eq("request_id", request_id)\
            .execute()
            
        # 2. Update blood_chains: confirmed → COMPLETED, pending/alerted → DECLINED (released)
        # First, find confirmed donors in this request
        chain_res = supabase.table("blood_chains").select("donor_id, donor_name, status").eq("request_id", request_id).execute()
        db_chain = chain_res.data or []
        
        confirmed_count = 0
        confirmed_donors = []
        
        for node in db_chain:
            donor_id = node.get("donor_id")
            status = node.get("status")
            if status == "CONFIRMED":
                confirmed_count += 1
                if donor_id:
                    confirmed_donors.append({
                        "donor_id": donor_id,
                        "name": node.get("donor_name", "Donor")
                    })
                    
        # Update confirmed to COMPLETED
        supabase.table("blood_chains")\
            .update({"status": "COMPLETED"})\
            .eq("request_id", request_id)\
            .eq("status", "CONFIRMED")\
            .execute()
            
        # Update pending/alerted/sms/voice to DECLINED (released)
        for stat in ["PENDING", "ALERTED", "SMS", "VOICE"]:
            supabase.table("blood_chains")\
                .update({"status": "DECLINED", "notes": "Released at request finalization"})\
                .eq("request_id", request_id)\
                .eq("status", stat)\
                .execute()
                
        # Update Neo4j IN_CHAIN edges
        from agents.neo4j_match import Neo4jMatcher
        for node in db_chain:
            donor_id = node.get("donor_id")
            if donor_id:
                new_status = "COMPLETED" if node["status"] == "CONFIRMED" else "DECLINED"
                await Neo4jMatcher.update_chain_status(request_id, donor_id, patient_id, new_status)
                
        # 3. Update patient: transfusion_count += confirmed_count
        if confirmed_count > 0:
            patient_res = supabase.table("patients").select("transfusion_count").eq("patient_id", patient_id).execute()
            current_count = patient_res.data[0].get("transfusion_count", 0) if patient_res.data else 0
            supabase.table("patients")\
                .update({"transfusion_count": current_count + confirmed_count})\
                .eq("patient_id", patient_id)\
                .execute()
                
        # 4. For each confirmed donor: donation_count+1, lives_saved+1, last_donation_date=today, churn_score=0.1, update donor_memory
        today_str = datetime.utcnow().date().isoformat()
        for donor in confirmed_donors:
            donor_id = donor["donor_id"]
            d_res = supabase.table("donors").select("donation_count, lives_saved").eq("donor_id", donor_id).execute()
            if d_res.data:
                d_count = d_res.data[0].get("donation_count", 0) or 0
                l_saved = d_res.data[0].get("lives_saved", 0) or 0
            else:
                d_count = 0
                l_saved = 0
                
            supabase.table("donors").update({
                "donation_count": d_count + 1,
                "lives_saved": l_saved + 1,
                "last_donation_date": today_str,
                "churn_score": 0.1,
                "churn_risk": "LOW"
            }).eq("donor_id", donor_id).execute()
            
            # Update donor memory last_interaction and streak
            mem_res = supabase.table("donor_memory").select("total_interactions, streak_days").eq("donor_id", donor_id).execute()
            if mem_res.data:
                total_int = mem_res.data[0].get("total_interactions", 0) or 0
                streak = mem_res.data[0].get("streak_days", 0) or 0
                new_streak = streak + 30
            else:
                total_int = 0
                new_streak = 30
                
            supabase.table("donor_memory").upsert({
                "donor_id": donor_id,
                "last_interaction": now_str,
                "total_interactions": total_int + 1,
                "streak_days": new_streak
            }).execute()
            
        # 5. Complete agent_trace: outcome, total_ms, nodes_json
        duration = (time.perf_counter() - start_time) * 1000.0
        timings = state.get("node_timings", {}).copy()
        timings["outcome_node"] = round(duration, 2)
        
        total_ms = sum(timings.values())
        error_msg = "\n".join(state.get("errors", [])) or None
        
        supabase.table("agent_traces").insert({
            "trace_id": state["trace_id"],
            "request_id": request_id,
            "patient_id": patient_id,
            "outcome": outcome,
            "completed_at": now_str,
            "total_ms": int(total_ms),
            "node_count": len(timings),
            "nodes_json": timings,
            "error_message": error_msg
        }).execute()
        
        # 6. Broadcast WebSocket {type:'emergency_completed', request_id, patient_id, outcome}
        await ws_manager.broadcast({
            "type": "emergency_completed",
            "request_id": request_id,
            "patient_id": patient_id,
            "outcome": outcome
        })
        
        # 7. If request_mode='proactive': call transfusion_calendar.mark_schedule_completed_by_request()
        if request_mode == "proactive":
            await mark_schedule_completed_by_request(request_id)
            
        return {
            "outcome": outcome,
            "node_timings": timings
        }
    except Exception as e:
        logger.error(f"OutcomeAgent error: {e}", exc_info=True)
        return {
            "errors": state.get("errors", []) + [f"Outcome agent error: {e}"],
            "outcome": "FAILED"
        }

async def escalate_agent(state: AgentState) -> dict:
    """Escalates requests to staff."""
    logger.info(f"[{state['trace_id']}] EscalateAgent called.")
    return {"outcome": "ESCALATED"}
