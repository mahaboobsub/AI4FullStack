"""
Bedrock LLM Provider — 3 real tiers using Converse API for native tool calling.

Tiers (deck-accurate, cost-aware):
  - get_fast_llm    → Claude Haiku 4.5   : high-volume, latency-sensitive (Telegram replies, outreach)
  - get_reasoning_llm → Claude Haiku 4.5  : planning, conflict, forecast, failure analysis, scripts
  - get_quality_llm → Claude Sonnet 4    : emotional impact stories (highest quality)

Notes:
  - Using ChatBedrockConverse for native tool-calling support (Claude tool_use blocks)
  - These newer models don't require inference profiles
"""
from langchain_aws import ChatBedrockConverse
from core.config import get_settings

# Default model IDs (Global inference profiles - available in ap-south-1 and globally)
_DEFAULT_FAST_MODEL = "global.anthropic.claude-haiku-4-5-20251001-v1:0"  # Fast, cheap for high-volume
_DEFAULT_REASONING_MODEL = "global.anthropic.claude-haiku-4-5-20251001-v1:0"  # Balanced reasoning
_DEFAULT_QUALITY_MODEL = "global.anthropic.claude-sonnet-4-6"  # Highest quality (latest Sonnet)


def _make_llm(model_id: str, temperature: float) -> ChatBedrockConverse:
    settings = get_settings()
    return ChatBedrockConverse(
        model=model_id,
        region_name=settings.AWS_REGION,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        temperature=temperature,
    )


def get_fast_llm() -> ChatBedrockConverse:
    """High-volume, latency-sensitive tier (Telegram replies, outreach messages)."""
    settings = get_settings()
    model_id = getattr(settings, "BEDROCK_FAST_MODEL_ID", "") or _DEFAULT_FAST_MODEL
    return _make_llm(model_id, temperature=0.5)


def get_reasoning_llm() -> ChatBedrockConverse:
    """Reasoning tier (planning, conflict resolution, forecast insight, script generation)."""
    settings = get_settings()
    model_id = getattr(settings, "BEDROCK_REASONING_MODEL_ID", "") or _DEFAULT_REASONING_MODEL
    return _make_llm(model_id, temperature=0.4)


def get_quality_llm() -> ChatBedrockConverse:
    """Highest-quality tier (emotional impact stories)."""
    settings = get_settings()
    model_id = getattr(settings, "BEDROCK_QUALITY_MODEL_ID", "") or _DEFAULT_QUALITY_MODEL
    return _make_llm(model_id, temperature=0.7)
