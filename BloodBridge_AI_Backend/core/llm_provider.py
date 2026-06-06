"""
Bedrock LLM Provider — 3 real tiers.

Tiers (deck-accurate, cost-aware):
  - get_fast_llm    → Claude Haiku 4.5   : high-volume, latency-sensitive (Telegram replies, outreach)
  - get_reasoning_llm → Claude Haiku 4.5  : planning, conflict, forecast, failure analysis, scripts
  - get_quality_llm → Claude Sonnet 4    : emotional impact stories (highest quality)

Notes:
  - Using Claude 4 and Nova 2 models which are available in all regions
  - These newer models don't require inference profiles
"""
from langchain_aws import ChatBedrock
from core.config import get_settings

# Default model IDs (Claude 4 inference profiles - available globally)
_DEFAULT_FAST_MODEL = "us.anthropic.claude-haiku-4-5-20251001-v1:0"  # Fast, cheap for high-volume
_DEFAULT_REASONING_MODEL = "us.anthropic.claude-haiku-4-5-20251001-v1:0"  # Balanced reasoning
_DEFAULT_QUALITY_MODEL = "us.anthropic.claude-sonnet-4-6"  # Highest quality (latest Sonnet)


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
