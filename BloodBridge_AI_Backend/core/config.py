"""
Configuration settings for BloodBridge AI.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    # Supabase settings
    SUPABASE_URL: str = Field(default="")
    SUPABASE_KEY: str = Field(default="")
    SUPABASE_SERVICE_KEY: str = Field(default="")

    # Neo4j settings
    NEO4J_URI: str = Field(default="")
    NEO4J_USERNAME: str = Field(default="")
    NEO4J_PASSWORD: str = Field(default="")

    # AWS Bedrock settings
    AWS_REGION: str = Field(default="ap-south-1")
    AWS_ACCESS_KEY_ID: str = Field(default="")
    AWS_SECRET_ACCESS_KEY: str = Field(default="")

    # Telegram settings
    TELEGRAM_BOT_TOKEN: str = Field(default="")
    TELEGRAM_WEBHOOK_URL: str = Field(default="")
    TELEGRAM_WEBHOOK_SECRET: str = Field(default="")

    # Bolna.ai settings (Voice calls to Indian numbers — India-first platform)
    # Create your agent at https://platform.bolna.ai, get API key from Developers tab
    # BOLNA_AGENT_ID: leave empty to skip voice calls gracefully (Telegram-only mode)
    BOLNA_API_KEY: str = Field(default="")
    BOLNA_AGENT_ID: str = Field(default="")   # Agent configured in Bolna dashboard
    BOLNA_WEBHOOK_SECRET: str = Field(default="")

    # ntfy.sh alert settings
    NTFY_TOPIC: str = Field(default="bloodbridge-alerts")

    # FastAPI application settings
    APP_ENV: str = Field(default="development")
    APP_HOST: str = Field(default="0.0.0.0")
    APP_PORT: int = Field(default=8000)
    APP_BASE_URL: str = Field(default="http://localhost:8000")
    LOG_LEVEL: str = Field(default="INFO")

    # Demo mode — when enabled, external APIs return mock responses
    DEMO_MOCK_MODE: bool = Field(default=False)
    # Web portal URL for Telegram deep links
    WEB_PORTAL_URL: str = Field(default="http://localhost:5173")

    # B6: Dedicated JWT secret (64-char, NOT the Supabase key)
    JWT_SECRET: str = Field(default="")
    JWT_EXPIRY_HOURS: int = Field(default=24)

    # A6: Production CORS origins
    ALLOWED_ORIGINS: str = Field(default="*")

    # B3: Twilio SMS fallback
    TWILIO_ACCOUNT_SID: str = Field(default="")
    TWILIO_AUTH_TOKEN: str = Field(default="")
    TWILIO_FROM_NUMBER: str = Field(default="")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

@lru_cache
def get_settings() -> Settings:
    """Get the cached configuration instance."""
    return Settings()
