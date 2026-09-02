#!/usr/bin/env bash
# ============================================================
# IBVAP — Development Environment Setup
# Run once after cloning the repository
# ============================================================
set -euo pipefail

IBVAP_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$IBVAP_ROOT"

echo ""
echo "=============================="
echo " IBVAP Dev Setup"
echo "=============================="
echo ""

# 1. Copy env file
if [ ! -f .env ]; then
  cp .env.example .env
  echo "[✓] .env created — fill in secrets before deploying"
else
  echo "[·] .env already exists"
fi

# 2. Generate self-signed TLS cert for development
CERT_DIR="nginx/ssl"
if [ ! -f "$CERT_DIR/server.crt" ]; then
  echo "[·] Generating self-signed TLS certificate..."
  openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout "$CERT_DIR/server.key" \
    -out    "$CERT_DIR/server.crt" \
    -subj   "/C=IN/ST=JK/L=Jammu/O=IBVAP-DEV/CN=localhost" \
    2>/dev/null
  echo "[✓] TLS cert generated: $CERT_DIR/"
else
  echo "[·] TLS cert already exists"
fi

# 3. Create required data directories
mkdir -p \
  data/evidence \
  data/face_db/embeddings \
  data/face_db/metadata \
  data/plate_db \
  models/yolo \
  models/face \
  models/anpr

echo "[✓] Data directories created"

# 4. Pull and build Docker images
echo ""
echo "[·] Building Docker images (this takes a few minutes first time)..."
docker compose build --parallel

# 5. Start infrastructure services only (DB + Redis)
echo ""
echo "[·] Starting infrastructure services..."
docker compose up -d postgres redis

echo "[·] Waiting for PostgreSQL..."
until docker compose exec -T postgres pg_isready -U ibvap_user -d ibvap 2>/dev/null; do
  sleep 2
done
echo "[✓] PostgreSQL ready"

# 6. Run migrations
echo ""
echo "[·] Running database migrations..."
docker compose run --rm backend alembic upgrade head
echo "[✓] Migrations complete"

# 7. Seed the database
echo ""
echo "[·] Seeding database..."
docker compose run --rm -e PYTHONPATH=/app backend python /app/../scripts/seed.py || \
  echo "[!] Seed script not run from container — run manually if needed"

echo ""
echo "=============================="
echo " Setup complete!"
echo "=============================="
echo ""
echo "  Start all services:   docker compose up -d"
echo "  Dashboard URL:        https://localhost"
echo "  API docs:             https://localhost/docs  (set APP_DEBUG=true)"
echo "  Default credentials:  admin / Admin@1234"
echo ""
