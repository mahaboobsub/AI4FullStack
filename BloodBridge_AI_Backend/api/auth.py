import logging
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import Optional
from core.database import get_supabase_admin
from core.security import create_access_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["auth"])

class LoginRequest(BaseModel):
    role: str
    identifier: str
    password: str

@router.post("/login")
async def login(req: LoginRequest):
    try:
        supabase = get_supabase_admin()
        
        if req.role == "staff":
            res = supabase.table("staff").select("*").eq("email", req.identifier).execute()
            if not res.data:
                raise HTTPException(status_code=401, detail="Invalid credentials")
            user = res.data[0]
            if user.get("password") != req.password:
                raise HTTPException(status_code=401, detail="Invalid credentials")
            
            token_data = {"sub": str(user["staff_id"]), "role": "staff"}
            token = create_access_token(token_data)
            return {"access_token": token, "token_type": "bearer", "user": user}
            
        elif req.role == "donor":
            res = supabase.table("donors").select("*").eq("donor_id", req.identifier).execute()
            if not res.data:
                res = supabase.table("donors").select("*").eq("phone", req.identifier).execute()
            if not res.data:
                raise HTTPException(status_code=401, detail="Invalid credentials")
                
            user = res.data[0]
            if user.get("password") != req.password:
                raise HTTPException(status_code=401, detail="Invalid credentials")
                
            token_data = {"sub": user["donor_id"], "role": "donor"}
            token = create_access_token(token_data)
            return {"access_token": token, "token_type": "bearer", "user": user}
            
        elif req.role == "patient":
            res = supabase.table("patients").select("*").eq("patient_id", req.identifier).execute()
            if not res.data:
                res = supabase.table("patients").select("*").eq("phone", req.identifier).execute()
            if not res.data:
                raise HTTPException(status_code=401, detail="Invalid credentials")
                
            user = res.data[0]
            if user.get("password") != req.password:
                raise HTTPException(status_code=401, detail="Invalid credentials")
                
            token_data = {"sub": user["patient_id"], "role": "patient"}
            token = create_access_token(token_data)
            return {"access_token": token, "token_type": "bearer", "user": user}
            
        raise HTTPException(status_code=400, detail="Invalid role")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

class SignupRequest(BaseModel):
    role: str
    first_name: str
    last_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    blood_group: Optional[str] = None
    password: str

@router.post("/signup")
async def signup(req: SignupRequest):
    supabase = get_supabase_admin()
    name = f"{req.first_name} {req.last_name}".strip()
    
    if req.role == "staff":
        res = supabase.table("staff").insert({
            "email": req.email,
            "password": req.password,
            "hospital": "Blood Warriors HQ",
            "role": "Staff",
            "telegram_username": f"staff_{req.first_name.lower()}"
        }).execute()
        return {"status": "success"}
    elif req.role == "donor":
        res = supabase.table("donors").insert({
            "name": name,
            "phone": req.phone,
            "password": req.password,
            "blood_type": req.blood_group,
            "city": "Hyderabad"
        }).execute()
        return {"status": "success"}
    elif req.role == "patient":
        res = supabase.table("patients").insert({
            "patient_id": f"P-{str(hash(name))[:5].replace('-','')}",
            "name": name,
            "phone": req.phone,
            "password": req.password,
            "blood_type": req.blood_group,
            "hospital": "KIMS Secunderabad",
            "city": "Hyderabad"
        }).execute()
        return {"status": "success"}
    
    raise HTTPException(status_code=400, detail="Invalid role")


# ── V2: Telegram → Web Portal Deep Link ──────────────────────────────────────

# In-memory token store (for demo purposes; use Redis in production)
_telegram_login_tokens: dict = {}

@router.post("/telegram-token")
async def create_telegram_login_token(chat_id: str):
    """
    POST /api/auth/telegram-token?chat_id=12345
    Creates a one-time UUID token for Telegram → Web Portal deep link.
    Called by the Telegram bot when a donor requests their medical data portal link.
    """
    import uuid
    from datetime import datetime, timedelta

    supabase = get_supabase_admin()
    donor_res = supabase.table("donors").select("donor_id").eq("telegram_chat_id", str(chat_id)).execute()
    if not donor_res.data:
        raise HTTPException(status_code=404, detail="Donor not found for this chat_id.")

    donor_id = donor_res.data[0]["donor_id"]
    token = str(uuid.uuid4())
    _telegram_login_tokens[token] = {
        "donor_id": donor_id,
        "chat_id": chat_id,
        "expires_at": (datetime.utcnow() + timedelta(minutes=10)).isoformat()
    }

    return {"token": token, "expires_in_seconds": 600}


@router.get("/telegram-login")
async def telegram_login(token: str):
    """
    GET /api/auth/telegram-login?token={uuid}
    Validates one-time token and returns JWT for web portal access.
    """
    from datetime import datetime

    if token not in _telegram_login_tokens:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")

    entry = _telegram_login_tokens.pop(token)
    expires_at = datetime.fromisoformat(entry["expires_at"])

    if datetime.utcnow() > expires_at:
        raise HTTPException(status_code=401, detail="Token has expired. Please request a new link via Telegram.")

    donor_id = entry["donor_id"]

    # Create JWT
    token_data = {"sub": donor_id, "role": "donor", "source": "telegram_deeplink"}
    jwt_token = create_access_token(token_data)

    return {
        "access_token": jwt_token,
        "token_type": "bearer",
        "donor_id": donor_id
    }
