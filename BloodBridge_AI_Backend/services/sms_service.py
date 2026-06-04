"""
SMS Service — DISABLED for BloodBridge AI MVP.

Twilio SMS has been removed from the MVP stack.
Outreach is handled via Telegram (primary) and Vapi voice calls (secondary).

This stub exists so any existing imports don't break.
All functions log a warning and return gracefully.
"""
import logging

logger = logging.getLogger(__name__)

_REMOVED_MSG = (
    "SMS outreach is disabled in this MVP build. "
    "All donor outreach goes via Telegram. "
    "Voice calls use Vapi.ai if VAPI_PHONE_NUMBER_ID is configured."
)


async def send_sms_batch(sms_batch: list) -> dict:
    """No-op: SMS removed from MVP. Returns mock success."""
    if sms_batch:
        logger.info(f"SMS disabled (MVP). Would have sent {len(sms_batch)} SMS messages via Telegram instead.")
    return {"sent": 0, "failed": 0, "skipped": len(sms_batch), "reason": "sms_disabled_mvp"}


async def send_sms(phone: str, message: str, language: str = "en") -> bool:
    """No-op: SMS removed from MVP."""
    logger.info(f"SMS disabled (MVP). Donor phone={phone} would receive message via Telegram.")
    return False


class SMSService:
    """No-op SMS service class — kept for import compatibility."""

    @staticmethod
    async def handle_incoming_sms(from_number: str, body: str) -> str:
        """No-op: returns empty TwiML."""
        logger.warning(f"Received SMS from {from_number} but SMS is disabled: '{body}'")
        return '<?xml version="1.0" encoding="UTF-8"?><Response></Response>'

    @staticmethod
    async def send_dlt_sms(phone: str, template_key: str, params: dict = None) -> bool:
        """No-op: DLT SMS removed."""
        return False
