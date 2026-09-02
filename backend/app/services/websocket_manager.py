"""
WebSocket Connection Manager
Broadcasts real-time alerts to connected dashboard clients.
Subscribes to Redis pub/sub channel published by the AI service.
"""
from __future__ import annotations

import asyncio
import json
from typing import Dict, Optional, Set

from fastapi import WebSocket, WebSocketDisconnect

from app.core.config import settings
from app.core.logger import logger
from app.db.redis import get_redis


class ConnectionManager:
    """
    Manages authenticated WebSocket connections.
    Supports per-camera subscriptions and broadcast to all.
    """

    def __init__(self) -> None:
        # user_id -> set of WebSocket connections
        self._connections: Dict[str, Set[WebSocket]] = {}
        # camera_id -> set of subscribed user WebSockets
        self._subscriptions: Dict[str, Set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, user_id: str) -> None:
        await websocket.accept()
        async with self._lock:
            if user_id not in self._connections:
                self._connections[user_id] = set()
            self._connections[user_id].add(websocket)
        logger.info(f"WS connected: user={user_id} total={self._total_connections()}")

    async def disconnect(self, websocket: WebSocket, user_id: str) -> None:
        async with self._lock:
            if user_id in self._connections:
                self._connections[user_id].discard(websocket)
                if not self._connections[user_id]:
                    del self._connections[user_id]
            # Remove from all subscriptions
            for subs in self._subscriptions.values():
                subs.discard(websocket)
        logger.info(f"WS disconnected: user={user_id}")

    async def subscribe_camera(self, websocket: WebSocket, camera_id: str) -> None:
        async with self._lock:
            if camera_id not in self._subscriptions:
                self._subscriptions[camera_id] = set()
            self._subscriptions[camera_id].add(websocket)

    async def unsubscribe_camera(self, websocket: WebSocket, camera_id: str) -> None:
        async with self._lock:
            if camera_id in self._subscriptions:
                self._subscriptions[camera_id].discard(websocket)

    async def broadcast(self, message: dict) -> None:
        """Send to all connected clients."""
        data = json.dumps(message)
        dead: list = []
        all_sockets: Set[WebSocket] = set()
        for sockets in self._connections.values():
            all_sockets.update(sockets)
        for ws in all_sockets:
            try:
                await ws.send_text(data)
            except Exception:
                dead.append(ws)
        # Clean up dead connections
        for ws in dead:
            for sockets in self._connections.values():
                sockets.discard(ws)

    async def broadcast_to_camera(self, camera_id: str, message: dict) -> None:
        """Send only to clients subscribed to a specific camera."""
        subs = self._subscriptions.get(camera_id, set())
        if not subs:
            await self.broadcast(message)   # fallback: broadcast to all
            return
        data = json.dumps(message)
        for ws in list(subs):
            try:
                await ws.send_text(data)
            except Exception:
                subs.discard(ws)

    def _total_connections(self) -> int:
        return sum(len(s) for s in self._connections.values())


# Singleton
ws_manager = ConnectionManager()


# ── Redis Subscriber ──────────────────────────────────────────

async def redis_alert_subscriber() -> None:
    """
    Long-running background task.
    Subscribes to the AI service's Redis alert channel and
    forwards each alert to connected WebSocket clients + DB ingestion.
    """
    from app.db.base import AsyncSessionLocal
    from app.services.alert_service import ingest_alert

    logger.info("Redis alert subscriber starting...")
    while True:
        try:
            r = await get_redis()
            pubsub = r.pubsub()
            await pubsub.subscribe("ibvap:alerts")
            logger.success("Subscribed to ibvap:alerts")

            async for message in pubsub.listen():
                if message["type"] != "message":
                    continue
                try:
                    alert_data = json.loads(message["data"])
                except json.JSONDecodeError:
                    continue

                # Persist to DB
                try:
                    async with AsyncSessionLocal() as db:
                        alert = await ingest_alert(db, alert_data)
                        await db.commit()
                        alert_data["db_id"] = str(alert.id)
                        alert_data["severity"] = alert.severity
                except Exception as exc:
                    logger.error(f"Alert DB persist failed: {exc}")

                # Push to WebSocket clients
                camera_id = alert_data.get("camera_id", "")
                await ws_manager.broadcast_to_camera(camera_id, {
                    "type": "alert",
                    "payload": alert_data,
                })

        except asyncio.CancelledError:
            logger.info("Redis subscriber cancelled")
            break
        except Exception as exc:
            logger.error(f"Redis subscriber error: {exc} — reconnecting in 3s")
            await asyncio.sleep(3)
