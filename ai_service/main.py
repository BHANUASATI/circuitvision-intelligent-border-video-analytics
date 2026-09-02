"""
IBVAP — AI Service Entry Point
FastAPI application serving AI/CV analytics APIs.
"""
from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from ai_service.api.routes import router as ai_router
from ai_service.configs.settings import settings
from ai_service.core.stream_manager import stream_manager
from ai_service.utils.logger import logger
from ai_service.utils.redis_client import close_redis, get_redis


# ── Lifespan ──────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("AI Service starting up...")

    # Warm up Redis connection
    try:
        r = await get_redis()
        await r.ping()
        logger.success("Redis connection established")
    except Exception as exc:
        logger.warning(f"Redis not available at startup: {exc}")

    yield  # application runs

    logger.info("AI Service shutting down — stopping all streams...")
    await stream_manager.stop_all()
    await close_redis()
    logger.info("AI Service shutdown complete")


# ── Application ───────────────────────────────────────────────

app = FastAPI(
    title="IBVAP AI Service",
    description="AI/CV analytics microservice for Intelligent Border Video Analytics Platform",
    version=settings.app_version if hasattr(settings, "app_version") else "1.0.0",
    docs_url="/docs" if settings.app_debug else None,
    redoc_url="/redoc" if settings.app_debug else None,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routes
app.include_router(ai_router, prefix="/api/v1", tags=["AI Analytics"])


# ── Health Check ──────────────────────────────────────────────

@app.get("/health", tags=["Health"])
async def health_check():
    streams = stream_manager.get_all_stats()
    return {
        "status": "ok",
        "service": "ibvap-ai-service",
        "active_streams": len(streams),
        "streams": [
            {"camera_id": s.camera_id, "status": s.status, "fps": s.fps}
            for s in streams
        ],
    }


@app.get("/", include_in_schema=False)
async def root():
    return JSONResponse({"service": "IBVAP AI Service", "status": "running"})


# ── Entrypoint ────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "ai_service.main:app",
        host=settings.service_host,
        port=settings.service_port,
        reload=settings.app_debug,
        workers=1,        # single worker — GPU is not fork-safe
        loop="uvloop",
    )
