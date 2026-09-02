"""
Stream endpoints — HLS transcoding for live camera viewing.

POST /api/v1/stream/{camera_id}/start          → launch FFmpeg, wait for playlist
POST /api/v1/stream/{camera_id}/stop           → kill FFmpeg
GET  /api/v1/stream/{camera_id}/status         → health check
GET  /api/v1/stream/{camera_id}/hls/index.m3u8 → playlist (no auth)
GET  /api/v1/stream/{camera_id}/hls/{segment}  → TS segment  (no auth)
"""
from __future__ import annotations

import asyncio
import re
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import logger
from app.db.base import get_db
from app.models.user import User
from app.services.auth_service import get_current_user
from app.services.camera_service import get_camera
from app.services.hls_service import (
    get_hls_dir,
    get_last_error,
    is_running,
    start_hls,
    stop_hls,
)

router = APIRouter(prefix="/stream", tags=["Stream"])

_STARTUP_TIMEOUT_S = 15
_POLL_INTERVAL_S   = 0.5


async def _check_host_reachable(url: str, connect_timeout: float = 5.0) -> None:
    """Quick TCP connect to verify the stream host is reachable before spawning FFmpeg."""
    parsed = urlparse(url)
    host   = parsed.hostname
    port   = parsed.port or (554 if parsed.scheme.startswith("rtsp") else 80)
    if not host:
        return  # can't parse, let FFmpeg handle it
    try:
        _, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port),
            timeout=connect_timeout,
        )
        writer.close()
        await writer.wait_closed()
    except (asyncio.TimeoutError, OSError) as exc:
        raise HTTPException(
            502,
            f"Cannot reach stream host {host}:{port} — "
            f"check network/firewall or the stream URL. ({exc})"
        )


@router.post("/{camera_id}/start")
async def start_camera_hls(
    camera_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Start FFmpeg HLS transcoding for a camera and wait for first segment."""
    camera = await get_camera(db, camera_id)
    if not camera:
        raise HTTPException(404, f"Camera not found: {camera_id}")

    stream_url = camera.stream_url.strip()
    if not stream_url:
        raise HTTPException(400, "Camera has no stream URL configured")

    # Fast pre-flight — fail immediately if host is unreachable
    await _check_host_reachable(stream_url)

    # Launch FFmpeg in a thread pool (blocking call)
    try:
        hls_dir = await asyncio.get_event_loop().run_in_executor(
            None, start_hls, camera_id, stream_url
        )
    except Exception as exc:
        logger.error(f"Failed to launch FFmpeg for {camera_id}: {exc}")
        raise HTTPException(500, f"Could not launch FFmpeg: {exc}")

    # Poll until playlist has content or FFmpeg dies early
    playlist = hls_dir / "index.m3u8"
    ticks    = int(_STARTUP_TIMEOUT_S / _POLL_INTERVAL_S)

    for _ in range(ticks):
        if not is_running(camera_id):
            err = get_last_error(camera_id)
            stop_hls(camera_id)
            # 503 from camera = another client has the stream open (e.g. VLC)
            if "503" in err or "Service Unavailable" in err:
                raise HTTPException(
                    502,
                    f"Camera refused the connection (503 Service Unavailable). "
                    f"The camera may only allow one viewer at a time — close any other "
                    f"RTSP clients (e.g. VLC) and try again."
                )
            raise HTTPException(502, f"FFmpeg exited before producing a stream. FFmpeg said: {err}")

        if playlist.exists() and playlist.stat().st_size > 0:
            return {
                "status": "started",
                "camera_id": camera_id,
                "playlist_url": f"/api/v1/stream/{camera_id}/hls/index.m3u8",
            }

        await asyncio.sleep(_POLL_INTERVAL_S)

    err = get_last_error(camera_id)
    stop_hls(camera_id)
    raise HTTPException(
        504,
        f"Stream did not produce output within {_STARTUP_TIMEOUT_S}s. FFmpeg said: {err}"
    )


@router.post("/{camera_id}/stop")
async def stop_camera_hls(
    camera_id: str,
    _: User = Depends(get_current_user),
):
    stop_hls(camera_id)
    return {"status": "stopped", "camera_id": camera_id}


@router.get("/{camera_id}/status")
async def hls_status(
    camera_id: str,
    _: User = Depends(get_current_user),
):
    running = is_running(camera_id)
    hls_dir = get_hls_dir(camera_id)
    playlist_ready = bool(hls_dir and (hls_dir / "index.m3u8").exists())
    return {
        "camera_id": camera_id,
        "running": running,
        "playlist_ready": playlist_ready,
        "playlist_url": f"/api/v1/stream/{camera_id}/hls/index.m3u8" if playlist_ready else None,
    }


# ── Segment & playlist serving (no auth — fetched by <video> element) ─────────

@router.get("/{camera_id}/hls/index.m3u8")
async def serve_playlist(camera_id: str):
    hls_dir = get_hls_dir(camera_id)
    if not hls_dir:
        raise HTTPException(404, "No active HLS session")

    playlist = hls_dir / "index.m3u8"
    if not playlist.exists():
        raise HTTPException(404, "Playlist not ready yet")

    return Response(
        content=playlist.read_text(),
        media_type="application/vnd.apple.mpegurl",
        headers={"Cache-Control": "no-cache, no-store", "Access-Control-Allow-Origin": "*"},
    )


@router.get("/{camera_id}/hls/{segment}")
async def serve_segment(camera_id: str, segment: str):
    if not segment.endswith(".ts"):
        raise HTTPException(400, "Only .ts segments are served here")

    hls_dir = get_hls_dir(camera_id)
    if not hls_dir:
        raise HTTPException(404, "No active HLS session")

    seg_path = hls_dir / segment
    if not seg_path.exists():
        raise HTTPException(404, f"Segment not found: {segment}")

    return FileResponse(
        str(seg_path),
        media_type="video/mp2t",
        headers={"Cache-Control": "no-cache, no-store", "Access-Control-Allow-Origin": "*"},
    )
