"""
Proactive Scheduler Agent for BloodBridge AI.
Helper function to initialize/run proactive workflows.
"""
import logging
from models.state import AgentState

logger = logging.getLogger(__name__)

def configure_proactive_state(state: AgentState) -> dict:
    """
    Ensures that proactive parameters are injected into the agent state.
    """
    logger.info(f"[{state['trace_id']}] Configuring state for PROACTIVE mode.")
    return {
        "request_mode": "proactive",
        "channel_strategy": "hybrid"
    }
