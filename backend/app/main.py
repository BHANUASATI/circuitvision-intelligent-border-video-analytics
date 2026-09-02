"""
IBVAP Backend — FastAPI Application Entry Point
"""
from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.logger import logger
from app.db.base import Base, engine
from app.db.redis import close_redis, get_redis
from app.services.websocket_manager import redis_alert_subscriber


# ── Rate Limiter ──────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address)


# ── Lifespan ──────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Backend starting up...")

    # Run DB migrations / create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.success("Database tables ready")

    # Verify Redis
    try:
        r = await get_redis()
        await r.ping()
        logger.success("Redis connected")
    except Exception as exc:
        logger.warning(f"Redis unavailable at startup: {exc}")

    # Start Redis → WebSocket alert subscriber
    subscriber_task = asyncio.create_task(
        redis_alert_subscriber(),
        name="redis-alert-subscriber",
    )

    yield  # application serves traffic

    # Shutdown
    subscriber_task.cancel()
    try:
        await subscriber_task
    except asyncio.CancelledError:
        pass
    await close_redis()
    await engine.dispose()
    logger.info("Backend shutdown complete")


# ── Application ───────────────────────────────────────────────

app = FastAPI(
    title=settings.app_title,
    description=(
        "IBVAP — Intelligent Border Video Analytics Platform. "
        "REST API for camera management, AI analytics, alerting, and RBAC."
    ),
    version=settings.app_version,
    docs_url="/docs" if settings.app_debug else None,
    redoc_url="/redoc" if settings.app_debug else None,
    openapi_url="/openapi.json" if settings.app_debug else None,
    lifespan=lifespan,
)

# ── Middleware ────────────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Prometheus Metrics ────────────────────────────────────────
Instrumentator(
    should_group_status_codes=True,
    should_ignore_untemplated=True,
).instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)

# ── Routes ────────────────────────────────────────────────────
app.include_router(api_router)


# ── Health ────────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "service": "ibvap-backend", "version": settings.app_version}


@app.get("/", include_in_schema=False)
async def root():
    return JSONResponse({"service": "IBVAP Backend", "status": "running"})


# ── Global exception handler ──────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


# ── Entrypoint ────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.app_debug,
        loop="uvloop",
    )
