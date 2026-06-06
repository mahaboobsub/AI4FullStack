"""
Voice Agent for BloodBridge AI.
Dispatches voice outreach calls and gathers intents via webhook.
"""
import logging
import time
from models.state import AgentState
from core.database import get_supabase_admin
from services.voice_service import make_bolna_call
from agents.neo4j_match import Neo4jMatcher
from api.websocket import ws_manager

logger = logging.getLogger(__name__)

async def voice_agent_node(state: AgentState) -> dict:
    """
    Voice Agent Node in LangGraph.
    Places calls via Bolna.ai to no-response alerted donors.
    """
    start_time = time.perf_counter()
    logger.info(f"[{state['trace_id']}] VoiceAgentNode started...")
    
    request_id = state["request_id"]
    patient_id = state["patient_id"]
    chain = state.get("chain", [])
    supabase = get_supabase_admin()
    
    updated_chain = chain.copy()
    calls_placed = 0
    stale_positions = state.get("stale_positions", [])
    
    try:
        for idx, chain_node in enumerate(updated_chain):
            if chain_node["status"] == "ALERTED" and chain_node.get("phone") and chain_node["chain_position"] in stale_positions:
                donor_id = chain_node["donor_id"]
                
                # Fetch donor profile
                donor_res = supabase.table("donors").select("*").eq("donor_id", donor_id).execute()
                if not donor_res.data:
                    continue
                donor = donor_res.data[0]
                
                # Place call
                result = await make_bolna_call(
                    phone=chain_node["phone"],
                    donor=donor,
                    emergency={
                        "blood_type": state["blood_type"],
                        "hospital_name": state["hospital_name"]
                    },
                    request_id=request_id
                )
                
                if result["status"] == "INITIATED":
                    calls_placed += 1
                    # Update status to VOICE
                    updated_chain[idx]["status"] = "VOICE"
                    
                    # Update Supabase blood_chains status to VOICE
                    supabase.table("blood_chains")\
                        .update({"status": "VOICE"})\
                        .eq("request_id", request_id)\
                        .eq("donor_id", donor_id)\
                        .execute()
                        
                    # Update Neo4j status
                    await Neo4jMatcher.update_chain_status(request_id, donor_id, patient_id, "VOICE")
                    
                    # Broadcast WebSocket
                    await ws_manager.broadcast({
                        "type": "voice_call_active",
                        "donor_id": donor_id,
                        "donor_name": chain_node["donor_name"]
                    })
                elif result["status"] == "QUEUED":
                    logger.info(f"Voice call queued for {donor_id} - outside safe hours.")
                elif result["status"] == "NO_CONSENT":
                    logger.info(f"Voice call skipped for {donor_id} - no outreach_voice consent.")
                    
        duration = (time.perf_counter() - start_time) * 1000.0
        timings = state.get("node_timings", {}).copy()
        timings["voice_node"] = round(duration, 2)
        
        return {
            "chain": updated_chain,
            "node_timings": timings
        }
    except Exception as e:
        logger.error(f"VoiceAgentNode error: {e}", exc_info=True)
        return {
            "errors": state.get("errors", []) + [f"Voice agent node error: {e}"]
        }
