"""
Backend — Application Configuration
"""
from __future__ import annotations

from typing import List, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # ── App ───────────────────────────────────────────────────
    app_env: str = "development"
    app_debug: bool = False
    app_version: str = "1.0.0"
    app_title: str = "IBVAP Backend API"

    # ── Database ──────────────────────────────────────────────
    database_url: str = "postgresql+asyncpg://ibvap_user:password@localhost:5432/ibvap"

    # ── Redis ─────────────────────────────────────────────────
    redis_url: str = "redis://localhost:6379/0"

    # ── JWT ───────────────────────────────────────────────────
    jwt_secret_key: str = "dev-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60
    jwt_refresh_token_expire_days: int = 7

    # ── AI Service ────────────────────────────────────────────
    ai_service_url: str = "http://ai_service:8001"

    # ── Security ──────────────────────────────────────────────
    cors_origins: Union[List[str], str] = Field(default="http://localhost:3000")
    rate_limit_per_minute: int = 120
    enable_audit_log: bool = True

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            return [o.strip() for o in v.split(",") if o.strip()]
        return v

    # ── Evidence ──────────────────────────────────────────────
    evidence_storage_path: str = "/data/evidence"
    evidence_retention_days: int = 90

    # ── Alert ─────────────────────────────────────────────────
    alert_websocket_ping_interval: int = 25


settings = Settings()
