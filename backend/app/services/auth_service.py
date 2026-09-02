"""
Auth Service — login, token refresh, current user resolution.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from app.db.base import get_db
from app.models.user import User
from app.schemas.user import TokenResponse

bearer_scheme = HTTPBearer()


async def authenticate_user(
    username: str,
    password: str,
    db: AsyncSession,
) -> Optional[User]:
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(password, user.hashed_password):
        return None
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")
    # Update last login
    user.last_login = datetime.now(timezone.utc)
    await db.flush()
    return user


def build_tokens(user: User) -> TokenResponse:
    extra = {"role": str(user.role_id) if user.role_id else None, "su": user.is_superuser}
    access = create_access_token(str(user.id), extra=extra)
    refresh = create_refresh_token(str(user.id))
    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        token_type="bearer",
        expires_in=settings.jwt_access_token_expire_minutes * 60,
    )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    token = credentials.credentials
    try:
        payload = decode_token(token)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Wrong token type")

    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    return user


async def get_superuser(current: User = Depends(get_current_user)) -> User:
    if not current.is_superuser:
        raise HTTPException(status_code=403, detail="Superuser access required")
    return current


def require_permission(permission: str):
    """Dependency factory — checks user role has the given permission string."""
    async def checker(
        current: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> User:
        if current.is_superuser:
            return current
        if not current.role_id:
            raise HTTPException(403, "No role assigned")
        from app.models.user import Role
        result = await db.execute(select(Role).where(Role.id == current.role_id))
        role = result.scalar_one_or_none()
        if not role:
            raise HTTPException(403, "Role not found")
        perms: list = json.loads(role.permissions) if role.permissions else []
        if permission not in perms:
            raise HTTPException(403, f"Permission denied: {permission}")
        return current
    return checker
