# ============================================================
# IBVAP — Backend (FastAPI) Dockerfile
# Multi-stage: builder -> production
# Python 3.11-slim
# ============================================================

# ── Stage 1: builder ─────────────────────────────────────────
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /build
COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt


# ── Stage 2: production ───────────────────────────────────────
FROM python:3.11-slim AS production

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH="/app"

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /opt/venv /opt/venv

# Non-root user
RUN groupadd -r ibvap && useradd -r -g ibvap -u 1001 ibvap && \
    mkdir -p /app /data/evidence /var/log/ibvap && \
    chown -R ibvap:ibvap /app /data /var/log/ibvap

WORKDIR /app
COPY --chown=ibvap:ibvap . .

# entrypoint.sh is included in the COPY above
RUN chmod +x /app/entrypoint.sh && ln -s /app/entrypoint.sh /entrypoint.sh

USER ibvap

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

ENTRYPOINT ["/entrypoint.sh"]
