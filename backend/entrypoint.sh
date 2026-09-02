#!/bin/sh
# Backend entrypoint — run Alembic migrations then start server

set -e

echo "Running database migrations..."
alembic upgrade head

echo "Starting IBVAP backend..."
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 2 \
    --loop uvloop \
    --log-level info
