"""
WebSocket connection manager singleton for BloodBridge AI.
Imported by other services and nodes to broadcast real-time updates.
"""
import json
import logging
from datetime import datetime
from fastapi import WebSocket

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active_connections.append(ws)
        logger.info(f"WebSocket client connected. Active connections: {len(self.active_connections)}")

    def disconnect(self, ws: WebSocket):
        if ws in self.active_connections:
            self.active_connections.remove(ws)
            logger.info(f"WebSocket client disconnected. Active connections: {len(self.active_connections)}")

    async def broadcast(self, event_type_or_msg, data=None):
        """
        Broadcast JSON payload to all active WebSocket connections.
        Supports both signatures:
        - ws_manager.broadcast("event_type", data_dict)
        - ws_manager.broadcast(message_dict)  # back-compat
        """
        if data is None:
            if isinstance(event_type_or_msg, dict):
                event_type = event_type_or_msg.get("type", "unknown")
                msg_data = event_type_or_msg
            else:
                event_type = "unknown"
                msg_data = event_type_or_msg
        else:
            event_type = event_type_or_msg
            msg_data = data
            
        payload = {
            "type": event_type,
            "data": msg_data,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        logger.info(f"Broadcasting WebSocket message: {event_type}")
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(payload))
            except Exception as e:
                logger.warning(f"Failed to send WS message: {e}")
                disconnected.append(connection)
                
        # Clean up any broken connections
        for conn in disconnected:
            self.disconnect(conn)

ws_manager = ConnectionManager()  # Singleton
