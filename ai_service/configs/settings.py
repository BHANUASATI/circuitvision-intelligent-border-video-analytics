"""
AI Service — Configuration
Loads from environment variables / .env file.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # ── Service ────────────────────────────────────────────────
    service_host: str = "0.0.0.0"
    service_port: int = 8001
    app_env: str = "development"
    app_debug: bool = False

    # ── YOLO ──────────────────────────────────────────────────
    yolo_model_path: str = "/models/yolo/yolov8n.pt"
    yolo_confidence_threshold: float = 0.45
    yolo_nms_threshold: float = 0.45
    yolo_device: str = "0"           # "0" for GPU 0, "cpu" for CPU

    # ── Face Recognition ──────────────────────────────────────
    face_model_path: str = "/models/face/buffalo_l"
    face_recognition_threshold: float = 0.5
    face_db_path: str = "/data/face_db"

    # ── ANPR ──────────────────────────────────────────────────
    anpr_model_path: str = "/models/anpr/anpr_yolo.pt"
    anpr_ocr_lang: str = "en"
    plate_db_path: str = "/data/plate_db"

    # ── Stream ────────────────────────────────────────────────
    stream_reconnect_delay: int = 5
    stream_frame_skip: int = 2
    max_concurrent_streams: int = 16

    # ── Evidence ──────────────────────────────────────────────
    evidence_storage_path: str = "/data/evidence"
    enable_evidence_hashing: bool = True

    # ── Redis ─────────────────────────────────────────────────
    redis_url: str = "redis://localhost:6379/0"

    # ── Alert ─────────────────────────────────────────────────
    alert_cooldown_seconds: int = 30

    # ── CORS ──────────────────────────────────────────────────
    cors_origins: List[str] = Field(default=["*"])


settings = Settings()
