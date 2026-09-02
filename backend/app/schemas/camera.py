"""Camera Pydantic schemas."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CameraCreate(BaseModel):
    camera_id: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=255)
    stream_url: str
    location: str = ""
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    enable_detection: bool = True
    enable_face_recognition: bool = True
    enable_anpr: bool = True
    enable_intrusion: bool = True
    enable_activity: bool = True
    frame_skip: int = Field(default=2, ge=1, le=10)


class CameraUpdate(BaseModel):
    name: Optional[str] = None
    stream_url: Optional[str] = None
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    enable_detection: Optional[bool] = None
    enable_face_recognition: Optional[bool] = None
    enable_anpr: Optional[bool] = None
    enable_intrusion: Optional[bool] = None
    enable_activity: Optional[bool] = None
    frame_skip: Optional[int] = Field(default=None, ge=1, le=10)
    is_active: Optional[bool] = None


class CameraOut(BaseModel):
    id: uuid.UUID
    camera_id: str
    name: str
    stream_url: str
    location: str
    latitude: Optional[float]
    longitude: Optional[float]
    enable_detection: bool
    enable_face_recognition: bool
    enable_anpr: bool
    enable_intrusion: bool
    enable_activity: bool
    frame_skip: int
    is_active: bool
    is_streaming: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class CameraStreamStats(BaseModel):
    camera_id: str
    status: str
    fps: float
    frame_count: int
    inference_ms: float
    alert_count: int
    error: Optional[str]
