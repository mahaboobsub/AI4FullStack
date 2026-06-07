"""
LangGraph Workflow Graph for BloodBridge AI.
"""
import random
import logging
import time
import asyncio
import functools
from typing import Any, Dict, Callable

from langgraph.graph import StateGraph, END
try:
    from langgraph.graph.state import CompiledStateGraph as CompiledGraph
except ImportError:
    try:
        from langgraph.graph import CompiledGraph
    except ImportError:
        CompiledGraph = Any

from models.state import AgentState
from agents.intake import intake_agent
from agents.eligibility import eligibility_agent
from agents.matching import antigen_scoring_agent, urgency_scoring_agent
from agents.neo4j_match import neo4j_matching_agent
from agents.conflict import conflict_resolver_agent
from agents.planner import planner_agent
from agents.outreach import outreach_agent
from agents.monitor import chain_monitor_agent
from agents.repair import chain_repair_agent, inventory_agent
from agents.voice import voice_agent_node
from agents.gamification import gamification_agent
from agents.outcome import outcome_agent

logger = logging.getLogger(__name__)

# ── Broadcasting Decorator ────────────────────────────────────────────────────
# Wraps each agent node to broadcast real-time WebSocket events so the
# frontend can display a live agent activity overlay as the pipeline runs.

AGENT_NODE_LABELS = {
    "intake": "Patient Intake",
    "eligibility": "Eligibility Check",
    "antigen_score": "Antigen Scoring",
    "urgency_score": "Urgency Scoring",
    "neo4j_match": "Neo4j Matching",
    "conflict": "Conflict Resolution",
    "planner": "Outreach Planning",
    "outreach": "Donor Outreach",
    "monitor": "Chain Monitor",
    "repair": "Chain Repair",
    "inventory": "Inventory Fallback",
    "voice": "Voice Call Agent",
    "gamification": "Gamification",
    "outcome_node": "Outcome Recording",
}

def broadcast_agent_node(node_name: str, agent_fn: Callable) -> Callable:
    """Decorator that broadcasts agent_node_started/completed events via WebSocket."""
    @functools.wraps(agent_fn)
    async def wrapper(state: AgentState) -> Any:
        from core.ws_manager import ws_manager
        request_id = state.get("request_id", "unknown")
        label = AGENT_NODE_LABELS.get(node_name, node_name)

        # Broadcast start
        try:
            await ws_manager.broadcast({
                "type": "agent_node_started",
                "node_name": node_name,
                "node_label": label,
                "request_id": request_id,
                "status": "running",
            })
        except Exception:
            pass

        t0 = time.perf_counter()
        error_msg = None
        try:
            # Support both sync and async agent functions
            if asyncio.iscoroutinefunction(agent_fn):
                result = await agent_fn(state)
            else:
                result = agent_fn(state)
            return result
        except Exception as e:
            error_msg = str(e)
            raise
        finally:
            duration_ms = int((time.perf_counter() - t0) * 1000)
            try:
                await ws_manager.broadcast({
                    "type": "agent_node_completed",
                    "node_name": node_name,
                    "node_label": label,
                    "request_id": request_id,
                    "status": "error" if error_msg else "completed",
                    "duration_ms": duration_ms,
                    "error": error_msg,
                })
            except Exception:
                pass

    return wrapper

def route_after_neo4j_match(state: AgentState) -> str:
    """Determine whether to route to conflict resolver or directly to outreach planner."""
    if state.get("conflict_detected", False):
        return "conflict"
    return "planner"

def route_after_monitor(state: AgentState) -> str:
    """Determine next action based on coordination state monitor results."""
    if state.get('outcome') in ['SUCCESS', 'ESCALATED']:
        return 'complete'
    stale = state.get('stale_positions', [])
    # Prevent infinite self-loop: escalate after 3 monitor iterations
    if state.get('monitor_iterations', 0) >= 3:
        return 'inventory'
    if len(stale) > 3:
        return 'inventory'
    if stale:
        chain = state.get("chain", [])
        has_telegram_timeout = any(
            n.get("chain_position") in stale and n.get("status") == "ALERTED"
            for n in chain
        )
        if has_telegram_timeout:
            return "voice"
        return "repair"
    # Donors alerted but none stale yet — leave IN_PROGRESS for scheduler monitoring
    return 'waiting'

