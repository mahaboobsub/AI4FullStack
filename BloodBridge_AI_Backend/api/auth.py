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
