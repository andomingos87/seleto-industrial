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
    CHATWOOT_INBOX_ID: int | None = None

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    # Business Hours (optional overrides for config/business_hours.yaml)
    # If set, these override the YAML configuration
    BUSINESS_HOURS_TIMEZONE: str | None = None  # e.g., "America/Sao_Paulo"
    BUSINESS_HOURS_START: str | None = None  # e.g., "08:00" (applies to all days)
    BUSINESS_HOURS_END: str | None = None  # e.g., "18:00" (applies to all days)
    # Note: For detailed per-day configuration, use config/business_hours.yaml

    # Alerts (TECH-024)
    ALERT_SLACK_WEBHOOK_URL: str | None = None  # Slack incoming webhook URL
    ALERT_WEBHOOK_URL: str | None = None  # Generic webhook URL for alerts
    ALERT_EMAIL_SMTP_HOST: str | None = None  # SMTP server hostname
    ALERT_EMAIL_SMTP_PORT: int = 587  # SMTP server port
    ALERT_EMAIL_FROM: str | None = None  # Sender email address
    ALERT_EMAIL_TO: str | None = None  # Recipient email address
    ALERT_ERROR_RATE_THRESHOLD: float = 0.10  # Error rate threshold (10%)
    ALERT_LATENCY_THRESHOLD_SECONDS: float = 10.0  # P95 latency threshold
    ALERT_CHECK_INTERVAL_SECONDS: int = 60  # How often to check for alerts
    ALERT_DEBOUNCE_MINUTES: int = 15  # Minimum time between same alerts

    # Audit Trail (TECH-028)
    AUDIT_RETENTION_DAYS: int = 90  # Days to retain audit logs

    # Data Retention / LGPD (TECH-031)
    TRANSCRIPT_RETENTION_DAYS: int = 90  # Days to retain conversation messages/transcripts
    CONTEXT_RETENTION_DAYS: int = 90  # Days to retain conversation context
    LEAD_INACTIVITY_DAYS: int = 365  # Days of inactivity before lead anonymization
    PENDING_OPERATIONS_RETENTION_DAYS: int = 7  # Days to retain completed pending operations


settings = Settings()
