"""
Emergency coordination API routes for BloodBridge AI.
"""
import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Request
from pydantic import BaseModel, Field
from typing import List, Optional

from core.database import get_supabase_admin
from core.limiter import limiter

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/emergencies", tags=["emergencies"])

# Pydantic Schemas matching lib/api.ts
class ChainNodeResponse(BaseModel):
    donor_id: str
    donor_name: str
    chain_position: int
    status: str
    antigen_score: float
    alerted_at: Optional[str] = None
    confirmed_at: Optional[str] = None

class EmergencyResponse(BaseModel):
    request_id: str
    patient_id: str
    blood_type: str
    city: str
    priority: str
    urgency_score: float
    hospital_name: str
    ward: Optional[str] = None
    status: str
    chain: List[ChainNodeResponse]
    created_at: str

class CreateEmergencyRequest(BaseModel):
    patient_id: str
    blood_type: str
    city: str
    ward: str
    hospital: str

@router.get("", response_model=List[EmergencyResponse])
async def list_emergencies():
    """
    GET /api/emergencies
    Lists all active (IN_PROGRESS) emergencies, including their donor chains.
    """
    supabase = get_supabase_admin()
    try:
        # Fetch active emergency requests
        res = supabase.table("emergency_requests")\
            .select("*")\
            .eq("status", "IN_PROGRESS")\
            .execute()
            
        active_requests = res.data or []
        
        # Populate each with its donor chain
        emergencies = []
        for req in active_requests:
            req_id = req["request_id"]
            chain_res = supabase.table("blood_chains")\
                .select("*")\
                .eq("request_id", req_id)\
                .order("chain_position")\
                .execute()
                
            chain = []
            for node in (chain_res.data or []):
                n = dict(node)
                if n.get("antigen_score") is None:
                    n["antigen_score"] = float(n.get("match_score") or 0.5)
                chain.append(n)
            emergencies.append({
                "request_id": req["request_id"],
                "patient_id": req.get("patient_id"),
                "blood_type": req.get("blood_type"),
                "city": req.get("city"),
                "priority": req.get("priority", "ROUTINE"),
                "urgency_score": req.get("urgency_score", 0.0) or 0.0,
                "hospital_name": req.get("hospital_name"),
                "ward": req.get("ward"),
                "status": req.get("status"),
                "chain": chain,
                "created_at": req.get("created_at")
            })
            
        return emergencies
    except Exception as e:
        logger.error(f"Failed to fetch emergencies: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database lookup failed.")

