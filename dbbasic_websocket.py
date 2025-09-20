#!/usr/bin/env python3
"""
DBBasic WebSocket Handler
Unified WebSocket support for live UI updates
"""

from fastapi import WebSocket, WebSocketDisconnect
from typing import List, Dict
import json
import asyncio

class ConnectionManager:
    """Manage WebSocket connections"""

    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.service_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, service: str = None):
        """Accept new connection"""
        await websocket.accept()
        self.active_connections.append(websocket)

        if service:
            if service not in self.service_connections:
                self.service_connections[service] = []
            self.service_connections[service].append(websocket)

    def disconnect(self, websocket: WebSocket, service: str = None):
        """Remove connection"""
        self.active_connections.remove(websocket)

        if service and service in self.service_connections:
            self.service_connections[service].remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send message to specific connection"""
        await websocket.send_text(message)

    async def broadcast(self, message: str, service: str = None):
        """Broadcast to all or service-specific connections"""
        connections = self.service_connections.get(service, self.active_connections) if service else self.active_connections

        for connection in connections:
            try:
                await connection.send_text(message)
            except:
                # Connection closed, remove it
                await self.disconnect(connection, service)

# Global connection manager
manager = ConnectionManager()

async def websocket_endpoint(websocket: WebSocket, service: str = None):
    """WebSocket endpoint for real-time updates"""
    await manager.connect(websocket, service)

    try:
        while True:
            # Wait for messages from client
            data = await websocket.receive_text()

            # Process message
            message = json.loads(data)

            if message.get('type') == 'subscribe':
                # Subscribe to specific events
                pass
            elif message.get('type') == 'update':
                # Broadcast UI update
                await manager.broadcast(json.dumps({
                    'type': 'ui_update',
                    'target': message.get('target'),
                    'data': message.get('data')
                }), service)

    except WebSocketDisconnect:
        manager.disconnect(websocket, service)

async def send_ui_update(target_id: str, new_value: any, service: str = None):
    """Send UI update to all connected clients"""
    await manager.broadcast(json.dumps({
        'type': 'ui_update',
        'target': target_id,
        'value': new_value
    }), service)

async def send_metric_update(metrics: Dict, service: str = None):
    """Send metric updates"""
    await manager.broadcast(json.dumps({
        'type': 'metrics',
        'data': metrics
    }), service)
