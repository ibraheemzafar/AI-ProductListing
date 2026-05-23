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
    aws_region: str = ""
    aws_s3_bucket: str = ""
    session_cookie_samesite: Literal["lax", "strict", "none"] = Field(default="lax")

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

    @model_validator(mode="after")
    def validate_production_secrets(self) -> "Settings":
        if self.environment.lower() != "local":
            if self.jwt_secret_key.startswith("dev-only-change-me"):
                msg = "JWT_SECRET_KEY must be configured outside local development"
                raise ValueError(msg)
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
