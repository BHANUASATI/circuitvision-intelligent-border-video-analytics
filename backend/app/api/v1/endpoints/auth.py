"""Auth endpoints — login, refresh, logout, me."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token, hash_password
from app.db.base import get_db
from app.models.user import User
from app.schemas.user import (
    ChangePasswordRequest,
    LoginRequest,
    RefreshRequest,
    TokenResponse,
    UserOut,
)
from app.services.audit_service import log_action
from app.services.auth_service import authenticate_user, build_tokens, get_current_user

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=TokenResponse)
async def login(
    req: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    user = await authenticate_user(req.username, req.password, db)
    if not user:
        await log_action(
            db, "login_failed", "auth",
            resource_id=req.username,
            ip_address=request.client.host if request.client else None,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    tokens = build_tokens(user)
    await log_action(
        db, "login", "auth",
        user_id=user.id,
        resource_id=str(user.id),
        ip_address=request.client.host if request.client else None,
    )
    return tokens


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(req: RefreshRequest, db: AsyncSession = Depends(get_db)):
    try:
        payload = decode_token(req.refresh_token)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Wrong token type")

    result = await db.execute(select(User).where(User.id == payload["sub"]))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found")
    return build_tokens(user)


@router.get("/me", response_model=UserOut)
async def me(current: User = Depends(get_current_user)):
    return current


@router.post("/change-password")
async def change_password(
    req: ChangePasswordRequest,
    current: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.core.security import verify_password
    if not verify_password(req.current_password, current.hashed_password):
        raise HTTPException(400, "Current password incorrect")
    current.hashed_password = hash_password(req.new_password)
    await db.flush()
    await log_action(db, "change_password", "user", user_id=current.id, resource_id=str(current.id))
    return {"message": "Password changed successfully"}
