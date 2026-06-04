"""
Chain Repair and Inventory Agents for BloodBridge AI.
Fixes collapsed donor chains and queries emergency inventory fallbacks.
"""
import logging
import re
import time
from datetime import datetime, timezone, timedelta
from core.database import get_supabase_admin
from core.neo4j_client import get_driver
from core.config import get_settings
from models.state import AgentState
from agents.neo4j_match import Neo4jMatcher
from api.websocket import ws_manager

logger = logging.getLogger(__name__)

async def chain_repair_agent(state: AgentState) -> dict:
    """
    Chain Repair Agent Node.
    Finds replacement donors for stale positions, registers them, and prepares outreach plans.
    """
    start_time = time.perf_counter()
    logger.info(f"[{state['trace_id']}] ChainRepairAgent started...")
    
    request_id = state["request_id"]
    patient_id = state["patient_id"]
    city = state["city"]
    stale_positions = state.get("stale_positions", [])
    supabase = get_supabase_admin()
    
    if not stale_positions:
        return {"chain_break_detected": False}
        
    try:
        # 1. Check repair attempts notes from emergency_requests
        req_res = supabase.table("emergency_requests").select("notes").eq("request_id", request_id).execute()
        notes = req_res.data[0].get("notes") or "" if req_res.data else ""
        
        match = re.search(r"Repair attempts: (\d+)", notes)
        attempts = int(match.group(1)) if match else 0
        
        if attempts >= 3:
            logger.warning(f"Max repair attempts (3) reached for request {request_id}. Escalating to InventoryAgent.")
            return {
                "outcome": "ESCALATED",
                "stale_positions": [],
                "chain_break_detected": False
            }
            
        # Get active chain nodes to exclude from search
        chain_res = supabase.table("blood_chains").select("donor_id, chain_position").eq("request_id", request_id).execute()
        db_chain = chain_res.data or []
        exclude_donor_ids = [n["donor_id"] for n in db_chain if n.get("donor_id")]
        
        # Build map of chain position to old donor_id
        pos_to_donor = {n["chain_position"]: n["donor_id"] for n in db_chain}
        
        driver = get_driver()
        repaired_nodes = []
        outreach_plan = []
        
        # Determine general tone and timeout duration
        request_mode = state.get("request_mode", "emergency")
        timeout_minutes = 2880 if request_mode == "proactive" else 7
        
        # Check current time in IST for Tier 2 voice routing (8am-8pm IST)
        ist_now = datetime.now(timezone.utc) + timedelta(hours=5, minutes=30)
        is_business_hours = 8 <= ist_now.hour < 20
        
        for stale_pos in stale_positions:
            old_donor_id = pos_to_donor.get(stale_pos)
            if old_donor_id:
                # Mark old donor relationship as DECLINED in Neo4j
                await Neo4jMatcher.update_chain_status(request_id, old_donor_id, patient_id, "DECLINED")
                # Mark old donor in Supabase as DECLINED
                supabase.table("blood_chains")\
                    .update({"status": "DECLINED", "declined_at": datetime.utcnow().isoformat() + "Z"})\
                    .eq("request_id", request_id)\
                    .eq("donor_id", old_donor_id)\
                    .execute()
            
            # Find next compatible donor using Neo4j precomputed compatible edges
            query = """
            MATCH (p:Patient {patient_id: $patient_id})
            MATCH (d:Donor)-[c:COMPATIBLE_WITH]->(p)
            WHERE d.is_active = true
              AND d.city = $city
              AND d.blood_type = p.blood_type
              AND (NOT p.antibody_kell OR d.kell_negative = true)
              AND (NOT p.antibody_duffy OR d.duffy_negative = true)
              AND (NOT p.antibody_kidd OR d.kidd_negative = true)
              AND (d.last_donation_date IS NULL OR date() - d.last_donation_date >= 56)
              AND NOT d.donor_id IN $exclude_donor_ids
            WITH d, c, p,
                 point.distance(
                     point({latitude: d.lat, longitude: d.lng}),
                     point({latitude: p.lat, longitude: p.lng})
                 ) AS distance_m
            ORDER BY d.churn_score ASC, c.antigen_score DESC, distance_m ASC
            LIMIT 1
            RETURN d.donor_id AS donor_id, d.name AS name, d.telegram_chat_id AS telegram_chat_id,
                   d.phone AS phone, d.preferred_language AS preferred_language,
                   d.churn_score AS churn_score, d.blood_type AS blood_type,
                   c.antigen_score AS antigen_score,
                   distance_m / 1000.0 AS distance_km
            """
            
            new_donor = None
            async with driver.session() as session:
                res = await session.run(query, {
                    "patient_id": patient_id,
                    "city": city,
                    "exclude_donor_ids": exclude_donor_ids
                })
                record = await res.single()
                if record:
                    new_donor = dict(record)
                    
            if new_donor:
                # Exclude this new donor from next stale positions in this iteration
                exclude_donor_ids.append(new_donor["donor_id"])
                
                # Determine channel
                telegram_chat_id = new_donor.get("telegram_chat_id")
                phone = new_donor.get("phone")
                
                # Fetch consent
                consent_res = supabase.table("consent_records")\
                    .select("consent_type")\
                    .eq("donor_id", new_donor["donor_id"])\
                    .eq("action", "granted")\
                    .execute()
                consents = {c["consent_type"] for c in (consent_res.data or [])}
                
                has_telegram_consent = "outreach_telegram" in consents or telegram_chat_id is not None
                has_voice_consent = "outreach_voice" in consents
                has_sms_consent = "outreach_sms" in consents or phone is not None
                
                channel = "sms_queue"
                if telegram_chat_id and has_telegram_consent:
                    channel = "telegram"
                elif phone and has_voice_consent and is_business_hours:
                    channel = "voice_queue"
                elif phone and has_sms_consent:
                    channel = "sms_queue"
                    
                # Update blood_chains table in Supabase
                supabase.table("blood_chains").delete().eq("request_id", request_id).eq("chain_position", stale_pos).execute()
                
                supabase.table("blood_chains").insert({
                    "request_id": request_id,
                    "donor_id": new_donor["donor_id"],
                    "donor_name": new_donor["name"],
                    "chain_position": stale_pos,
                    "status": "PENDING",
                    "antigen_score": new_donor["antigen_score"],
                    "notes": f"Repaired position. Previous: {old_donor_id}"
                }).execute()
                
                # Create Neo4j IN_CHAIN edge
                async with driver.session() as session:
                    await session.run(
                        """
                        MATCH (d:Donor {donor_id: $new_donor_id})
                        MATCH (p:Patient {patient_id: $patient_id})
                        MERGE (d)-[r:IN_CHAIN {request_id: $request_id}]->(p)
                        SET r.chain_position = $chain_position,
                            r.status = 'PENDING',
                            r.antigen_score = $antigen_score
                        """,
                        {
                            "new_donor_id": new_donor["donor_id"],
                            "patient_id": patient_id,
                            "request_id": request_id,
                            "chain_position": stale_pos,
                            "antigen_score": new_donor["antigen_score"]
                        }
                    )
                    
                # Generate repair message (Groq, shorter/more urgent tone)
                msg = None
                settings = get_settings()
                if settings.GROQ_API_KEY:
                    try:
                        from langchain_groq import ChatGroq
                        llm = ChatGroq(
                            model="llama-3.3-70b-versatile",
                            api_key=settings.GROQ_API_KEY,
                            temperature=0.3
                        )
                        repair_prompt = (
                            f"Generate an extremely short and urgent emergency blood donation request. "
                            f"The previous donor failed, so we need a replacement immediately. "
                            f"Donor: {new_donor['name']}. Language: {new_donor['preferred_language']}. "
                            f"Patient needs {state['blood_type']} at {state.get('hospital_name')}. "
                            f"Must be in their preferred language, under 80 words, ending with 'Reply YES to confirm'."
                        )
                        resp = await llm.ainvoke([
                            ("system", "You are BloodBridge AI, coordinator for emergency blood donation. Keep it extremely urgent and concise."),
                            ("user", repair_prompt)
                        ])
                        msg = resp.content.strip()
                    except Exception as e:
                        logger.warning(f"Groq repair message gen failed: {e}")
                        
                if not msg:
                    from agents.outreach import FALLBACK_TEMPLATES
                    lang_key = new_donor.get("preferred_language", "hi").lower()[:2]
                    template = FALLBACK_TEMPLATES.get(lang_key, FALLBACK_TEMPLATES['hi'])
                    msg = template.format(
                        blood_type=state['blood_type'],
                        hospital=state.get("hospital_name")
                    ) + " (Urgent repair request)"
                    
                outreach_plan.append({
                    "donor_id": new_donor["donor_id"],
                    "name": new_donor["name"],
                    "telegram_chat_id": telegram_chat_id,
                    "phone": phone,
                    "preferred_language": new_donor["preferred_language"],
                    "distance_km": new_donor["distance_km"],
                    "channel": channel,
                    "tone": "shorter_urgent",
                    "message": msg,
                    "timeout_minutes": timeout_minutes
                })
                
                repaired_nodes.append({
                    "donor_id": new_donor["donor_id"],
                    "donor_name": new_donor["name"],
                    "chain_position": stale_pos,
                    "status": "PENDING",
                    "antigen_score": new_donor["antigen_score"],
                    "telegram_chat_id": telegram_chat_id,
                    "phone": phone,
                    "preferred_language": new_donor["preferred_language"],
                    "distance_km": new_donor["distance_km"]
                })
                
                # Broadcast WebSocket {type:'chain_repaired', new_donor_name, position}
                await ws_manager.broadcast({
                    "type": "chain_repaired",
                    "request_id": request_id,
                    "new_donor_name": new_donor["name"],
                    "position": stale_pos
                })
                
        # Update attempts
        attempts += len(repaired_nodes)
        new_notes = re.sub(r"Repair attempts: \d+", f"Repair attempts: {attempts}", notes) if match else f"{notes}\nRepair attempts: {attempts}".strip()
        supabase.table("emergency_requests").update({"notes": new_notes}).eq("request_id", request_id).execute()
        
        # Re-build state chain
        updated_chain = state.get("chain", []).copy()
        for node in repaired_nodes:
            pos = node["chain_position"]
            found_old_pos = False
            for idx, old_node in enumerate(updated_chain):
                if old_node["chain_position"] == pos:
                    updated_chain[idx] = node
                    found_old_pos = True
                    break
            if not found_old_pos:
                updated_chain.append(node)
                
        duration = (time.perf_counter() - start_time) * 1000.0
        logger.info(f"ChainRepair: {len(repaired_nodes)} positions repaired in {int(duration)}ms")
        
        return {
            "chain": updated_chain,
            "outreach_plan": outreach_plan,
            "chain_break_detected": False,
            "stale_positions": [],
            "node_timings": {**state.get("node_timings", {}), "repair_node": round(duration, 2)}
        }
    except Exception as e:
        logger.error(f"ChainRepairAgent error: {e}", exc_info=True)
        return {
            "errors": state.get("errors", []) + [f"Chain repair error: {e}"],
            "chain_break_detected": False
        }

