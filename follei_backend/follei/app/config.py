"""Central application configuration loaded from environment variables."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    """Runtime settings.

    Values can be supplied through process environment variables or the
    ``follei/.env`` file. Environment variables always take precedence.
    """

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    environment: str = "development"
    log_level: str = "INFO"

    database_url: str = "postgresql+psycopg2://admin:secret@localhost:55589/follei_db"

    secret_key: str = "dev-secret-change-me"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = Field(default=60, gt=0)

    mistral_api_key: str | None = None
    mistral_model: str = "mistral-large-latest"
    anthropic_api_key: str | None = None

    qdrant_url: str | None = None
    qdrant_api_key: str | None = None
    qdrant_collection: str = "document_chunks"

    smtp_host: str | None = None
    smtp_port: int = Field(default=587, ge=1, le=65535)
    smtp_user: str | None = None
    smtp_password: str | None = None
    smtp_from: str | None = None
    smtp_tls: bool = True

    mailjet_api_key: str | None = None
    mailjet_api_secret: str | None = None
    mailjet_from_email: str | None = None
    mailjet_from_name: str = "Follei"

    brevo_api_key: str | None = None
    brevo_from_email: str | None = None
    brevo_from_name: str = "Follei"

    twilio_account_sid: str | None = None
    twilio_auth_token: str | None = None
    twilio_from_phone: str | None = None
    default_phone_country_code: str = "+91"

    follei_upload_dir: Path = Path("uploads/documents")
    follei_dataset_dir: Path | None = None


@lru_cache
def get_settings() -> Settings:
    """Return one validated settings object for the application process."""

    return Settings()


settings = get_settings()
