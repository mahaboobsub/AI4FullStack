"""
Gemini Impact Story Generator for BloodBridge AI.
Generates personalized, emotional, 3-sentence donor impact stories in the donor's preferred language.
Schedules dispatch exactly 2 hours after donation confirmation.
"""
import logging
from datetime import datetime, timedelta
from core.database import get_supabase_admin
from core.config import get_settings
from services.donor_memory import build_memory_context_for_llm
from services.telegram_bot import send_telegram_message

logger = logging.getLogger(__name__)

LANGUAGE_MAP = {
    'hi': 'Hindi',
    'te': 'Telugu',
    'ta': 'Tamil',
    'en': 'English',
    'kn': 'Kannada',
    'ml': 'Malayalam',
    'mr': 'Marathi',
    'bn': 'Bengali',
    'gu': 'Gujarati',
    'pa': 'Punjabi'
}

async def generate_impact_story(donor: dict, patient: dict, language: str) -> str:
    """
    Gemini 1.5 Flash — 3 sentences max. Personal, authentic, NOT corporate.
    Injects memory context: await build_memory_context_for_llm(donor['donor_id'])
    Anonymized (no patient last name/patient_id in story). In correct script.
    """
    settings = get_settings()
    donor_id = donor.get("donor_id")
    donor_name = donor.get("name", "Donor")
    
    # Extract patient first name only (anonymized last name)
    patient_name = patient.get("name", "a patient")
    patient_first_name = patient_name.split()[0] if patient_name else "a patient"
    hospital = patient.get("hospital", "the hospital")
    
    memory_context = await build_memory_context_for_llm(donor_id) if donor_id else ""
    lang_name = LANGUAGE_MAP.get(language[:2].lower() if language else "en", "Hindi")
    
    prompt = (
        f"You are the founder of Blood Warriors Foundation, an organization in India connecting voluntary blood donors with children having Thalassemia.\n"
        f"Generate a personal, authentic, emotional (NOT corporate) thank-you impact story for a donor named {donor_name}.\n"
        f"Language of story: {lang_name} (written in the correct local script, e.g. Hindi in Devanagari, Telugu in Telugu script, etc.).\n"
        f"Use these details:\n"
        f"- Patient first name: {patient_first_name}\n"
        f"- Hospital: {hospital}\n"
        f"- Donor memory context:\n{memory_context}\n\n"
        f"CRITICAL CONSTRAINTS:\n"
        f"1. Maximum of 3 sentences.\n"
        f"2. Make it deeply personal, warm, and authentic.\n"
        f"3. Do not mention any patient last name or patient_id.\n"
        f"4. Do not use corporate jargon or placeholders.\n"
        f"5. Reply ONLY with the localized story text."
    )
    
    story = ""
    if settings.GEMINI_API_KEY:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            llm = ChatGoogleGenerativeAI(
                model="gemini-1.5-flash",
                google_api_key=settings.GEMINI_API_KEY,
                temperature=0.7
            )
            resp = await llm.ainvoke(prompt)
            story = resp.content.strip()
        except Exception as e:
            logger.error(f"Failed to generate impact story using Gemini: {e}")
            
    if not story:
        # Fallback story
        if language[:2].lower() == 'hi':
            story = f"Aapke ek baar dene se {patient_first_name} ki transfusion poori hui. Unke parivar ne aapko dil se duayein di hain. Aap sach mein ek farishta hain, {donor_name} bhai."
        elif language[:2].lower() == 'te':
            story = f"మీరు చేసిన రక్తదానం ద్వారా {patient_first_name} కి సకాలంలో చికిత్స అందింది. వారి కుటుంబ సభ్యులు మీకు కృతజ్ఞతలు తెలుపుతున్నారు. థాంక్యూ {donor_name} గారు."
        else:
            story = f"Your kind donation helped {patient_first_name} receive their critical blood transfusion at {hospital}. Their mother expressed deep gratitude for your selfless act. Thank you, {donor_name}."
            
    # Store in donor_memory
    if donor_id:
        try:
            supabase = get_supabase_admin()
            supabase.table("donor_memory").upsert({
                "donor_id": donor_id,
                "impact_story": story,
                "last_story_date": datetime.utcnow().strftime("%Y-%m-%d")
            }).execute()
        except Exception as e:
            logger.error(f"Failed to save impact story to donor memory for {donor_id}: {e}")
            
    return story

async def send_impact_story_via_telegram(donor_id: str, story: str):
    """
    Schedules sending the impact story via Telegram exactly 2 hours later.
    """
    run_time = datetime.now() + timedelta(hours=2)
    
    try:
        from scheduler.cron import get_global_scheduler
        scheduler = get_global_scheduler()
        
        async def send_task(d_id: str, story_text: str):
            supabase = get_supabase_admin()
            res = supabase.table("donors").select("telegram_chat_id").eq("donor_id", d_id).execute()
            if res.data and res.data[0].get("telegram_chat_id"):
                chat_id = res.data[0]["telegram_chat_id"]
                await send_telegram_message(chat_id, story_text)
                logger.info(f"Delayed impact story successfully sent to donor {d_id}")
                
        # Schedule the job
        scheduler.add_job(
            send_task,
            'date',
            run_date=run_time,
            args=[donor_id, story],
            id=f"story_{donor_id}_{int(datetime.utcnow().timestamp())}"
        )
        logger.info(f"Scheduled 2-hour delayed impact story send for donor {donor_id} at {run_time.isoformat()}")
    except Exception as e:
        logger.error(f"Failed to schedule delayed impact story send for donor {donor_id}: {e}", exc_info=True)
        # Fallback: run immediately if scheduler fails
        try:
            supabase = get_supabase_admin()
            res = supabase.table("donors").select("telegram_chat_id").eq("donor_id", donor_id).execute()
            if res.data and res.data[0].get("telegram_chat_id"):
                chat_id = res.data[0]["telegram_chat_id"]
                await send_telegram_message(chat_id, story)
        except Exception as ex:
            logger.error(f"Immediate fallback send also failed: {ex}")
