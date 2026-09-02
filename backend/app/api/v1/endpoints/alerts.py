"""Alert & Incident management endpoints."""
from __future__ import annotations

import uuid
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import get_db
from app.models.user import User
from app.schemas.alert import (
    AlertAcknowledge,
    AlertFilter,
    AlertOut,
    IncidentCreate,
    IncidentOut,
    IncidentUpdate,
)
from app.services.alert_service import (
    acknowledge_alert,
    create_incident,
    get_alert,
    get_alert_counts,
    list_alerts,
    list_incidents,
    update_incident,
)
from app.services.audit_service import log_action
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get("", response_model=List[AlertOut])
async def get_alerts(
    camera_id: Optional[str] = Query(None),
    event_type: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    from_ts: Optional[datetime] = Query(None),
    to_ts: Optional[datetime] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    filters = AlertFilter(
        camera_id=camera_id,
        event_type=event_type,
        severity=severity,
        status=status,
        from_ts=from_ts,
        to_ts=to_ts,
        page=page,
        page_size=page_size,
    )
    alerts = await list_alerts(db, filters)
    out = []
    for a in alerts:
        import json
        out.append(AlertOut(
            id=a.id,
            alert_id=a.alert_id,
            camera_id=a.camera_id,
            event_type=a.event_type,
            severity=a.severity,
            status=a.status,
            description=a.description,
            payload=json.loads(a.payload) if a.payload else {},
            evidence_path=a.evidence_path,
            evidence_hash=a.evidence_hash,
            created_at=a.created_at,
        ))
    return out


@router.get("/counts")
async def alert_counts(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return await get_alert_counts(db)


@router.get("/{alert_id}", response_model=AlertOut)
async def get_alert_detail(
    alert_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    import json
    alert = await get_alert(db, alert_id)
    if not alert:
        raise HTTPException(404, f"Alert not found: {alert_id}")
    return AlertOut(
        id=alert.id,
        alert_id=alert.alert_id,
        camera_id=alert.camera_id,
        event_type=alert.event_type,
        severity=alert.severity,
        status=alert.status,
        description=alert.description,
        payload=json.loads(alert.payload) if alert.payload else {},
        evidence_path=alert.evidence_path,
        evidence_hash=alert.evidence_hash,
        created_at=alert.created_at,
    )


@router.patch("/{alert_id}/acknowledge")
async def ack_alert(
    alert_id: str,
    data: AlertAcknowledge,
    db: AsyncSession = Depends(get_db),
    current: User = Depends(get_current_user),
):
    alert = await acknowledge_alert(db, alert_id, data.status, current.id)
    if not alert:
        raise HTTPException(404, f"Alert not found: {alert_id}")
    await log_action(
        db, "acknowledge_alert", "alert",
        resource_id=alert_id,
        user_id=current.id,
        detail={"status": data.status, "note": data.note},
    )
    return {"message": f"Alert {data.status}", "alert_id": alert_id}


# ── Incidents ─────────────────────────────────────────────────

incidents_router = APIRouter(prefix="/incidents", tags=["Incidents"])


@incidents_router.post("", response_model=IncidentOut)
async def create_incident_endpoint(
    data: IncidentCreate,
    db: AsyncSession = Depends(get_db),
    current: User = Depends(get_current_user),
):
    incident = await create_incident(db, data)
    await log_action(db, "create_incident", "incident", resource_id=str(incident.id), user_id=current.id)
    return incident


@incidents_router.get("", response_model=List[IncidentOut])
async def get_incidents(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return await list_incidents(db, skip, limit)


@incidents_router.patch("/{incident_id}", response_model=IncidentOut)
async def update_incident_endpoint(
    incident_id: uuid.UUID,
    data: IncidentUpdate,
    db: AsyncSession = Depends(get_db),
    current: User = Depends(get_current_user),
):
    incident = await update_incident(db, incident_id, data)
    if not incident:
        raise HTTPException(404, f"Incident not found: {incident_id}")
    await log_action(db, "update_incident", "incident", resource_id=str(incident_id), user_id=current.id)
    return incident
