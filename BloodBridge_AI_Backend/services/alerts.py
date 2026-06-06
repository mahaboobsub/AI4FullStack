"""
Alerts module for BloodBridge AI.
Dispatches zero-cost mobile push notifications for staff via ntfy.sh.
"""
import logging
import httpx
from core.config import get_settings

logger = logging.getLogger(__name__)

ALERT_CONFIGS = {
    'critical':    {'priority': 5, 'tags': ['rotating_light', 'drop_of_blood']},
    'chain_break': {'priority': 4, 'tags': ['warning', 'chains']},
    'escalation':  {'priority': 4, 'tags': ['hospital', 'warning']},
    'success':     {'priority': 2, 'tags': ['white_check_mark', 'drop_of_blood']},
    'info':        {'priority': 2, 'tags': ['information_source']},
}

async def send_alert(title: str, message: str, level: str = 'info', actions: list | None = None):
    """
    POST to ntfy.sh/{NTFY_TOPIC} with headers.
    Actions: list of dicts [{action: "view", label: "label", url: "url"}]
    """
    settings = get_settings()
    if not settings.NTFY_TOPIC:
        logger.warning("NTFY_TOPIC is not set. Mocking ntfy alert.")
        return
        
    config = ALERT_CONFIGS.get(level, ALERT_CONFIGS['info'])
    url = f"https://ntfy.sh/{settings.NTFY_TOPIC}"
    
    # HTTP headers MUST be ASCII-only (RFC 7230).
    # Strip all non-ASCII (emoji, Unicode) before setting headers.
    import re
    safe_title = re.sub(r'[^\x00-\x7F]+', '', title).strip()
    if not safe_title:
        safe_title = "BloodBridge Alert"
    
    # Include the original emoji-rich title at the start of the message body
    full_message = f"{title}\n{message}" if title != safe_title else message
    
    headers = {
        "Title": safe_title,
        "Priority": str(config['priority']),
        "Tags": ",".join(config['tags'])
    }
    
    if actions:
        action_parts = []
        for act in actions:
            action_type = act.get("action", "view")
            label = act.get("label", "View Details")
            target_url = act.get("url", settings.APP_BASE_URL)
            action_parts.append(f"{action_type}, {label}, {target_url}")
        headers["Click"] = actions[0].get("url", "")
        headers["Actions"] = "; ".join(action_parts)
        
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                url,
                content=full_message.encode("utf-8"),
                headers=headers,
                timeout=5.0
            )
            if resp.status_code == 200:
                logger.info(f"Ntfy alert successfully sent. Level: {level}, Title: {safe_title}")
            else:
                logger.warning(f"Ntfy returned code {resp.status_code}: {resp.text}")
    except Exception as e:
        logger.error(f"Failed to send ntfy alert: {e}", exc_info=True)

async def send_critical_staff_alert(message: str):
    """Helper to dispatch direct staff critical alerts."""
    await send_alert(
        title="⚠️ CRITICAL STAFF ALERT",
        message=message,
        level="critical"
    )

async def alert_critical_patient(patient_id: str, blood_type: str, hospital: str):
    await send_alert(
        title="🔴 CRITICAL PATIENT RECEIVED",
        message=f"Patient {patient_id} needs {blood_type} at {hospital}.",
        level="critical"
    )

async def alert_chain_break(patient_id: str, position: int):
    await send_alert(
        title="⚠️ CHAIN BREAK ALERT",
        message=f"Chain position {position} for patient {patient_id} broke or timed out.",
        level="chain_break"
    )

async def alert_escalation(patient_id: str, blood_banks: list):
    names = ", ".join([b.get("name", "Unknown") for b in blood_banks])
    await send_alert(
        title="🚨 EMERGENCY ESCALATION",
        message=f"Emergency request for Patient {patient_id} escalated. Reserve stocks found at: {names}",
        level="escalation"
    )

async def alert_success(patient_id: str, donor_name: str):
    await send_alert(
        title="✅ DONATION CONFIRMED",
        message=f"Donor {donor_name} confirmed donation for Patient {patient_id}.",
        level="success"
    )

async def alert_lora_received(gateway_id: str, rssi: int, patient_id: str):
    await send_alert(
        title="📡 LoRa GATEWAY ALERT",
        message=f"Gateway {gateway_id} received signal (RSSI {rssi} dBm) for Patient {patient_id}.",
        level="info"
    )

async def escalate_voice_failure_to_admin(request_id: str, donor_id: str, reason: str):
    from core.database import get_supabase_admin
    from services.telegram_bot import send_telegram_message
    supabase = get_supabase_admin()
    
    # 1. Fetch emergency details
    req_res = supabase.table("emergency_requests").select("*").eq("request_id", request_id).execute()
    if not req_res.data:
        return
    emergency = req_res.data[0]
    
    # 2. Fetch all donors contacted in this chain
    chain_res = supabase.table("blood_chains").select("*").eq("request_id", request_id).order("chain_position").execute()
    donors = chain_res.data or []
    
    # Build summary
    donor_lines = []
    for d in donors:
        status_icon = {"CONFIRMED": "✅", "DECLINED": "❌", "VOICE": "📞", "ALERTED": "📨", "PENDING": "⏳"}.get(d["status"], "❓")
        method = "AI Voice Call" if d["status"] == "DECLINED" and d["donor_id"] == donor_id else "Telegram / Wait"
        donor_lines.append(f"  {status_icon} {d.get('donor_name', 'Unknown')} — {method}")
        
    donor_summary = "\n".join(donor_lines) if donor_lines else "  — No donors found"
    
    msg = (
        f"🚨 *BLOODBRIDGE — MANUAL INTERVENTION REQUIRED*\n\n"
        f"*Emergency ID:* `{request_id}`\n"
        f"*Patient ID:* `{emergency.get('patient_id', 'Unknown')}`\n"
        f"*Blood Type:* `{emergency.get('blood_type', 'Unknown')}`\n"
        f"*Hospital:* {emergency.get('hospital_name', 'Unknown')}\n"
        f"*City:* {emergency.get('city', 'Unknown')}\n\n"
        f"*Automated Outreach Results:*\n{donor_summary}\n\n"
        f"*Reason:* {reason}\n\n"
        f"_All automated attempts exhausted or AI Voice Call failed. Please assign a donor manually._"
    )
    
    # 3. Mark as ESCALATED in DB to prevent further loops
    supabase.table("emergency_requests").update({
        "status": "ESCALATED",
        "notes": f"Voice Call Failed ({reason})"
    }).eq("request_id", request_id).execute()
    
    # 4. Notify all staff via Telegram
    staff_res = supabase.table("staff").select("telegram_chat_id").eq("is_active", True).execute()
    for s in (staff_res.data or []):
        if s.get("telegram_chat_id"):
            await send_telegram_message(s["telegram_chat_id"], msg)
