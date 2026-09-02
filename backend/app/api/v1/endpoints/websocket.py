"""
WebSocket endpoint — real-time alert streaming to dashboard.
Clients connect with a valid JWT token as a query param.
"""
from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.core.security import decode_token
from app.core.config import settings
from app.services.websocket_manager import ws_manager

router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws/alerts")
async def ws_alerts(
    websocket: WebSocket,
    token: str = Query(...),
    camera_id: str = Query(None),
):
    """
    WebSocket endpoint for real-time alert push.
    - Authenticate via ?token=<JWT>
    - Optionally filter by ?camera_id=<id>
    - Client can send JSON: {"action": "subscribe", "camera_id": "cam-01"}
    """
    # Authenticate before accepting
    try:
        payload = decode_token(token)
        user_id = payload["sub"]
    except Exception:
        await websocket.close(code=4001)
        return

    await ws_manager.connect(websocket, user_id)
    if camera_id:
        await ws_manager.subscribe_camera(websocket, camera_id)

    try:
        # Send connection ACK
        await websocket.send_text(json.dumps({
            "type": "connected",
            "user_id": user_id,
            "message": "IBVAP alert stream connected",
        }))

        # Keep alive + handle client messages
        while True:
            try:
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=settings.alert_websocket_ping_interval,
                )
                msg = json.loads(data)
                action = msg.get("action")

                if action == "subscribe":
                    cam = msg.get("camera_id")
                    if cam:
                        await ws_manager.subscribe_camera(websocket, cam)
                        await websocket.send_text(json.dumps({
                            "type": "subscribed",
                            "camera_id": cam,
                        }))

                elif action == "unsubscribe":
                    cam = msg.get("camera_id")
                    if cam:
                        await ws_manager.unsubscribe_camera(websocket, cam)

                elif action == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))

            except asyncio.TimeoutError:
                # Send ping to keep connection alive
                await websocket.send_text(json.dumps({"type": "ping"}))

    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        await ws_manager.disconnect(websocket, user_id)
