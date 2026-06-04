"""
DPDP 2023 Consent Management Service for BloodBridge AI.
Compliance layer for India's Digital Personal Data Protection Act 2023.
"""
import logging
import hashlib
from datetime import datetime
from core.database import get_supabase_admin

logger = logging.getLogger(__name__)

# Consent texts shown to donors in each language before any data is stored
CONSENT_TEXTS = {
    'hi': "BloodBridge AI aapka naam, phone number, aur blood type store karega taaki "
          "aapko blood donation ke liye contact kar sake. Kya aap agree karte hain? "
          "DPDP Act 2023 ke anusar aap kabhi bhi consent wapas le sakte hain. Reply HAAN ya NA.",
    'te': "BloodBridge AI మీ పేరు, ఫోన్ నంబర్, బ్లడ్ టైప్ స్టోర్ చేస్తుంది. "
          "Blood donation కోసం మిమ్మల్ని contact చేయడానికి. మీరు agree అవుతారా? "
          "DPDP Act 2023 కింద మీరు ఎప్పుడైనా consent తీసుకోవచ్చు. Reply HAAN లేదా NA.",
    'ta': "BloodBridge AI உங்கள் பெயர், தொலைபேசி எண், இரத்த வகை சேமிக்கும். "
          "இரத்த தானத்திற்கு உங்களை தொடர்புகொள்ள. ஒப்புக்கொள்கிறீர்களா? "
          "DPDP Act 2023 படி எப்போதும் சம்மதத்தை திரும்பப் பெறலாம். Reply HAAN அல்லது NA.",
    'en': "BloodBridge AI will store your name, phone number, and blood type to contact "
          "you for blood donation requests. Do you agree? Under DPDP Act 2023 you can "
          "withdraw consent at any time. Reply YES or NO.",
    'kn': "BloodBridge AI ನಿಮ್ಮ ಹೆಸರು, ಫೋನ್ ನಂಬರ್, ರಕ್ತದ ಗುಂಪು ಸಂಗ್ರಹಿಸುತ್ತದೆ. "
          "ರಕ್ತ ದಾನಕ್ಕಾಗಿ ನಿಮ್ಮನ್ನು ಸಂಪರ್ಕಿಸಲು. ಒಪ್ಪಿಗೆ ಇದೆಯೇ? Reply HAAN ಅಥವಾ NA.",
    'ml': "BloodBridge AI നിങ്ങളുടെ പേര്, ഫോൺ നമ്പർ, രക്ത ഗ്രൂപ്പ് സ്റ്റോർ ചെയ്യും. "
          "രക്ത ദാനത്തിനായി നിങ്ങളെ ബന്ധപ്പെടാൻ. സമ്മതിക്കുന്നുവോ? Reply HAAN അല്ലെങ്കിൽ NA.",
    'mr': "BloodBridge AI तुमचे नाव, फोन नंबर, रक्त प्रकार साठवेल. "
          "रक्तदानासाठी तुमच्याशी संपर्क साधण्यासाठी. तुम्ही सहमत आहात का? Reply HAAN किंवा NA.",
    'bn': "BloodBridge AI আপনার নাম, ফোন নম্বর, রক্তের গ্রুপ সংরক্ষণ করবে। "
          "রক্ত দানের জন্য আপনাকে যোগাযোগ করতে। সম্মতি দেন? Reply HAAN বা NA.",
    'gu': "BloodBridge AI તમારું નામ, ફોન નંબર, બ્લડ ટાઇપ સ્ટોર કરશે. "
          "Blood donation માટે તમારો સંપર્ક કરવા. સંમતિ આપો? Reply HAAN અથવા NA.",
    'pa': "BloodBridge AI ਤੁਹਾਡਾ ਨਾਮ, ਫ਼ੋਨ ਨੰਬਰ, ਬਲੱਡ ਟਾਈਪ ਸਟੋਰ ਕਰੇਗਾ. "
          "ਖੂਨ ਦਾਨ ਲਈ ਤੁਹਾਡੇ ਨਾਲ ਸੰਪਰਕ ਕਰਨ ਲਈ. ਕੀ ਤੁਸੀਂ ਸਹਿਮਤ ਹੋ? Reply HAAN ਜਾਂ NA.",
}

# SHA256 hash of each consent text — stored in consent_records for audit trail
CONSENT_TEXT_HASHES = {
    lang: hashlib.sha256(text.encode('utf-8')).hexdigest()
    for lang, text in CONSENT_TEXTS.items()
}

