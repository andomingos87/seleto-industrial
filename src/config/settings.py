"""
Application settings using Pydantic BaseSettings
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # App
    APP_NAME: str = "Seleto Industrial SDR Agent"
    APP_ENV: str = "development"
    DEBUG: bool = False

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # OpenAI / LLM
    OPENAI_API_KEY: str | None = None
    OPENAI_MODEL: str = "gpt-4o"

    # Supabase
    SUPABASE_URL: str | None = None
    SUPABASE_ANON_KEY: str | None = None
    SUPABASE_SERVICE_ROLE_KEY: str | None = None

    # PipeRun CRM
    PIPERUN_API_URL: str = "https://api.pipe.run/v1"
    PIPERUN_API_TOKEN: str | None = None
    PIPERUN_PIPELINE_ID: int | None = None
    PIPERUN_STAGE_ID: int | None = None
    PIPERUN_ORIGIN_ID: int | None = None

    # Z-API Configuration (WhatsApp Provider)
    ZAPI_INSTANCE_ID: str | None = None
    ZAPI_INSTANCE_TOKEN: str | None = None
    ZAPI_CLIENT_TOKEN: str | None = None
    # Note: Z-API does not support custom webhook authentication headers
    # Security relies on HTTPS (required) and payload validation

    # Legacy WhatsApp variables (deprecated, use Z-API variables above)
    WHATSAPP_API_URL: str | None = None
    WHATSAPP_API_TOKEN: str | None = None

    # Chatwoot
    CHATWOOT_API_URL: str | None = None
    CHATWOOT_API_TOKEN: str | None = None
    CHATWOOT_ACCOUNT_ID: int | None = None

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"


settings = Settings()
