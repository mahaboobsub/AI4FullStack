"""
Conflict Resolver Agent for BloodBridge AI.
Resolves competing donor conflicts when two CRITICAL patients need the same rare donor.
"""
import json
import asyncio
import logging
from typing import Dict, Any
from models.state import AgentState
from core.database import get_supabase_admin
from core.config import get_settings


logger = logging.getLogger(__name__)

async def conflict_resolver_agent(state: AgentState) -> dict:
    """
    Conflict Resolver Agent Node.
    Resolves competing donor conflicts when two CRITICAL patients need the same rare donor.
    Uses Gemini to clinically triage and determine priority, with a 3-second hard timeout fallback.
    """
    logger.info(f"[{state['trace_id']}] ConflictResolverAgent started...")
    
    patient_a = state["patient"]
    chain = state.get("chain", [])
    request_id = state["request_id"]
    supabase = get_supabase_admin()
    
    if not patient_a or not chain:
        return {"conflict_detected": False}
        
    # 1. Identify which donor is in conflict.
    # We find other IN_PROGRESS CRITICAL requests
    try:
        res = supabase.table("emergency_requests")\
            .select("request_id, patient_id")\
            .eq("status", "IN_PROGRESS")\
            .eq("priority", "CRITICAL")\
            .neq("request_id", request_id)\
            .execute()
            
        other_requests = res.data or []
        conflicting_request = None
        conflicting_donor_id = None
        
        if other_requests:
            our_donor_ids = {n["donor_id"] for n in chain}
            other_req_ids = [r["request_id"] for r in other_requests]
            
            chains_res = supabase.table("blood_chains")\
                .select("request_id, donor_id")\
                .in_("request_id", other_req_ids)\
                .execute()
                
            other_chains = chains_res.data or []
            for oc in other_chains:
                if oc["donor_id"] in our_donor_ids:
                    conflicting_donor_id = oc["donor_id"]
                    conflicting_request = next(r for r in other_requests if r["request_id"] == oc["request_id"])
                    break
                    
        # If no actual conflicting donor is found, clear conflict flag and return
        if not conflicting_donor_id or not conflicting_request:
            logger.info("Conflict resolver called but no active conflicting request/donor found.")
            return {"conflict_detected": False}
            
        # 2. Fetch Patient B details
        patient_b_res = supabase.table("patients")\
            .select("*")\
            .eq("patient_id", conflicting_request["patient_id"])\
            .execute()
            
        if not patient_b_res.data:
            logger.warning(f"Conflicting patient {conflicting_request['patient_id']} not found.")
            return {"conflict_detected": False}
            
        patient_b = patient_b_res.data[0]
        
        # Get donor details
        donor_res = supabase.table("donors")\
            .select("*")\
            .eq("donor_id", conflicting_donor_id)\
            .execute()
            
        donor = donor_res.data[0] if donor_res.data else {}
        
        # 3. Call Gemini to triage
        settings = get_settings()
        
        system_prompt = (
            "Clinical triage AI. Two Thalassemia patients need same rare donor. "
            "Respond ONLY with valid JSON."
        )
        
        user_content = {
            "conflict_type": "rare_donor_shared",
            "donor": {
                "donor_id": donor.get("donor_id"),
                "blood_type": donor.get("blood_type"),
                "kell_negative": donor.get("kell_negative"),
                "duffy_negative": donor.get("duffy_negative"),
                "kidd_negative": donor.get("kidd_negative")
            },
            "patient_a": {
                "patient_id": patient_a.get("patient_id"),
                "age": patient_a.get("age"),
                "hemoglobin": patient_a.get("hemoglobin"),
                "urgency_score": state.get("urgency_result", {}).get("urgency_score", 5.0),
                "status": patient_a.get("status"),
                "antibodies": {
                    "kell": patient_a.get("antibody_kell"),
                    "duffy": patient_a.get("antibody_duffy"),
                    "kidd": patient_a.get("antibody_kidd")
                }
            },
            "patient_b": {
                "patient_id": patient_b.get("patient_id"),
                "age": patient_b.get("age"),
                "hemoglobin": patient_b.get("hemoglobin"),
                "urgency_score": patient_b.get("urgency_score", 5.0),
                "status": patient_b.get("status"),
                "antibodies": {
                    "kell": patient_b.get("antibody_kell"),
                    "duffy": patient_b.get("antibody_duffy"),
                    "kidd": patient_b.get("antibody_kidd")
                }
            },
            "question": "Which patient should be prioritized for this shared donor, and how should outreach be scheduled?"
        }
        
        # Fallback comparison logic
        def run_fallback() -> Dict[str, Any]:
            score_a = state.get("urgency_result", {}).get("urgency_score", 5.0)
            score_b = patient_b.get("urgency_score", 5.0)
            p_id = patient_a["patient_id"] if score_a >= score_b else patient_b["patient_id"]
            sec_id = patient_b["patient_id"] if p_id == patient_a["patient_id"] else patient_a["patient_id"]
            return {
                "priority_patient_id": p_id,
                "secondary_patient_id": sec_id,
                "justification": f"Fallback applied: Patient {p_id} has higher or equal urgency score ({max(score_a, score_b)} vs {min(score_a, score_b)}).",
                "confidence": 0.7,
                "recommendation": f"Prioritize patient {p_id} based on urgency metrics."
            }
            
        triage_result = None
        try:
            # hard timeout limit 3.0s
            async def call_gemini():
                from core.llm_provider import get_reasoning_llm
                llm = get_reasoning_llm()
                prompt = f"SYSTEM: {system_prompt}\nUSER: {json.dumps(user_content)}"
                resp = await llm.ainvoke(prompt)
                # Clean response string to parse JSON
                content = resp.content if isinstance(resp.content, str) else str(resp.content)
                content = content.strip()
                if content.startswith("```json"):
                    content = content.split("```json")[1].split("```")[0].strip()
                elif content.startswith("```"):
                    content = content.split("```")[1].split("```")[0].strip()
                return json.loads(content)
                
            triage_result = await asyncio.wait_for(call_gemini(), timeout=3.0)
            logger.info(f"Gemini conflict resolution returned successfully: {triage_result}")
        except asyncio.TimeoutError:
            logger.warning("Gemini conflict resolution timed out (3s hard limit). Using fallback.")
            triage_result = run_fallback()
        except Exception as e:
            logger.warning(f"Gemini conflict resolution failed: {e}. Using fallback.")
            triage_result = run_fallback()
            
        # 4. Reorder chain: prioritized patient's donors first.
        # If Patient B is prioritized, move conflicting donor to the end of Patient A's chain
        priority_id = triage_result.get("priority_patient_id")
        reordered_chain = []
        
        if priority_id == patient_b["patient_id"]:
            # Move conflicting donor to the end
            conflicting_node = None
            other_nodes = []
            for node in chain:
                if node["donor_id"] == conflicting_donor_id:
                    conflicting_node = node
                else:
                    other_nodes.append(node)
                    
            if conflicting_node:
                # Rebuild positions
                for i, node in enumerate(other_nodes):
                    node["chain_position"] = i + 1
                    # Update status if position changed (only index 0 gets alerted initially)
                    node["status"] = "ALERTED" if i == 0 else "PENDING"
                    
                conflicting_node["chain_position"] = len(chain)
                conflicting_node["status"] = "PENDING"
                
                reordered_chain = other_nodes + [conflicting_node]
                logger.info(f"Reordered chain for Patient A: moved conflicting donor {conflicting_donor_id} to position {len(chain)}")
            else:
                reordered_chain = chain
        else:
            # Patient A is prioritized; keep the chain as is
            reordered_chain = chain
            logger.info("Patient A is prioritized. Chain order unchanged.")
            
        # Update Neo4j and Supabase with the reordered chain
        from agents.neo4j_match import Neo4jMatcher
        # Write to Neo4j
        await Neo4jMatcher.create_chain(request_id, patient_a["patient_id"], reordered_chain)  # type: ignore
        
        # Write to Supabase (delete old chain first to prevent unique constraint conflicts)
        supabase.table("blood_chains").delete().eq("request_id", request_id).execute()
        
        supabase_chain_data = []
        for node in reordered_chain:
            supabase_chain_data.append({
                "request_id": request_id,
                "donor_id": node["donor_id"],
                "donor_name": node["donor_name"],
                "chain_position": node["chain_position"],
                "status": node["status"],
                "antigen_score": node["antigen_score"],
                "alerted_at": node["alerted_at"],
                "confirmed_at": node["confirmed_at"]
            })
        if supabase_chain_data:
            supabase.table("blood_chains").insert(supabase_chain_data).execute()
            
        resolution_str = f"Priority: {priority_id}. Justification: {triage_result.get('justification')}"
        
        return {
            "chain": reordered_chain,
            "conflict_detected": True,
            "conflict_resolution": resolution_str
        }
        
    except Exception as e:
        logger.error(f"ConflictResolverAgent error: {e}", exc_info=True)
        return {
            "errors": state.get("errors", []) + [f"Conflict resolver error: {e}"],
            "conflict_detected": False
        }
