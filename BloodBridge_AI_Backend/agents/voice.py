"""
Voice Agent for BloodBridge AI.
Dispatches voice outreach calls and gathers intents via webhook.
"""
import logging
import time
from datetime import datetime, timezone
from models.state import AgentState
from core.database import get_supabase_admin
from services.voice_service import make_bolna_call
from agents.neo4j_match import Neo4jMatcher
from api.websocket import ws_manager

logger = logging.getLogger(__name__)


def _record_voice_attempt(supabase, request_id: str, donor_id: str, call_id: str, status: str):
    """Best-effort insert into voice_call_attempts for retry/SMS fallback tracking."""
    try:
        supabase.table("voice_call_attempts").insert({
            "attempt_id": call_id,
            "request_id": request_id,
            "donor_id": donor_id,
            "status": status,
            "attempts_count": 1,
            "initiated_at": datetime.now(timezone.utc).isoformat(),
        }).execute()
    except Exception as e:
        logger.debug(f"voice_call_attempts insert skipped: {e}")


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

    # Pre-fetch donor phones (blood_chains rows do not store phone)
    donor_ids = [n["donor_id"] for n in updated_chain if n.get("donor_id")]
    phone_map = {}
    if donor_ids:
        donors_res = supabase.table("donors").select("donor_id, phone, name, preferred_language").in_("donor_id", donor_ids).execute()
        phone_map = {d["donor_id"]: d for d in (donors_res.data or [])}
    
    try:
        for idx, chain_node in enumerate(updated_chain):
            if chain_node["status"] != "ALERTED" or chain_node["chain_position"] not in stale_positions:
                continue

            donor_id = chain_node["donor_id"]
            donor = phone_map.get(donor_id) or {}
            phone = chain_node.get("phone") or donor.get("phone")
            if not phone:
                logger.warning(f"VoiceAgent: donor {donor_id} has no phone — skipping voice call.")
                continue

            merged_donor = {**donor, **chain_node, "donor_id": donor_id, "phone": phone}

            result = await make_bolna_call(
                phone=phone,
                donor=merged_donor,
                emergency={
                    "blood_type": state["blood_type"],
                    "hospital_name": state["hospital_name"],
                    "city": state.get("city", ""),
                },
                request_id=request_id
            )

            if result["status"] == "INITIATED":
                calls_placed += 1
                updated_chain[idx]["status"] = "VOICE"
                call_id = result.get("call_id", f"CALL-{donor_id}")

                supabase.table("blood_chains")\
                    .update({"status": "VOICE"})\
                    .eq("request_id", request_id)\
                    .eq("donor_id", donor_id)\
                    .execute()

                await Neo4jMatcher.update_chain_status(request_id, donor_id, patient_id, "VOICE")
                _record_voice_attempt(supabase, request_id, donor_id, call_id, "PLACED")

                await ws_manager.broadcast({
                    "type": "voice_call_active",
                    "donor_id": donor_id,
                    "donor_name": chain_node.get("donor_name", merged_donor.get("name", "Donor")),
                    "request_id": request_id,
                })
            elif result["status"] == "QUEUED":
                logger.info(f"Voice call queued for {donor_id} - outside safe hours.")
            elif result["status"] == "NO_CONSENT":
                logger.info(f"Voice call skipped for {donor_id} - no outreach_voice consent.")
            else:
                logger.warning(f"Voice call failed for {donor_id}: {result.get('error') or result.get('reason')}")
                    
        duration = (time.perf_counter() - start_time) * 1000.0
        timings = state.get("node_timings", {}).copy()
        timings["voice_node"] = round(duration, 2)
        
        logger.info(f"VoiceAgentNode: placed {calls_placed} Bolna call(s) for request {request_id}")
        return {
            "chain": updated_chain,
            "node_timings": timings
        }
    except Exception as e:
        logger.error(f"VoiceAgentNode error: {e}", exc_info=True)
        return {
            "errors": state.get("errors", []) + [f"Voice agent node error: {e}"]
        }
