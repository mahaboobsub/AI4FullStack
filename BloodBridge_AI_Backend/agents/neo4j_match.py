"""
Neo4j Graph Database Matcher and Chain Handler for BloodBridge AI.
Handles high-performance matching queries and donor chain state modifications.
"""
import time
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from models.state import AgentState
from core.neo4j_client import get_driver, get_neo4j
from core.database import get_supabase_admin
from ml.antigen_scorer import compute_antigen_score, get_eligibility_flags
from api.websocket import ws_manager

logger = logging.getLogger(__name__)

class Neo4jMatcher:
    MATCH_QUERY = """
    MATCH (p:Patient {patient_id: $patient_id})
    MATCH (d:Donor)-[c:COMPATIBLE_WITH]->(p)
    WHERE d.is_active = true
      AND d.blood_type = p.blood_type
      AND (NOT p.antibody_kell OR d.kell_negative = true)
      AND (NOT p.antibody_duffy OR d.duffy_negative = true)
      AND (NOT p.antibody_kidd OR d.kidd_negative = true)
    WITH d, c, p,
         point.distance(
             point({latitude: d.lat, longitude: d.lng}),
             point({latitude: p.lat, longitude: p.lng})
         ) AS distance_m
    WHERE d.last_donation_date IS NULL OR date() - d.last_donation_date >= 56
    ORDER BY c.antigen_score DESC, distance_m ASC
    LIMIT 8
    RETURN d.donor_id AS donor_id, d.name AS name, d.telegram_chat_id AS telegram_chat_id,
           d.phone AS phone, d.preferred_language AS preferred_language,
           d.churn_score AS churn_score, d.blood_type AS blood_type,
           c.antigen_score AS antigen_score, c.kell_safe AS kell_safe,
           distance_m / 1000.0 AS distance_km
    """

    UPDATE_CHAIN_STATUS_QUERY = """
    MATCH (d:Donor {donor_id: $donor_id})-[r:IN_CHAIN {request_id: $request_id}]->(p:Patient {patient_id: $patient_id})
    SET r.status = $status,
        r.confirmed_at = CASE WHEN $status = 'CONFIRMED' THEN datetime() ELSE r.confirmed_at END,
        r.declined_at = CASE WHEN $status = 'DECLINED' THEN datetime() ELSE r.declined_at END
    """

    CREATE_CHAIN_EDGES_QUERY = """
    UNWIND $chain_nodes AS node
    MATCH (d:Donor {donor_id: node.donor_id})
    MATCH (p:Patient {patient_id: $patient_id})
    MERGE (d)-[r:IN_CHAIN {request_id: $request_id}]->(p)
    SET r.chain_position = node.chain_position,
        r.status = node.status,
        r.antigen_score = node.antigen_score,
        r.alerted_at = CASE WHEN node.status = 'ALERTED' THEN datetime() ELSE null END
    """

    STALE_ALERTED_QUERY = """
    MATCH (d:Donor)-[r:IN_CHAIN]->(p:Patient)
    WHERE r.status = 'ALERTED'
      AND r.alerted_at < datetime() - duration({minutes: $timeout_minutes})
    RETURN d.donor_id AS donor_id, d.name AS name, d.phone AS phone, d.telegram_chat_id AS telegram_chat_id,
           p.patient_id AS patient_id, r.chain_position AS chain_position, r.request_id AS request_id
    """

    @staticmethod
    async def find_top_donors(patient_id: str) -> List[Dict[str, Any]]:
        """
        Execute Cypher graph query to find up to 8 compatible and physically close donors.
        Returns:
            List[Dict]: List of donor dicts with antigen scores and distances.
        """
        logger.info(f"Finding top donors in graph for patient {patient_id}...")
        # GAP-15: Demo fallback when Neo4j is down
        from core.config import get_settings
        settings = get_settings()
        if settings.DEMO_MOCK_MODE:
            logger.info("DEMO_MOCK_MODE: Returning synthetic donors instead of Neo4j query.")
            return [
                {"donor_id": "D-DEMO-001", "name": "Ravi Kumar", "blood_type": "O+", "antigen_score": 0.92, "telegram_chat_id": None, "phone": "+919000000001", "preferred_language": "hi", "distance_km": 2.1, "kell_safe": True, "churn_score": 0.2},
                {"donor_id": "D-DEMO-002", "name": "Priya Sharma", "blood_type": "O+", "antigen_score": 0.88, "telegram_chat_id": None, "phone": "+919000000002", "preferred_language": "en", "distance_km": 3.5, "kell_safe": True, "churn_score": 0.3},
                {"donor_id": "D-DEMO-003", "name": "Suresh Reddy", "blood_type": "O+", "antigen_score": 0.85, "telegram_chat_id": None, "phone": "+919000000003", "preferred_language": "te", "distance_km": 4.2, "kell_safe": True, "churn_score": 0.15},
                {"donor_id": "D-DEMO-004", "name": "Anjali Patel", "blood_type": "O+", "antigen_score": 0.82, "telegram_chat_id": None, "phone": "+919000000004", "preferred_language": "hi", "distance_km": 5.0, "kell_safe": True, "churn_score": 0.4},
                {"donor_id": "D-DEMO-005", "name": "Mohammed Khan", "blood_type": "O+", "antigen_score": 0.79, "telegram_chat_id": None, "phone": "+919000000005", "preferred_language": "hi", "distance_km": 6.3, "kell_safe": True, "churn_score": 0.25},
                {"donor_id": "D-DEMO-006", "name": "Lakshmi Devi", "blood_type": "O+", "antigen_score": 0.76, "telegram_chat_id": None, "phone": "+919000000006", "preferred_language": "te", "distance_km": 7.1, "kell_safe": True, "churn_score": 0.35},
                {"donor_id": "D-DEMO-007", "name": "Arjun Singh", "blood_type": "O+", "antigen_score": 0.73, "telegram_chat_id": None, "phone": "+919000000007", "preferred_language": "en", "distance_km": 8.0, "kell_safe": True, "churn_score": 0.5},
                {"donor_id": "D-DEMO-008", "name": "Fatima Begum", "blood_type": "O+", "antigen_score": 0.70, "telegram_chat_id": None, "phone": "+919000000008", "preferred_language": "hi", "distance_km": 9.2, "kell_safe": True, "churn_score": 0.45},
            ]
        driver = get_driver()
        records_list = []
        try:
            async with driver.session() as session:
                result = await session.run(Neo4jMatcher.MATCH_QUERY, {"patient_id": patient_id})
                async for record in result:
                    records_list.append(dict(record))
            logger.info(f"Neo4j match: {len(records_list)} compatible donors found for patient {patient_id}")
        except Exception as e:
            logger.error(f"Neo4j matching query failed: {e}", exc_info=True)
        return records_list

    @staticmethod
    async def create_chain(request_id: str, patient_id: str, chain_nodes: List[Dict[str, Any]]):
        """Create :IN_CHAIN edges in the graph for coordination visualization."""
        driver = get_driver()
        try:
            async with driver.session() as session:
                await session.run(
                    Neo4jMatcher.CREATE_CHAIN_EDGES_QUERY,
                    {
                        "request_id": request_id,
                        "patient_id": patient_id,
                        "chain_nodes": chain_nodes
                    }
                )
            logger.info(f"Neo4j: Created outreach chain edges for request {request_id}")
        except Exception as e:
            logger.error(f"Neo4j: Failed to create chain edges: {e}", exc_info=True)

    @staticmethod
    async def update_chain_status(request_id: str, donor_id: str, patient_id: str, status: str):
        """Update the status parameter of an active :IN_CHAIN edge."""
        driver = get_driver()
        try:
            async with driver.session() as session:
                await session.run(
                    Neo4jMatcher.UPDATE_CHAIN_STATUS_QUERY,
                    {
                        "request_id": request_id,
                        "donor_id": donor_id,
                        "patient_id": patient_id,
                        "status": status
                    }
                )
            logger.info(f"Neo4j: Updated chain edge status to {status} for donor {donor_id} (req: {request_id})")
        except Exception as e:
            logger.error(f"Neo4j: Failed to update chain status: {e}", exc_info=True)

    @staticmethod
    async def get_stale_alerted_nodes(timeout_minutes: int = 7) -> List[Dict[str, Any]]:
        """Find ALERTED donor chain links that haven't responded within the timeout."""
        driver = get_driver()
        records_list = []
        try:
            async with driver.session() as session:
                result = await session.run(
                    Neo4jMatcher.STALE_ALERTED_QUERY,
                    {"timeout_minutes": timeout_minutes}
                )
                async for record in result:
                    records_list.append(dict(record))
        except Exception as e:
            logger.error(f"Neo4j: Failed to query stale alerted nodes: {e}", exc_info=True)
        return records_list

    @staticmethod
    async def rebuild_edges_for_donor(donor_id: str):
        """Recompute compatibility edges when donor metadata or antigens change."""
        print(f"Rebuilding compatibility edges for donor {donor_id}...")
        try:
            supabase = get_supabase_admin()
            # Fetch donor
            donor_res = supabase.table("donors").select("*").eq("donor_id", donor_id).execute()
            if not donor_res.data:
                logger.warning(f"Donor {donor_id} not found in Supabase.")
                return
            donor = donor_res.data[0]
            
            # Fetch patients matching blood type
            patients_res = supabase.table("patients").select("*").eq("blood_type", donor["blood_type"]).execute()
            patients = patients_res.data
            
            driver = get_driver()
            async with driver.session() as session:
                # 1. Delete old compatibility edges
                await session.run(
                    "MATCH (d:Donor {donor_id: $donor_id})-[r:COMPATIBLE_WITH]->() DELETE r",
                    {"donor_id": donor_id}
                )
                
                # 2. Re-evaluate compatibility for each patient and re-create edges
                for p in patients:
                    score = compute_antigen_score(donor, p)
                    if score >= 0.60:
                        elig = get_eligibility_flags(donor)
                        await session.run(
                            """
                            MATCH (d:Donor {donor_id: $donor_id})
                            MATCH (p:Patient {patient_id: $patient_id})
                            MERGE (d)-[r:COMPATIBLE_WITH]->(p)
                            SET r.antigen_score = $score,
                                r.kell_safe = $kell_safe,
                                r.duffy_safe = $duffy_safe,
                                r.kidd_safe = $kidd_safe,
                                r.last_computed = datetime()
                            """,
                            {
                                "donor_id": donor_id,
                                "patient_id": p["patient_id"],
                                "score": score,
                                "kell_safe": elig["kell_safe"],
                                "duffy_safe": elig["duffy_safe"],
                                "kidd_safe": elig["kidd_safe"]
                            }
                        )
            logger.info(f"Neo4j: Rebuilt compatibility edges for donor {donor_id}")
        except Exception as e:
            logger.error(f"Neo4j: Failed to rebuild edges for donor {donor_id}: {e}", exc_info=True)


