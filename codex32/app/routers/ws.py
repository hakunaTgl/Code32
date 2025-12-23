"""WebSocket endpoints.

Implements:
- /ws/updates: broadcast-ish minimal feed (per-connection keepalive)
- /ws/command/{user}: simple command channel echo for conversational integration

These are intentionally minimal and safe: they don't execute arbitrary code.
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime
from app.utils import get_timestamp

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()


@router.websocket("/ws/updates")
async def ws_updates(websocket: WebSocket) -> None:
    await websocket.accept()
    try:
        while True:
            # Keepalive heartbeat; clients can treat these as liveness pings.
            await websocket.send_json({
                "type": "heartbeat",
                "ts": get_timestamp(),
            })
            await asyncio.sleep(5)
    except WebSocketDisconnect:
        return


@router.websocket("/ws/command/{user_id}")
async def ws_command(websocket: WebSocket, user_id: str) -> None:
    await websocket.accept()
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                payload = json.loads(raw)
            except Exception:
                payload = {"message": raw}

            # Safe default: echo with metadata.
            await websocket.send_json({
                "type": "echo",
                "user_id": user_id,
                "payload": payload,
                "ts": get_timestamp(),
            })
    except WebSocketDisconnect:
        return
