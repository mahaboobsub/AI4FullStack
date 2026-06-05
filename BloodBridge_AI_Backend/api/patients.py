"""
Patient operations API routes for BloodBridge AI.
"""
import logging
from datetime import date, datetime
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional

from core.database import get_supabase_admin

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/patients", tags=["patients"])

# Pydantic Schemas matching lib/api.ts
class LinkedDonor(BaseModel):
    donor_id: str
    donor_name: str
    antigen_score: float
    status: str
    donation_count: int
    badges: List[str]

class TransfusionLogEntry(BaseModel):
    date: str
    donor_name: str
    blood_type: str
    outcome: str

class PatientProfileResponse(BaseModel):
    patient_id: str
    name: str
    age: int
    blood_type: str
    hospital: str
    ward: str
    transfusion_count: int
    next_transfusion_due: str
    hemoglobin: float
    status: str
    antibody_flags: List[str]
    kell_negative: bool
    linked_donors: List[LinkedDonor]
    transfusion_history: List[TransfusionLogEntry]
    active_request: Optional[str] = None

@router.get("/{id}", response_model=PatientProfileResponse)
async def get_patient_profile(id: str):
    """
    GET /api/patients/{id}
    Retrieves the complete profile for a Thalassemia patient, including linked donors
    in their active emergency chain and their historical transfusion records.
    """
    supabase = get_supabase_admin()
    
    try:
        # 1. Fetch Patient
        p_res = supabase.table("patients").select("*").eq("patient_id", id).execute()
        if not p_res.data:
            raise HTTPException(status_code=404, detail="Patient profile not found.")
            
        patient = p_res.data[0]
        
        # 2. Map antibody flags
        antibody_flags = []
        if patient.get("antibody_kell"): antibody_flags.append("Anti-Kell")
        if patient.get("antibody_duffy"): antibody_flags.append("Anti-Duffy")
        if patient.get("antibody_kidd"): antibody_flags.append("Anti-Kidd")
        if patient.get("antibody_rh_e"): antibody_flags.append("Anti-E")
        if patient.get("antibody_rh_c"): antibody_flags.append("Anti-c")
        if patient.get("antibody_mns"): antibody_flags.append("Anti-MNS")
        
        # 3. Check for active request
        active_req_id = None
        req_res = supabase.table("emergency_requests")\
            .select("request_id")\
            .eq("patient_id", id)\
            .eq("status", "IN_PROGRESS")\
            .execute()
            
        if req_res.data:
            active_req_id = req_res.data[0]["request_id"]
            
        # 4. Fetch linked donors if active request exists
        linked_donors = []
        if active_req_id:
            chain_res = supabase.table("blood_chains")\
                .select("donor_id, donor_name, status, antigen_score")\
                .eq("request_id", active_req_id)\
                .order("chain_position")\
                .execute()
                
            for node in (chain_res.data or []):
                d_id = node["donor_id"]
                
                # Fetch donor count and memory badges
                d_profile = supabase.table("donors").select("donation_count").eq("donor_id", d_id).execute()
                d_count = d_profile.data[0]["donation_count"] if d_profile.data else 0
                
                d_mem = supabase.table("donor_memory").select("badges").eq("donor_id", d_id).execute()
                d_badges = d_mem.data[0]["badges"] if d_mem.data else []
                
                linked_donors.append({
                    "donor_id": d_id,
                    "donor_name": node["donor_name"],
                    "antigen_score": node.get("antigen_score", 0.5) or 0.5,
                    "status": node["status"],
                    "donation_count": d_count,
                    "badges": d_badges
                })
                
        # 5. Fetch transfusion history
        history_res = supabase.table("transfusion_schedule")\
            .select("scheduled_date, hospital, blood_type, request_id, status")\
            .eq("patient_id", id)\
            .eq("status", "COMPLETED")\
            .order("scheduled_date", desc=True)\
            .execute()
            
        transfusion_history = []
        for entry in (history_res.data or []):
            req_id = entry.get("request_id")
            donor_name = "Voluntary Donor"
            
            # Fetch who completed it from chains
            if req_id:
                completed_res = supabase.table("blood_chains")\
                    .select("donor_name")\
                    .eq("request_id", req_id)\
                    .eq("status", "COMPLETED")\
                    .execute()
                if completed_res.data:
                    donor_name = completed_res.data[0]["donor_name"]
                    
            transfusion_history.append({
                "date": entry["scheduled_date"],
                "donor_name": donor_name,
                "blood_type": entry["blood_type"],
                "outcome": "Successful transfusion"
            })
            
        return {
            "patient_id": patient["patient_id"],
            "name": patient["name"],
            "age": patient.get("age", 0) or 0,
            "blood_type": patient["blood_type"],
            "hospital": patient["hospital"],
            "ward": patient.get("ward", "General Ward"),
            "transfusion_count": patient.get("transfusion_count", 0) or 0,
            "next_transfusion_due": patient.get("next_transfusion_due") or "",
            "hemoglobin": patient.get("hemoglobin", 0.0) or 0.0,
            "status": patient.get("status", "STABLE"),
            "antibody_flags": antibody_flags,
            "kell_negative": patient.get("kell_negative", False),
            "linked_donors": linked_donors,
            "transfusion_history": transfusion_history,
            "active_request": active_req_id
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resolving patient profile {id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch patient profile: {str(e)}")


@router.get("/{id}/schedule")
async def get_patient_schedule(
    id: str,
    status_filter: Optional[str] = Query(None, description="Filter by schedule status (PENDING, COMPLETED, OUTREACH_STARTED)")
):
    """
    GET /api/patients/{id}/schedule
    Returns the transfusion schedule entries for a patient with days_until calculation.
    """
    supabase = get_supabase_admin()
    try:
        query = supabase.table("transfusion_schedule")\
            .select("schedule_id, patient_id, scheduled_date, hospital, blood_type, status, request_id")\
            .eq("patient_id", id)\
            .order("scheduled_date")

        if status_filter:
            query = query.eq("status", status_filter.upper())

        res = query.execute()
        today = date.today()

        results = []
        for entry in (res.data or []):
            sched_date = entry.get("scheduled_date")
            days_until = None
            if sched_date:
                try:
                    d = date.fromisoformat(str(sched_date))
                    days_until = (d - today).days
                except Exception:
                    pass

            results.append({
                "schedule_id": entry.get("schedule_id"),
                "patient_id": entry.get("patient_id"),
                "scheduled_date": sched_date,
                "hospital": entry.get("hospital"),
                "blood_type": entry.get("blood_type"),
                "status": entry.get("status", "PENDING"),
                "request_id": entry.get("request_id"),
                "days_until": days_until
            })

        return results
    except Exception as e:
        logger.error(f"Error fetching schedule for patient {id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch patient schedule.")


@router.get("/{id}/chain-history")
async def get_patient_chain_history(id: str, limit: int = Query(10, ge=1, le=50)):
    """
    GET /api/patients/{id}/chain-history
    Returns completed/in-progress blood chains for a patient with anonymized donor names.
    """
    supabase = get_supabase_admin()
    try:
        # Fetch emergency requests for this patient
        req_res = supabase.table("emergency_requests")\
            .select("request_id, blood_type, hospital_name, city, status, created_at, completed_at")\
            .eq("patient_id", id)\
            .order("created_at", desc=True)\
            .limit(limit)\
            .execute()

        results = []
        for req in (req_res.data or []):
            request_id = req["request_id"]

            # Fetch chain nodes for this request
            chain_res = supabase.table("blood_chains")\
                .select("donor_name, status, chain_position, antigen_score, confirmed_at")\
                .eq("request_id", request_id)\
                .order("chain_position")\
                .execute()

            # Anonymize donor names: first name + last initial (DPDP compliance)
            donors = []
            for node in (chain_res.data or []):
                full_name = node.get("donor_name", "Donor")
                parts = full_name.split()
                if len(parts) >= 2:
                    anon_name = f"{parts[0]} {parts[-1][0]}."
                else:
                    anon_name = parts[0] if parts else "Donor"

                donors.append({
                    "name": anon_name,
                    "position": node.get("chain_position"),
                    "status": node.get("status"),
                    "antigen_score": node.get("antigen_score"),
                    "confirmed_at": node.get("confirmed_at")
                })

            confirmed_count = sum(1 for d in donors if d["status"] in ["CONFIRMED", "COMPLETED"])

            results.append({
                "request_id": request_id,
                "blood_type": req.get("blood_type"),
                "hospital": req.get("hospital_name"),
                "city": req.get("city"),
                "status": req.get("status"),
                "created_at": req.get("created_at"),
                "completed_at": req.get("completed_at"),
                "confirmed_donors": confirmed_count,
                "total_chain_size": len(donors),
                "donors": donors
            })

        return results
    except Exception as e:
        logger.error(f"Error fetching chain history for patient {id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch chain history.")


@router.post("/{id}/auto-schedule")
async def auto_schedule_patient(id: str, background_tasks: BackgroundTasks):
    """
    POST /api/patients/{id}/auto-schedule
    Triggers auto_generate_schedule_from_history() as a background task.
    Only works for patients with 2+ completed transfusions.
    """
    supabase = get_supabase_admin()

    req_res = supabase.table("emergency_requests")\
        .select("request_id")\
        .eq("patient_id", id)\
        .eq("status", "COMPLETED")\
        .execute()

    if len(req_res.data or []) < 2:
        raise HTTPException(
            status_code=400,
            detail="Patient needs at least 2 completed transfusions for auto-schedule generation."
        )

    from services.transfusion_calendar import auto_generate_schedule_from_history
    background_tasks.add_task(auto_generate_schedule_from_history, id)

    return {"success": True, "message": f"Auto-schedule generation queued for patient {id}."}