def build_bloodbridge_graph() -> CompiledGraph:
    """Compile the LangGraph workflow with 14 nodes and conditional routing."""
    graph = StateGraph(AgentState)
    
    # Register 14 nodes — each wrapped with broadcast decorator for live UI
    graph.add_node("intake", broadcast_agent_node("intake", intake_agent))
    graph.add_node("eligibility", broadcast_agent_node("eligibility", eligibility_agent))
    graph.add_node("antigen_score", broadcast_agent_node("antigen_score", antigen_scoring_agent))
    graph.add_node("urgency_score", broadcast_agent_node("urgency_score", urgency_scoring_agent))
    graph.add_node("neo4j_match", broadcast_agent_node("neo4j_match", neo4j_matching_agent))
    graph.add_node("conflict", broadcast_agent_node("conflict", conflict_resolver_agent))
    graph.add_node("planner", broadcast_agent_node("planner", planner_agent))
    graph.add_node("outreach", broadcast_agent_node("outreach", outreach_agent))
    graph.add_node("monitor", broadcast_agent_node("monitor", chain_monitor_agent))
    graph.add_node("repair", broadcast_agent_node("repair", chain_repair_agent))
    graph.add_node("inventory", broadcast_agent_node("inventory", inventory_agent))
    graph.add_node("voice", broadcast_agent_node("voice", voice_agent_node))
    graph.add_node("gamification", broadcast_agent_node("gamification", gamification_agent))
    graph.add_node("outcome_node", broadcast_agent_node("outcome_node", outcome_agent))
    
    # Define execution flow
    graph.set_entry_point("intake")
    
    # 1. Intake to eligibility
    graph.add_edge("intake", "eligibility")
    
    # 2. Eligibility to antigen scoring & urgency scoring (Parallel)
    graph.add_edge("eligibility", "antigen_score")
    graph.add_edge("eligibility", "urgency_score")
    
    # 3. Parallel paths join at neo4j_match
    graph.add_edge("antigen_score", "neo4j_match")
    graph.add_edge("urgency_score", "neo4j_match")
    
    # 4. Neo4j match routes conditionally
    graph.add_conditional_edges(
        "neo4j_match",
        route_after_neo4j_match,
        {
            "conflict": "conflict",
            "planner": "planner"
        }
    )
    
    # 5. Paths converge at planner
    graph.add_edge("conflict", "planner")
    
    # 6. Planner to outreach to monitor
    graph.add_edge("planner", "outreach")
    graph.add_edge("outreach", "monitor")
    
    # 7. Monitor routes conditionally — NO self-loop to prevent infinite recursion
    graph.add_conditional_edges(
        "monitor",
        route_after_monitor,
        {
            "complete": "outcome_node",
            "repair": "repair",
            "voice": "voice",
            "inventory": "inventory",
            "waiting": END,
        }
    )
    
    # 8. Loop-back and auxiliary agent transitions
    graph.add_edge("repair", "outreach")
    graph.add_edge("voice", "monitor")
    graph.add_edge("inventory", "outcome_node")
    
    # 9. Completion sequence
    graph.add_edge("outcome_node", "gamification")
    graph.add_edge("gamification", END)
    
    return graph.compile()

# Module-level graph instance singleton
_graph = None

def get_graph() -> CompiledGraph:
    """Retrieve or build the graph singleton instance."""
    global _graph
    if _graph is None:
        _graph = build_bloodbridge_graph()
    return _graph

async def run_emergency_pipeline(request_data: dict) -> AgentState:
    """Main entry point called by FastAPI. Returns final AgentState."""
    from core.ws_manager import ws_manager

    request_id = request_data['request_id']

    # Broadcast pipeline started
    try:
        await ws_manager.broadcast({
            "type": "pipeline_started",
            "request_id": request_id,
            "patient_id": request_data['patient_id'],
            "blood_type": request_data['blood_type'],
            "hospital": request_data.get('hospital_name', ''),
            "total_nodes": 14,
        })
    except Exception:
        pass

    initial_state: AgentState = {
        'request_id': request_id,
        'patient_id': request_data['patient_id'],
        'blood_type': request_data['blood_type'],
        'city': request_data['city'],
        'hospital_name': request_data['hospital_name'],
        'ward': request_data.get('ward'),
        'triggered_by': request_data.get('triggered_by', 'staff'),
        'language': 'en',
        'request_mode': request_data.get('request_mode', 'emergency'),
        'days_until_due': request_data.get('days_until_due'),
        'patient': None,
        'eligible_donors': [],
        'scored_donors': [],
        'matched_donors': [],
        'wide_net_donors': [],        # R3 backup donors
        'chain': [],
        'chain_confirmed_count': 0,
        'chain_declined_count': 0,
        'conflict_detected': False,
        'conflict_resolution': None,
        'outreach_plan': [],
        'channel_strategy': '',       # Set by planner agent
        'chain_break_detected': False,
        'stale_positions': [],
        'urgency_result': {},
        'patient_antibody_flags': {},
        'donors_consent_checked': False,
        'non_consented_donors': [],
        'outcome': None,
        'badges_awarded': [],
        'impact_story': None,
        'monitor_iterations': 0,      # Loop counter — escalate at >= 3
        'node_timings': {},           # Per-node latency ms
        'trace_id': f"TRC-{random.randint(1000, 9999)}",
        'errors': []
    }

    t0 = time.perf_counter()
    try:
        result = await get_graph().ainvoke(initial_state)
    finally:
        total_ms = int((time.perf_counter() - t0) * 1000)
        # Broadcast pipeline completed
        try:
            await ws_manager.broadcast({
                "type": "pipeline_completed",
                "request_id": request_id,
                "patient_id": request_data['patient_id'],
                "total_ms": total_ms,
                "outcome": result.get("outcome", "UNKNOWN") if 'result' in dir() else "ERROR",
            })
        except Exception:
            pass

    return result

