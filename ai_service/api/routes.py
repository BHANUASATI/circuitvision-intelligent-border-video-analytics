"""
AI Service API Routes
Exposes stream control, fence config, face enrollment, and analytics endpoints.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel

from ai_service.core.stream_manager import stream_manager
from ai_service.core.stream_worker import CameraConfig
from ai_service.modules.intrusion.virtual_fence import (
    FenceConfig, FenceType, CrossingDirection, fence_manager
)
from ai_service.utils.logger import logger

router = APIRouter()


# ── Pydantic Schemas ──────────────────────────────────────────

class StartStreamRequest(BaseModel):
    camera_id: str
    name: str
    stream_url: str
    location: str = ""
    enable_detection: bool = True
    enable_face_recognition: bool = True
    enable_anpr: bool = True
    enable_intrusion: bool = True
    enable_activity: bool = True
    frame_skip: int = 2


class FenceCreateRequest(BaseModel):
    fence_id: str
    fence_type: FenceType
    name: str
    camera_id: str
    points: List[List[int]]
    direction: CrossingDirection = CrossingDirection.ANY
    alert_cooldown: int = 30


class AlertResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None


# ── Stream Control ────────────────────────────────────────────

@router.post("/streams/start", response_model=AlertResponse)
async def start_stream(req: StartStreamRequest):
    config = CameraConfig(
        camera_id=req.camera_id,
        name=req.name,
        stream_url=req.stream_url,
        location=req.location,
        enable_detection=req.enable_detection,
        enable_face_recognition=req.enable_face_recognition,
        enable_anpr=req.enable_anpr,
        enable_intrusion=req.enable_intrusion,
        enable_activity=req.enable_activity,
        frame_skip=req.frame_skip,
    )
    try:
        started = await stream_manager.start_stream(config)
        if not started:
            raise HTTPException(409, f"Stream already running: {req.camera_id}")
        return AlertResponse(success=True, message=f"Stream started: {req.camera_id}")
    except RuntimeError as exc:
        raise HTTPException(429, str(exc))


@router.post("/streams/{camera_id}/stop", response_model=AlertResponse)
async def stop_stream(camera_id: str):
    stopped = await stream_manager.stop_stream(camera_id)
    if not stopped:
        raise HTTPException(404, f"Stream not found: {camera_id}")
    return AlertResponse(success=True, message=f"Stream stopped: {camera_id}")


@router.get("/streams/status")
async def all_stream_status():
    stats = stream_manager.get_all_stats()
    return {
        "total": len(stats),
        "streams": [
            {
                "camera_id": s.camera_id,
                "status": s.status,
                "fps": s.fps,
                "frame_count": s.frame_count,
                "inference_ms": s.inference_ms,
                "alert_count": s.alert_count,
                "error": s.error,
            }
            for s in stats
        ],
    }


@router.get("/streams/{camera_id}/status")
async def stream_status(camera_id: str):
    stats = stream_manager.get_stats(camera_id)
    if not stats:
        raise HTTPException(404, f"Stream not found: {camera_id}")
    return {
        "camera_id": stats.camera_id,
        "status": stats.status,
        "fps": stats.fps,
        "frame_count": stats.frame_count,
        "inference_ms": stats.inference_ms,
        "alert_count": stats.alert_count,
        "last_frame_ts": stats.last_frame_ts,
        "error": stats.error,
    }


# ── Virtual Fence ─────────────────────────────────────────────

@router.post("/fences", response_model=AlertResponse)
async def create_fence(req: FenceCreateRequest):
    config = FenceConfig(
        fence_id=req.fence_id,
        fence_type=req.fence_type,
        name=req.name,
        camera_id=req.camera_id,
        points=[tuple(p) for p in req.points],
        direction=req.direction,
        alert_cooldown=req.alert_cooldown,
    )
    fence_manager.add_fence(config)
    return AlertResponse(success=True, message=f"Fence created: {req.fence_id}")


@router.delete("/fences/{fence_id}", response_model=AlertResponse)
async def delete_fence(fence_id: str):
    fence_manager.remove_fence(fence_id)
    return AlertResponse(success=True, message=f"Fence removed: {fence_id}")


@router.get("/fences/{camera_id}")
async def get_fences(camera_id: str):
    fences = fence_manager.get_fences_for_camera(camera_id)
    return {
        "camera_id": camera_id,
        "fences": [
            {
                "fence_id": f.fence_id,
                "name": f.name,
                "fence_type": f.fence_type,
                "points": f.points,
                "direction": f.direction,
            }
            for f in fences
        ],
    }


# ── Face Enrollment ───────────────────────────────────────────

@router.post("/faces/enroll", response_model=AlertResponse)
async def enroll_face(
    identity_id: str = Form(...),
    name: str = Form(...),
    category: str = Form("enrolled"),
    image: UploadFile = File(...),
):
    import io
    import cv2
    import numpy as np

    contents = await image.read()
    nparr = np.frombuffer(contents, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if frame is None:
        raise HTTPException(400, "Invalid image file")

    from ai_service.modules.face_recognition.face_engine import face_engine
    success = face_engine.enroll_face(frame, identity_id, name, category)
    if not success:
        raise HTTPException(422, "No face detected in image")
    return AlertResponse(success=True, message=f"Face enrolled: {name} ({identity_id})")


# ── ANPR Watchlist ────────────────────────────────────────────

class PlateWatchlistRequest(BaseModel):
    plate: str
    category: str
    notes: str = ""


@router.post("/anpr/watchlist", response_model=AlertResponse)
async def add_plate_watchlist(req: PlateWatchlistRequest):
    from ai_service.modules.anpr.anpr import anpr_engine
    anpr_engine.add_to_watchlist(req.plate, req.category, req.notes)
    return AlertResponse(success=True, message=f"Plate added to watchlist: {req.plate}")
