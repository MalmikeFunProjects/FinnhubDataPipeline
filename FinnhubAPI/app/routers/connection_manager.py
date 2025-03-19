from fastapi import WebSocket
from pydantic import BaseModel

from utils.singleton import Singleton

class ConnectionManager(metaclass=Singleton):
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def send_pydantic_message(self, message: BaseModel, websocket: WebSocket):
        await websocket.send_json(message.model_dump())

    async def send_json(self, message: dict[any], websocket: WebSocket):
        await websocket.send_json(message)

    async def recieve_json(self, websocket: WebSocket):
        return await websocket.receive_json()

    async def recieve_text(self, websocket: WebSocket):
        return await websocket.receive_text()

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)
