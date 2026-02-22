"""
Thread-Safe WebSocket Manager for Real-time Updates
"""

import asyncio
from fastapi import WebSocket
from typing import Dict, Set, Optional
import logging

logger = logging.getLogger(__name__)


class ThreadSafeWebSocketManager:
    """
    Manages WebSocket connections with proper locking mechanisms
    to prevent race conditions
    """
    
    def __init__(self, max_connections: int = 100):
        self.max_connections = max_connections
        self._connections: Dict[str, WebSocket] = {}
        self._lock = asyncio.Lock()
        self._connection_count = 0
        self._closed = False
    
    async def connect(self, websocket: WebSocket, job_id: str) -> bool:
        """
        Accept and store WebSocket connection
        
        Returns:
            True if connected successfully, False otherwise
        """
        if self._closed:
            logger.warning("WebSocket manager is closed")
            return False
        
        async with self._lock:
            # Check connection limit
            if len(self._connections) >= self.max_connections:
                logger.warning(f"Max connections ({self.max_connections}) reached, rejecting {job_id}")
                return False
            
            # Close existing connection for this job if present
            if job_id in self._connections:
                old_ws = self._connections[job_id]
                try:
                    await old_ws.close()
                except Exception:
                    pass
            
            try:
                await websocket.accept()
                self._connections[job_id] = websocket
                self._connection_count += 1
                logger.info(f"WebSocket connected for job: {job_id} (total: {len(self._connections)})")
                return True
            except Exception as e:
                logger.error(f"Failed to accept WebSocket connection: {e}")
                return False
    
    async def disconnect(self, job_id: str) -> None:
        """Remove WebSocket connection"""
        async with self._lock:
            if job_id in self._connections:
                try:
                    websocket = self._connections[job_id]
                    if not websocket.client_state.DISCONNECTED:
                        await websocket.close()
                except Exception:
                    pass
                finally:
                    del self._connections[job_id]
                    logger.info(f"WebSocket disconnected for job: {job_id} (total: {len(self._connections)})")
    
    async def send_update(self, job_id: str, data: dict) -> bool:
        """
        Send update to specific job
        
        Returns:
            True if sent successfully, False otherwise
        """
        # Get connection outside lock to avoid blocking
        websocket = None
        async with self._lock:
            websocket = self._connections.get(job_id)
        
        if not websocket:
            return False
        
        try:
            await websocket.send_json(data)
            return True
        except Exception as e:
            logger.error(f"Error sending WebSocket update to {job_id}: {e}")
            # Clean up dead connection
            await self.disconnect(job_id)
            return False
    
    async def broadcast(self, message: dict) -> int:
        """
        Broadcast message to all connected clients
        
        Returns:
            Number of successful sends
        """
        # Get all connections outside lock
        connections = []
        async with self._lock:
            connections = list(self._connections.items())
        
        successful = 0
        failed_jobs = []
        
        for job_id, websocket in connections:
            try:
                await websocket.send_json(message)
                successful += 1
            except Exception as e:
                logger.error(f"Error broadcasting to {job_id}: {e}")
                failed_jobs.append(job_id)
        
        # Clean up failed connections
        for job_id in failed_jobs:
            await self.disconnect(job_id)
        
        return successful
    
    async def is_connected(self, job_id: str) -> bool:
        """Check if a job has an active connection"""
        async with self._lock:
            return job_id in self._connections
    
    def get_connection_count(self) -> int:
        """Get current number of connections"""
        return len(self._connections)
    
    async def close_all(self) -> None:
        """Close all connections gracefully"""
        self._closed = True
        
        async with self._lock:
            connections = list(self._connections.items())
            self._connections.clear()
        
        for job_id, websocket in connections:
            try:
                await websocket.close()
            except Exception:
                pass
        
        logger.info(f"Closed all {len(connections)} WebSocket connections")


# Backward compatibility - alias for old code
WebSocketManager = ThreadSafeWebSocketManager
