-- ============================================================
-- IBVAP — PostgreSQL Initialisation Script
-- Runs once on first container startup via docker-entrypoint-initdb.d
-- ============================================================

-- Enable useful extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";   -- fuzzy text search on plates / names
CREATE EXTENSION IF NOT EXISTS "btree_gin"; -- composite GIN indexes

-- ── Performance indexes (Alembic creates tables; we add extra indexes here) ──

-- Alerts: most common query patterns
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_alerts_camera_created
    ON alerts (camera_id, created_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_alerts_status_severity
    ON alerts (status, severity);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_alerts_event_type
    ON alerts (event_type, created_at DESC);

-- Full-text search on alert description
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_alerts_description_gin
    ON alerts USING gin (description gin_trgm_ops);

-- Incidents
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_incidents_status_created
    ON incidents (status, created_at DESC);

-- Audit log
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_user_action
    ON audit_logs (user_id, action, timestamp DESC);

-- ── Row-level security policies ──────────────────────────────
-- (Enforced in application layer; DB policies as defence-in-depth)

ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

-- Superuser can do everything; other DB roles are read-only on audit_logs
CREATE POLICY audit_superuser_policy ON audit_logs
    USING (current_user = 'ibvap_user');
