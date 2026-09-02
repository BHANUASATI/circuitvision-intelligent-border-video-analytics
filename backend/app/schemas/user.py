"""User + Auth Pydantic schemas."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


# ── Auth ──────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class RefreshRequest(BaseModel):
    refresh_token: str


# ── User ──────────────────────────────────────────────────────

class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    email: EmailStr
    full_name: str = ""
    password: str = Field(min_length=8)
    role_id: Optional[uuid.UUID] = None


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None
    role_id: Optional[uuid.UUID] = None


class UserOut(BaseModel):
    id: uuid.UUID
    username: str
    email: str
    full_name: str
    is_active: bool
    is_superuser: bool
    role_id: Optional[uuid.UUID]
    last_login: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8)


# ── Role ──────────────────────────────────────────────────────

class RoleCreate(BaseModel):
    name: str = Field(min_length=2, max_length=50)
    description: str = ""
    permissions: List[str] = []


class RoleOut(BaseModel):
    id: uuid.UUID
    name: str
    description: str
    permissions: List[str]
    created_at: datetime

    model_config = {"from_attributes": True}