class ConsentService:
    @staticmethod
    async def grant_consent(donor_id: str, consent_types: list[str], channel: str, language: str, ip_hash=None) -> bool:
        """
        INSERT consent_records for each type. Update donor summary flags.
        Used during /register, /start, and staff bulk import.
        """
        supabase = get_supabase_admin()
        now_str = datetime.utcnow().isoformat() + "Z"
        lang_key = (language or "en").lower()[:2]
        text_hash = CONSENT_TEXT_HASHES.get(lang_key, CONSENT_TEXT_HASHES['en'])
        
        records = []
        for c_type in consent_types:
            records.append({
                "donor_id": donor_id,
                "consent_type": c_type,
                "action": "granted",
                "granted_at": now_str,
                "channel": channel,
                "language": lang_key,
                "consent_text_hash": text_hash,
                "ip_hash": ip_hash
            })
            
        try:
            if records:
                supabase.table("consent_records").insert(records).execute()
                
            # Update donors flags
            update_data = {}
            if "data_storage" in consent_types:
                update_data["consent_data_storage"] = True
                update_data["consent_granted_at"] = now_str
            if any(x in consent_types for x in ["outreach_telegram", "outreach_voice", "outreach_sms"]):
                update_data["consent_outreach"] = True
                
            if update_data:
                supabase.table("donors").update(update_data).eq("donor_id", donor_id).execute()
                
            logger.info(f"Granted consent types {consent_types} for donor {donor_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to grant consent for donor {donor_id}: {e}", exc_info=True)
            return False

    @staticmethod
    async def revoke_consent(donor_id: str, consent_type='all') -> bool:
        """
        INSERT revocation record. Stop outreach immediately.
        If revoking 'data_storage': set donor.is_active=False
        """
        supabase = get_supabase_admin()
        now_str = datetime.utcnow().isoformat() + "Z"
        
        types_to_revoke = [
            'data_storage', 'outreach_telegram', 'outreach_voice',
            'outreach_sms', 'data_sharing_bloodwarriors', 'data_sharing_hospitals'
        ] if consent_type == 'all' else [consent_type]
        
        records = []
        for c_type in types_to_revoke:
            records.append({
                "donor_id": donor_id,
                "consent_type": c_type,
                "action": "revoked",
                "revoked_at": now_str,
                "channel": "api_revoke"
            })
            
        try:
            if records:
                supabase.table("consent_records").insert(records).execute()
                
            # Update donors flags
            update_data = {}
            if 'data_storage' in types_to_revoke:
                update_data["consent_data_storage"] = False
                update_data["is_active"] = False
                
            if all(x in types_to_revoke for x in ["outreach_telegram", "outreach_voice", "outreach_sms"]):
                update_data["consent_outreach"] = False
                
            if update_data:
                supabase.table("donors").update(update_data).eq("donor_id", donor_id).execute()
                
            logger.info(f"Revoked consent type '{consent_type}' for donor {donor_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to revoke consent for donor {donor_id}: {e}", exc_info=True)
            return False

    @staticmethod
    async def check_consent(donor_id: str, consent_type: str) -> bool:
        """
        Fast check — latest record for donor+type. True if action='granted'.
        """
        supabase = get_supabase_admin()
        try:
            res = supabase.table("consent_records")\
                .select("action")\
                .eq("donor_id", donor_id)\
                .eq("consent_type", consent_type)\
                .order("created_at", desc=True)\
                .limit(1)\
                .execute()
                
            if res.data:
                return res.data[0]["action"] == "granted"
                
            # Fallback to donors table profile flags
            donor_res = supabase.table("donors").select("consent_data_storage, consent_outreach").eq("donor_id", donor_id).execute()
            if donor_res.data:
                d = donor_res.data[0]
                if consent_type == "data_storage":
                    return d.get("consent_data_storage", False)
                elif consent_type in ["outreach_telegram", "outreach_voice", "outreach_sms"]:
                    return d.get("consent_outreach", False)
                    
            return False
        except Exception as e:
            logger.error(f"Error checking consent for donor {donor_id} type {consent_type}: {e}")
            return False

    @staticmethod
    async def get_consent_summary(donor_id: str) -> dict:
        """
        All consent statuses for dashboard display and /consent command.
        """
        consent_types = [
            'data_storage', 'outreach_telegram', 'outreach_voice',
            'outreach_sms', 'data_sharing_bloodwarriors', 'data_sharing_hospitals'
        ]
        
        summary = {}
        for c_type in consent_types:
            summary[c_type] = await ConsentService.check_consent(donor_id, c_type)
        return summary

    @staticmethod
    async def erase_donor_data(donor_id: str, requested_by: str) -> dict:
        """
        RIGHT TO ERASURE — DPDP Section 12.
        1. Check no active IN_PROGRESS emergency
        2. Delete: donor_memory, gamification, consent_records, donor_verifications
        3. Anonymize donor
        4. Log to erasure_log table (retained 7 years per DPDP)
        """
        supabase = get_supabase_admin()
        now_str = datetime.utcnow().isoformat() + "Z"
        
        try:
            # 1. Check active coordinate requests containing this donor
            res_chains = supabase.table("blood_chains")\
                .select("request_id, status")\
                .eq("donor_id", donor_id)\
                .in_("status", ["PENDING", "ALERTED", "CONFIRMED", "VOICE", "SMS"])\
                .execute()
                
            if res_chains.data:
                # Check if request status is still active (IN_PROGRESS)
                req_ids = [c["request_id"] for c in res_chains.data]
                res_reqs = supabase.table("emergency_requests")\
                    .select("request_id")\
                    .in_("request_id", req_ids)\
                    .eq("status", "IN_PROGRESS")\
                    .execute()
                if res_reqs.data:
                    return {
                        "success": False,
                        "error": "Active emergency coordination in progress. Erasure blocked."
                    }
                    
            # 2. Deletions
            supabase.table("donor_memory").delete().eq("donor_id", donor_id).execute()
            supabase.table("gamification").delete().eq("donor_id", donor_id).execute()
            supabase.table("consent_records").delete().eq("donor_id", donor_id).execute()
            supabase.table("donor_verifications").delete().eq("donor_id", donor_id).execute()
            
            # 3. Anonymize core record
            supabase.table("donors")\
                .update({
                    "name": "[DELETED]",
                    "phone": None,
                    "telegram_chat_id": None,
                    "lat": None,
                    "lng": None,
                    "is_active": False,
                    "consent_data_storage": False,
                    "consent_outreach": False,
                    "updated_at": now_str
                })\
                .eq("donor_id", donor_id)\
                .execute()
                
            # 4. Log to audit trail erasure_log (7 years retention)
            try:
                supabase.table("erasure_log").insert({
                    "donor_id": donor_id,
                    "erased_by": requested_by,
                    "erased_at": now_str
                }).execute()
            except Exception as e:
                logger.warning(f"Could not log to erasure_log table: {e}. (Ignore if table does not exist).")
                
            logger.info(f"Right to Erasure executed for donor {donor_id} requested by {requested_by}")
            return {
                "success": True,
                "donor_id": donor_id,
                "erased_at": now_str
            }
        except Exception as e:
            logger.error(f"Failed to erase donor data for {donor_id}: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }

    @staticmethod
    async def export_donor_data(donor_id: str) -> dict:
        """
        RIGHT TO ACCESS — DPDP Section 11. All stored data, structured format.
        """
        supabase = get_supabase_admin()
        export = {
            "exported_at": datetime.utcnow().isoformat() + "Z",
            "donor_profile": {},
            "donor_memory": {},
            "gamification_badges": [],
            "consent_audit_records": [],
            "verification_history": []
        }
        
        try:
            # 1. Profile
            d_res = supabase.table("donors").select("*").eq("donor_id", donor_id).execute()
            if d_res.data:
                export["donor_profile"] = d_res.data[0]
                
            # 2. Memory
            m_res = supabase.table("donor_memory").select("*").eq("donor_id", donor_id).execute()
            if m_res.data:
                export["donor_memory"] = m_res.data[0]
                
            # 3. Badges
            g_res = supabase.table("gamification").select("*").eq("donor_id", donor_id).execute()
            export["gamification_badges"] = g_res.data or []
            
            # 4. Consent records
            c_res = supabase.table("consent_records").select("*").eq("donor_id", donor_id).execute()
            export["consent_audit_records"] = c_res.data or []
            
            # 5. Verifications
            v_res = supabase.table("donor_verifications").select("*").eq("donor_id", donor_id).execute()
            export["verification_history"] = v_res.data or []
            
            return export
        except Exception as e:
            logger.error(f"Failed to export data for donor {donor_id}: {e}", exc_info=True)
            return {"error": str(e)}

consent_service = ConsentService()  # Module-level singleton
