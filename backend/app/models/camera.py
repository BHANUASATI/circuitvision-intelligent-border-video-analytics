"""
Camera & Stream Models
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Camera(Base):
    __tablename__ = "cameras"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    camera_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    stream_url: Mapped[str] = mapped_column(Text, nullable=False)
    location: Mapped[str] = mapped_column(String(255), default="")
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Analytics toggles
    enable_detection: Mapped[bool] = mapped_column(Boolean, default=True)
    enable_face_recognition: Mapped[bool] = mapped_column(Boolean, default=True)
    enable_anpr: Mapped[bool] = mapped_column(Boolean, default=True)
    enable_intrusion: Mapped[bool] = mapped_column(Boolean, default=True)
    enable_activity: Mapped[bool] = mapped_column(Boolean, default=True)

    frame_skip: Mapped[int] = mapped_column(Integer, default=2)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_streaming: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    incidents: Mapped[list["Incident"]] = relationship("Incident", back_populates="camera")
    alerts: Mapped[list["Alert"]] = relationship("Alert", back_populates="camera")
