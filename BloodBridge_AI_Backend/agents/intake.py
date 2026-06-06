"""
Intake Agent for BloodBridge AI.
Fetches patient information, detects language, and creates initial emergency requests.
"""
import time
import logging
from datetime import datetime
from services.language_service import detect_dominant_language
from models.state import AgentState
from core.database import get_supabase_admin

logger = logging.getLogger(__name__)

async def intake_agent(state: AgentState) -> dict:
    """
    Intake node for LangGraph pipeline.
    Fetches patient profile and registers request in database.
    """
    start_time = time.perf_counter()
    logger.info(f"[{state['trace_id']}] IntakeAgent started...")
    
    patient_id = state["patient_id"]
    supabase = get_supabase_admin()
    
    try:
        # 1. Fetch patient details
        res = supabase.table("patients").select("*").eq("patient_id", patient_id).execute()
        if not res.data:
            err_msg = f"Patient {patient_id} not found."
            logger.error(err_msg)
            return {
                "errors": state.get("errors", []) + [err_msg],
                "outcome": "FAILED"
            }
            
        patient = res.data[0]
        
        # 2. Extract antibody flags
        antibody_flags = {
            "antibody_kell": patient.get("antibody_kell", False),
            "antibody_duffy": patient.get("antibody_duffy", False),
            "antibody_kidd": patient.get("antibody_kidd", False),
            "antibody_rh_e": patient.get("antibody_rh_e", False),
            "antibody_rh_c": patient.get("antibody_rh_c", False),
            "antibody_mns": patient.get("antibody_mns", False),
            "kell_negative": patient.get("kell_negative", False)
        }
        
        # 3. Detect language
        detected_lang = "hi"
        try:
            # Detect language of ward/hospital description to personalize outreach
            text_to_detect = f"{state.get('hospital_name', '')} {state.get('ward', '')}"
            if len(text_to_detect.strip()) > 3:
                detected_lang = detect_dominant_language(text_to_detect)
        except Exception:
            pass # fallback to default 'hi'
            
        # 4. Upsert emergency request in database
        emergency_data = {
            "request_id": state["request_id"],
            "patient_id": patient_id,
            "blood_type": state["blood_type"],
            "city": state["city"],
            "hospital_name": state["hospital_name"],
            "ward": state.get("ward"),
            "priority": "ROUTINE", # Will be updated by urgency scoring node
            "status": "IN_PROGRESS",
            "triggered_by": state.get("triggered_by", "staff"),
            "request_mode": state.get("request_mode", "emergency"),
            "created_at": datetime.now().isoformat()
        }
        supabase.table("emergency_requests").upsert(emergency_data).execute()
        
        # 5. Create initial agent trace log entry
        trace_data = {
            "trace_id": state["trace_id"],
            "request_id": state["request_id"],
            "patient_id": patient_id,
            "started_at": datetime.now().isoformat(),
            "outcome": "IN_PROGRESS",
            "node_count": 1,
            "nodes_json": []
        }
        supabase.table("agent_traces").upsert(trace_data).execute()
        
        duration = (time.perf_counter() - start_time) * 1000.0
        timings = state.get("node_timings", {}).copy()
        timings["intake_node"] = round(duration, 2)
        
        return {
            "patient": patient,
            "patient_antibody_flags": antibody_flags,
            "language": detected_lang,
            "node_timings": timings
        }
        
    except Exception as e:
        err_msg = f"Intake agent error: {e}"
        logger.error(err_msg, exc_info=True)
        return {
            "errors": state.get("errors", []) + [err_msg],
            "outcome": "FAILED"
        }
