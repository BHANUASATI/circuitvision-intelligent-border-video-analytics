"""Initial schema — roles, users, audit_logs, cameras, alerts, incidents

Revision ID: 0001
Revises:
Create Date: 2026-09-02 00:00:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── roles ──────────────────────────────────────────────────
    op.create_table(
        "roles",
        sa.Column("id",          postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name",        sa.String(50),  unique=True, nullable=False),
        sa.Column("description", sa.Text,        server_default=""),
        sa.Column("permissions", sa.Text,        server_default="[]"),
        sa.Column("created_at",  sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
    )

    # ── users ──────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id",              postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("username",        sa.String(64),  unique=True, nullable=False),
        sa.Column("email",           sa.String(255), unique=True, nullable=False),
        sa.Column("full_name",       sa.String(255), server_default=""),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("is_active",       sa.Boolean,     server_default=sa.text("true")),
        sa.Column("is_superuser",    sa.Boolean,     server_default=sa.text("false")),
        sa.Column("role_id",         postgresql.UUID(as_uuid=True), sa.ForeignKey("roles.id"), nullable=True),
        sa.Column("last_login",      sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at",      sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.Column("updated_at",      sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
    )
    op.create_index("ix_users_username", "users", ["username"])
    op.create_index("ix_users_email",    "users", ["email"])

    # ── audit_logs ─────────────────────────────────────────────
    op.create_table(
        "audit_logs",
        sa.Column("id",            postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id",       postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("action",        sa.String(100), nullable=False),
        sa.Column("resource_type", sa.String(100), nullable=False),
        sa.Column("resource_id",   sa.String(255), nullable=True),
        sa.Column("detail",        sa.Text, server_default="{}"),
        sa.Column("ip_address",    sa.String(45),  nullable=True),
        sa.Column("timestamp",     sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
    )
    op.create_index("ix_audit_logs_timestamp", "audit_logs", ["timestamp"])

    # ── cameras ────────────────────────────────────────────────
    op.create_table(
        "cameras",
        sa.Column("id",                      postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("camera_id",               sa.String(64),  unique=True, nullable=False),
        sa.Column("name",                    sa.String(255), nullable=False),
        sa.Column("stream_url",              sa.Text,        nullable=False),
        sa.Column("location",                sa.String(255), server_default=""),
        sa.Column("latitude",                sa.Float,       nullable=True),
        sa.Column("longitude",               sa.Float,       nullable=True),
        sa.Column("enable_detection",        sa.Boolean, server_default=sa.text("true")),
        sa.Column("enable_face_recognition", sa.Boolean, server_default=sa.text("true")),
        sa.Column("enable_anpr",             sa.Boolean, server_default=sa.text("true")),
        sa.Column("enable_intrusion",        sa.Boolean, server_default=sa.text("true")),
        sa.Column("enable_activity",         sa.Boolean, server_default=sa.text("true")),
        sa.Column("frame_skip",              sa.Integer, server_default="2"),
        sa.Column("is_active",               sa.Boolean, server_default=sa.text("true")),
        sa.Column("is_streaming",            sa.Boolean, server_default=sa.text("false")),
        sa.Column("created_at",              sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.Column("updated_at",              sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
    )
    op.create_index("ix_cameras_camera_id", "cameras", ["camera_id"])

    # ── alerts ─────────────────────────────────────────────────
    op.create_table(
        "alerts",
        sa.Column("id",               postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("alert_id",         sa.String(64),  unique=True, nullable=False),
        sa.Column("camera_id",        sa.String(64),  sa.ForeignKey("cameras.camera_id"), nullable=False),
        sa.Column("event_type",       sa.String(100), nullable=False),
        sa.Column("severity",         sa.String(20),  server_default="MEDIUM"),
        sa.Column("status",           sa.String(30),  server_default="new"),
        sa.Column("description",      sa.Text,        server_default=""),
        sa.Column("payload",          sa.Text,        server_default="{}"),
        sa.Column("evidence_path",    sa.Text,        nullable=True),
        sa.Column("evidence_hash",    sa.String(64),  nullable=True),
        sa.Column("acknowledged_by",  postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("acknowledged_at",  sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at",       sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.Column("updated_at",       sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
    )
    op.create_index("ix_alerts_alert_id",    "alerts", ["alert_id"])
    op.create_index("ix_alerts_camera_id",   "alerts", ["camera_id"])
    op.create_index("ix_alerts_event_type",  "alerts", ["event_type"])
    op.create_index("ix_alerts_severity",    "alerts", ["severity"])
    op.create_index("ix_alerts_status",      "alerts", ["status"])
    op.create_index("ix_alerts_created_at",  "alerts", ["created_at"])

    # ── incidents ──────────────────────────────────────────────
    op.create_table(
        "incidents",
        sa.Column("id",          postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("title",       sa.String(255), nullable=False),
        sa.Column("description", sa.Text, server_default=""),
        sa.Column("severity",    sa.String(20), server_default="MEDIUM"),
        sa.Column("status",      sa.String(30), server_default="open"),
        sa.Column("camera_id",   sa.String(64), sa.ForeignKey("cameras.camera_id"), nullable=True),
        sa.Column("assigned_to", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at",  sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.Column("updated_at",  sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_incidents_status",     "incidents", ["status"])
    op.create_index("ix_incidents_created_at", "incidents", ["created_at"])

    # ── incident_alerts (junction) ─────────────────────────────
    op.create_table(
        "incident_alerts",
        sa.Column("incident_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("incidents.id"), primary_key=True),
        sa.Column("alert_id",    postgresql.UUID(as_uuid=True), sa.ForeignKey("alerts.id"),    primary_key=True),
    )


def downgrade() -> None:
    op.drop_table("incident_alerts")
    op.drop_table("incidents")
    op.drop_table("alerts")
    op.drop_table("cameras")
    op.drop_table("audit_logs")
    op.drop_table("users")
    op.drop_table("roles")
