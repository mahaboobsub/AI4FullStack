"""
AI Voice Agent Service for BloodBridge AI.
Integrates with Bolna.ai to place automated outbound voice calls to Indian donors.

Why Bolna over Vapi:
  - Native Indian number support (Plivo, Exotel, Vobiz — no US number workarounds)
  - Built-in Sarvam AI TTS/STT for Hindi, Telugu, Tamil, Kannada, Malayalam etc.
  - India-first platform: lower latency, TRAI-compliant calling guardrails
  - Simpler API: just agent_id + recipient phone, no complex assistant config per-call

API reference: https://docs.bolna.ai
"""
import logging
import httpx
import pytz
from datetime import datetime
import services.consent_service as consent_service
from services.donor_memory import build_memory_context_for_llm
from core.config import get_settings

logger = logging.getLogger(__name__)

BOLNA_CALL_ENDPOINT = "https://api.bolna.ai/call"

# Language code → Bolna/Sarvam voice IDs
# Sarvam AI voices: optimized for Indian regional languages, natural accents
BOLNA_VOICE_CONFIG = {
    "hi": {"tts_provider": "sarvam", "language": "hi-IN", "voice": "meera"},    # Hindi female
    "te": {"tts_provider": "sarvam", "language": "te-IN", "voice": "padmaja"},  # Telugu female
    "ta": {"tts_provider": "sarvam", "language": "ta-IN", "voice": "lakshmi"},  # Tamil female
    "kn": {"tts_provider": "sarvam", "language": "kn-IN", "voice": "ananya"},   # Kannada female
    "ml": {"tts_provider": "sarvam", "language": "ml-IN", "voice": "maya"},     # Malayalam female
    "mr": {"tts_provider": "sarvam", "language": "mr-IN", "voice": "priya"},    # Marathi female
    "bn": {"tts_provider": "sarvam", "language": "bn-IN", "voice": "ria"},      # Bengali female
    "gu": {"tts_provider": "sarvam", "language": "gu-IN", "voice": "gauri"},    # Gujarati female
    "pa": {"tts_provider": "sarvam", "language": "pa-IN", "voice": "harpreet"}, # Punjabi female
    "en": {"tts_provider": "sarvam", "language": "en-IN", "voice": "arjun"},    # English-India
}

# Fallback call scripts per language (used if Gemini script generation fails)
CALL_SCRIPTS = {
    "hi": "Namaste {name}. Main BloodBridge AI se bol rahi hoon. {hospital} mein {blood_type} blood ki ati zarurat hai. Kya aap aaj donate kar sakte hain? Please Haan ya Na boliye.",
    "te": "Namaskaram {name}. Nenu BloodBridge AI nunchi matladutunna. {hospital} lo {blood_type} blood chala avasaram. Meeru donate cheyagalara? Dayachesi Avunu ya Kadu cheppandi.",
    "ta": "Vanakkam {name}. Naan BloodBridge AI irundu pesugiren. {hospital} il {blood_type} rakam urgently thevaippadugiradu. Neenga donate seiya mudiyuma? Aamaam ya Illai sollunga.",
    "kn": "Namaskara {name}. Naanu BloodBridge AI yinda matnadutiddene. {hospital} nalli {blood_type} raktha urgently beka aagide. Neevu donate maadabahudu? Haudo athava Illa heli.",
    "ml": "Namaskaram {name}. Njan BloodBridge AI il ninnu saadikkukaya aanu. {hospital} il {blood_type} blood adiyantiramayi vendum. Ningalku donate cheyyaan kazhiyumoo? Aam athava Illa parayan.",
    "en": "Hello {name}. This is BloodBridge AI calling. {blood_type} blood is urgently needed at {hospital}. Can you donate today? Please say Yes or No.",
}


async def generate_bolna_script(donor: dict, emergency: dict, memory_context: str) -> str:
    """
    Use Gemini 1.5 Flash to generate a short, natural spoken script (40-50 words).
    Falls back to CALL_SCRIPTS template if Gemini fails.
    """
    settings = get_settings()
    lang = donor.get("preferred_language", "hi")
    lang_key = lang.lower()[:2]

    if settings.GEMINI_API_KEY:
        prompt = (
            f"You are BloodBridge AI — an Indian emergency blood donation voice assistant.\n"
            f"Generate a warm, natural spoken script in the donor's language: {lang}.\n"
            f"Keep it under 50 words. No emojis, no markdown, no bullet points.\n"
            f"End with a clear YES/NO question in {lang}.\n\n"
            f"Donor: {donor.get('name')}\n"
            f"Hospital: {emergency.get('hospital_name', 'the hospital')}\n"
            f"Blood type needed: {emergency.get('blood_type')}\n"
            f"Donor history context: {memory_context}\n\n"
            f"Generate the spoken script only."
        )
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            llm = ChatGoogleGenerativeAI(
                model="gemini-1.5-flash",
                google_api_key=settings.GEMINI_API_KEY,
                temperature=0.3
            )
            resp = await llm.ainvoke(prompt)
            script = resp.content.strip()
            logger.info(f"Bolna script generated for {donor.get('donor_id')} ({lang}): {len(script.split())} words")
            return script
        except Exception as e:
            logger.warning(f"Gemini script generation failed: {e}. Using fallback template.")

    # Fallback template
    template = CALL_SCRIPTS.get(lang_key, CALL_SCRIPTS["en"])
    return template.format(
        name=donor.get("name", "Donor"),
        hospital=emergency.get("hospital_name", "the hospital"),
        blood_type=emergency.get("blood_type", ""),
    )


