"""Analytics & dashboard summary endpoints."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import get_db
from app.models.alert import Alert, Incident
from app.models.camera import Camera
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/dashboard")
async def dashboard_summary(
    db: AsyncSession = Depends(get_db),
    _ = Depends(get_current_user),
):
    """Top-level dashboard metrics."""
    now = datetime.now(timezone.utc)
    last_24h = now - timedelta(hours=24)
    last_hour = now - timedelta(hours=1)

    # Camera counts
    cam_result = await db.execute(
        select(func.count(Camera.id), func.count(Camera.id).filter(Camera.is_streaming == True))
    )
    total_cameras, active_streams = cam_result.one()

    # Alert counts last 24h
    alert_result = await db.execute(
        select(
            func.count(Alert.id),
            func.count(Alert.id).filter(Alert.status == "new"),
        ).where(Alert.created_at >= last_24h)
    )
    alerts_24h, unack_alerts = alert_result.one()

    # Alert breakdown by event type (last 24h)
    type_result = await db.execute(
        select(Alert.event_type, func.count(Alert.id))
        .where(Alert.created_at >= last_24h)
        .group_by(Alert.event_type)
    )
    by_type = {row[0]: row[1] for row in type_result.all()}

    # Alert breakdown by severity (last 24h)
    sev_result = await db.execute(
        select(Alert.severity, func.count(Alert.id))
        .where(Alert.created_at >= last_24h)
        .group_by(Alert.severity)
    )
    by_severity = {row[0]: row[1] for row in sev_result.all()}

    # Open incidents
    inc_result = await db.execute(
        select(func.count(Incident.id)).where(Incident.status == "open")
    )
    open_incidents = inc_result.scalar()

    # Hourly alert trend (last 24 hours, 1h buckets)
    hourly_result = await db.execute(
        select(
            func.date_trunc("hour", Alert.created_at).label("hour"),
            func.count(Alert.id).label("count"),
        )
        .where(Alert.created_at >= last_24h)
        .group_by("hour")
        .order_by("hour")
    )
    hourly_trend = [
        {"hour": row.hour.isoformat(), "count": row.count}
        for row in hourly_result.all()
    ]

    return {
        "cameras": {
            "total": total_cameras,
            "active_streams": active_streams,
        },
        "alerts": {
            "last_24h": alerts_24h,
            "unacknowledged": unack_alerts,
            "by_event_type": by_type,
            "by_severity": by_severity,
            "hourly_trend": hourly_trend,
        },
        "incidents": {
            "open": open_incidents,
        },
        "generated_at": now.isoformat(),
    }


@router.get("/alerts/timeline")
async def alert_timeline(
    camera_id: str = Query(None),
    hours: int = Query(24, ge=1, le=168),
    db: AsyncSession = Depends(get_db),
    _ = Depends(get_current_user),
):
    """Per-event-type alert counts over time."""
    since = datetime.now(timezone.utc) - timedelta(hours=hours)

    q = (
        select(
            func.date_trunc("hour", Alert.created_at).label("hour"),
            Alert.event_type,
            func.count(Alert.id).label("count"),
        )
        .where(Alert.created_at >= since)
        .group_by("hour", Alert.event_type)
        .order_by("hour")
    )
    if camera_id:
        q = q.where(Alert.camera_id == camera_id)

    result = await db.execute(q)
    return [
        {"hour": row.hour.isoformat(), "event_type": row.event_type, "count": row.count}
        for row in result.all()
    ]


@router.get("/cameras/heatmap")
async def camera_alert_heatmap(
    hours: int = Query(24, ge=1, le=720),
    db: AsyncSession = Depends(get_db),
    _ = Depends(get_current_user),
):
    """Alert counts per camera for map overlay."""
    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    result = await db.execute(
        select(Alert.camera_id, func.count(Alert.id).label("total"))
        .where(Alert.created_at >= since)
        .group_by(Alert.camera_id)
        .order_by(func.count(Alert.id).desc())
    )
    return [{"camera_id": row.camera_id, "total": row.total} for row in result.all()]
