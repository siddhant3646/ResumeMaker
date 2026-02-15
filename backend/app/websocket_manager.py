"""
WebSocket Manager for Real-time Updates
"""

from fastapi import WebSocket
from typing import Dict, Optional
import json
import logging

logger = logging.getLogger(__name__)

class WebSocketManager:
    """Manages WebSocket connections for real-time generation updates"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, job_id: str):
        """Accept WebSocket connection"""
        await websocket.accept()
        self.active_connections[job_id] = websocket
        logger.info(f"WebSocket connected for job: {job_id}")
    
    async def disconnect(self, job_id: str):
        """Remove WebSocket connection"""
        if job_id in self.active_connections:
            del self.active_connections[job_id]
            logger.info(f"WebSocket disconnected for job: {job_id}")
    
    async def send_update(self, job_id: str, data: dict):
        """Send update to specific job"""
        if job_id in self.active_connections:
            try:
                await self.active_connections[job_id].send_json(data)
            except Exception as e:
                logger.error(f"Error sending WebSocket update: {e}")
    
    async def broadcast(self, message: dict):
        """Broadcast to all connected clients"""
        disconnected = []
        for job_id, connection in self.active_connections.items():
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to {job_id}: {e}")
                disconnected.append(job_id)
        
        # Clean up disconnected clients
        for job_id in disconnected:
            await self.disconnect(job_id)
