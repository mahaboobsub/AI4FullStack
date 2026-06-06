import logging
import boto3
from core.config import get_settings

logger = logging.getLogger(__name__)

# Map AWS Comprehend codes to our internal system language codes
COMPREHEND_TO_INTERNAL = {
    "hi": "hi",
    "ta": "ta",
    "te": "te",
    "kn": "kn",
    "ml": "ml",
    "bn": "bn",
    "mr": "mr",
    "gu": "gu",
    "pa": "pa",
    "ur": "ur",
    "en": "en"
}

def detect_dominant_language(text: str) -> str:
    """
    Wraps AWS Comprehend's detect_dominant_language().
    Returns the mapped internal language code of the highest-confidence language.
    Defaults to 'en' if confidence is low or detection fails.
    """
    if not text or len(text.strip()) < 5:
        return "en"
        
    settings = get_settings()
    try:
        client = boto3.client(
            'comprehend',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        
        response = client.detect_dominant_language(Text=text[:4500])  # AWS limits to 5000 bytes
        languages = response.get("Languages", [])
        
        if languages:
            # Sort by highest score
            languages.sort(key=lambda x: x.get("Score", 0), reverse=True)
            top_lang_code = languages[0].get("LanguageCode", "en")
            
            # Comprehend might return regional codes or ones we don't map explicitly
            return COMPREHEND_TO_INTERNAL.get(top_lang_code, "en")
    except Exception as e:
        logger.warning(f"AWS Comprehend language detection failed: {e}")
        
    return "en"
