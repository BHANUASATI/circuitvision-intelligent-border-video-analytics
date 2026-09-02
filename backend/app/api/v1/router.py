"""Aggregate all v1 API routers."""
from fastapi import APIRouter

from app.api.v1.endpoints.alerts import incidents_router, router as alerts_router
from app.api.v1.endpoints.analytics import router as analytics_router
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.cameras import router as cameras_router
from app.api.v1.endpoints.stream import router as stream_router
from app.api.v1.endpoints.users import router as users_router
from app.api.v1.endpoints.websocket import router as ws_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(cameras_router)
api_router.include_router(stream_router)
api_router.include_router(alerts_router)
api_router.include_router(incidents_router)
api_router.include_router(analytics_router)
api_router.include_router(ws_router)
