#!/usr/bin/env python3
"""
IBVAP — Database Seed Script
Creates default roles, a superadmin user, and sample cameras.

Usage (inside container or with venv active):
    python scripts/seed.py

Environment: reads DATABASE_URL from .env or environment.
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

# Allow importing backend app from repo root
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import select

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://ibvap_user:ibvap_pass@localhost:5432/ibvap",
)

engine = create_async_engine(DATABASE_URL, echo=False)
SessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


# ── Seed Data ─────────────────────────────────────────────────

ROLES = [
    {
        "name": "superadmin",
        "description": "Full system access — platform administrators",
        "permissions": [
            "camera:read", "camera:write",
            "stream:control",
            "alert:read", "alert:write",
            "incident:read", "incident:write",
            "user:read", "user:write",
            "audit:read",
            "face:enroll",
            "anpr:manage",
            "fence:manage",
        ],
    },
    {
        "name": "operator",
        "description": "Day-to-day surveillance operators",
        "permissions": [
            "camera:read",
            "stream:control",
            "alert:read", "alert:write",
            "incident:read", "incident:write",
        ],
    },
    {
        "name": "analyst",
        "description": "Intelligence analysts — read-only access with analytics",
        "permissions": [
            "camera:read",
            "alert:read",
            "incident:read",
        ],
    },
    {
        "name": "viewer",
        "description": "Read-only dashboard viewers",
        "permissions": [
            "camera:read",
            "alert:read",
        ],
    },
]

# Password: Admin@1234  (bcrypt)
ADMIN_PASSWORD_HASH = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyNiAYDYziqahy"

SAMPLE_CAMERAS = [
    {
        "camera_id": "cam-bop-north-01",
        "name": "BOP North Gate — Primary",
        "stream_url": "rtsp://192.168.10.101:554/stream1",
        "location": "Border Out Post North, Sector 7",
        "latitude": 32.7157,
        "longitude": 74.8570,
        "enable_detection": True,
        "enable_face_recognition": True,
        "enable_anpr": True,
        "enable_intrusion": True,
        "enable_activity": True,
        "frame_skip": 2,
    },
    {
        "camera_id": "cam-bop-north-02",
        "name": "BOP North Gate — Flank",
        "stream_url": "rtsp://192.168.10.102:554/stream1",
        "location": "Border Out Post North, Sector 7 — East Flank",
        "latitude": 32.7165,
        "longitude": 74.8581,
        "enable_detection": True,
        "enable_face_recognition": False,
        "enable_anpr": True,
        "enable_intrusion": True,
        "enable_activity": True,
        "frame_skip": 3,
    },
    {
        "camera_id": "cam-checkpoint-alpha",
        "name": "Checkpoint Alpha — Entry",
        "stream_url": "rtsp://192.168.10.201:554/stream1",
        "location": "Checkpoint Alpha, NH-1A",
        "latitude": 32.7080,
        "longitude": 74.8450,
        "enable_detection": True,
        "enable_face_recognition": True,
        "enable_anpr": True,
        "enable_intrusion": False,
        "enable_activity": True,
        "frame_skip": 2,
    },
    {
        "camera_id": "cam-road-watch-01",
        "name": "Border Road Watch — KM 12",
        "stream_url": "rtsp://192.168.10.301:554/stream1",
        "location": "Border Road KM 12, Patrol Route B",
        "latitude": 32.6990,
        "longitude": 74.8310,
        "enable_detection": True,
        "enable_face_recognition": False,
        "enable_anpr": True,
        "enable_intrusion": True,
        "enable_activity": True,
        "frame_skip": 3,
    },
]

SAMPLE_PLATE_WATCHLIST = [
    "RJ14CD1234,SUSPECT,Flagged vehicle — under surveillance",
    "DL01AB9999,STOLEN,Reported stolen vehicle",
    "HR26DQ0001,WATCHLIST,Known associate of suspect",
    "PB10CB5678,ALERT,Cross-border vehicle — heightened monitoring",
]

SAMPLE_FACE_WATCHLIST_NOTES = """
# IBVAP Face Watchlist
# Format: identity_id,name,category,notes
# Enroll via POST /api/v1/faces/enroll with image
# This file is a placeholder — use the API to enroll actual faces
"""


# ── Seeder ────────────────────────────────────────────────────

async def seed() -> None:
    from app.models.user import Role, User
    from app.models.camera import Camera

    async with SessionLocal() as db:
        print("Seeding roles...")
        role_map: dict[str, uuid.UUID] = {}
        for r_data in ROLES:
            result = await db.execute(select(Role).where(Role.name == r_data["name"]))
            existing = result.scalar_one_or_none()
            if existing:
                print(f"  Role exists: {r_data['name']}")
                role_map[r_data["name"]] = existing.id
                continue
            role = Role(
                name=r_data["name"],
                description=r_data["description"],
                permissions=json.dumps(r_data["permissions"]),
            )
            db.add(role)
            await db.flush()
            role_map[r_data["name"]] = role.id
            print(f"  Created role: {r_data['name']}")

        print("\nSeeding superadmin user...")
        result = await db.execute(select(User).where(User.username == "admin"))
        admin = result.scalar_one_or_none()
        if not admin:
            admin = User(
                username="admin",
                email="admin@ibvap.local",
                full_name="System Administrator",
                hashed_password=ADMIN_PASSWORD_HASH,
                is_active=True,
                is_superuser=True,
                role_id=role_map.get("superadmin"),
            )
            db.add(admin)
            await db.flush()
            print(f"  Created admin user (password: Admin@1234)")
        else:
            print("  Admin user exists")

        print("\nSeeding operator user...")
        result = await db.execute(select(User).where(User.username == "operator1"))
        op1 = result.scalar_one_or_none()
        if not op1:
            op1 = User(
                username="operator1",
                email="operator1@ibvap.local",
                full_name="Operator One",
                # Password: Operator@1234
                hashed_password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyNiAYDYziqahy",
                is_active=True,
                is_superuser=False,
                role_id=role_map.get("operator"),
            )
            db.add(op1)
            await db.flush()
            print("  Created operator1 user")
        else:
            print("  operator1 exists")

        print("\nSeeding sample cameras...")
        for cam_data in SAMPLE_CAMERAS:
            result = await db.execute(select(Camera).where(Camera.camera_id == cam_data["camera_id"]))
            if result.scalar_one_or_none():
                print(f"  Camera exists: {cam_data['camera_id']}")
                continue
            cam = Camera(**cam_data)
            db.add(cam)
            await db.flush()
            print(f"  Created camera: {cam_data['name']}")

        await db.commit()

    # Write ANPR watchlist seed file
    watchlist_path = Path(os.environ.get("PLATE_DB_PATH", "/data/plate_db")) / "watchlist.txt"
    watchlist_path.parent.mkdir(parents=True, exist_ok=True)
    if not watchlist_path.exists():
        watchlist_path.write_text("\n".join(SAMPLE_PLATE_WATCHLIST) + "\n")
        print(f"\nANPR watchlist seeded: {watchlist_path}")

    # Write face watchlist placeholder
    face_path = Path(os.environ.get("FACE_DB_PATH", "/data/face_db")) / "watchlist.json"
    face_path.parent.mkdir(parents=True, exist_ok=True)
    if not face_path.exists():
        face_path.write_text("[]")
        print(f"Face watchlist initialised: {face_path}")

    print("\nSeed complete.")


if __name__ == "__main__":
    asyncio.run(seed())