async def neo4j_matching_agent(state: AgentState) -> dict:
    """
    Neo4j Matching Agent Node.
    1. Runs matcher.find_top_donors(state['patient_id'])
    2. Escalates if 0 compatible donors found
    3. Builds the coordination chain ChainNodeState list
    4. Checks for conflicts with other active (IN_PROGRESS) CRITICAL requests
    5. Writes IN_CHAIN edges to Neo4j and blood_chains records to Supabase
    6. Broadcasts starting event to websocket dashboard
    """
    start_time = time.perf_counter()
    logger.info(f"[{state['trace_id']}] Neo4jMatchingAgent started...")
    
    patient_id = state["patient_id"]
    request_id = state["request_id"]
    supabase = get_supabase_admin()
    
    try:
        # 1. Run matcher
        matched = await Neo4jMatcher.find_top_donors(patient_id)
        
        # If Neo4j returns nothing (e.g. database unseeded/empty), fallback to local scored_donors
        if not matched and state.get("scored_donors"):
            logger.warning(f"Neo4j MATCH query returned 0. Falling back to local scored_donors.")
            matched = state["scored_donors"][:8]
            
        # 2. If zero: escalate
        if not matched:
            err_msg = f"Zero compatible donors found for patient {patient_id}. Escalating request."
            logger.error(err_msg)
            return {
                "errors": state.get("errors", []) + [err_msg],
                "outcome": "ESCALATED"
            }
            
        # 3. Build chain ChainNodeState list
        chain_nodes = []
        for idx, d in enumerate(matched):
            # Position is 1-indexed. The first node starts as 'ALERTED', others 'PENDING'
            status = "ALERTED" if idx == 0 else "PENDING"
            chain_nodes.append({
                "donor_id": d["donor_id"],
                "donor_name": d["name"],
                "chain_position": idx + 1,
                "status": status,
                "antigen_score": float(d["antigen_score"]),
                "telegram_chat_id": d.get("telegram_chat_id"),
                "phone": d.get("phone"),
                "preferred_language": d.get("preferred_language", "hi"),
                "distance_km": float(d.get("distance_km", 0.0)),
                "alerted_at": datetime.now().isoformat() if idx == 0 else None,
                "confirmed_at": None
            })
            
        # 4. Check conflict: other IN_PROGRESS CRITICAL requests sharing our matched donors
        conflict_detected = False
        res = supabase.table("emergency_requests")\
            .select("request_id, patient_id")\
            .eq("status", "IN_PROGRESS")\
            .eq("priority", "CRITICAL")\
            .neq("request_id", request_id)\
            .execute()
            
        other_requests = res.data or []
        if other_requests:
            our_donor_ids = {n["donor_id"] for n in chain_nodes}
            other_req_ids = [r["request_id"] for r in other_requests]
            
            chains_res = supabase.table("blood_chains")\
                .select("request_id, donor_id")\
                .in_("request_id", other_req_ids)\
                .execute()
                
            other_chains = chains_res.data or []
            shared_donor_ids = {c["donor_id"] for c in other_chains}.intersection(our_donor_ids)
            if shared_donor_ids:
                logger.warning(f"Conflict detected! Active critical requests share donors: {shared_donor_ids}")
                conflict_detected = True
                
        # 5. Write IN_CHAIN edges to Neo4j + blood_chains to Supabase
        # Neo4j write
        await Neo4jMatcher.create_chain(request_id, patient_id, chain_nodes)
        
        # Supabase write
        supabase_chain_data = []
        for node in chain_nodes:
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
            # Clear old chain just in case of retry/restart to prevent unique constraint conflicts
            supabase.table("blood_chains").delete().eq("request_id", request_id).execute()
            supabase.table("blood_chains").insert(supabase_chain_data).execute()
            
        # 6. Broadcast WebSocket {type:'chain_started', request_id, chain_summary}
        duration = (time.perf_counter() - start_time) * 1000.0
        timings = state.get("node_timings", {}).copy()
        timings["neo4j_match_node"] = round(duration, 2)
        
        chain_summary = {
            "patient_id": patient_id,
            "blood_type": state["blood_type"],
            "donor_count": len(chain_nodes),
            "top_antigen_score": chain_nodes[0]["antigen_score"] if chain_nodes else 0.0
        }
        
        await ws_manager.broadcast({
            "type": "chain_started",
            "request_id": request_id,
            "chain_summary": chain_summary
        })
        
        # Log latency exactly like prompt format:
        logger.info(f"Neo4j match: {len(matched)} donors found in {int(duration)}ms for {patient_id}")
        
        return {
            "matched_donors": matched,
            "chain": chain_nodes,
            "conflict_detected": conflict_detected,
            "node_timings": timings
        }
        
    except Exception as e:
        err_msg = f"Neo4j matching agent error: {e}"
        logger.error(err_msg, exc_info=True)
        return {
            "errors": state.get("errors", []) + [err_msg],
            "outcome": "FAILED"
        }
