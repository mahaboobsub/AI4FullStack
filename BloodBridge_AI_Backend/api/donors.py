"""
Donor operations API routes for BloodBridge AI.
Implements listing, sorting, filtering, voice/telegram triggers, leaderboard, DPDP 2023 consent compliance, and CSV bulk import.
"""
import io
import csv
import uuid
import re
import logging
from datetime import datetime, date
from fastapi import APIRouter, HTTPException, Depends, Query, Request, UploadFile, File, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

from core.database import get_supabase_admin
from core.neo4j_client import get_neo4j
from core.limiter import limiter
from core.security import get_current_staff_admin
from services.consent_service import consent_service
from services.gamification_service import get_city_leaderboard

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/donors", tags=["donors"])

# ── Constants ──────────────────────────────────────────────────────────────────
VALID_BLOOD_TYPES = {"A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"}
CSV_REQUIRED_COLS = {"name", "phone", "blood_type", "city"}
CSV_OPTIONAL_COLS = {
    "ward", "kell_negative", "duffy_negative", "kidd_negative",
    "preferred_language", "donation_count", "hemoglobin", "last_donation_date"
}

# Pydantic Schemas matching lib/api.ts
class DonorResponse(BaseModel):
    donor_id: str
    name: str
    blood_type: str
    city: str
    kell_negative: bool
    churn_score: float
    churn_risk: str
    donation_count: int
    lives_saved: int
    last_donation_days: int
    response_rate: float
    badges: List[str]
    preferred_language: str
    antigen_score: Optional[float] = None
    telegram_chat_id: Optional[str] = None

class RevokeConsentRequest(BaseModel):
    consent_type: str = Field(default="all", description="The type of consent to revoke (e.g. 'all', 'sms', 'voice', 'telegram')")

class VoiceCallResponse(BaseModel):
    callSid: str

class OutreachResponse(BaseModel):
    messageId: str

class LeaderboardEntryResponse(BaseModel):
    rank: int
    name: str
    city: str
    lives_saved: int
    donation_count: int
    badges: List[str]

class BulkImportRequest(BaseModel):
    donors: List[Dict[str, Any]]

class BulkImportResponse(BaseModel):
    success: bool
    imported_count: int
    failed_count: int
    errors: List[str]

class CsvBulkImportResponse(BaseModel):
    success: bool
    imported_count: int
    skipped_duplicates: int
    failed_count: int
    errors: List[str]
    neo4j_edges_queued: bool

@router.get("", response_model=List[DonorResponse])
async def list_donors(
    sortBy: Optional[str] = Query("churn_score", description="Column to sort donors by"),
    riskFilter: Optional[str] = Query(None, description="Filter by churn risk tier")
):
    """
    GET /api/donors
    Lists all registered donors with optional sorting and churn risk filtering.
    """
    supabase = get_supabase_admin()
    try:
        # Query donors
        query = supabase.table("donors").select("*")
        if riskFilter:
            query = query.eq("churn_risk", riskFilter.upper())
            
        res = query.execute()
        donors_raw = res.data or []
        
        # Optimize badges query: fetch all memory mappings
        mem_res = supabase.table("donor_memory").select("donor_id, badges").execute()
        badge_map = {m["donor_id"]: m.get("badges", []) for m in mem_res.data} if mem_res.data else {}
        
        donors = []
        for d in donors_raw:
            d_id = d["donor_id"]
            
            # Calculate last donation days
            last_donation = d.get("last_donation_date")
            days_ago = 365
            if last_donation:
                try:
                    days_ago = (date.today() - date.fromisoformat(str(last_donation))).days
                except Exception:
                    pass
                    
            donors.append({
                "donor_id": d_id,
                "name": d["name"],
                "blood_type": d["blood_type"],
                "city": d["city"],
                "kell_negative": d.get("kell_negative", False),
                "churn_score": d.get("churn_score", 0.5) or 0.5,
                "churn_risk": d.get("churn_risk", "MEDIUM"),
                "donation_count": d.get("donation_count", 0) or 0,
                "lives_saved": d.get("lives_saved", 0) or 0,
                "last_donation_days": days_ago,
                "response_rate": d.get("response_rate", 0.5) or 0.5,
                "badges": badge_map.get(d_id, []),
                "preferred_language": d.get("preferred_language", "Hindi"),
                "telegram_chat_id": d.get("telegram_chat_id")
            })
            
        # Sorting
        rev = True
        if sortBy == "name":
            rev = False
            
        def sort_key(x):
            val = x.get(sortBy, 0)
            return val if val is not None else 0
            
        donors_sorted = sorted(donors, key=sort_key, reverse=rev)
        return donors_sorted
    except Exception as e:
        logger.error(f"Failed to list donors: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch donors.")

@router.get("/leaderboard", response_model=List[LeaderboardEntryResponse])
async def get_leaderboard(city: str = Query(..., description="The city for the leaderboard")):
    """
    GET /api/leaderboard
    Retrieves the pre-computed top-10 leaderboard rankings for a city.
    """
    try:
        raw_leaderboard = await get_city_leaderboard(city)
        
        # Populate each entry with donation count and badges from database
        supabase = get_supabase_admin()
        results = []
        
        for r in raw_leaderboard:
            d_id = r["donor_id"]
            
            d_profile = supabase.table("donors").select("donation_count").eq("donor_id", d_id).execute()
            d_count = d_profile.data[0]["donation_count"] if d_profile.data else 0
            
            d_mem = supabase.table("donor_memory").select("badges").eq("donor_id", d_id).execute()
            d_badges = d_mem.data[0]["badges"] if d_mem.data else []
            
            results.append({
                "rank": r["rank"],
                "name": r["name"],
                "city": city,
                "lives_saved": r["lives_saved"],
                "donation_count": d_count,
                "badges": d_badges
            })
            
        return results
    except Exception as e:
        logger.error(f"Failed to fetch leaderboard for city {city}: {e}")
        raise HTTPException(status_code=500, detail="Database lookup failed.")

# ── Phase 1.2: Donor Lookup by Phone / Telegram Chat ID ────────────────────────

class AvailabilityRequest(BaseModel):
    available: bool = Field(description="Whether the donor is available for donations")
    until: Optional[str] = Field(default=None, description="Date until which the donor is unavailable (ISO format, e.g. 2026-06-20)")

