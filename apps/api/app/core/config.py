from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    environment: str = "local"
    log_level: str = "info"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_cors_origins: str = "http://localhost:3000"
    database_url: str = ""
    redis_url: str = ""
    local_storage_path: str = "storage"
    public_storage_url: str = "http://localhost:8000/uploads"
    jwt_secret_key: str = "dev-only-change-me-please-use-32-plus-characters"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440
    session_cookie_name: str = "apl_session"
    session_cookie_secure: bool = False
    openai_api_key: str = ""
    openai_vision_model: str = "gpt-4.1-mini"
    openai_text_model: str = "gpt-4.1-mini"
    openai_image_model: str = "gpt-image-1.5"
    openai_timeout_seconds: float = 30.0
    openai_image_timeout_seconds: float = 90.0
    ai_retry_attempts: int = 3
    ai_rate_limit_requests_per_minute: int = 10
    remove_bg_api_key: str = ""
    image_provider_timeout_seconds: float = 45.0
    aws_region: str = ""
    aws_s3_bucket: str = ""
    session_cookie_samesite: Literal["lax", "strict", "none"] = Field(default="lax")
    # Billing / wallet
    signup_bonus_enabled: bool = False
    stripe_secret_key: str = ""
    stripe_publishable_key: str = ""
    stripe_webhook_secret: str = ""
    billing_success_url: str = "http://localhost:3000/dashboard/billing?status=success"
    billing_cancel_url: str = "http://localhost:3000/dashboard/billing?status=cancelled"
    billing_portal_return_url: str = "http://localhost:3000/dashboard/billing"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="",
        case_sensitive=False,
    )

    @field_validator("access_token_expire_minutes")
    @classmethod
    def validate_access_token_expiry(cls, value: int) -> int:
        if value <= 0:
            msg = "ACCESS_TOKEN_EXPIRE_MINUTES must be greater than zero"
            raise ValueError(msg)
        return value

    @field_validator("openai_timeout_seconds")
    @classmethod
    def validate_openai_timeout(cls, value: float) -> float:
        if value <= 0:
            msg = "OPENAI_TIMEOUT_SECONDS must be greater than zero"
            raise ValueError(msg)
        return value

    @field_validator("openai_image_timeout_seconds")
    @classmethod
    def validate_openai_image_timeout(cls, value: float) -> float:
        if value <= 0:
            msg = "OPENAI_IMAGE_TIMEOUT_SECONDS must be greater than zero"
            raise ValueError(msg)
        return value

    @field_validator("ai_retry_attempts")
    @classmethod
    def validate_ai_retry_attempts(cls, value: int) -> int:
        if value <= 0:
            msg = "AI_RETRY_ATTEMPTS must be greater than zero"
            raise ValueError(msg)
        return value

    @field_validator("ai_rate_limit_requests_per_minute")
    @classmethod
    def validate_ai_rate_limit(cls, value: int) -> int:
        if value <= 0:
            msg = "AI_RATE_LIMIT_REQUESTS_PER_MINUTE must be greater than zero"
            raise ValueError(msg)
        return value

    @field_validator("image_provider_timeout_seconds")
    @classmethod
    def validate_image_provider_timeout(cls, value: float) -> float:
        if value <= 0:
            msg = "IMAGE_PROVIDER_TIMEOUT_SECONDS must be greater than zero"
            raise ValueError(msg)
        return value

    @model_validator(mode="after")
    def validate_production_secrets(self) -> "Settings":
        if self.environment.lower() != "local":
            if self.jwt_secret_key.startswith("dev-only-change-me"):
                msg = "JWT_SECRET_KEY must be configured outside local development"
                raise ValueError(msg)
            if not self.openai_api_key:
                msg = "OPENAI_API_KEY must be configured outside local development"
                raise ValueError(msg)
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
