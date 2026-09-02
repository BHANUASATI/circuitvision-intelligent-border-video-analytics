"""
Camera Service — CRUD + AI service stream orchestration.
"""
from __future__ import annotations

import uuid
from typing import List, Optional

import httpx
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logger import logger
from app.models.camera import Camera
from app.schemas.camera import CameraCreate, CameraUpdate


async def create_camera(db: AsyncSession, data: CameraCreate) -> Camera:
    camera = Camera(**data.model_dump())
    db.add(camera)
    await db.flush()
    await db.refresh(camera)
    return camera


async def get_camera(db: AsyncSession, camera_id: str) -> Optional[Camera]:
    result = await db.execute(select(Camera).where(Camera.camera_id == camera_id))
    return result.scalar_one_or_none()


async def list_cameras(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Camera]:
    result = await db.execute(select(Camera).offset(skip).limit(limit))
    return list(result.scalars().all())


async def update_camera(db: AsyncSession, camera_id: str, data: CameraUpdate) -> Optional[Camera]:
    camera = await get_camera(db, camera_id)
    if not camera:
        return None
    for k, v in data.model_dump(exclude_none=True).items():
        setattr(camera, k, v)
    await db.flush()
    await db.refresh(camera)
    return camera


async def delete_camera(db: AsyncSession, camera_id: str) -> bool:
    camera = await get_camera(db, camera_id)
    if not camera:
        return False
    await db.delete(camera)
    await db.flush()
    return True


async def start_stream(db: AsyncSession, camera_id: str) -> dict:
    """Tell AI service to start stream, update DB state."""
    camera = await get_camera(db, camera_id)
    if not camera:
        raise ValueError(f"Camera not found: {camera_id}")

    payload = {
        "camera_id": camera.camera_id,
        "name": camera.name,
        "stream_url": camera.stream_url,
        "location": camera.location,
        "enable_detection": camera.enable_detection,
        "enable_face_recognition": camera.enable_face_recognition,
        "enable_anpr": camera.enable_anpr,
        "enable_intrusion": camera.enable_intrusion,
        "enable_activity": camera.enable_activity,
        "frame_skip": camera.frame_skip,
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{settings.ai_service_url}/api/v1/streams/start",
                json=payload,
            )
            resp.raise_for_status()
            ai_response = resp.json()
    except (httpx.ConnectError, httpx.ConnectTimeout, httpx.TimeoutException) as exc:
        # AI service not running (local dev) — mark as streaming anyway
        logger.warning(f"AI service unreachable for start_stream({camera_id}): {exc}")
        ai_response = {
            "status": "started",
            "camera_id": camera_id,
            "message": "AI service unavailable — stream registered locally",
        }

    camera.is_streaming = True
    await db.flush()
    return ai_response


async def stop_stream(db: AsyncSession, camera_id: str) -> dict:
    camera = await get_camera(db, camera_id)
    if not camera:
        raise ValueError(f"Camera not found: {camera_id}")

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{settings.ai_service_url}/api/v1/streams/{camera_id}/stop"
            )
            resp.raise_for_status()
            ai_response = resp.json()
    except (httpx.ConnectError, httpx.ConnectTimeout, httpx.TimeoutException) as exc:
        logger.warning(f"AI service unreachable for stop_stream({camera_id}): {exc}")
        ai_response = {
            "status": "stopped",
            "camera_id": camera_id,
            "message": "AI service unavailable — stream unregistered locally",
        }

    camera.is_streaming = False
    await db.flush()
    return ai_response


async def get_stream_stats(camera_id: str) -> Optional[dict]:
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(
                f"{settings.ai_service_url}/api/v1/streams/{camera_id}/status"
            )
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.warning(f"Failed to get stream stats for {camera_id}: {exc}")
        return None
