import uuid

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.board import Board
from app.models.user import User
from app.models.workspace import WorkspaceMember
from app.realtime.connection_manager import manager
from app.security import decode_access_token

router = APIRouter(tags=["websocket"])


async def _authenticate_ws(websocket: WebSocket, board_id: uuid.UUID, db: AsyncSession) -> User | None:
    """WebSocket connections can't participate in the same auto-refresh flow
    as regular requests (no Response object to set cookies on mid-handshake),
    so this only accepts a currently-valid access token. If it's expired,
    the frontend should hit a regular REST endpoint first (which refreshes
    it) before opening the socket, or just reconnect after login."""
    access_token = websocket.cookies.get("access_token")
    if not access_token:
        return None

    user_id = decode_access_token(access_token)
    if not user_id:
        return None

    user = await db.get(User, uuid.UUID(user_id))
    if not user:
        return None

    board = await db.get(Board, board_id)
    if not board:
        return None

    member = await db.scalar(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == board.workspace_id,
            WorkspaceMember.user_id == user.id,
        )
    )
    return user if member else None


@router.websocket("/ws/boards/{board_id}")
async def board_websocket(websocket: WebSocket, board_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    user = await _authenticate_ws(websocket, board_id, db)
    if not user:
        await websocket.close(code=4401)  # custom close code, matches HTTP 401 in spirit
        return

    board_key = str(board_id)
    await manager.connect(board_key, websocket)

    try:
        while True:
            # Clients don't need to send anything — this just keeps the
            # connection alive and detects disconnects. If you want a
            # heartbeat/ping later, handle it here.
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(board_key, websocket)