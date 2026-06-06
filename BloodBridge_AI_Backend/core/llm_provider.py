"""
Bedrock LLM Provider — 3 real tiers.

Tiers (deck-accurate, cost-aware):
  - get_fast_llm    → Claude 3.5 Haiku   : high-volume, latency-sensitive (Telegram replies, outreach)
  - get_reasoning_llm → Claude 3.5 Haiku : planning, conflict, forecast, failure analysis, scripts
  - get_quality_llm → Claude 3.5 Sonnet  : emotional impact stories (highest quality)

Notes:
  - Standard on-demand model IDs work in us-east-1 / us-west-2 without an inference profile.
  - If running in ap-south-1 (Mumbai), set the *_MODEL_ID env vars to APAC inference-profile IDs
    (e.g. "apac.anthropic.claude-3-5-sonnet-20241022-v2:0").
  - Amazon Nova Lite is intentionally NOT used here: it requires a different request schema
    (ChatBedrockConverse) than the Anthropic models. Haiku is the cheap+fast tier instead.
"""
from langchain_aws import ChatBedrock
from core.config import get_settings

# Default on-demand model IDs (valid in us-east-1 / us-west-2)
_DEFAULT_FAST_MODEL = "anthropic.claude-3-5-haiku-20241022-v1:0"
_DEFAULT_REASONING_MODEL = "anthropic.claude-3-5-haiku-20241022-v1:0"
_DEFAULT_QUALITY_MODEL = "anthropic.claude-3-5-sonnet-20241022-v2:0"


def _make_llm(model_id: str, temperature: float) -> ChatBedrock:
    settings = get_settings()
    return ChatBedrock(
        model=model_id,
        region=settings.AWS_REGION,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        model_kwargs={"temperature": temperature},
    )


def get_fast_llm() -> ChatBedrock:
    """High-volume, latency-sensitive tier (Telegram replies, outreach messages)."""
    settings = get_settings()
    model_id = getattr(settings, "BEDROCK_FAST_MODEL_ID", "") or _DEFAULT_FAST_MODEL
    return _make_llm(model_id, temperature=0.5)


def get_reasoning_llm() -> ChatBedrock:
    """Reasoning tier (planning, conflict resolution, forecast insight, script generation)."""
    settings = get_settings()
    model_id = getattr(settings, "BEDROCK_REASONING_MODEL_ID", "") or _DEFAULT_REASONING_MODEL
    return _make_llm(model_id, temperature=0.4)


def get_quality_llm() -> ChatBedrock:
    """Highest-quality tier (emotional impact stories)."""
    settings = get_settings()
    model_id = getattr(settings, "BEDROCK_QUALITY_MODEL_ID", "") or _DEFAULT_QUALITY_MODEL
    return _make_llm(model_id, temperature=0.7)
