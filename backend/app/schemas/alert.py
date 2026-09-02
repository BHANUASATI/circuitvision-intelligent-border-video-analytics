"""Alert + Incident Pydantic schemas."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class AlertOut(BaseModel):
    id: uuid.UUID
    alert_id: str
    camera_id: str
    event_type: str
    severity: str
    status: str
    description: str
    payload: Dict[str, Any]
    evidence_path: Optional[str]
    evidence_hash: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class AlertAcknowledge(BaseModel):
    status: str   # acknowledged | resolved | false_positive
    note: Optional[str] = None


class AlertFilter(BaseModel):
    camera_id: Optional[str] = None
    event_type: Optional[str] = None
    severity: Optional[str] = None
    status: Optional[str] = None
    from_ts: Optional[datetime] = None
    to_ts: Optional[datetime] = None
    page: int = 1
    page_size: int = 50


class IncidentCreate(BaseModel):
    title: str
    description: str = ""
    severity: str = "MEDIUM"
    camera_id: Optional[str] = None
    alert_ids: List[uuid.UUID] = []


class IncidentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    severity: Optional[str] = None
    status: Optional[str] = None
    assigned_to: Optional[uuid.UUID] = None


class IncidentOut(BaseModel):
    id: uuid.UUID
    title: str
    description: str
    severity: str
    status: str
    camera_id: Optional[str]
    assigned_to: Optional[uuid.UUID]
    created_at: datetime
    resolved_at: Optional[datetime]

    model_config = {"from_attributes": True}
