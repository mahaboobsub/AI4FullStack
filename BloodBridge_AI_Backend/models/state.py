"""
LangGraph AgentState Definitions for BloodBridge AI.
"""
from typing import TypedDict, Optional, Literal, List, Dict, Any

class ChainNodeState(TypedDict):
    donor_id: str
    donor_name: str
    chain_position: int
    status: Literal['PENDING', 'ALERTED', 'CONFIRMED', 'DECLINED', 'VOICE', 'SMS', 'COMPLETED']
    antigen_score: float
    telegram_chat_id: Optional[str]
    phone: Optional[str]
    preferred_language: str
    distance_km: float
    alerted_at: Optional[str]
    confirmed_at: Optional[str]

class AgentState(TypedDict):
    # Input Request context
    request_id: str
    patient_id: str
    blood_type: str
    city: str
    hospital_name: str
    ward: Optional[str]
    triggered_by: str
    language: str
    request_mode: Literal['emergency', 'proactive']
    days_until_due: Optional[int]
    
    # Patient clinical profile
    patient: Optional[Dict[str, Any]]
    patient_antibody_flags: Dict[str, Any]
    
    # Matching process intermediate variables
    eligible_donors: List[Dict[str, Any]]
    scored_donors: List[Dict[str, Any]]
    urgency_result: Dict[str, Any]
    matched_donors: List[Dict[str, Any]]
    
    # Conflict resolution flags
    conflict_detected: bool
    conflict_resolution: Optional[str]
    
    # Strategy planning
    outreach_plan: List[Dict[str, Any]]
    channel_strategy: str
    
    # Coordination chain statuses
    chain: List[ChainNodeState]
    chain_confirmed_count: int
    chain_declined_count: int
    
    # Stale/failed checks
    chain_break_detected: bool
    stale_positions: List[int]
    
    # Consent management audits
    donors_consent_checked: bool
    non_consented_donors: List[str]
    
    # Coordination outcomes
    outcome: Optional[Literal['SUCCESS', 'ESCALATED', 'IN_PROGRESS', 'FAILED']]
    badges_awarded: List[str]
    impact_story: Optional[str]
    
    # Latency tracking audit logs
    trace_id: str
    node_timings: Dict[str, float]
    errors: List[str]
