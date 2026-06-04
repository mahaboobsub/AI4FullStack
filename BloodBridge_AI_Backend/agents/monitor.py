"""
Chain Monitor Agent for BloodBridge AI.
Monitors donor responses, checks for timeouts, and updates coordination outcomes.
"""
import time
import logging
from datetime import datetime
from models.state import AgentState
from core.database import get_supabase_admin
from agents.neo4j_match import Neo4jMatcher
from api.websocket import ws_manager

logger = logging.getLogger(__name__)

async def chain_monitor_agent(state: AgentState) -> dict:
    """
    Chain Monitor Agent Node.
    Monitors response status, checks for timeouts, and triggers repair loops if needed.
    """
    start_time = time.perf_counter()
    logger.info(f"[{state['trace_id']}] ChainMonitorAgent started...")
    
    request_id = state["request_id"]
    patient_id = state["patient_id"]
    supabase = get_supabase_admin()
    
    try:
        # 1. Query Neo4j stale ALERTED nodes for this request_id (older than 7 minutes)
        stale_nodes = await Neo4jMatcher.get_stale_alerted_nodes(timeout_minutes=7)
        # Filter for this request_id
        stale_this_request = [n for n in stale_nodes if n.get("request_id") == request_id]
        stale_positions = [int(n["chain_position"]) for n in stale_this_request]
        
        # 2. Query blood_chains CONFIRMED count from Supabase
        confirmed_res = supabase.table("blood_chains")\
            .select("chain_position", count="exact")\
            .eq("request_id", request_id)\
            .eq("status", "CONFIRMED")\
            .execute()
            
        confirmed_count = confirmed_res.count or 0
        
        # 3. If confirmed >= 1: state['outcome'] = 'SUCCESS'; return
        outcome = state.get("outcome")
        if confirmed_count >= 1:
            logger.info(f"ChainMonitorAgent: Patient {patient_id} has {confirmed_count} confirmed donor(s). Request SUCCESS.")
            outcome = "SUCCESS"
            return {
                "outcome": outcome,
                "chain_break_detected": False,
                "stale_positions": [],
                "node_timings": {**state.get("node_timings", {}), "monitor_node": round((time.perf_counter() - start_time) * 1000.0, 2)}
            }
            
        # 4. Fetch the full chain from Supabase to check if all are declined or stale
        chain_res = supabase.table("blood_chains")\
            .select("chain_position, status")\
            .eq("request_id", request_id)\
            .execute()
            
        db_chain = chain_res.data or []
        
        # Calculate if all are declined/stale
        all_failed = False
        if db_chain:
            failed_count = 0
            for node in db_chain:
                pos = node["chain_position"]
                status = node["status"]
                if status == "DECLINED" or pos in stale_positions:
                    failed_count += 1
            if failed_count >= len(db_chain):
                all_failed = True
                
        if all_failed:
            logger.warning(f"All {len(db_chain)} donors in chain for patient {patient_id} declined or timed out. Escalating request.")
            outcome = "ESCALATED"
            
        # 5. state['stale_positions'] = [stale chain positions]
        # 6. state['chain_break_detected'] = len(stale) > 0
        chain_break_detected = len(stale_positions) > 0
        
        # 7. Broadcast WebSocket {type:'chain_monitor_update', ...}
        await ws_manager.broadcast({
            "type": "chain_monitor_update",
            "request_id": request_id,
            "patient_id": patient_id,
            "confirmed_count": confirmed_count,
            "stale_positions": stale_positions,
            "chain_break_detected": chain_break_detected,
            "outcome": outcome
        })
        
        duration = (time.perf_counter() - start_time) * 1000.0
        timings = state.get("node_timings", {}).copy()
        timings["monitor_node"] = round(duration, 2)
        
        return {
            "stale_positions": stale_positions,
            "chain_break_detected": chain_break_detected,
            "outcome": outcome,
            "node_timings": timings
        }
    except Exception as e:
        logger.error(f"ChainMonitorAgent error: {e}", exc_info=True)
        return {
            "errors": state.get("errors", []) + [f"Chain monitor error: {e}"],
            "outcome": "FAILED"
        }