async def inventory_agent(state: AgentState) -> dict:
    """
    Inventory Agent Node.
    Scrapes nearest stocks from blood banks and alerts staff.
    """
    start_time = time.perf_counter()
    logger.info(f"[{state['trace_id']}] InventoryAgent started...")
    
    request_id = state["request_id"]
    patient_id = state["patient_id"]
    city = state["city"]
    blood_type = state["blood_type"]
    supabase = get_supabase_admin()
    
    try:
        # 1. Call blood_bank_scraper.get_nearest_banks_with_stock(city, blood_type)
        from services.blood_bank_scraper import get_nearest_banks_with_stock
        banks = await get_nearest_banks_with_stock(city, blood_type)
        
        # 2. Alert staff via ntfy.sh: "⚠️ CHAIN FAILED — nearest banks: {names}"
        from services.alerts import alert_escalation
        await alert_escalation(patient_id, banks)
        
        # 3. Update emergency_request status='ESCALATED'
        supabase.table("emergency_requests")\
            .update({"status": "ESCALATED", "updated_at": datetime.utcnow().isoformat() + "Z"})\
            .eq("request_id", request_id)\
            .execute()
            
        # 4. Send Telegram to staff: bank list + distances + contacts
        bank_details = []
        for idx, b in enumerate(banks[:5]):
            bank_details.append(f"{idx+1}. {b['name']} ({b['units']} units) - Contact: {b['contact']}")
            
        bank_list_str = "\n".join(bank_details) if bank_details else "No available stocks found in nearby blood banks."
        
        telegram_message = (
            f"🚨 *EMERGENCY PIPELINE ESCALATION*\n\n"
            f"All donor chain coordination attempts failed or timed out for Patient *{patient_id}* ({blood_type}) in {city}.\n\n"
            f"*Nearest Blood Banks with Stock:*\n{bank_list_str}"
        )
        
        # Query staff chat ids
        staff_res = supabase.table("staff").select("telegram_chat_id").eq("is_active", True).execute()
        from services.telegram_bot import send_telegram_message
        for s in (staff_res.data or []):
            chat_id = s.get("telegram_chat_id")
            if chat_id:
                await send_telegram_message(chat_id, telegram_message)
                
        # 5. Broadcast websocket
        await ws_manager.broadcast({
            "type": "emergency_escalated",
            "request_id": request_id,
            "patient_id": patient_id,
            "banks": banks
        })
        
        duration = (time.perf_counter() - start_time) * 1000.0
        timings = state.get("node_timings", {}).copy()
        timings["inventory_node"] = round(duration, 2)
        
        return {
            "outcome": "ESCALATED",
            "chain_break_detected": False,
            "stale_positions": [],
            "node_timings": timings
        }
    except Exception as e:
        logger.error(f"InventoryAgent error: {e}", exc_info=True)
        return {
            "outcome": "FAILED",
            "errors": state.get("errors", []) + [f"Inventory agent error: {e}"]
        }
