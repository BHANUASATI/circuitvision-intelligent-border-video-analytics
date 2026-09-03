#!/bin/sh
# Backend entrypoint — run Alembic migrations then start server
set -e

# Railway provides DATABASE_URL as postgresql:// — fix for asyncpg
if [ -n "$DATABASE_URL" ]; then
  export DATABASE_URL=$(echo "$DATABASE_URL" | sed 's|^postgresql://|postgresql+asyncpg://|')
fi

echo "Running database migrations..."
alembic upgrade head

echo "Starting IBVAP backend..."
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port ${PORT:-8080} \
    --workers 1 \
    --loop uvloop \
    --log-level info
