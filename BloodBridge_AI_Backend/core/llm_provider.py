"""
Bedrock LLM Provider.
Exposes specific Bedrock adapters for fast replies, reasoning, and high quality outputs.
"""
from langchain_aws import ChatBedrock
from core.config import get_settings

def get_fast_llm() -> ChatBedrock:
    """High-volume, latency-sensitive model."""
    settings = get_settings()
    return ChatBedrock(
        model="anthropic.claude-3-5-sonnet-20241022-v2:0",
        region=settings.AWS_REGION,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
    )

def get_reasoning_llm() -> ChatBedrock:
    """Reasoning model for planning and script generation."""
    settings = get_settings()
    return ChatBedrock(
        model="anthropic.claude-3-5-sonnet-20241022-v2:0",
        region=settings.AWS_REGION,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
    )

def get_quality_llm() -> ChatBedrock:
    """Highest quality model for impact stories."""
    settings = get_settings()
    return ChatBedrock(
        model="anthropic.claude-3-5-sonnet-20241022-v2:0",
        region=settings.AWS_REGION,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
    )
