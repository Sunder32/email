import json
from collections import defaultdict

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.rooms: dict[int, list[WebSocket]] = defaultdict(list)

    async def connect(self, campaign_id: int, ws: WebSocket):
        await ws.accept()
        self.rooms[campaign_id].append(ws)

    def disconnect(self, campaign_id: int, ws: WebSocket):
        self.rooms[campaign_id].remove(ws)
        if not self.rooms[campaign_id]:
            del self.rooms[campaign_id]

    async def broadcast(self, campaign_id: int, message: dict):
        dead = []
        for ws in self.rooms.get(campaign_id, []):
            try:
                await ws.send_text(json.dumps(message, default=str))
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(campaign_id, ws)


ws_manager = ConnectionManager()