@router.get("/{id}", response_model=EmergencyResponse)
async def get_emergency(id: str):
    """
    GET /api/emergencies/{id}
    Retrieves a single emergency request details.
    """
    supabase = get_supabase_admin()
    try:
        res = supabase.table("emergency_requests").select("*").eq("request_id", id).execute()
        if not res.data:
            raise HTTPException(status_code=404, detail="Emergency request not found.")
            
        req = res.data[0]
        chain_res = supabase.table("blood_chains")\
            .select("*")\
            .eq("request_id", id)\
            .order("chain_position")\
            .execute()
            
        return {
            "request_id": req["request_id"],
            "patient_id": req.get("patient_id"),
            "blood_type": req.get("blood_type"),
            "city": req.get("city"),
            "priority": req.get("priority", "ROUTINE"),
            "urgency_score": req.get("urgency_score", 0.0) or 0.0,
            "hospital_name": req.get("hospital_name"),
            "ward": req.get("ward"),
            "status": req.get("status"),
            "chain": chain_res.data or [],
            "created_at": req.get("created_at")
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching emergency request {id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database lookup failed.")

@router.post("")
@limiter.limit("5/hour")
async def create_emergency(
    request: Request,
    payload: CreateEmergencyRequest,
    background_tasks: BackgroundTasks
):
    """
    POST /api/emergencies
    Creates a new emergency request and schedules the coordination pipeline in the background.
    """
    supabase = get_supabase_admin()
    now_str = datetime.utcnow().isoformat() + "Z"
    
    # Check idempotency key from headers to prevent double submissions
    idempotency_key = request.headers.get("X-Idempotency-Key")
    
    if idempotency_key:
        try:
            existing_res = supabase.table("emergency_requests")\
                .select("request_id")\
                .eq("idempotency_key", idempotency_key)\
                .execute()
            if existing_res.data:
                logger.info(f"Duplicate emergency request intercepted for key: {idempotency_key}")
                return {"requestId": existing_res.data[0]["request_id"]}
        except Exception as e:
            logger.warning(f"Idempotency validation lookup failed: {e}")
            
    # Verify patient exists
    try:
        pat_res = supabase.table("patients").select("patient_id").eq("patient_id", payload.patient_id).execute()
        if not pat_res.data:
            raise HTTPException(status_code=400, detail="Invalid patient_id. Patient profile does not exist.")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Patient validation failed: {e}")

    try:
        # Create emergency_request record
        # Note: postgres default generates request_id as REQ-XXXXX
        insert_data = {
            "patient_id": payload.patient_id,
            "blood_type": payload.blood_type,
            "city": payload.city,
            "hospital_name": payload.hospital,
            "ward": payload.ward,
            "status": "IN_PROGRESS",
            "request_mode": "emergency",
            "created_at": now_str
        }
        if idempotency_key:
            insert_data["idempotency_key"] = idempotency_key
            
        res = supabase.table("emergency_requests").insert(insert_data).execute()
        if not res.data:
            raise HTTPException(status_code=500, detail="Failed to create emergency request.")
            
        request_id = res.data[0]["request_id"]
        
        # Trigger coordination pipeline in background
        from agents.graph import run_emergency_pipeline
        background_tasks.add_task(run_emergency_pipeline, {
            "request_id": request_id,
            "patient_id": payload.patient_id,
            "blood_type": payload.blood_type,
            "city": payload.city,
            "hospital_name": payload.hospital,
            "ward": payload.ward,
            "triggered_by": "staff",
            "request_mode": "emergency",
        })
        
        # Broadcast via websocket to trigger reload on dashboards
        from core.ws_manager import ws_manager
        await ws_manager.broadcast("new_emergency", {
            "request_id": request_id,
            "patient_id": payload.patient_id,
            "blood_type": payload.blood_type,
            "city": payload.city,
            "hospital_name": payload.hospital
        })
        
        return {"requestId": request_id}
    except Exception as e:
        logger.error(f"Failed to create emergency request: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Emergency creation failed: {str(e)}")

@router.post("/{id}/confirm")
async def confirm_emergency(id: str):
    """
    POST /api/emergencies/{id}/confirm
    Closes the emergency coordination chain as successfully resolved.
    """
    supabase = get_supabase_admin()
    try:
        # Check request exists
        res = supabase.table("emergency_requests").select("status").eq("request_id", id).execute()
        if not res.data:
            raise HTTPException(status_code=404, detail="Emergency request not found.")
            
        # Update request status to COMPLETED
        supabase.table("emergency_requests")\
            .update({
                "status": "COMPLETED",
                "completed_at": datetime.utcnow().isoformat() + "Z"
            })\
            .eq("request_id", id)\
            .execute()
            
        # Set all active alerted chain nodes to COMPLETED, others to PENDING/released
        supabase.table("blood_chains")\
            .update({"status": "COMPLETED"})\
            .eq("request_id", id)\
            .eq("status", "CONFIRMED")\
            .execute()
            
        from core.ws_manager import ws_manager
        await ws_manager.broadcast("emergency_completed", {"request_id": id})
        
        return {"success": True}
    except Exception as e:
        logger.error(f"Failed to confirm emergency request {id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{id}/chain", response_model=List[ChainNodeResponse])
async def get_emergency_chain(id: str):
    """
    GET /api/emergencies/{id}/chain
    Returns the active donor chain for a given emergency coordination.
    """
    supabase = get_supabase_admin()
    try:
        res = supabase.table("blood_chains")\
            .select("*")\
            .eq("request_id", id)\
            .order("chain_position")\
            .execute()
            
        return res.data or []
    except Exception as e:
        logger.error(f"Failed to fetch chain for request {id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database lookup failed.")

@router.get("/{id}/trace")
async def get_emergency_trace(id: str):
    """
    GET /api/emergencies/{id}/trace
    Fetches the agentic trace/execution latency log for a request.
    """
    supabase = get_supabase_admin()
    try:
        res = supabase.table("agent_traces")\
            .select("*")\
            .eq("request_id", id)\
            .order("started_at", desc=True)\
            .limit(1)\
            .execute()
            
        if not res.data:
            raise HTTPException(status_code=404, detail="No agent execution trace found for this request.")
            
        trace = res.data[0]
        # Map fields to match AgentTrace format
        return {
            "request_id": trace["request_id"],
            "patient_id": trace.get("patient_id"),
            "timestamp": trace.get("started_at"),
            "outcome": trace.get("outcome", "SUCCESS"),
            "node_count": trace.get("node_count", 0),
            "total_ms": trace.get("total_ms", 0),
            "nodes": trace.get("nodes_json") or []
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching trace for request {id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database lookup failed.")