@router.get("/lookup")
@limiter.limit("1/second")
async def lookup_donor(
    request: Request,
    phone: Optional[str] = Query(None, description="Phone number to look up"),
    telegram_chat_id: Optional[str] = Query(None, description="Telegram chat ID to look up")
):
    """
    GET /api/donors/lookup?phone={phone_number}
    GET /api/donors/lookup?telegram_chat_id={chat_id}
    Looks up a donor by phone number or Telegram chat ID. Rate-limited 1 req/sec/IP.
    """
    if not phone and not telegram_chat_id:
        raise HTTPException(status_code=400, detail="Provide either 'phone' or 'telegram_chat_id' query parameter.")

    supabase = get_supabase_admin()
    try:
        if phone:
            # Normalize phone for lookup
            from api.donors import _normalize_phone
            normalized = _normalize_phone(phone)
            res = supabase.table("donors").select("*").eq("phone", normalized).execute()
            if not res.data:
                # Try raw phone as fallback
                res = supabase.table("donors").select("*").eq("phone", phone).execute()
        else:
            res = supabase.table("donors").select("*").eq("telegram_chat_id", str(telegram_chat_id)).execute()

        if not res.data:
            raise HTTPException(status_code=404, detail="Donor not found.")

        d = res.data[0]
        d_id = d["donor_id"]

        # Fetch badges
        mem_res = supabase.table("donor_memory").select("badges").eq("donor_id", d_id).execute()
        badges = mem_res.data[0].get("badges", []) if mem_res.data else []

        # Calculate days
        last_donation = d.get("last_donation_date")
        days_ago = 365
        if last_donation:
            try:
                days_ago = (date.today() - date.fromisoformat(str(last_donation))).days
            except Exception:
                pass

        return {
            "donor_id": d_id,
            "name": d["name"],
            "blood_type": d["blood_type"],
            "city": d["city"],
            "kell_negative": d.get("kell_negative", False),
            "churn_score": d.get("churn_score", 0.5) or 0.5,
            "churn_risk": d.get("churn_risk", "MEDIUM"),
            "donation_count": d.get("donation_count", 0) or 0,
            "lives_saved": d.get("lives_saved", 0) or 0,
            "last_donation_days": days_ago,
            "response_rate": d.get("response_rate", 0.5) or 0.5,
            "badges": badges,
            "preferred_language": d.get("preferred_language", "Hindi"),
            "telegram_chat_id": d.get("telegram_chat_id")
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Donor lookup failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Donor lookup failed.")

@router.get("/{id}", response_model=DonorResponse)
async def get_donor(id: str):
    """
    GET /api/donors/{id}
    Retrieves a single donor profile.
    """
    supabase = get_supabase_admin()
    try:
        res = supabase.table("donors").select("*").eq("donor_id", id).execute()
        if not res.data:
            raise HTTPException(status_code=404, detail="Donor not found.")
            
        d = res.data[0]
        
        # Fetch badges
        mem_res = supabase.table("donor_memory").select("badges").eq("donor_id", id).execute()
        badges = mem_res.data[0].get("badges", []) if mem_res.data else []
        
        # Calculate days
        last_donation = d.get("last_donation_date")
        days_ago = 365
        if last_donation:
            try:
                days_ago = (date.today() - date.fromisoformat(str(last_donation))).days
            except Exception:
                pass
                
        return {
            "donor_id": d["donor_id"],
            "name": d["name"],
            "blood_type": d["blood_type"],
            "city": d["city"],
            "kell_negative": d.get("kell_negative", False),
            "churn_score": d.get("churn_score", 0.5) or 0.5,
            "churn_risk": d.get("churn_risk", "MEDIUM"),
            "donation_count": d.get("donation_count", 0) or 0,
            "lives_saved": d.get("lives_saved", 0) or 0,
            "last_donation_days": days_ago,
            "response_rate": d.get("response_rate", 0.5) or 0.5,
            "badges": badges,
            "preferred_language": d.get("preferred_language", "Hindi"),
            "telegram_chat_id": d.get("telegram_chat_id"),
            "is_active": d.get("is_active", True)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching donor {id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database query failed.")

@router.get("/{id}/memory")
async def get_donor_memory(id: str):
    """GET /api/donors/{id}/memory — Returns non-sensitive donor memory fields."""
    supabase = get_supabase_admin()
    try:
        res = supabase.table("donor_memory").select("badges, impact_stories, streak_days").eq("donor_id", id).execute()
        if not res.data:
            return {"badges": [], "impact_stories": [], "streak_days": 0}
        d = res.data[0]
        return {
            "badges": d.get("badges", []) or [],
            "impact_stories": d.get("impact_stories", []) or [],
            "streak_days": d.get("streak_days", 0) or 0
        }
    except Exception as e:
        logger.error(f"Error fetching donor memory {id}: {e}")
        return {"badges": [], "impact_stories": [], "streak_days": 0}

@router.get("/{id}/eligibility")
async def check_donor_eligibility_status(id: str):
    """
    GET /api/donors/{id}/eligibility
    Checks the general WHO/NBTC eligibility gates for a donor.
    """
    supabase = get_supabase_admin()
    try:
        res = supabase.table("donors").select("*").eq("donor_id", id).execute()
        if not res.data:
            raise HTTPException(status_code=404, detail="Donor not found.")
            
        donor = res.data[0]
        
        eligible = True
        reasons = []
        days_until_eligible = 0
        
        if not donor.get("is_active"):
            eligible = False
            reasons.append("Donor profile is inactive.")
        if donor.get("medical_hold"):
            eligible = False
            reasons.append("Donor is on active medical hold.")
            
        last_date = donor.get("last_donation_date")
        if last_date:
            delta = (date.today() - date.fromisoformat(str(last_date))).days
            if delta < 56:
                eligible = False
                days_until_eligible = 56 - delta
                reasons.append(f"Less than 56 days since last donation ({delta} days passed, {days_until_eligible} remaining).")
                
        hgb = donor.get("hemoglobin")
        if hgb is not None and hgb < 12.5:
            eligible = False
            reasons.append(f"Hemoglobin level is low ({hgb} g/dL, minimum required is 12.5 g/dL).")
            
        return {
            "eligible": eligible,
            "reason": "; ".join(reasons) if not eligible else None,
            "days_until_eligible": days_until_eligible if days_until_eligible > 0 else None
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking eligibility for donor {id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Eligibility check failed.")

# ── Phase 1.3: Leaderboard Rank for Single Donor ──────────────────────────────

@router.get("/{id}/rank")
async def get_donor_rank(id: str):
    """
    GET /api/donors/{id}/rank
    Returns the donor's leaderboard rank and lives_saved count for their city.
    """
    supabase = get_supabase_admin()
    try:
        # Get donor city
        d_res = supabase.table("donors").select("city, lives_saved").eq("donor_id", id).execute()
        if not d_res.data:
            raise HTTPException(status_code=404, detail="Donor not found.")

        city = d_res.data[0].get("city", "Hyderabad")
        lives_saved = d_res.data[0].get("lives_saved", 0) or 0

        # Try leaderboard_cache first
        rank = None
        try:
            lb_res = supabase.table("leaderboard_cache")\
                .select("rank, lives_saved")\
                .eq("donor_id", id)\
                .eq("city", city)\
                .execute()
            if lb_res.data:
                rank = lb_res.data[0].get("rank")
                lives_saved = lb_res.data[0].get("lives_saved", lives_saved)
        except Exception:
            pass

        # If not in cache, compute rank from all donors in same city
        if rank is None:
            all_donors = supabase.table("donors")\
                .select("donor_id, lives_saved")\
                .eq("city", city)\
                .order("lives_saved", desc=True)\
                .execute()
            for idx, d in enumerate(all_donors.data or []):
                if d["donor_id"] == id:
                    rank = idx + 1
                    break
            if rank is None:
                rank = 0

        return {
            "donor_id": id,
            "city": city,
            "rank": rank,
            "lives_saved": lives_saved
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching rank for donor {id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Rank lookup failed.")

# ── Phase 1.4: Active Emergency Request for Donor ─────────────────────────────

@router.get("/{id}/active-request")
async def get_donor_active_request(id: str):
    """
    GET /api/donors/{id}/active-request
    Returns active emergency request if one exists for this donor, or null.
    Powers the 'Urgent Match Found' card in DonorPortal.
    """
    supabase = get_supabase_admin()
    try:
        # Find active chain nodes for this donor
        chain_res = supabase.table("blood_chains")\
            .select("*")\
            .eq("donor_id", id)\
            .in_("status", ["ALERTED", "SMS", "VOICE"])\
            .order("alerted_at", desc=True)\
            .limit(1)\
            .execute()

        if not chain_res.data:
            return None

        node = chain_res.data[0]
        request_id = node["request_id"]

        # Get emergency request details
        req_res = supabase.table("emergency_requests")\
            .select("patient_id, blood_type, hospital_name, city, urgency_score, status")\
            .eq("request_id", request_id)\
            .execute()

        if not req_res.data:
            return None

        req = req_res.data[0]

        # Get patient info for display
        patient_name = "Patient"
        patient_age = None
        p_res = supabase.table("patients").select("name, age").eq("patient_id", req["patient_id"]).execute()
        if p_res.data:
            # Anonymize: first name only
            patient_name = p_res.data[0].get("name", "Patient").split()[0]
            patient_age = p_res.data[0].get("age")

        return {
            "request_id": request_id,
            "patient_first_name": patient_name,
            "patient_age": patient_age,
            "blood_type": req.get("blood_type"),
            "hospital": req.get("hospital_name"),
            "city": req.get("city"),
            "urgency_score": req.get("urgency_score"),
            "urgency_level": "CRITICAL" if (req.get("urgency_score") or 0) >= 80 else ("HIGH" if (req.get("urgency_score") or 0) >= 50 else "ROUTINE"),
            "compatibility_score": node.get("antigen_score"),
            "chain_position": node.get("chain_position"),
            "alerted_at": node.get("alerted_at")
        }
    except Exception as e:
        logger.error(f"Error fetching active request for donor {id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Active request lookup failed.")

# ── Phase 1.6: Availability Toggle for Donors ────────────────────────────────

@router.post("/{id}/availability")
async def set_donor_availability(id: str, body: AvailabilityRequest):
    """
    POST /api/donors/{id}/availability
    Toggles donor availability. Sets is_active flag and optional medical_hold_until date.
    """
    supabase = get_supabase_admin()
    try:
        # Verify donor exists
        d_res = supabase.table("donors").select("donor_id").eq("donor_id", id).execute()
        if not d_res.data:
            raise HTTPException(status_code=404, detail="Donor not found.")

        update_data = {
            "is_active": body.available,
            "medical_hold": not body.available,
        }

        if body.until and not body.available:
            # Validate date format
            try:
                date.fromisoformat(body.until)
                update_data["medical_hold_until"] = body.until
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format. Use ISO format (YYYY-MM-DD).")
        elif body.available:
            update_data["medical_hold"] = False
            update_data["medical_hold_until"] = None

        supabase.table("donors").update(update_data).eq("donor_id", id).execute()

        return {
            "success": True,
            "donor_id": id,
            "available": body.available,
            "until": body.until if not body.available else None
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating availability for donor {id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Availability update failed.")

@router.post("/{id}/voice", response_model=VoiceCallResponse)
@limiter.limit("10/hour")
async def trigger_voice_call_public(id: str, request: Request):
    """
    POST /api/donors/{id}/voice
    Triggers an outbound Vapi.ai automated voice call to the donor.
    """
    supabase = get_supabase_admin()
    try:
        # Fetch donor profile
        res = supabase.table("donors").select("*").eq("donor_id", id).execute()
        if not res.data:
            raise HTTPException(status_code=404, detail="Donor not found.")
        donor = res.data[0]
        phone = donor.get("phone")
        if not phone:
            raise HTTPException(status_code=400, detail="Donor does not have a registered phone number.")
            
        # Trigger outbound voice call
        from services.voice_service import make_bolna_call
        result = await make_bolna_call(
            phone=phone,
            donor=donor,
            emergency={"blood_type": donor["blood_type"], "hospital_name": "Blood Warriors Center"},
            request_id=f"MANUAL-{id[:4]}"
        )
        
        if result["status"] == "INITIATED":
            return {"callSid": result["call_id"]}
        elif result["status"] == "QUEUED":
            raise HTTPException(status_code=202, detail=f"Call queued: {result.get('reason', 'will retry during safe hours')}. TRAI safe hours: 8 AM - 9 PM IST.")
        elif result["status"] == "SKIPPED":
            raise HTTPException(status_code=400, detail=f"Call skipped: {result.get('reason', 'configuration issue')}")
        elif result["status"] == "NO_CONSENT":
            raise HTTPException(status_code=403, detail="Donor has not consented to voice outreach.")
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "Bolna call initiation failed."))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to trigger manual voice call to donor {id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{id}/outreach", response_model=OutreachResponse)
async def trigger_outreach_public(id: str):
    """
    POST /api/donors/{id}/outreach
    Triggers a manual outreach message to the donor via Telegram.
    """
    supabase = get_supabase_admin()
    try:
        res = supabase.table("donors").select("name, preferred_language, telegram_chat_id").eq("donor_id", id).execute()
        if not res.data:
            raise HTTPException(status_code=404, detail="Donor not found.")
            
        donor = res.data[0]
        chat_id = donor.get("telegram_chat_id")
        name = donor["name"]
        lang = donor.get("preferred_language", "en")
        
        if not chat_id:
            raise HTTPException(status_code=400, detail="Donor does not have a registered Telegram Chat ID.")
            
        msg = f"Namaste {name}. We appreciate your support at Blood Warriors. Feel free to interact with our bot or check your progress on /badges."
        if lang.lower().startswith("te"):
            msg = f"నమస్తే {name}. బ్లడ్ వారియర్స్ కి మీ మద్దతును మేము అభినందిస్తున్నాము. మీ వివరాలు మరియు బ్యాడ్జ్ ల కోసం /badges టైప్ చేయండి."
            
        from services.telegram_bot import send_telegram_message
        success = await send_telegram_message(chat_id, msg)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to deliver Telegram message.")
            
        return {"messageId": f"MSG-{id}-{int(datetime.utcnow().timestamp())}"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to trigger outreach to donor {id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{id}/consent")
async def get_consent_summary(id: str):
    """
    GET /api/donors/{id}/consent
    Fetch the status of all consent categories for a given donor.
    """
    summary = await consent_service.get_consent_summary(id)
    return summary

@router.post("/{id}/consent/revoke")
async def revoke_consent(id: str, request: RevokeConsentRequest):
    """
    POST /api/donors/{id}/consent/revoke
    Revoke a specific consent type or all consents.
    """
    type_clean = request.consent_type.lower().strip()
    
    if type_clean in ['sms', 'outreach_sms']:
        c_type = 'outreach_sms'
    elif type_clean in ['voice', 'outreach_voice']:
        c_type = 'outreach_voice'
    elif type_clean in ['telegram', 'outreach_telegram']:
        c_type = 'outreach_telegram'
    elif type_clean == 'all':
        c_type = 'all'
    else:
        allowed_types = {
            'data_storage', 'outreach_telegram', 'outreach_voice',
            'outreach_sms', 'data_sharing_bloodwarriors', 'data_sharing_hospitals'
        }
        if type_clean not in allowed_types:
            raise HTTPException(status_code=400, detail=f"Invalid consent type. Allowed: {list(allowed_types)} or 'all'/'sms'/'voice'/'telegram'")
        c_type = type_clean
        
    success = await consent_service.revoke_consent(id, c_type)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to revoke consent.")
        
    return {"success": True, "message": f"Consent for '{c_type}' successfully revoked."}

@router.delete("/{id}/data")
async def delete_donor_data(id: str):
    """
    DELETE /api/donors/{id}/data
    Right to Erasure (DPDP Section 12).
    """
    result = await consent_service.erase_donor_data(id, requested_by="api_request")
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to execute right to erasure."))
        
    return {"success": True}

@router.get("/{id}/my-data")
async def export_donor_data(id: str):
    """
    GET /api/donors/{id}/my-data
    Right to Access (DPDP Section 11).
    """
    export = await consent_service.export_donor_data(id)
    if "error" in export:
        raise HTTPException(status_code=500, detail=export["error"])
        
    return export

@router.post("/bulk-import", response_model=BulkImportResponse)
@limiter.limit("3/day")
async def bulk_import_donors(request: Request, payload: BulkImportRequest):
    """
    POST /api/donors/bulk-import
    Admin endpoint to upload a batch of pre-consented donor records (JSON body).
    """
    supabase = get_supabase_admin()
    imported = 0
    failed = 0
    errors = []
    
    for idx, raw_d in enumerate(payload.donors):
        try:
            name = raw_d.get("name")
            blood_type = raw_d.get("blood_type")
            city = raw_d.get("city")
            phone = raw_d.get("phone")
            
            if not name or not blood_type or not city:
                raise ValueError("Missing critical fields: 'name', 'blood_type', or 'city'.")
                
            # Check duplicates by phone
            if phone:
                dup_res = supabase.table("donors").select("donor_id").eq("phone", phone).execute()
                if dup_res.data:
                    raise ValueError(f"Phone {phone} already registered to donor {dup_res.data[0]['donor_id']}.")
                    
            # Insert donor
            insert_res = supabase.table("donors").insert({
                "name": name,
                "blood_type": blood_type,
                "city": city,
                "phone": phone,
                "telegram_chat_id": raw_d.get("telegram_chat_id"),
                "kell_negative": raw_d.get("kell_negative", False),
                "preferred_language": raw_d.get("preferred_language", "Hindi"),
                "is_active": True,
                "consent_data_storage": True,
                "consent_outreach": True,
                "consent_granted_at": datetime.utcnow().isoformat() + "Z"
            }).execute()
            
            if not insert_res.data:
                raise RuntimeError("Failed to insert record into Supabase donors table.")
                
            donor_id = insert_res.data[0]["donor_id"]
            
            # Setup consent record
            await consent_service.grant_consent(
                donor_id=donor_id,
                consent_types=["data_storage", "outreach_telegram", "outreach_sms"],
                channel="bulk_import",
                language=raw_d.get("preferred_language", "en")
            )
            
            # Initialize empty memory record
            supabase.table("donor_memory").insert({
                "donor_id": donor_id,
                "preferred_language": raw_d.get("preferred_language", "Hindi")
            }).execute()
            
            imported += 1
        except Exception as e:
            failed += 1
            err_msg = f"Donor #{idx} ({raw_d.get('name', 'Unknown')}): {str(e)}"
            errors.append(err_msg)
            logger.warning(err_msg)
            
    return {
        "success": True if imported > 0 else False,
        "imported_count": imported,
        "failed_count": failed,
        "errors": errors
    }


# ── CSV Bulk Import (P6-D) ─────────────────────────────────────────────────────

def _normalize_phone(raw: str) -> str:
    """Strip non-digit chars, enforce E.164 +91 prefix for Indian numbers."""
    digits = re.sub(r"\D", "", raw or "")
    if len(digits) == 10:
        return f"+91{digits}"
    elif len(digits) == 12 and digits.startswith("91"):
        return f"+{digits}"
    elif len(digits) == 13 and digits.startswith("091"):
        return f"+{digits[1:]}"
    return digits  # Return as-is if format is unexpected


def _bool_field(val: str) -> bool:
    """Parse truthy CSV strings to Python bool."""
    return str(val).strip().lower() in ("true", "1", "yes", "y")


async def _build_neo4j_edges_background(donor_ids: List[str]):
    """
    Background task: build COMPATIBLE_WITH edges in Neo4j for newly imported donors.
    Runs after the HTTP response is sent, so the API stays fast.
    """
    try:
        from core.neo4j_client import get_driver
        from ml.antigen_scorer import score_antigen_compatibility
        supabase = get_supabase_admin()
        driver = get_driver()

        # Fetch newly inserted donor records
        res = supabase.table("donors").select("*").in_("donor_id", donor_ids).execute()
        donors = res.data or []

        # Fetch all active patients
        pat_res = supabase.table("patients").select("*").eq("is_active", True).execute()
        patients = pat_res.data or []

        edges_created = 0
        async with driver.session() as session:
            for donor in donors:
                for patient in patients:
                    try:
                        score_result = score_antigen_compatibility(donor, patient)
                        if score_result.get("compatible", False):
                            await session.run(
                                """
                                MERGE (d:Donor {donor_id: $donor_id})
                                MERGE (p:Patient {patient_id: $patient_id})
                                MERGE (d)-[r:COMPATIBLE_WITH]->(p)
                                SET r.score = $score, r.created_at = datetime()
                                """,
                                {
                                    "donor_id": donor["donor_id"],
                                    "patient_id": patient["patient_id"],
                                    "score": score_result.get("score", 0.5)
                                }
                            )
                            edges_created += 1
                    except Exception as e:
                        logger.warning(f"Neo4j edge build failed for {donor['donor_id']}: {e}")

        logger.info(f"Neo4j background task: {edges_created} COMPATIBLE_WITH edges created for {len(donor_ids)} new donors.")
    except Exception as e:
        logger.error(f"Neo4j background edge-build task failed: {e}", exc_info=True)


@router.post("/bulk-import-csv", response_model=CsvBulkImportResponse)
@limiter.limit("3/day")
async def bulk_import_donors_csv(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="CSV file with donor records. Required columns: name, phone, blood_type, city"),
    grant_consent: bool = Query(True, description="Set True if offline consent was already obtained from all donors"),
    staff: dict = Depends(get_current_staff_admin)
):
    """
    POST /api/donors/bulk-import-csv  (Admin only, 3/day)
    ---
    Bulk-imports donors from a UTF-8 CSV file.
    Required CSV columns: name, phone, blood_type, city
    Optional: ward, kell_negative, duffy_negative, kidd_negative,
              preferred_language, donation_count, hemoglobin, last_donation_date

    Processing steps:
      1. Decode CSV (UTF-8 / UTF-8-BOM)
      2. Validate required headers
      3. Per-row: validate blood_type, normalize phone, dedup, build insert record
      4. Batch upsert to Supabase donors table
      5. Grant consent if grant_consent=True
      6. Create donor_verifications records (channel=csv_import)
      7. Background task: build Neo4j COMPATIBLE_WITH edges
      8. Return structured import report
    """
    # ── 1. Decode ─────────────────────────────────────────────────────────────
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only .csv files are accepted.")

    try:
        raw_bytes = await file.read()
        # Strip UTF-8 BOM if present
        content = raw_bytes.decode("utf-8-sig").strip()
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be UTF-8 or UTF-8-BOM encoded.")

    # ── 2. Parse + validate headers ───────────────────────────────────────────
    try:
        reader = csv.DictReader(io.StringIO(content))
        fieldnames = set(f.strip().lower() for f in (reader.fieldnames or []))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid CSV format: {e}")

    missing_cols = CSV_REQUIRED_COLS - fieldnames
    if missing_cols:
        raise HTTPException(
            status_code=400,
            detail=f"Missing required CSV columns: {sorted(missing_cols)}"
        )

    # ── 3. Process rows ───────────────────────────────────────────────────────
    supabase = get_supabase_admin()
    insert_batch: List[dict] = []
    skipped_duplicates = 0
    failed_count = 0
    errors: List[str] = []

    rows = list(reader)
    if not rows:
        raise HTTPException(status_code=400, detail="CSV file contains no data rows.")

    if len(rows) > 5000:
        raise HTTPException(status_code=400, detail="Maximum 5,000 rows per import. Split into smaller batches.")

    # Pre-load all existing phones for dedup (one query vs N queries)
    existing_phones_res = supabase.table("donors").select("phone, donor_id").execute()
    existing_phone_map: Dict[str, str] = {
        r["phone"]: r["donor_id"]
        for r in (existing_phones_res.data or [])
        if r.get("phone")
    }

    for row_num, row in enumerate(rows, start=2):  # row 1 = header
        # Normalize column keys
        clean_row = {k.strip().lower(): v.strip() for k, v in row.items() if k}
        row_label = f"Row {row_num} (name={clean_row.get('name', '?')})"

        try:
            # Validate blood_type
            bt = clean_row.get("blood_type", "").upper().replace(" ", "")
            if bt not in VALID_BLOOD_TYPES:
                raise ValueError(f"Invalid blood_type '{bt}'. Must be one of {sorted(VALID_BLOOD_TYPES)}.")

            # Normalize phone
            raw_phone = clean_row.get("phone", "")
            if not raw_phone:
                raise ValueError("Phone number is required.")
            phone = _normalize_phone(raw_phone)
            if len(re.sub(r"\D", "", phone)) < 10:
                raise ValueError(f"Phone number '{raw_phone}' is too short after normalization.")

            # Duplicate check (in-memory dedup against pre-loaded map)
            if phone in existing_phone_map:
                skipped_duplicates += 1
                logger.debug(f"{row_label}: skipped — phone {phone} already exists as {existing_phone_map[phone]}")
                continue

            # Avoid in-batch duplicates too
            existing_phone_map[phone] = "PENDING"

            # Build insert record
            new_donor_id = str(uuid.uuid4())
            record = {
                "donor_id": new_donor_id,
                "name": clean_row.get("name", "").strip(),
                "blood_type": bt,
                "city": clean_row.get("city", "").strip(),
                "phone": phone,
                "ward": clean_row.get("ward") or None,
                "kell_negative": _bool_field(clean_row.get("kell_negative", "false")),
                "duffy_negative": _bool_field(clean_row.get("duffy_negative", "false")),
                "kidd_negative": _bool_field(clean_row.get("kidd_negative", "false")),
                "preferred_language": clean_row.get("preferred_language") or "Hindi",
                "donation_count": int(clean_row["donation_count"]) if clean_row.get("donation_count") else 0,
                "is_active": True,
                "created_at": datetime.utcnow().isoformat() + "Z",
            }

            # Optional hemoglobin
            if clean_row.get("hemoglobin"):
                try:
                    record["hemoglobin"] = float(clean_row["hemoglobin"])
                except ValueError:
                    pass

            # Optional last_donation_date
            if clean_row.get("last_donation_date"):
                try:
                    date.fromisoformat(clean_row["last_donation_date"])  # validate format
                    record["last_donation_date"] = clean_row["last_donation_date"]
                except ValueError:
                    logger.warning(f"{row_label}: invalid last_donation_date '{clean_row['last_donation_date']}', skipped field.")

            insert_batch.append(record)

        except ValueError as ve:
            failed_count += 1
            msg = f"{row_label}: {ve}"
            errors.append(msg)
            logger.warning(msg)
        except Exception as e:
            failed_count += 1
            msg = f"{row_label}: Unexpected error — {e}"
            errors.append(msg)
            logger.error(msg, exc_info=True)

    if not insert_batch:
        return CsvBulkImportResponse(
            success=False,
            imported_count=0,
            skipped_duplicates=skipped_duplicates,
            failed_count=failed_count,
            errors=errors,
            neo4j_edges_queued=False
        )

    # ── 4. Batch upsert ───────────────────────────────────────────────────────
    try:
        upsert_res = supabase.table("donors").upsert(
            insert_batch, on_conflict="phone"
        ).execute()
        inserted_donors = upsert_res.data or []
        new_donor_ids = [d["donor_id"] for d in inserted_donors if "donor_id" in d]
        imported_count = len(new_donor_ids)
    except Exception as e:
        logger.error(f"Batch upsert failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Database batch insert failed: {e}")

    # ── 5. Grant consent ──────────────────────────────────────────────────────
    if grant_consent and new_donor_ids:
        consent_types = ["data_storage", "outreach_telegram", "outreach_sms", "outreach_voice"]
        for d_id in new_donor_ids:
            try:
                await consent_service.grant_consent(
                    donor_id=d_id,
                    consent_types=consent_types,
                    channel="csv_import_offline_consent",
                    language="en"
                )
            except Exception as e:
                logger.warning(f"Consent grant failed for {d_id}: {e}")

    # ── 6. Create donor_verifications records ─────────────────────────────────
    if new_donor_ids:
        verification_records = [
            {
                "donor_id": d_id,
                "verification_method": "bulk_csv_import",
                "verified_by": staff.get("telegram_username", "admin"),
                "verified_at": datetime.utcnow().isoformat() + "Z",
                "notes": f"Imported via CSV by {staff.get('role', 'Staff')}"
            }
            for d_id in new_donor_ids
        ]
        try:
            supabase.table("donor_verifications").insert(verification_records).execute()
        except Exception as e:
            logger.warning(f"Failed to create verification records: {e}")

    # ── 7. Background: build Neo4j COMPATIBLE_WITH edges ─────────────────────
    neo4j_queued = False
    if new_donor_ids:
        background_tasks.add_task(_build_neo4j_edges_background, new_donor_ids)
        neo4j_queued = True
        logger.info(f"Neo4j edge build queued for {len(new_donor_ids)} donors.")

    # ── 8. Return import report ───────────────────────────────────────────────
    logger.info(
        f"CSV import complete: {imported_count} imported, "
        f"{skipped_duplicates} skipped (duplicates), {failed_count} failed."
    )
    return CsvBulkImportResponse(
        success=imported_count > 0,
        imported_count=imported_count,
        skipped_duplicates=skipped_duplicates,
        failed_count=failed_count,
        errors=errors,
        neo4j_edges_queued=neo4j_queued
    )

# ══════════════════════════════════════════════════════════════════════════════
# Graph Data Endpoint (Neo4j primary, Supabase fallback)
# ══════════════════════════════════════════════════════════════════════════════

def _graph_add_node(nodes: List[Dict[str, Any]], seen: set, node_id: str, **fields) -> None:
    if node_id in seen:
        return
    seen.add(node_id)
    nodes.append({"id": node_id, **fields})


async def _graph_from_neo4j(request_ids: Optional[List[str]] = None, city: str = "Hyderabad") -> Dict[str, Any]:
    """Build force-graph payload from Neo4j Donor/Patient nodes and COMPATIBLE_WITH / IN_CHAIN edges."""
    nodes: List[Dict[str, Any]] = []
    links: List[Dict[str, Any]] = []
    seen: set = set()

    supabase = get_supabase_admin()
    async with get_neo4j() as session:
        if request_ids:
            for req_id in request_ids:
                # Hospital node from Supabase request metadata
                try:
                    req_res = supabase.table("emergency_requests").select("patient_id,blood_type,hospital_name").eq("request_id", req_id).limit(1).execute()
                    if req_res.data:
                        req_row = req_res.data[0]
                        patient_id = req_row.get("patient_id", req_id)
                        hospital = req_row.get("hospital_name") or "Hospital"
                        hosp_id = f"HOSP-{abs(hash(hospital)) % 9999}"
                        _graph_add_node(nodes, seen, patient_id, type="patient",
                                        name=f"Patient {patient_id}", blood_type=req_row.get("blood_type"))
                        _graph_add_node(nodes, seen, hosp_id, type="hospital", name=hospital)
                        links.append({"source": hosp_id, "target": patient_id, "antigen_score": 1.0, "status": "HOSPITAL"})
                except Exception:
                    pass

                result = await session.run(
                    """
                    MATCH (d:Donor)-[r:IN_CHAIN {request_id: $request_id}]->(p:Patient)
                    RETURN d.donor_id AS donor_id, d.name AS donor_name, d.blood_type AS blood_type,
                           d.churn_score AS churn_score, d.donation_count AS donation_count,
                           d.kell_negative AS kell_negative, d.antigen_panel_json AS antigen_panel_json,
                           p.patient_id AS patient_id, p.name AS patient_name, p.blood_type AS patient_blood_type,
                           r.antigen_score AS antigen_score, r.status AS status, r.chain_position AS chain_position
                    ORDER BY r.chain_position
                    """,
                    request_id=req_id,
                )
                records = [r async for r in result]
                for rec in records:
                    pid = rec["patient_id"]
                    did = rec["donor_id"]
                    _graph_add_node(
                        nodes, seen, pid, type="patient",
                        name=rec.get("patient_name") or f"Patient {pid}",
                        blood_type=rec.get("patient_blood_type"),
                    )
                    panel_json = rec.get("antigen_panel_json")
                    panel = {}
                    if panel_json:
                        try:
                            import json as _json
                            panel = _json.loads(panel_json) if isinstance(panel_json, str) else panel_json
                        except Exception:
                            panel = {}
                    _graph_add_node(
                        nodes, seen, did, type="donor",
                        name=rec.get("donor_name") or did,
                        blood_type=rec.get("blood_type"),
                        churn_score=rec.get("churn_score"),
                        donation_count=rec.get("donation_count"),
                        antigen_score=rec.get("antigen_score"),
                        status=rec.get("status", "PENDING"),
                        antigen_panel=panel,
                        kell_negative=rec.get("kell_negative"),
                    )
                    # Link donors via hospital hub when present (Test 11 graph layout)
                    hosp_links = [l for l in links if l.get("status") == "HOSPITAL"]
                    link_source = hosp_links[-1]["source"] if hosp_links else pid
                    links.append({
                        "source": link_source, "target": did,
                        "antigen_score": rec.get("antigen_score") or 0.5,
                        "status": rec.get("status", "PENDING"),
                    })
        else:
            result = await session.run(
                """
                MATCH (d:Donor)-[c:COMPATIBLE_WITH]->(p:Patient)
                WHERE d.city = $city AND p.city = $city AND coalesce(d.is_active, true) = true
                RETURN d.donor_id AS donor_id, d.name AS donor_name, d.blood_type AS blood_type,
                       d.churn_score AS churn_score, d.donation_count AS donation_count,
                       p.patient_id AS patient_id, p.name AS patient_name, p.blood_type AS patient_blood_type,
                       c.antigen_score AS antigen_score
                ORDER BY c.antigen_score DESC
                LIMIT 40
                """,
                city=city,
            )
            records = [r async for r in result]
            for rec in records:
                pid = rec["patient_id"]
                did = rec["donor_id"]
                _graph_add_node(
                    nodes, seen, pid, type="patient",
                    name=rec.get("patient_name") or f"Patient {pid}",
                    blood_type=rec.get("patient_blood_type"),
                )
                _graph_add_node(
                    nodes, seen, did, type="donor",
                    name=rec.get("donor_name") or did,
                    blood_type=rec.get("blood_type"),
                    churn_score=rec.get("churn_score"),
                    donation_count=rec.get("donation_count"),
                    antigen_score=rec.get("antigen_score"),
                )
                links.append({
                    "source": pid, "target": did,
                    "antigen_score": rec.get("antigen_score") or 0.5,
                    "status": "COMPATIBLE",
                })

    return {"nodes": nodes, "links": links}


def _donor_antigen_panel(donor_row: Optional[dict], memory_notes: Optional[str] = None) -> dict:
    if not donor_row:
        return {}
    data = donor_row.get("antigen_data")
    if isinstance(data, dict):
        return data
    if isinstance(data, str):
        try:
            import json as _json
            return _json.loads(data)
        except Exception:
            pass
    if memory_notes:
        try:
            import json as _json
            parsed = _json.loads(memory_notes)
            if isinstance(parsed, dict) and parsed.get("antigen_panel"):
                return parsed["antigen_panel"]
        except Exception:
            pass
    return {}


async def _graph_from_supabase(request_id: Optional[str], city: str = "Hyderabad") -> Dict[str, Any]:
    """Supabase fallback when Neo4j is unavailable or returns empty."""
    supabase = get_supabase_admin()
    nodes: List[Dict[str, Any]] = []
    links: List[Dict[str, Any]] = []
    seen: set = set()
    donor_cache: Dict[str, dict] = {}

    if request_id and request_id != "all":
        req_res = supabase.table("emergency_requests").select("*").eq("request_id", request_id).execute()
        if req_res.data:
            req = req_res.data[0]
            patient_id = req.get("patient_id", request_id)
            _graph_add_node(nodes, seen, patient_id, type="patient",
                            name=f"Patient {patient_id}", blood_type=req.get("blood_type"))
            hospital = req.get("hospital_name", "Hospital")
            hosp_id = f"HOSP-{abs(hash(hospital)) % 9999}"
            _graph_add_node(nodes, seen, hosp_id, type="hospital", name=hospital)
            links.append({"source": hosp_id, "target": patient_id, "antigen_score": 1.0, "status": "HOSPITAL"})
            chain_res = supabase.table("blood_chains").select("*").eq("request_id", request_id).order("chain_position").execute()
            donor_ids = [n["donor_id"] for n in (chain_res.data or [])]
            memory_cache: Dict[str, str] = {}
            if donor_ids:
                d_rows = supabase.table("donors").select("*").in_("donor_id", donor_ids).execute()
                donor_cache = {d["donor_id"]: d for d in (d_rows.data or [])}
                mem_rows = supabase.table("donor_memory").select("donor_id,notes").in_("donor_id", donor_ids).execute()
                memory_cache = {m["donor_id"]: m.get("notes") or "" for m in (mem_rows.data or [])}
            for node in (chain_res.data or []):
                d_id = node["donor_id"]
                d_row = donor_cache.get(d_id, {})
                _graph_add_node(nodes, seen, d_id, type="donor", name=node.get("donor_name", d_id),
                                antigen_score=node.get("antigen_score", 0.5), status=node.get("status", "PENDING"),
                                blood_type=d_row.get("blood_type"), churn_score=d_row.get("churn_score"),
                                donation_count=d_row.get("donation_count"),
                                antigen_panel=_donor_antigen_panel(d_row, memory_cache.get(d_id)),
                                kell_negative=d_row.get("kell_negative"))
                links.append({"source": hosp_id, "target": d_id,
                              "antigen_score": node.get("antigen_score", 0.5), "status": node.get("status", "PENDING")})
    elif request_id == "all":
        active = supabase.table("emergency_requests").select("request_id").eq("status", "IN_PROGRESS").order("created_at", desc=True).limit(5).execute()
        for req in (active.data or []):
            sub = await _graph_from_supabase(req["request_id"], city)
            for n in sub["nodes"]:
                _graph_add_node(nodes, seen, n["id"], **{k: v for k, v in n.items() if k != "id"})
            links.extend(sub["links"])
    else:
        donors_res = supabase.table("donors").select("*").eq("is_active", True).eq("city", city).order("churn_score").limit(20).execute()
        for d in (donors_res.data or []):
            d_id = d.get("donor_id", "")
            _graph_add_node(nodes, seen, d_id, type="donor", name=d.get("name", d_id),
                            blood_type=d.get("blood_type"), churn_score=d.get("churn_score", 0.5),
                            donation_count=d.get("donation_count", 0))

    return {"nodes": nodes, "links": links}


@router.get("/graph/data")
async def get_graph_data(
    request_id: Optional[str] = Query(None, description="Specific request_id, 'all' for active emergencies, or omit for city network"),
    city: str = Query("Hyderabad", description="City filter for network view"),
):
    """
    GET /api/donors/graph/data
    Returns donor-patient graph nodes and links for react-force-graph-2d.
    Primary source: Neo4j (COMPATIBLE_WITH + IN_CHAIN). Falls back to Supabase.
    """
    try:
        request_ids: Optional[List[str]] = None
        if request_id and request_id != "all":
            request_ids = [request_id]
        elif request_id == "all":
            supabase = get_supabase_admin()
            active = supabase.table("emergency_requests").select("request_id").eq("status", "IN_PROGRESS").order("created_at", desc=True).limit(5).execute()
            request_ids = [r["request_id"] for r in (active.data or [])]

        try:
            data = await _graph_from_neo4j(request_ids=request_ids, city=city)
            if data["nodes"]:
                return data
        except Exception as neo_err:
            logger.warning(f"Neo4j graph query failed, using Supabase fallback: {neo_err}")

        return await _graph_from_supabase(request_id, city)
    except Exception as e:
        logger.error(f"Failed to fetch graph data: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Graph data fetch failed.")


# ═══════════════════════════════════════════════════════════════════════════════
# M4 — DONOR LOCATION APIs (multi-location CRUD)
# ═══════════════════════════════════════════════════════════════════════════════

class DonorLocationCreate(BaseModel):
    label: str
    lat: float
    lng: float
    is_primary: bool = False
    priority_order: int = 1

class DonorLocationPatch(BaseModel):
    is_primary: Optional[bool] = None

@router.post("/{id}/locations")
async def add_donor_location(id: str, loc: DonorLocationCreate):
    """POST /api/donors/{id}/locations — add backup location (soft-limit 10)."""
    from services.geo_service import encode_geohash
    if not (-90 <= loc.lat <= 90) or not (-180 <= loc.lng <= 180):
        raise HTTPException(status_code=400, detail="Invalid lat/lng range.")

    supabase = get_supabase_admin()
    existing = supabase.table("donor_locations").select("location_id", count="exact").eq("donor_id", id).execute()
    if (existing.count or 0) >= 10:
        raise HTTPException(status_code=400, detail="Soft limit: max 10 locations per donor.")

    geohash = encode_geohash(loc.lat, loc.lng, precision=6)
    if loc.is_primary:
        supabase.table("donor_locations").update({"is_primary": False}).eq("donor_id", id).execute()

    row = supabase.table("donor_locations").insert({
        "donor_id": id, "label": loc.label, "lat": loc.lat, "lng": loc.lng,
        "geohash": geohash, "is_primary": loc.is_primary, "priority_order": loc.priority_order
    }).execute()

    # Update primary geohash on donor record if primary
    if loc.is_primary:
        supabase.table("donors").update({"geohash": geohash, "lat": loc.lat, "lng": loc.lng}).eq("donor_id", id).execute()

    return {"success": True, "location": row.data[0] if row.data else {}}

@router.get("/{id}/locations")
async def list_donor_locations(id: str):
    """GET /api/donors/{id}/locations — list ordered by priority_order."""
    supabase = get_supabase_admin()
    res = supabase.table("donor_locations").select("*").eq("donor_id", id).order("priority_order").execute()
    return res.data or []

@router.delete("/{id}/locations/{location_id}")
async def delete_donor_location(id: str, location_id: str):
    """DELETE — remove a donor location."""
    supabase = get_supabase_admin()
    supabase.table("donor_locations").delete().eq("location_id", location_id).eq("donor_id", id).execute()
    return {"success": True}

@router.patch("/{id}/locations/{location_id}")
async def patch_donor_location(id: str, location_id: str, patch: DonorLocationPatch):
    """PATCH — set is_primary (only one primary; unset others)."""
    supabase = get_supabase_admin()
    if patch.is_primary:
        supabase.table("donor_locations").update({"is_primary": False}).eq("donor_id", id).execute()
    supabase.table("donor_locations").update({"is_primary": patch.is_primary}).eq("location_id", location_id).execute()
    return {"success": True}


# ═══════════════════════════════════════════════════════════════════════════════
# M5 — DONOR HEALTH SELF-UPDATE + AUTO-REPAIR
# ═══════════════════════════════════════════════════════════════════════════════

class HealthStatusUpdate(BaseModel):
    available: bool
    reason: Optional[str] = None
    hold_until: Optional[str] = None
    note: Optional[str] = None

@router.post("/{id}/health-status")
async def update_health_status(id: str, body: HealthStatusUpdate, background_tasks: BackgroundTasks):
    """
    POST /api/donors/{id}/health-status
    When available=false: set medical_hold, log to donor_health_log, auto-repair active chains.
    When available=true: clear medical_hold.
    """
    supabase = get_supabase_admin()
    d_res = supabase.table("donors").select("donor_id, name").eq("donor_id", id).execute()
    if not d_res.data:
        raise HTTPException(status_code=404, detail="Donor not found.")

    if not body.available:
        update_data = {
            "medical_hold": True,
            "is_active": False,
            "churn_risk_reason": body.reason or "self_reported_unavailable"
        }
        if body.hold_until:
            try:
                date.fromisoformat(body.hold_until)
                update_data["medical_hold_until"] = body.hold_until
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid hold_until date format.")

        supabase.table("donors").update(update_data).eq("donor_id", id).execute()

        # Log health event
        try:
            supabase.table("donor_health_log").insert({
                "donor_id": id, "status": "unavailable",
                "reason": body.reason, "hold_until": body.hold_until,
                "reported_via": "api", "note": body.note
            }).execute()
        except Exception:
            logger.warning(f"donor_health_log table may not exist yet for donor {id}")

        # Auto-repair: mark active chain positions as DECLINED + notify
        chain_res = supabase.table("blood_chains")\
            .select("request_id, chain_position")\
            .eq("donor_id", id)\
            .in_("status", ["ALERTED", "PENDING", "CONFIRMED"])\
            .execute()

        donor_name = d_res.data[0].get("name", "A donor")
        affected_requests = []
        for chain in (chain_res.data or []):
            req_id = chain["request_id"]
            supabase.table("blood_chains")\
                .update({"status": "DECLINED", "notes": "donor_medical_hold"})\
                .eq("request_id", req_id)\
                .eq("donor_id", id)\
                .execute()
            affected_requests.append((req_id, chain["chain_position"]))
            logger.info(f"M5 auto-repair: Declined donor {id} from chain {req_id}")

            # Update Neo4j edge
            try:
                req_lookup = supabase.table("emergency_requests").select("patient_id").eq("request_id", req_id).execute()
                if req_lookup.data:
                    p_id = req_lookup.data[0]["patient_id"]
                    from agents.neo4j_match import Neo4jMatcher
                    await Neo4jMatcher.update_chain_status(req_id, id, p_id, "DECLINED")
                    # Trigger chain repair in background to pull next-best donor
                    from services.telegram_bot import run_repair_in_background
                    background_tasks.add_task(run_repair_in_background, req_id, p_id, chain["chain_position"])
            except Exception as repair_err:
                logger.warning(f"M5 Neo4j/repair trigger failed for {req_id}: {repair_err}")

        # Notify staff (ntfy) + broadcast WS that a donor went unavailable
        if affected_requests:
            try:
                import httpx
                from core.config import get_settings
                topic = get_settings().NTFY_TOPIC
                msg = f"{donor_name} reported unavailable ({body.reason or 'no reason'}). Auto-repairing {len(affected_requests)} active chain position(s)."
                await httpx.AsyncClient().post(f"https://ntfy.sh/{topic}", content=msg.encode("utf-8"),
                                               headers={"Title": "Donor Unavailable", "Tags": "warning"}, timeout=3.0)
            except Exception:
                pass
            try:
                from api.websocket import ws_manager
                for req_id, pos in affected_requests:
                    await ws_manager.broadcast({
                        "type": "donor_unavailable",
                        "request_id": req_id,
                        "position": pos,
                        "reason": body.reason or "medical_hold"
                    })
            except Exception:
                pass

    else:
        supabase.table("donors").update({
            "medical_hold": False, "is_active": True, "medical_hold_until": None
        }).eq("donor_id", id).execute()

        try:
            supabase.table("donor_health_log").insert({
                "donor_id": id, "status": "available",
                "reason": "self_reported_available", "reported_via": "api"
            }).execute()
        except Exception:
            pass

    return {"success": True, "donor_id": id, "available": body.available}


# ═══════════════════════════════════════════════════════════════════════════════
# BLOOD CARD OCR UPLOAD (Web frontend — wraps ocr_service)
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/upload-card")
async def upload_blood_card(file: UploadFile = File(...)):
    """
    POST /api/donors/upload-card
    Accepts a multipart image upload, runs AWS Textract + Bedrock Claude Sonnet vision,
    returns detected blood_group, name, and antigen panel. Used by SignUp page OCR feature.
    """
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Please upload an image file (JPEG, PNG).")

    image_bytes = await file.read()
    if len(image_bytes) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Image too large. Max 10MB.")

    try:
        from services.ocr_service import extract_blood_type_from_image
        result = await extract_blood_type_from_image(image_bytes)
        return {
            "blood_group": result.get("blood_group"),
            "name": result.get("name"),
            "antigen_panel": result.get("antigen_panel", {}),
            "antigen_flags": result.get("antigen_flags", {}),
            "ocr_source": result.get("ocr_source", []),
            "vision_confidence": result.get("vision_confidence", 0.0),
        }
    except Exception as e:
        logger.error(f"OCR upload-card failed: {e}")
        raise HTTPException(status_code=500, detail="OCR processing failed. Please try again.")


# ═══════════════════════════════════════════════════════════════════════════════
# Feature 1: Donor Profile Update
# ═══════════════════════════════════════════════════════════════════════════════

class DonorProfileUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    city: Optional[str] = None
    preferred_language: Optional[str] = None


@router.patch("/{id}/profile")
async def update_donor_profile(id: str, body: DonorProfileUpdate):
    """
    PATCH /api/donors/{id}/profile
    Updates editable donor profile fields (name, phone, city, preferred_language).
    Blood type is immutable (set via OCR).
    """
    supabase = get_supabase_admin()
    try:
        # Verify donor exists
        d_res = supabase.table("donors").select("donor_id").eq("donor_id", id).execute()
        if not d_res.data:
            raise HTTPException(status_code=404, detail="Donor not found.")

        update_data = {}
        if body.name is not None:
            update_data["name"] = body.name.strip()
        if body.phone is not None:
            update_data["phone"] = _normalize_phone(body.phone)
        if body.city is not None:
            update_data["city"] = body.city.strip()
        if body.preferred_language is not None:
            if body.preferred_language not in ("Hindi", "English", "Telugu"):
                raise HTTPException(status_code=400, detail="preferred_language must be Hindi, English, or Telugu.")
            update_data["preferred_language"] = body.preferred_language

        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update.")

        supabase.table("donors").update(update_data).eq("donor_id", id).execute()

        return {"success": True, "updated": update_data}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating profile for donor {id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Profile update failed.")


# ═══════════════════════════════════════════════════════════════════════════════
# Feature 5: Donor Bridges (Blood Bridge Visualization)
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/{id}/bridges")
async def get_donor_bridges(id: str):
    """
    GET /api/donors/{id}/bridges
    Returns list of patients this donor is mapped to via bridge_memberships.
    """
    supabase = get_supabase_admin()
    try:
        # Verify donor exists - fetch full record
        d_res = supabase.table("donors").select("*").eq("donor_id", id).execute()
        if not d_res.data:
            raise HTTPException(status_code=404, detail="Donor not found.")
        donor = d_res.data[0]

        # Query bridge memberships for this donor
        bridge_res = supabase.table("bridge_memberships")\
            .select("*")\
            .eq("donor_id", id)\
            .execute()

        from ml.antigen_scorer import compute_antigen_score

        results = []
        for membership in (bridge_res.data or []):
            patient_id = membership.get("bridge_id") or membership.get("patient_id")
            if not patient_id:
                continue

            # Fetch patient info - fetch full record
            p_res = supabase.table("patients").select("*").eq("patient_id", patient_id).execute()
            if not p_res.data:
                continue
            patient = p_res.data[0]
            patient_name = patient.get("name", "Patient")
            patient_blood_type = patient.get("blood_type", "Unknown")

            # Dynamically compute matching score
            score = 0.5
            try:
                score = compute_antigen_score(donor, patient)
            except Exception as e:
                logger.warning(f"Failed to compute antigen score: {e}")

            results.append({
                "patient_id": patient_id,
                "patient_name": patient_name,
                "blood_type": patient_blood_type,
                "antigen_score": score,
                "joined_at": membership.get("created_at") or membership.get("joined_at"),
            })

        return results
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching bridges for donor {id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch bridge data.")
