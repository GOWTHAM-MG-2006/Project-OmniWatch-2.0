"""
OmniWatch 2.0 — NexusUX
Component: WebSocket Manager
Layer: 11
Phase: 1
Purpose: Real-time event streaming via WebSocket connections
Inputs: Backend events (incidents, anomalies, drift)
Outputs: Pushed events to connected dashboard clients
"""

import json
import logging
from datetime import datetime
from typing import Any, Optional

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for real-time event streaming."""

    def __init__(self):
        self._connections: list[WebSocket] = []
        self._subscriptions: dict[str, list[WebSocket]] = {}
        self._authenticated: dict[WebSocket, dict] = {}

    async def connect(self, websocket: WebSocket, user: Optional[dict] = None):
        """Accept a new WebSocket connection.

        Args:
            websocket: The WebSocket connection to accept.
            user: Optional decoded JWT payload with user info.
        """
        await websocket.accept()
        self._connections.append(websocket)
        if user:
            self._authenticated[websocket] = user
        logger.info(
            "WebSocket connected. Total: %d, user: %s",
            len(self._connections),
            user.get("user_id", "unknown") if user else "anonymous",
        )

    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        if websocket in self._connections:
            self._connections.remove(websocket)
        self._authenticated.pop(websocket, None)
        # Remove from all subscriptions
        for topic in list(self._subscriptions.keys()):
            if websocket in self._subscriptions[topic]:
                self._subscriptions[topic].remove(websocket)
        logger.info("WebSocket disconnected. Total: %d", len(self._connections))

    async def broadcast(self, message: str):
        """Broadcast a message to all connected clients."""
        disconnected = []
        for connection in self._connections:
            try:
                await connection.send_text(message)
            except Exception:
                disconnected.append(connection)
        for conn in disconnected:
            self.disconnect(conn)

    async def broadcast_event(self, event_type: str, data: Any):
        """Broadcast a structured event to all clients."""
        event = json.dumps({
            "type": event_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
        })
        await self.broadcast(event)

    async def send_to_topic(self, topic: str, message: str):
        """Send a message to clients subscribed to a topic."""
        subscribers = self._subscriptions.get(topic, [])
        disconnected = []
        for connection in subscribers:
            try:
                await connection.send_text(message)
            except Exception:
                disconnected.append(connection)
        for conn in disconnected:
            self.disconnect(conn)

    def subscribe(self, websocket: WebSocket, topic: str):
        """Subscribe a connection to a topic."""
        if topic not in self._subscriptions:
            self._subscriptions[topic] = []
        if websocket not in self._subscriptions[topic]:
            self._subscriptions[topic].append(websocket)

    def unsubscribe(self, websocket: WebSocket, topic: str):
        """Unsubscribe a connection from a topic."""
        if topic in self._subscriptions:
            self._subscriptions[topic] = [
                ws for ws in self._subscriptions[topic] if ws != websocket
            ]

    @property
    def connection_count(self) -> int:
        return len(self._connections)

    @property
    def topic_counts(self) -> dict[str, int]:
        return {topic: len(subs) for topic, subs in self._subscriptions.items()}
