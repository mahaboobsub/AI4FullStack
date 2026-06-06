"""
Planner Agent for BloodBridge AI.
Determines optimal outreach strategy, channel, tone, and personalization for each donor.
Channels (MVP): Telegram (primary) → Voice via Vapi (secondary, if phone number configured).
SMS removed from MVP stack.
"""
import time
import json
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any

from models.state import AgentState
from core.database import get_supabase_admin
from core.config import get_settings
from core.time_utils import utc_now_iso
from services.demo_phones import is_valid_telegram_chat_id, is_demo_mode


logger = logging.getLogger(__name__)

async def planner_agent(state: AgentState) -> dict:
    """
    Outreach Planner Agent Node.
    Determines outreach strategy (channel, tone, personalization) for each donor in the chain.
    Batches all donors in the chain into a single Gemini call for high-performance generation (<1.5s target).
    """
    start_time = time.perf_counter()
    logger.info(f"[{state['trace_id']}] PlannerAgent started...")
    
    chain = state.get("chain", [])
    request_mode = state.get("request_mode", "emergency")
    patient = state.get("patient") or {}
    request_id = state["request_id"]
    supabase = get_supabase_admin()
    
    if not chain:
        logger.warning("No coordination chain found in state. Skipping planning.")
        return {"outreach_plan": []}
        
    # Truncate chain based on request mode
    # If proactive: chain size = 5
    # If emergency: chain size = 8
    target_size = 5 if request_mode == "proactive" else 8
    active_chain = chain[:target_size]
    
    # 1. Determine general tone and timeout duration
    general_tone = "warm_advance" if request_mode == "proactive" else "urgent"
    timeout_str = "48h" if request_mode == "proactive" else "1min"
    timeout_minutes = 2880 if request_mode == "proactive" else (0.5 if is_demo_mode() else 1)
    
    # 2. Check current time in IST for Tier 2 voice routing (8am-8pm IST)
    # UTC + 5:30
    ist_now = datetime.now(timezone.utc) + timedelta(hours=5, minutes=30)
    is_business_hours = 8 <= ist_now.hour < 20
    
    planner_donors_data = []
    
    # Fetch donor memory and consent details for each donor
    for node in active_chain:
        donor_id = node["donor_id"]
        
        # Fetch donor profile
        donor_res = supabase.table("donors").select("*").eq("donor_id", donor_id).execute()
        donor_profile = donor_res.data[0] if donor_res.data else {}
        
        # Fetch donor memory
        mem_res = supabase.table("donor_memory").select("*").eq("donor_id", donor_id).execute()
        donor_memory = mem_res.data[0] if mem_res.data else {}
        
        # Fetch consent records
        consent_res = supabase.table("consent_records")\
            .select("consent_type")\
            .eq("donor_id", donor_id)\
            .eq("action", "granted")\
            .execute()
        consents = {c["consent_type"] for c in (consent_res.data or [])}
        
        # Determine consents
        has_telegram_consent = "outreach_telegram" in consents or donor_profile.get("consent_outreach", False)
        has_voice_consent = "outreach_voice" in consents or donor_profile.get("consent_outreach", False)

        telegram_chat_id = donor_profile.get("telegram_chat_id")
        if not is_valid_telegram_chat_id(telegram_chat_id):
            telegram_chat_id = None
        phone = donor_profile.get("phone")

        # 2-Tier Channel Routing (MVP — SMS removed):
        # Tier 1: telegram_chat_id AND outreach_telegram consent → 'telegram'
        # Tier 2: phone AND outreach_voice consent AND 8am-8pm IST AND Bolna configured → 'voice_queue'
        # Fallback: telegram (best effort, even without chat_id logged) → 'telegram'
        settings_inner = get_settings()
        bolna_configured = bool(settings_inner.BOLNA_API_KEY and settings_inner.BOLNA_AGENT_ID)

        if telegram_chat_id and has_telegram_consent:
            channel = "telegram"
        elif phone and has_voice_consent and is_business_hours and bolna_configured:
            channel = "voice_queue"
        else:
            channel = "telegram"  # best-effort fallback (Telegram without confirmed chat_id)
            
        planner_donors_data.append({
            "donor_id": donor_id,
            "name": donor_profile.get("name", node["donor_name"]),
            "preferred_language": donor_profile.get("preferred_language", node["preferred_language"]),
            "distance_km": node["distance_km"],
            "channel": channel,
            "telegram_chat_id": telegram_chat_id,
            "phone": phone,
            "memory": {
                "total_interactions": donor_memory.get("total_interactions", 0),
                "streak_days": donor_memory.get("streak_days", 0),
                "badges": donor_memory.get("badges", []),
                "tone_profile": donor_memory.get("tone_profile", "warm")
            }
        })

    # Fallback plan in case Gemini fails
    def run_fallback() -> List[Dict[str, Any]]:
        fallback_plan = []
        for d in planner_donors_data:
            fallback_plan.append({
                "donor_id": d["donor_id"],
                "name": d.get("name", "Donor"),
                "telegram_chat_id": d.get("telegram_chat_id"),
                "phone": d.get("phone"),
                "distance_km": d.get("distance_km", 0.0),
                "preferred_language": d.get("preferred_language", "hi"),
                "channel": d["channel"],
                "tone": "warm_urgent",
                "opening_hook": f"Namaste {d['name']}, hoping you are doing well.",
                "key_message": f"A patient at {patient.get('hospital', 'hospital')} requires matching blood. As a close-proximity donor, your help is urgently needed.",
                "include_badge_mention": False,
                "timeout_minutes": timeout_minutes
            })
        return fallback_plan

    # Batch call all donors into one Gemini request
    settings = get_settings()
    outreach_plan = []
    
    if planner_donors_data:
        system_prompt = (
            "You are an outreach coordinator AI for BloodBridge. "
            "Generate custom greeting hooks and core request messages for blood donors. "
            "Incorporate donor history (badges, streak, previous interactions) if relevant. "
            "Respond ONLY with a valid JSON array of objects matching the input order."
        )
        
        user_content = {
            "request_mode": request_mode,
            "general_tone": general_tone,
            "patient": {
                "hospital": patient.get("hospital", "Hospital"),
                "city": patient.get("city", state.get("city")),
                "blood_type": state.get("blood_type")
            },
            "donors": planner_donors_data
        }
        
        prompt_instruction = (
            "For each donor, generate:\n"
            "1. 'tone': string ('warm_advance', 'urgent', or 'warm_urgent')\n"
            "2. 'opening_hook': A highly personalized 1-sentence greeting in their preferred language (e.g. Hindi/English).\n"
            "3. 'key_message': A compelling 1-to-2 sentence message requesting donation for the patient, mentioning the hospital.\n"
            "4. 'include_badge_mention': boolean (true if donor has badges and they fit naturally in the hook/message, else false).\n"
            "Return EXACTLY a JSON list of objects: "
            "[{\"donor_id\": ..., \"tone\": ..., \"opening_hook\": ..., \"key_message\": ..., \"include_badge_mention\": ...}]"
        )
        
        try:
            async def call_gemini():
                from core.llm_provider import get_reasoning_llm
                llm = get_reasoning_llm()
                full_prompt = f"SYSTEM: {system_prompt}\nUSER: {json.dumps(user_content)}\nINSTRUCTION: {prompt_instruction}"
                resp = await llm.ainvoke(full_prompt)
                
                content = resp.content if isinstance(resp.content, str) else str(resp.content)
                content = content.strip()
                if content.startswith("```json"):
                    content = content.split("```json")[1].split("```")[0].strip()
                elif content.startswith("```"):
                    content = content.split("```")[1].split("```")[0].strip()
                    
                return json.loads(content)
                
            # Set a 1.5s hard timeout limit
            batch_results = await asyncio.wait_for(call_gemini(), timeout=1.5)
            
            # Map batch results back to outreach plan
            results_map = {r["donor_id"]: r for r in batch_results if "donor_id" in r}
            
            for d in planner_donors_data:
                donor_id = d["donor_id"]
                res = results_map.get(donor_id, {})
                
                # Include all donor metadata so outreach agent avoids N+1 DB queries
                outreach_plan.append({
                    "donor_id": donor_id,
                    "name": d.get("name", "Donor"),
                    "telegram_chat_id": d.get("telegram_chat_id"),
                    "phone": d.get("phone"),
                    "distance_km": d.get("distance_km", 0.0),
                    "preferred_language": d.get("preferred_language", "hi"),
                    "channel": d["channel"],
                    "tone": res.get("tone", "warm_urgent"),
                    "opening_hook": res.get("opening_hook", f"Namaste {d['name']}."),
                    "key_message": res.get("key_message", f"Please help save a life at {patient.get('hospital')}."),
                    "include_badge_mention": res.get("include_badge_mention", False),
                    "timeout_minutes": timeout_minutes
                })
                
            logger.info("Successfully generated batched outreach plans using Gemini.")
            
        except asyncio.TimeoutError:
            logger.warning("Gemini outreach planning timed out. Applying warm_urgent fallback.")
            outreach_plan = run_fallback()
        except Exception as e:
            logger.warning(f"Gemini outreach planning failed: {e}. Applying fallback.")
            outreach_plan = run_fallback()
    else:
        logger.info("Skipping Gemini call (no key or empty chain). Applying fallback.")
        outreach_plan = run_fallback()
        
    duration = (time.perf_counter() - start_time) * 1000.0
    timings = state.get("node_timings", {}).copy()
    timings["planner_node"] = round(duration, 2)
    
    # Store channel strategy (e.g. 'hybrid' or determined by predominant channel)
    channels = [o["channel"] for o in outreach_plan]
    strategy = "hybrid"
    if channels:
        if all(c == "telegram" for c in channels):
            strategy = "telegram_only"
        elif all(c == "voice_queue" for c in channels):
            strategy = "voice_only"

    return {
        "chain": active_chain,
        "outreach_plan": outreach_plan,
        "channel_strategy": strategy,
        "node_timings": timings
    }
