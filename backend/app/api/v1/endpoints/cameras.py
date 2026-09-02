"""Camera management + stream control endpoints."""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import get_db
from app.models.user import User
from app.schemas.camera import CameraCreate, CameraOut, CameraStreamStats, CameraUpdate
from app.services.audit_service import log_action
from app.services.auth_service import get_current_user, require_permission
from app.services.camera_service import (
    create_camera,
    delete_camera,
    get_camera,
    get_stream_stats,
    list_cameras,
    start_stream,
    stop_stream,
    update_camera,
)

router = APIRouter(prefix="/cameras", tags=["Cameras"])


@router.post("", response_model=CameraOut)
async def add_camera(
    data: CameraCreate,
    db: AsyncSession = Depends(get_db),
    current: User = Depends(require_permission("camera:write")),
):
    camera = await create_camera(db, data)
    await log_action(db, "create_camera", "camera", resource_id=data.camera_id, user_id=current.id)
    return camera


@router.get("", response_model=List[CameraOut])
async def get_cameras(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return await list_cameras(db, skip, limit)


@router.get("/{camera_id}", response_model=CameraOut)
async def get_camera_detail(
    camera_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    camera = await get_camera(db, camera_id)
    if not camera:
        raise HTTPException(404, f"Camera not found: {camera_id}")
    return camera


@router.patch("/{camera_id}", response_model=CameraOut)
async def update_camera_detail(
    camera_id: str,
    data: CameraUpdate,
    db: AsyncSession = Depends(get_db),
    current: User = Depends(require_permission("camera:write")),
):
    camera = await update_camera(db, camera_id, data)
    if not camera:
        raise HTTPException(404, f"Camera not found: {camera_id}")
    await log_action(db, "update_camera", "camera", resource_id=camera_id, user_id=current.id)
    return camera


@router.delete("/{camera_id}")
async def remove_camera(
    camera_id: str,
    db: AsyncSession = Depends(get_db),
    current: User = Depends(require_permission("camera:write")),
):
    # Stop stream first if running
    try:
        await stop_stream(db, camera_id)
    except Exception:
        pass
    deleted = await delete_camera(db, camera_id)
    if not deleted:
        raise HTTPException(404, f"Camera not found: {camera_id}")
    await log_action(db, "delete_camera", "camera", resource_id=camera_id, user_id=current.id)
    return {"message": f"Camera deleted: {camera_id}"}


@router.post("/{camera_id}/start-stream")
async def start_camera_stream(
    camera_id: str,
    db: AsyncSession = Depends(get_db),
    current: User = Depends(require_permission("stream:control")),
):
    try:
        result = await start_stream(db, camera_id)
        await log_action(db, "start_stream", "camera", resource_id=camera_id, user_id=current.id)
        return result
    except ValueError as exc:
        raise HTTPException(404, str(exc))
    except Exception as exc:
        raise HTTPException(502, f"AI service error: {exc}")


@router.post("/{camera_id}/stop-stream")
async def stop_camera_stream(
    camera_id: str,
    db: AsyncSession = Depends(get_db),
    current: User = Depends(require_permission("stream:control")),
):
    try:
        result = await stop_stream(db, camera_id)
        await log_action(db, "stop_stream", "camera", resource_id=camera_id, user_id=current.id)
        return result
    except ValueError as exc:
        raise HTTPException(404, str(exc))
    except Exception as exc:
        raise HTTPException(502, f"AI service error: {exc}")


@router.get("/{camera_id}/stats", response_model=CameraStreamStats)
async def camera_stream_stats(
    camera_id: str,
    _: User = Depends(get_current_user),
):
    stats = await get_stream_stats(camera_id)
    if not stats:
        raise HTTPException(404, f"No active stream for: {camera_id}")
    return CameraStreamStats(**stats)
