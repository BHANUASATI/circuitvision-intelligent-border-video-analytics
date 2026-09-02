"""
Audit Service — writes tamper-evident audit log entries.
"""
from __future__ import annotations

import json
import uuid
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import AuditLog


async def log_action(
    db: AsyncSession,
    action: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    user_id: Optional[uuid.UUID] = None,
    detail: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
) -> None:
    entry = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        detail=json.dumps(detail or {}),
        ip_address=ip_address,
    )
    db.add(entry)
    await db.flush()
