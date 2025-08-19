from fastapi import WebSocket

class WebSocketManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[websocket.client] = websocket

    def disconnect(self, websocket: WebSocket):
        del self.active_connections[websocket.client]

    async def send_message(self, message: str):
        for connection in self.active_connections.values():
            await connection.send_text(message)
