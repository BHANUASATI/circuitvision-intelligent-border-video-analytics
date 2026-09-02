"""
Alert Service — ingest, persist, query alerts.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert, AlertStatus, Incident, IncidentAlert
from app.schemas.alert import AlertFilter, IncidentCreate, IncidentUpdate


# ── Alert CRUD ────────────────────────────────────────────────

async def ingest_alert(db: AsyncSession, raw: dict) -> Alert:
    """Persist a raw alert dict received from Redis pub/sub."""
    data = raw.get("data", {})
    severity = data.get("severity", "MEDIUM")
    # Map event_type -> severity heuristic
    event_type = raw.get("event_type", "unknown")
    if event_type in ("intrusion", "face_alert", "night_movement"):
        severity = "HIGH"
    elif event_type in ("anpr",) and data.get("is_watchlisted"):
        severity = "HIGH"

    alert = Alert(
        alert_id=raw.get("alert_id", str(uuid.uuid4())),
        camera_id=raw.get("camera_id", "unknown"),
        event_type=event_type,
        severity=severity,
        description=data.get("description", event_type.replace("_", " ").title()),
        payload=json.dumps(data),
        status=AlertStatus.NEW,
    )
    db.add(alert)
    await db.flush()
    await db.refresh(alert)
    return alert


async def get_alert(db: AsyncSession, alert_id: str) -> Optional[Alert]:
    result = await db.execute(select(Alert).where(Alert.alert_id == alert_id))
    return result.scalar_one_or_none()


async def list_alerts(db: AsyncSession, filters: AlertFilter) -> List[Alert]:
    q = select(Alert).order_by(desc(Alert.created_at))

    conditions = []
    if filters.camera_id:
        conditions.append(Alert.camera_id == filters.camera_id)
    if filters.event_type:
        conditions.append(Alert.event_type == filters.event_type)
    if filters.severity:
        conditions.append(Alert.severity == filters.severity)
    if filters.status:
        conditions.append(Alert.status == filters.status)
    if filters.from_ts:
        conditions.append(Alert.created_at >= filters.from_ts)
    if filters.to_ts:
        conditions.append(Alert.created_at <= filters.to_ts)

    if conditions:
        q = q.where(and_(*conditions))

    offset = (filters.page - 1) * filters.page_size
    q = q.offset(offset).limit(filters.page_size)
    result = await db.execute(q)
    return list(result.scalars().all())


async def acknowledge_alert(
    db: AsyncSession,
    alert_id: str,
    status: str,
    user_id: uuid.UUID,
) -> Optional[Alert]:
    alert = await get_alert(db, alert_id)
    if not alert:
        return None
    alert.status = status
    alert.acknowledged_by = user_id
    alert.acknowledged_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(alert)
    return alert


async def get_alert_counts(db: AsyncSession) -> dict:
    """Dashboard summary counts."""
    from sqlalchemy import func
    result = await db.execute(
        select(Alert.severity, func.count(Alert.id))
        .where(Alert.status == AlertStatus.NEW)
        .group_by(Alert.severity)
    )
    rows = result.all()
    counts = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
    for severity, count in rows:
        counts[severity] = count
    return counts


# ── Incident CRUD ─────────────────────────────────────────────

async def create_incident(db: AsyncSession, data: IncidentCreate) -> Incident:
    incident = Incident(
        title=data.title,
        description=data.description,
        severity=data.severity,
        camera_id=data.camera_id,
    )
    db.add(incident)
    await db.flush()

    # Link alerts
    for alert_uuid in data.alert_ids:
        link = IncidentAlert(incident_id=incident.id, alert_id=alert_uuid)
        db.add(link)
    await db.flush()
    await db.refresh(incident)
    return incident


async def list_incidents(db: AsyncSession, skip: int = 0, limit: int = 50) -> List[Incident]:
    result = await db.execute(
        select(Incident).order_by(desc(Incident.created_at)).offset(skip).limit(limit)
    )
    return list(result.scalars().all())


async def update_incident(
    db: AsyncSession, incident_id: uuid.UUID, data: IncidentUpdate
) -> Optional[Incident]:
    result = await db.execute(select(Incident).where(Incident.id == incident_id))
    incident = result.scalar_one_or_none()
    if not incident:
        return None
    for k, v in data.model_dump(exclude_none=True).items():
        setattr(incident, k, v)
    if data.status == "resolved" and not incident.resolved_at:
        incident.resolved_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(incident)
    return incident
