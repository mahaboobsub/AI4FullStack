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
    ward: Optional[str] = None
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

    pat_res = supabase.table("patients").select("transfusion_count").eq("patient_id", id).execute()
    transfusion_count = (pat_res.data[0].get("transfusion_count", 0) if pat_res.data else 0) or 0
    completed_emergencies = len(req_res.data or [])

    if completed_emergencies < 2 and transfusion_count < 2:
        raise HTTPException(
            status_code=400,
            detail="Patient needs at least 2 completed transfusions for auto-schedule generation."
        )

    from services.transfusion_calendar import auto_generate_schedule_from_history
    background_tasks.add_task(auto_generate_schedule_from_history, id)

    return {"success": True, "message": f"Auto-schedule generation queued for patient {id}."}


# ═══════════════════════════════════════════════════════════════════════════════
# M4 — PATIENT LOCATION APIs (multi-location CRUD)
# ═══════════════════════════════════════════════════════════════════════════════

class LocationCreate(BaseModel):
    label: str
    lat: float
    lng: float
    is_primary: bool = False
    priority_order: int = 1

class LocationPatch(BaseModel):
    is_primary: Optional[bool] = None

@router.post("/{id}/locations")
async def add_patient_location(id: str, loc: LocationCreate):
    """POST /api/patients/{id}/locations — add a location (max 5 per patient)."""
    from services.geo_service import encode_geohash
    if not (-90 <= loc.lat <= 90) or not (-180 <= loc.lng <= 180):
        raise HTTPException(status_code=400, detail="Invalid lat/lng range.")

    supabase = get_supabase_admin()
    existing = supabase.table("patient_locations").select("location_id", count="exact").eq("patient_id", id).execute()
    if (existing.count or 0) >= 5:
        raise HTTPException(status_code=400, detail="Maximum 5 locations per patient.")

    geohash = encode_geohash(loc.lat, loc.lng, precision=6)

    # If setting as primary, unset others first
    if loc.is_primary:
        supabase.table("patient_locations").update({"is_primary": False}).eq("patient_id", id).execute()

    row = supabase.table("patient_locations").insert({
        "patient_id": id, "label": loc.label, "lat": loc.lat, "lng": loc.lng,
        "geohash": geohash, "is_primary": loc.is_primary, "priority_order": loc.priority_order
    }).execute()
    return {"success": True, "location": row.data[0] if row.data else {}}

@router.get("/{id}/locations")
async def list_patient_locations(id: str):
    """GET /api/patients/{id}/locations — list ordered by priority_order."""
    try:
        supabase = get_supabase_admin()
        res = supabase.table("patient_locations").select("*").eq("patient_id", id).order("priority_order").execute()
        return res.data or []
    except Exception as e:
        logger.error(f"Error fetching patient locations for {id}: {e}", exc_info=True)
        return []

@router.delete("/{id}/locations/{location_id}")
async def delete_patient_location(id: str, location_id: str):
    """DELETE — cannot delete the last remaining location."""
    supabase = get_supabase_admin()
    existing = supabase.table("patient_locations").select("location_id", count="exact").eq("patient_id", id).execute()
    if (existing.count or 0) <= 1:
        raise HTTPException(status_code=400, detail="Cannot delete the last remaining location.")
    supabase.table("patient_locations").delete().eq("location_id", location_id).eq("patient_id", id).execute()
    return {"success": True}

@router.patch("/{id}/locations/{location_id}")
async def patch_patient_location(id: str, location_id: str, patch: LocationPatch):
    """PATCH — set is_primary (only one primary; unset others)."""
    supabase = get_supabase_admin()
    if patch.is_primary:
        supabase.table("patient_locations").update({"is_primary": False}).eq("patient_id", id).execute()
    supabase.table("patient_locations").update({"is_primary": patch.is_primary}).eq("location_id", location_id).execute()
    return {"success": True}



# ═══════════════════════════════════════════════════════════════════════════════
# Feature 2: Patient Profile Update
# ═══════════════════════════════════════════════════════════════════════════════

class PatientProfileUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    hospital: Optional[str] = None
    ward: Optional[str] = None


