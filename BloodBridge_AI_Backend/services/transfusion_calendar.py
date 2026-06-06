"""
Transfusion calendar module for BloodBridge AI.
"""
from datetime import date, datetime, timedelta
import logging
from core.database import get_supabase_admin
from core.config import get_settings

logger = logging.getLogger(__name__)

async def get_patients_due_in_days(advance_days: int = 5) -> list:
    """Fetch patients who have a transfusion scheduled in advance_days (or up to 7 days)."""
    supabase = get_supabase_admin()
    today = date.today()
    target_date = today + timedelta(days=advance_days)
    target_date_str = target_date.isoformat()
    
    try:
        # Query transfusion_schedule for PENDING scheduled transfusions
        res = supabase.table("transfusion_schedule")\
            .select("schedule_id, patient_id, scheduled_date, hospital, blood_type")\
            .eq("status", "PENDING")\
            .lte("scheduled_date", (today + timedelta(days=7)).isoformat())\
            .gte("scheduled_date", target_date_str)\
            .execute()
            
        results = []
        for item in (res.data or []):
            due_date = date.fromisoformat(item["scheduled_date"])
            days_until = (due_date - today).days
            results.append({
                "schedule_id": item["schedule_id"],
                "patient_id": item["patient_id"],
                "blood_type": item["blood_type"],
                "hospital": item["hospital"],
                "city": "Hyderabad",  # Fallback city
                "days_until_due": days_until
            })
            
        # Get patient details to fill in city
        for item in results:
            p_res = supabase.table("patients").select("city").eq("patient_id", item["patient_id"]).execute()
            if p_res.data:
                item["city"] = p_res.data[0].get("city", "Hyderabad")
                
        return results
    except Exception as e:
        logger.error(f"Error getting patients due: {e}")
        return []

async def mark_schedule_outreach_started(schedule_id: int, request_id: str):
    """Update scheduled transfusion status to OUTREACH_STARTED and bind the request_id."""
    supabase = get_supabase_admin()
    try:
        supabase.table("transfusion_schedule")\
            .update({
                "status": "OUTREACH_STARTED",
                "request_id": request_id,
                "outreach_started_at": datetime.now().isoformat()
            })\
            .eq("schedule_id", schedule_id)\
            .execute()
        logger.info(f"Updated transfusion schedule {schedule_id} with request {request_id}")
    except Exception as e:
        logger.error(f"Failed to update transfusion schedule {schedule_id}: {e}")

async def mark_schedule_completed(schedule_id: int):
    """Update status to COMPLETED."""
    supabase = get_supabase_admin()
    try:
        supabase.table("transfusion_schedule")\
            .update({
                "status": "COMPLETED",
                "completed_at": datetime.now().isoformat()
            })\
            .eq("schedule_id", schedule_id)\
            .execute()
        logger.info(f"Marked transfusion schedule {schedule_id} as COMPLETED")
    except Exception as e:
        logger.error(f"Failed to update transfusion schedule {schedule_id}: {e}")

async def mark_schedule_completed_by_request(request_id: str):
    """Mark transfusion schedule as completed based on request_id."""
    supabase = get_supabase_admin()
    try:
        supabase.table("transfusion_schedule")\
            .update({
                "status": "COMPLETED",
                "completed_at": datetime.now().isoformat()
            })\
            .eq("request_id", request_id)\
            .execute()
        logger.info(f"Marked transfusion schedule for request {request_id} as COMPLETED")
    except Exception as e:
        logger.error(f"Failed to update transfusion schedule for request {request_id}: {e}")

async def get_upcoming_schedule(days: int = 30) -> list:
    """Dashboard calendar view — all upcoming scheduled transfusions sorted by date."""
    supabase = get_supabase_admin()
    today = date.today()
    target_date = today + timedelta(days=days)
    try:
        res = supabase.table("transfusion_schedule")\
            .select("*")\
            .gte("scheduled_date", today.isoformat())\
            .lte("scheduled_date", target_date.isoformat())\
            .order("scheduled_date")\
            .execute()
        return res.data or []
    except Exception as e:
        logger.error(f"Error getting upcoming schedule: {e}")
        return []

async def create_schedule_entry(patient_id: str, scheduled_date: str, hospital: str, advance_days: int = 5, created_by: str = "staff") -> dict:
    """Create a new transfusion schedule entry."""
    supabase = get_supabase_admin()
    try:
        p_res = supabase.table("patients").select("blood_type").eq("patient_id", patient_id).execute()
        blood_type = p_res.data[0].get("blood_type", "O+") if p_res.data else "O+"
        
        res = supabase.table("transfusion_schedule").insert({
            "patient_id": patient_id,
            "scheduled_date": scheduled_date,
            "hospital": hospital,
            "blood_type": blood_type,
            "status": "PENDING",
            "created_by": created_by
        }).execute()
        return res.data[0] if res.data else {}
    except Exception as e:
        logger.error(f"Error creating schedule entry: {e}")
        return {}

async def auto_generate_schedule_from_history(patient_id: str):
    """Gemini infers transfusion intervals from patient history and predicts next 3 entries."""
    supabase = get_supabase_admin()
    try:
        res = supabase.table("emergency_requests")\
            .select("completed_at, hospital_name")\
            .eq("patient_id", patient_id)\
            .eq("status", "COMPLETED")\
            .order("completed_at")\
            .execute()
            
        completed_requests = res.data or []
        if len(completed_requests) < 2:
            logger.warning(f"Not enough history for patient {patient_id} to generate schedule automatically.")
            return
            
        dates = [datetime.fromisoformat(r["completed_at"].replace("Z", "")).date().isoformat() for r in completed_requests]
        hospital = completed_requests[-1].get("hospital_name", "General Hospital")
        
        settings = get_settings()
        try:
            from core.llm_provider import get_reasoning_llm
            import json
            
            llm = get_reasoning_llm()
            
            prompt = (
                f"A Thalassemia patient with ID {patient_id} had successful transfusions on the following dates: {dates}. "
                f"Based on this history, calculate the average interval between transfusions (in days) "
                f"and predict the dates of the next 3 scheduled transfusions. "
                f"Respond ONLY with a JSON list of ISO-formatted date strings (YYYY-MM-DD) representing the next 3 dates. "
                f"Do not include markdown tags, reply only with the JSON list."
            )
            resp = await llm.ainvoke(prompt)
            content = resp.content.strip()
            
            if content.startswith("```json"):
                content = content.split("```json")[1].split("```")[0].strip()
            elif content.startswith("```"):
                content = content.split("```")[1].split("```")[0].strip()
                
            predicted_dates = json.loads(content)
            for d in predicted_dates:
                await create_schedule_entry(patient_id, d, hospital, advance_days=5, created_by="gemini_auto")
            logger.info(f"Auto-generated 3 schedule entries for patient {patient_id}: {predicted_dates}")
        except Exception as e:
            logger.error(f"Gemini auto schedule generation failed: {e}", exc_info=True)
    except Exception as e:
        logger.error(f"auto_generate_schedule_from_history failed for {patient_id}: {e}", exc_info=True)
