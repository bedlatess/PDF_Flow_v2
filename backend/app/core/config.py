"""
Core configuration settings for PDF-Flow backend
Based on v4.0 specification: Enterprise-grade architecture with STRIDE security model
"""
import json
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings"""

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
    )

    # Project Info
    PROJECT_NAME: str = "PDF-Flow API"
    VERSION: str = "2.0.0"
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    DEBUG: bool = Field(default=True, env="DEBUG")

    # API Configuration
    API_V1_PREFIX: str = "/api/v1"

    # Security - JWT
    SECRET_KEY: str = Field(..., env="SECRET_KEY")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    ALLOWED_ORIGINS_RAW: str = Field(
        default="http://localhost:5173,http://localhost:3000",
        alias="ALLOWED_ORIGINS"
    )
    ALLOWED_HOSTS_RAW: str = Field(
        default="localhost,127.0.0.1",
        alias="ALLOWED_HOSTS"
    )

    # Database (Supabase PostgreSQL)
    DATABASE_URL: str = Field(..., env="DATABASE_URL")
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    # Redis Configuration
    REDIS_URL: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    REDIS_QUEUE_NAME: str = "pdf_processing_queue"

    # File Storage
    UPLOAD_DIR: str = "/tmp/pdf-flow/uploads"
    MAX_UPLOAD_SIZE: int = 500 * 1024 * 1024  # 500MB for Pro users
    FREE_TIER_MAX_SIZE: int = 20 * 1024 * 1024  # 20MB for free users
    ALLOWED_EXTENSIONS: List[str] = ["pdf", "jpg", "jpeg", "png", "docx", "xlsx", "pptx"]

    # Rate Limiting (Redis sliding window)
    RATE_LIMIT_FREE: int = 3  # 3 requests per day for free users
    RATE_LIMIT_PRO: int = -1  # Unlimited for Pro users
    RATE_LIMIT_WINDOW: int = 86400  # 24 hours in seconds

    # OCR Configuration
    TESSERACT_PATH: Optional[str] = Field(default=None, env="TESSERACT_PATH")
    OCR_LANGUAGES: List[str] = ["eng", "chi_sim", "spa"]

    # Stripe Configuration (for Pro subscription)
    STRIPE_SECRET_KEY: Optional[str] = Field(default=None, env="STRIPE_SECRET_KEY")
    STRIPE_PUBLISHABLE_KEY: Optional[str] = Field(default=None, env="STRIPE_PUBLISHABLE_KEY")
    STRIPE_WEBHOOK_SECRET: Optional[str] = Field(default=None, env="STRIPE_WEBHOOK_SECRET")
    STRIPE_PRICE_ID_MONTHLY: Optional[str] = Field(default=None, env="STRIPE_PRICE_ID_MONTHLY")
    STRIPE_PRICE_ID_YEARLY: Optional[str] = Field(default=None, env="STRIPE_PRICE_ID_YEARLY")

    # Email Configuration (Resend)
    RESEND_API_KEY: Optional[str] = Field(default=None, env="RESEND_API_KEY")
    EMAIL_FROM: str = Field(default="PDF-Flow <noreply@pdf-flow.com>", env="EMAIL_FROM")
    FRONTEND_URL: str = Field(default="http://localhost:5173", env="FRONTEND_URL")
    PASSWORD_RESET_TOKEN_EXPIRE_HOURS: int = 1

    # OAuth Configuration
    GOOGLE_CLIENT_ID: Optional[str] = Field(default=None, env="GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET: Optional[str] = Field(default=None, env="GOOGLE_CLIENT_SECRET")
    GITHUB_CLIENT_ID: Optional[str] = Field(default=None, env="GITHUB_CLIENT_ID")
    GITHUB_CLIENT_SECRET: Optional[str] = Field(default=None, env="GITHUB_CLIENT_SECRET")
    OAUTH_REDIRECT_URL: str = Field(default="http://localhost:8000", env="OAUTH_REDIRECT_URL")

    # Monitoring & Analytics
    SENTRY_DSN: Optional[str] = Field(default=None, env="SENTRY_DSN")
    POSTHOG_API_KEY: Optional[str] = Field(default=None, env="POSTHOG_API_KEY")

    # AI / Gemini
    GEMINI_API_KEY: Optional[str] = Field(default=None, env="GEMINI_API_KEY")

    # Celery Configuration
    CELERY_BROKER_URL: str = Field(default="redis://localhost:6379/0", env="CELERY_BROKER_URL")
    CELERY_RESULT_BACKEND: str = Field(default="redis://localhost:6379/1", env="CELERY_RESULT_BACKEND")

    # Security - STRIDE Model Implementation
    # S (Spoofing): API Keys stored as SHA-256 hashes only
    # T (Tampering): Magic number validation for all uploads
    # R (Repudiation): Audit logs in read-only stream
    # I (Information Disclosure): CSP headers, Tmpfs storage
    # D (Denial of Service): Cloudflare + Redis rate limiting
    # E (Elevation of Privilege): Non-root containers, minimum permissions

    @staticmethod
    def _parse_list_setting(value: str) -> List[str]:
        value = (value or "").strip()
        if not value:
            return []
        if value.startswith("["):
            return [item.strip() for item in json.loads(value) if str(item).strip()]
        return [item.strip() for item in value.split(",") if item.strip()]

    @property
    def ALLOWED_ORIGINS(self) -> List[str]:
        return self._parse_list_setting(self.ALLOWED_ORIGINS_RAW)

    @property
    def ALLOWED_HOSTS(self) -> List[str]:
        return self._parse_list_setting(self.ALLOWED_HOSTS_RAW)


# Create settings instance
settings = Settings()