@router.patch("/{id}/profile")
async def update_patient_profile(id: str, body: PatientProfileUpdate):
    """
    PATCH /api/patients/{id}/profile
    Updates editable patient profile fields (name, phone, hospital, ward).
    """
    supabase = get_supabase_admin()
    try:
        p_res = supabase.table("patients").select("patient_id").eq("patient_id", id).execute()
        if not p_res.data:
            raise HTTPException(status_code=404, detail="Patient not found.")

        update_data = {}
        if body.name is not None:
            update_data["name"] = body.name.strip()
        if body.phone is not None:
            update_data["phone"] = body.phone.strip()
        if body.hospital is not None:
            update_data["hospital"] = body.hospital.strip()
        if body.ward is not None:
            update_data["ward"] = body.ward.strip()

        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update.")

        supabase.table("patients").update(update_data).eq("patient_id", id).execute()

        return {"success": True, "updated": update_data}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating profile for patient {id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Profile update failed.")


# ═══════════════════════════════════════════════════════════════════════════════
# Feature 4: Set Next Transfusion Date
# ═══════════════════════════════════════════════════════════════════════════════

class SetNextTransfusionRequest(BaseModel):
    date: str


@router.post("/{id}/set-next-transfusion")
async def set_next_transfusion(id: str, body: SetNextTransfusionRequest):
    """
    POST /api/patients/{id}/set-next-transfusion
    Sets the next_transfusion_due date for a patient manually.
    """
    supabase = get_supabase_admin()
    try:
        p_res = supabase.table("patients").select("patient_id").eq("patient_id", id).execute()
        if not p_res.data:
            raise HTTPException(status_code=404, detail="Patient not found.")

        # Validate date format
        try:
            date.fromisoformat(body.date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use ISO format (YYYY-MM-DD).")

        supabase.table("patients").update({"next_transfusion_due": body.date}).eq("patient_id", id).execute()

        return {"success": True, "next_transfusion_due": body.date}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting next transfusion for patient {id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to set next transfusion date.")


# ═══════════════════════════════════════════════════════════════════════════════
# Feature: Patient Health Record Update (hemoglobin + antigen flags)
# ═══════════════════════════════════════════════════════════════════════════════

class PatientHealthUpdate(BaseModel):
    hemoglobin: Optional[float] = None
    antibody_kell: Optional[bool] = None
    antibody_duffy: Optional[bool] = None
    antibody_kidd: Optional[bool] = None
    antibody_rh_e: Optional[bool] = None
    antibody_rh_c: Optional[bool] = None
    antibody_mns: Optional[bool] = None


@router.patch("/{id}/health")
async def update_patient_health(id: str, body: PatientHealthUpdate):
    """
    PATCH /api/patients/{id}/health
    Updates patient hemoglobin level and antibody/antigen flags.
    """
    supabase = get_supabase_admin()
    try:
        p_res = supabase.table("patients").select("patient_id").eq("patient_id", id).execute()
        if not p_res.data:
            raise HTTPException(status_code=404, detail="Patient not found.")

        update_data = {}
        if body.hemoglobin is not None:
            update_data["hemoglobin"] = body.hemoglobin
        if body.antibody_kell is not None:
            update_data["antibody_kell"] = body.antibody_kell
        if body.antibody_duffy is not None:
            update_data["antibody_duffy"] = body.antibody_duffy
        if body.antibody_kidd is not None:
            update_data["antibody_kidd"] = body.antibody_kidd
        if body.antibody_rh_e is not None:
            update_data["antibody_rh_e"] = body.antibody_rh_e
        if body.antibody_rh_c is not None:
            update_data["antibody_rh_c"] = body.antibody_rh_c
        if body.antibody_mns is not None:
            update_data["antibody_mns"] = body.antibody_mns

        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update.")

        supabase.table("patients").update(update_data).eq("patient_id", id).execute()

        return {"success": True, "updated": update_data}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating health for patient {id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Health record update failed.")


# ═══════════════════════════════════════════════════════════════════════════════
# Feature 5: Patient Bridges (Blood Bridge Visualization)
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/{id}/bridges")
async def get_patient_bridges(id: str):
    """
    GET /api/patients/{id}/bridges
    Returns list of donors mapped to this patient via bridge_memberships.
    """
    supabase = get_supabase_admin()
    try:
        p_res = supabase.table("patients").select("*").eq("patient_id", id).execute()
        if not p_res.data:
            raise HTTPException(status_code=404, detail="Patient not found.")
        patient = p_res.data[0]

        # Query bridge memberships where this patient is the bridge
        bridge_res = supabase.table("bridge_memberships")\
            .select("*")\
            .eq("bridge_id", id)\
            .execute()

        from ml.antigen_scorer import compute_antigen_score

        results = []
        for membership in (bridge_res.data or []):
            donor_id = membership.get("donor_id")
            if not donor_id:
                continue

            # Fetch donor info
            d_res = supabase.table("donors").select("*").eq("donor_id", donor_id).execute()
            if not d_res.data:
                continue
            donor = d_res.data[0]
            donor_name = donor.get("name", "Donor")
            donor_blood_type = donor.get("blood_type", "Unknown")

            # Dynamically compute matching score
            score = 0.5
            try:
                score = compute_antigen_score(donor, patient)
            except Exception as e:
                logger.warning(f"Failed to compute antigen score for donor {donor_id}: {e}")

            results.append({
                "donor_id": donor_id,
                "donor_name": donor_name,
                "blood_type": donor_blood_type,
                "antigen_score": score,
                "joined_at": membership.get("created_at") or membership.get("joined_at"),
            })

        return results
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching bridges for patient {id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch bridge data.")
