"""User management endpoints (admin only)."""
from __future__ import annotations

import json
import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.db.base import get_db
from app.models.user import Role, User
from app.schemas.user import RoleCreate, RoleOut, UserCreate, UserOut, UserUpdate
from app.services.audit_service import log_action
from app.services.auth_service import get_current_user, get_superuser

router = APIRouter(prefix="/users", tags=["Users"])


# ── Users ─────────────────────────────────────────────────────

@router.post("", response_model=UserOut)
async def create_user(
    data: UserCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_superuser),
):
    # Check duplicate
    result = await db.execute(select(User).where(User.username == data.username))
    if result.scalar_one_or_none():
        raise HTTPException(409, f"Username already exists: {data.username}")

    user = User(
        username=data.username,
        email=data.email,
        full_name=data.full_name,
        hashed_password=hash_password(data.password),
        role_id=data.role_id,
    )
    db.add(user)
    await db.flush()
    await log_action(db, "create_user", "user", resource_id=str(user.id))
    await db.refresh(user)
    return user


@router.get("", response_model=List[UserOut])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_superuser),
):
    result = await db.execute(select(User).offset(skip).limit(limit))
    return list(result.scalars().all())


@router.get("/{user_id}", response_model=UserOut)
async def get_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current: User = Depends(get_current_user),
):
    if str(current.id) != str(user_id) and not current.is_superuser:
        raise HTTPException(403, "Forbidden")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User not found")
    return user


@router.patch("/{user_id}", response_model=UserOut)
async def update_user(
    user_id: uuid.UUID,
    data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_superuser),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User not found")
    for k, v in data.model_dump(exclude_none=True).items():
        setattr(user, k, v)
    await db.flush()
    await log_action(db, "update_user", "user", resource_id=str(user_id))
    await db.refresh(user)
    return user


@router.delete("/{user_id}")
async def delete_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_superuser),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User not found")
    await db.delete(user)
    await log_action(db, "delete_user", "user", resource_id=str(user_id))
    return {"message": "User deleted"}


# ── Roles ─────────────────────────────────────────────────────

@router.post("/roles", response_model=RoleOut, tags=["Roles"])
async def create_role(
    data: RoleCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_superuser),
):
    role = Role(
        name=data.name,
        description=data.description,
        permissions=json.dumps(data.permissions),
    )
    db.add(role)
    await db.flush()
    await db.refresh(role)
    return _role_out(role)


@router.get("/roles", response_model=List[RoleOut], tags=["Roles"])
async def list_roles(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(select(Role))
    return [_role_out(r) for r in result.scalars().all()]


def _role_out(role: Role) -> dict:
    return {
        "id": role.id,
        "name": role.name,
        "description": role.description,
        "permissions": json.loads(role.permissions) if role.permissions else [],
        "created_at": role.created_at,
    }
