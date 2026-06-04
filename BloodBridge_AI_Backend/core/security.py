"""
Security utilities and dependencies for BloodBridge AI.
"""
import hmac
import hashlib
import time
import logging
import ipaddress
from fastapi import Request, HTTPException, Depends
from core.config import get_settings
from core.database import get_supabase_admin

logger = logging.getLogger(__name__)

# Standard Twilio IP CIDR ranges for webhook verification
TWILIO_IP_RANGES = [
    "54.172.60.0/23",
    "54.244.141.32/27",
    "54.171.127.192/26",
    "177.71.206.192/26",
    "54.65.187.192/26",
    "54.169.127.128/26",
    "54.252.127.192/26",
    "18.230.127.192/26",
    "54.244.141.0/24",
    "3.93.30.224/27"
]

def verify_telegram_webhook(request: Request, secret_token: str) -> bool:
    """
    Verify Telegram webhook request using hmac.compare_digest
    against the X-Telegram-Bot-Api-Secret-Token header.
    Returns True in development if secret_token is not configured.
    """
    settings = get_settings()
    token_header = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
    
    if settings.APP_ENV == "development" and not secret_token:
        logger.debug("Telegram webhook bypass in development (secret_token not configured)")
        return True
        
    if not token_header or not secret_token:
        return False
        
    return hmac.compare_digest(token_header, secret_token)

async def verify_vapi_webhook(request: Request, secret: str) -> bool:
    """
    Verify Vapi.ai webhook signature header using HMAC-SHA256.
    Returns True in development mode.
    """
    settings = get_settings()
    if settings.APP_ENV == "development":
        logger.debug("Vapi webhook signature verification bypassed in development mode")
        return True
        
    signature = request.headers.get("X-Vapi-Signature")
    if not signature or not secret:
        return False
        
    try:
        body = await request.body()
        computed_sig = hmac.new(
            secret.encode("utf-8"),
            body,
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(signature, computed_sig)
    except Exception as e:
        logger.error(f"Error verifying Vapi webhook: {e}", exc_info=True)
        return False

def generate_idempotency_key(patient_id: str, blood_type: str, city: str) -> str:
    """
    Generate a unique idempotency key using SHA256.
    Same patient + blood_type + city within 30 minutes gets the same key.
    """
    # Round current time to the nearest 30-minute block (1800 seconds)
    time_window = int(time.time() // 1800)
    raw_key = f"{patient_id}:{blood_type}:{city}:{time_window}"
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()[:32]

def is_twilio_ip(ip: str) -> bool:
    """
    Checks if an IP address belongs to Twilio's public API CIDR ranges.
    Used for verifying Twilio SMS webhooks.
    """
    try:
        ip_addr = ipaddress.ip_address(ip)
        for cidr in TWILIO_IP_RANGES:
            if ip_addr in ipaddress.ip_network(cidr):
                return True
        return False
    except ValueError:
        logger.warning(f"Invalid IP address format: {ip}")
        return False

def hash_ip(ip: str) -> str:
    """
    Generate SHA256 of IP address, first 16 chars.
    Used for DPDP-compliant audit logging to avoid storing raw IPs.
    """
    if not ip:
        return ""
    return hashlib.sha256(ip.encode("utf-8")).hexdigest()[:16]

async def get_current_staff(request: Request) -> dict:
    """
    FastAPI Depends() dependency for staff-authenticated routes.
    Checks the X-Staff-Token header against the staff table.
    """
    settings = get_settings()
    token = request.headers.get("X-Staff-Token")
    
    # Dev bypass helper if in development and token is missing
    if settings.APP_ENV == "development" and not token:
        logger.warning("Development bypass: Authenticating as Mock Admin Staff")
        return {"staff_id": 0, "telegram_username": "mock_admin", "role": "Admin", "hospital": "Development", "is_active": True}
        
    if not token:
        raise HTTPException(status_code=401, detail="X-Staff-Token header is missing")
        
    try:
        supabase = get_supabase_admin()
        # Query staff table for matching token
        res = supabase.table("staff").select("*").eq("auth_token", token).execute()
        if not res.data:
            raise HTTPException(status_code=401, detail="Invalid staff auth token")
            
        staff_member = res.data[0]
        if not staff_member.get("is_active", True):
            raise HTTPException(status_code=403, detail="Staff member account is disabled")
            
        return staff_member
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Staff authentication database error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal staff authentication service error")

async def get_current_staff_admin(staff: dict = Depends(get_current_staff)) -> dict:
    """
    FastAPI Depends() dependency requiring staff role to be Admin.
    """
    if staff.get("role") != "Admin":
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return staff
