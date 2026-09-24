from fastapi import WebSocket


class ConnectionManager:
    """Tracks which WebSocket connections are watching which board.

    In-memory only — works fine for one server process. If you ever run
    multiple backend instances behind a load balancer, a client connected
    to instance A won't see broadcasts triggered on instance B. That's the
    point where you'd swap this for Redis pub/sub: instead of broadcasting
    directly to self.active, you'd publish to a Redis channel, and every
    instance would subscribe and forward to its own local connections.
    """

    def __init__(self):
        self.active: dict[str, set[WebSocket]] = {}

    async def connect(self, board_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active.setdefault(board_id, set()).add(websocket)

    def disconnect(self, board_id: str, websocket: WebSocket) -> None:
        connections = self.active.get(board_id)
        if connections:
            connections.discard(websocket)
            if not connections:
                del self.active[board_id]

    async def broadcast(self, board_id: str, message: dict, exclude: WebSocket | None = None) -> None:
        connections = self.active.get(board_id, set())
        dead: list[WebSocket] = []
        for connection in connections:
            if connection is exclude:
                continue
            try:
                await connection.send_json(message)
            except Exception:
                dead.append(connection)
        for connection in dead:
            self.disconnect(board_id, connection)


# Module-level singleton — imported wherever a broadcast needs to happen.
manager = ConnectionManager()