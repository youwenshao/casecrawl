"""
WebSocket endpoint for real-time batch progress updates.
"""
import json
from typing import Dict, Set
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["websocket"])


class ConnectionManager:
    """
    Manage WebSocket connections for real-time updates.
    
    Supports:
    - Broadcasting to all clients
    - Sending to specific batch subscribers
    """
    
    def __init__(self):
        # All active connections
        self.active_connections: Set[WebSocket] = set()
        # Connections subscribed to specific batches
        self.batch_subscribers: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, batch_id: str = None):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.add(websocket)
        
        if batch_id:
            if batch_id not in self.batch_subscribers:
                self.batch_subscribers[batch_id] = set()
            self.batch_subscribers[batch_id].add(websocket)
        
        logger.info(
            "websocket_connected",
            client=str(websocket.client),
            batch_id=batch_id,
            total_connections=len(self.active_connections),
        )
    
    def disconnect(self, websocket: WebSocket, batch_id: str = None):
        """Remove a WebSocket connection."""
        self.active_connections.discard(websocket)
        
        if batch_id and batch_id in self.batch_subscribers:
            self.batch_subscribers[batch_id].discard(websocket)
            if not self.batch_subscribers[batch_id]:
                del self.batch_subscribers[batch_id]
        
        logger.info(
            "websocket_disconnected",
            batch_id=batch_id,
            total_connections=len(self.active_connections),
        )
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send a message to a specific client."""
        await websocket.send_json(message)
    
    async def broadcast(self, message: dict):
        """Broadcast a message to all connected clients."""
        disconnected = set()
        
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.add(connection)
        
        # Clean up disconnected clients
        for conn in disconnected:
            self.active_connections.discard(conn)
    
    async def broadcast_to_batch(self, batch_id: str, message: dict):
        """Broadcast a message to all subscribers of a specific batch."""
        if batch_id not in self.batch_subscribers:
            return
        
        disconnected = set()
        
        for connection in self.batch_subscribers[batch_id]:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.add(connection)
        
        # Clean up disconnected clients
        for conn in disconnected:
            self.batch_subscribers[batch_id].discard(conn)
            self.active_connections.discard(conn)


# Global connection manager
manager = ConnectionManager()


@router.websocket("/ws/batch-progress")
async def batch_progress_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for batch progress updates.
    
    Query parameters:
    - batch_id: Subscribe to updates for a specific batch
    
    Events sent:
    - case_completed: When a case is successfully downloaded
    - case_error: When a case processing fails
    - civil_procedure_detected: When civil procedure case is found
    - ambiguous_requires_selection: When human disambiguation needed
    - batch_complete: When all cases in batch are processed
    """
    batch_id = None
    
    try:
        # Wait for connection with optional batch_id query parameter
        await websocket.accept()
        
        # Receive subscription message
        data = await websocket.receive_text()
        subscription = json.loads(data)
        batch_id = subscription.get("batch_id")
        
        await manager.connect(websocket, batch_id)
        
        # Send confirmation
        await websocket.send_json({
            "type": "connected",
            "message": "Subscribed to batch updates" if batch_id else "Connected to general updates",
            "batch_id": batch_id,
        })
        
        # Keep connection alive and handle client messages
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle ping/pong
                if message.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                    continue
                
                # Handle subscription changes
                if message.get("type") == "subscribe":
                    new_batch_id = message.get("batch_id")
                    if new_batch_id != batch_id:
                        manager.disconnect(websocket, batch_id)
                        batch_id = new_batch_id
                        await manager.connect(websocket, batch_id)
                        await websocket.send_json({
                            "type": "subscribed",
                            "batch_id": batch_id,
                        })
                
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON",
                })
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, batch_id)
        logger.info("websocket_disconnected_cleanly", batch_id=batch_id)
        
    except Exception as e:
        manager.disconnect(websocket, batch_id)
        logger.error("websocket_error", error=str(e), batch_id=batch_id)


# Helper functions for sending notifications

async def notify_case_completed(case_id: str, batch_id: str, file_name: str):
    """Notify clients that a case was completed."""
    await manager.broadcast_to_batch(batch_id, {
        "type": "case_completed",
        "case_id": case_id,
        "batch_id": batch_id,
        "file_name": file_name,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


async def notify_case_error(case_id: str, batch_id: str, error: str):
    """Notify clients of a case processing error."""
    await manager.broadcast_to_batch(batch_id, {
        "type": "case_error",
        "case_id": case_id,
        "batch_id": batch_id,
        "error": error,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


async def notify_civil_procedure_detected(case_id: str, batch_id: str, citation: str):
    """Notify clients of civil procedure case detection."""
    await manager.broadcast_to_batch(batch_id, {
        "type": "civil_procedure_detected",
        "case_id": case_id,
        "batch_id": batch_id,
        "citation": citation,
        "message": "Civil Procedure case detected. Manual Westlaw review required.",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


async def notify_ambiguous_requires_selection(case_id: str, batch_id: str, results_count: int):
    """Notify clients that human disambiguation is needed."""
    await manager.broadcast_to_batch(batch_id, {
        "type": "ambiguous_requires_selection",
        "case_id": case_id,
        "batch_id": batch_id,
        "results_count": results_count,
        "message": f"Multiple matches found ({results_count}). Human selection required.",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


async def notify_batch_complete(batch_id: str, statistics: dict):
    """Notify clients that a batch is complete."""
    await manager.broadcast_to_batch(batch_id, {
        "type": "batch_complete",
        "batch_id": batch_id,
        "statistics": statistics,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


# Import at end to avoid circular imports
from datetime import datetime, timezone