async def make_bolna_call(phone: str, donor: dict, emergency: dict, request_id: str) -> dict:
    """
    Place an outbound AI voice call via Bolna.ai to a donor.

    Flow:
      1. Safe calling hours check (8 AM - 9 PM IST per TRAI guidelines)
      2. Consent check (outreach_voice)
      3. Generate personalized spoken script (Gemini → fallback template)
      4. POST to Bolna API with agent_id + phone + metadata
      5. Return call status dict

    Returns:
      {'status': 'INITIATED', 'call_id': '...'} on success
      {'status': 'SKIPPED', 'reason': '...'} if call cannot be placed
      {'status': 'FAILED', 'error': '...'} on API error
    """
    settings = get_settings()

    # GAP-15: Demo fallback — simulate successful call
    if settings.DEMO_MOCK_MODE:
        logger.info(f"DEMO_MOCK_MODE: Simulating successful call to {phone}")
        return {"status": "INITIATED", "call_id": f"DEMO-CALL-{donor.get('donor_id', '0000')}", "provider": "demo_mock"}
    # 1. Guard: Bolna API key required
    if not settings.BOLNA_API_KEY:
        logger.info(
            "BOLNA_API_KEY not set — voice call skipped. "
            "Set up your Bolna agent at https://platform.bolna.ai and paste API key in .env"
        )
        return {"status": "SKIPPED", "reason": "bolna_not_configured"}

    if not settings.BOLNA_AGENT_ID:
        logger.info(
            "BOLNA_AGENT_ID not set — voice call skipped. "
            "Create a voice agent at https://platform.bolna.ai and paste Agent ID in .env"
        )
        return {"status": "SKIPPED", "reason": "bolna_agent_not_configured"}

    # 2. TRAI safe hours check (8 AM - 9 PM IST)
    tz_ist = pytz.timezone("Asia/Kolkata")
    now_ist = datetime.now(tz_ist)
    if now_ist.hour < 8 or now_ist.hour >= 21:
        logger.info(
            f"Voice call to {phone} queued — outside TRAI safe hours "
            f"(current IST: {now_ist.hour:02d}:{now_ist.minute:02d})"
        )
        return {"status": "QUEUED", "reason": "outside_trai_safe_hours"}

    # 3. Consent check
    donor_id = donor.get("donor_id", "")
    has_consent = await consent_service.check_consent(donor_id, "outreach_voice")
    if not has_consent:
        logger.info(f"Voice call to donor {donor_id} skipped: no outreach_voice consent.")
        return {"status": "NO_CONSENT"}

    # 4. Generate personalized call script
    memory_context = await build_memory_context_for_llm(donor_id)
    script = await generate_bolna_script(donor, emergency, memory_context)

    # 5. Determine language config
    lang_key = donor.get("preferred_language", "hi").lower()[:2]
    voice_cfg = BOLNA_VOICE_CONFIG.get(lang_key, BOLNA_VOICE_CONFIG["en"])

    # 6. POST to Bolna API
    payload = {
        "agent_id": settings.BOLNA_AGENT_ID,
        "recipient_phone_number": phone,  # Must be E.164 format e.g. +919876543210
        "user_data": {
            # Bolna injects these as variables into the agent's prompt template
            "donor_name": donor.get("name", "Donor"),
            "blood_type": emergency.get("blood_type", ""),
            "hospital_name": emergency.get("hospital_name", "the hospital"),
            "city": emergency.get("city", ""),
            "urgency": emergency.get("urgency_level", "HIGH"),
            "custom_script": script,
            # Metadata for webhook callback
            "request_id": request_id,
            "donor_id": donor_id,
        }
    }

    logger.info(
        f"Placing Bolna voice call to {phone} | donor={donor_id} | "
        f"lang={lang_key} | request={request_id}"
    )

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                BOLNA_CALL_ENDPOINT,
                headers={
                    "Authorization": f"Bearer {settings.BOLNA_API_KEY}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )

        if resp.status_code == 200:
            call_data = resp.json()
            call_id = call_data.get("call_id") or call_data.get("id", "unknown")
            logger.info(f"Bolna call initiated successfully. call_id={call_id}")
            return {"status": "INITIATED", "call_id": call_id, "provider": "bolna"}

        else:
            logger.error(
                f"Bolna API error {resp.status_code} for donor {donor_id}: {resp.text}"
            )
            return {"status": "FAILED", "error": f"HTTP {resp.status_code}: {resp.text}"}

    except httpx.TimeoutException:
        logger.error(f"Bolna API timeout for donor {donor_id}")
        return {"status": "FAILED", "error": "request_timeout"}
    except Exception as e:
        logger.error(f"Bolna call failed for donor {donor_id}: {e}", exc_info=True)
        return {"status": "FAILED", "error": str(e)}
