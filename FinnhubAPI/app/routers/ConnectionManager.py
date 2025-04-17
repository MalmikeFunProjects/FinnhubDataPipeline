"""
connection_manager.py - Async-safe WebSocket connection manager
"""

import asyncio
import sys
from fastapi import WebSocket
from typing import Dict, Set, Any, Optional, List, Union
import uuid
from contextlib import asynccontextmanager

from app.utils.default_log_setting import DefaultLogger

# Create a logger for the connection manager
logger = DefaultLogger.get_err_logger(name="connection_manager", log_to_console=True)

# Dependency to get the connection manager instance
def get_connection_manager():
    return ConnectionManager()

class ConnectionManager:
    """
    Async-safe WebSocket connection manager that can be shared across multiple classes.

    This manager uses asyncio locks instead of threading locks to properly handle
    concurrent access in an async environment.
    """

    # Class variable to hold the singleton instance
    _instance = None
    _initialized = False

    def __new__(cls):
        """Implement the singleton pattern using __new__"""
        if cls._instance is None:
            cls._instance = super(ConnectionManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the connection manager once"""
        if ConnectionManager._initialized:
            return

        logger.info("Initializing WebSocket ConnectionManager")

        # Lock to protect concurrent modification of connection collections
        self._lock = asyncio.Lock()

        # Store connections with additional metadata
        self.connections: Dict[str, Dict[str, Any]] = {}

        # Connection groups (for pub/sub patterns)
        self.groups: Dict[str, Set[str]] = {}

        ConnectionManager._initialized = True

    async def connect(self, websocket: WebSocket, client_id: str = None, metadata: Dict[str, Any] = None) -> str:
        """
        Accept a WebSocket connection and register it with the manager.

        Args:
            websocket: The WebSocket connection
            client_id: Optional client identifier (generated if not provided)
            metadata: Optional metadata to store with the connection

        Returns:
            The client ID for the connection
        """
        # Generate client ID if not provided
        if client_id is None:
            client_id = str(uuid.uuid4())

        # Metadata defaults to empty dict
        if metadata is None:
            metadata = {}

        # Accept the connection
        await websocket.accept()

        # Register the connection with async lock protection
        async with self._lock:
            self.connections[client_id] = {
                "websocket": websocket,
                "metadata": metadata,
                "connected_at": asyncio.get_event_loop().time(),
                "last_activity": asyncio.get_event_loop().time()
            }

        client_info = websocket.client.host if websocket.client else "unknown"
        logger.info(f"WebSocket connection established: ID={client_id}, Client={client_info}")

        return client_id

    async def disconnect(self, client_id: str) -> None:
        """
        Remove a connection from the manager.

        Args:
            client_id: The client identifier
        """
        async with self._lock:
            if client_id in self.connections:
                connection = self.connections.pop(client_id)

                # Also remove from any groups
                for group_name, members in self.groups.items():
                    if client_id in members:
                        members.remove(client_id)

                client_info = connection["websocket"].client.host if connection["websocket"].client else "unknown"
                logger.info(f"WebSocket connection removed: ID={client_id}, Client={client_info}")

    async def send_text(self, client_id: str, message: str) -> bool:
        """
        Send a text message to a specific client.

        Args:
            client_id: The client identifier
            message: The message to send

        Returns:
            True if sent successfully, False otherwise
        """
        async with self._lock:
            if client_id not in self.connections:
                return False

            connection = self.connections[client_id]
            websocket = connection["websocket"]

        try:
            await websocket.send_text(message)

            # Update last activity time
            async with self._lock:
                self.connections[client_id]["last_activity"] = asyncio.get_event_loop().time()

            return True
        except Exception as e:
            logger.error(f"Failed to send message to client {client_id}: {str(e)}")
            # Connection may be closed, remove it
            await self.disconnect(client_id)
            return False

    async def send_json(self, client_id: str, data: Any) -> bool:
        """
        Send a JSON message to a specific client.

        Args:
            client_id: The client identifier
            data: The JSON-serializable data to send

        Returns:
            True if sent successfully, False otherwise
        """
        async with self._lock:
            if client_id not in self.connections:
                return False

            connection = self.connections[client_id]
            websocket = connection["websocket"]

        try:
            await websocket.send_json(data)

            # Update last activity time
            async with self._lock:
                self.connections[client_id]["last_activity"] = asyncio.get_event_loop().time()

            return True
        except Exception as e:
            logger.error(f"Failed to send JSON to client {client_id}: {str(e)}")
            await self.disconnect(client_id)
            return False

    async def broadcast(self, message: str, exclude: Union[str, List[str]] = None) -> int:
        """
        Broadcast a text message to all connected clients.

        Args:
            message: The message to send
            exclude: Client ID(s) to exclude from broadcast

        Returns:
            Number of clients that received the message
        """
        if exclude is None:
            exclude = []
        elif isinstance(exclude, str):
            exclude = [exclude]

        successful_sends = 0

        # Get a safe copy of client IDs
        async with self._lock:
            client_ids = list(self.connections.keys())

        for client_id in client_ids:
            if client_id not in exclude:
                success = await self.send_text(client_id, message)
                if success:
                    successful_sends += 1

        logger.info(f"Broadcast message to {successful_sends} clients")
        return successful_sends

    async def broadcast_json(self, data: Any, exclude: Union[str, List[str]] = None) -> int:
        """
        Broadcast a JSON message to all connected clients.

        Args:
            data: The JSON-serializable data to send
            exclude: Client ID(s) to exclude from broadcast

        Returns:
            Number of clients that received the message
        """
        if exclude is None:
            exclude = []
        elif isinstance(exclude, str):
            exclude = [exclude]

        successful_sends = 0

        # Get a safe copy of client IDs
        async with self._lock:
            client_ids = list(self.connections.keys())

        for client_id in client_ids:
            if client_id not in exclude:
                success = await self.send_json(client_id, data)
                if success:
                    successful_sends += 1

        logger.info(f"Broadcast JSON to {successful_sends} clients")
        return successful_sends

    async def join_group(self, group_name: str, client_id: str) -> bool:
        """
        Add a client to a group for targeted broadcasts.

        Args:
            group_name: The name of the group
            client_id: The client identifier

        Returns:
            True if joined successfully, False if client doesn't exist
        """
        async with self._lock:
            if client_id not in self.connections:
                return False

            if group_name not in self.groups:
                self.groups[group_name] = set()

            self.groups[group_name].add(client_id)
            logger.info(f"Client {client_id} joined group '{group_name}'")

        return True

    async def leave_group(self, group_name: str, client_id: str) -> bool:
        """
        Remove a client from a group.

        Args:
            group_name: The name of the group
            client_id: The client identifier

        Returns:
            True if removed successfully, False if client or group doesn't exist
        """
        async with self._lock:
            if group_name not in self.groups:
                return False

            if client_id not in self.groups[group_name]:
                return False

            self.groups[group_name].remove(client_id)
            logger.info(f"Client {client_id} left group '{group_name}'")

            # Clean up empty groups
            if not self.groups[group_name]:
                del self.groups[group_name]

        return True

    async def broadcast_to_group(self, group_name: str, message: str) -> int:
        """
        Broadcast a text message to all clients in a group.

        Args:
            group_name: The name of the group
            message: The message to send

        Returns:
            Number of clients that received the message
        """
        # Get a safe copy of client IDs in this group
        client_ids = []
        async with self._lock:
            if group_name in self.groups:
                client_ids = list(self.groups[group_name])

        successful_sends = 0
        for client_id in client_ids:
            success = await self.send_text(client_id, message)
            if success:
                successful_sends += 1

        logger.info(f"Broadcast message to {successful_sends} clients in group '{group_name}'")
        return successful_sends

    async def broadcast_json_to_group(self, group_name: str, data: Any) -> int:
        """
        Broadcast a JSON message to all clients in a group.

        Args:
            group_name: The name of the group
            data: The JSON-serializable data to send

        Returns:
            Number of clients that received the message
        """
        # Get a safe copy of client IDs in this group
        client_ids = []
        async with self._lock:
            if group_name in self.groups:
                client_ids = list(self.groups[group_name])

        successful_sends = 0
        for client_id in client_ids:
            success = await self.send_json(client_id, data)
            if success:
                successful_sends += 1

        logger.info(f"Broadcast JSON to {successful_sends} clients in group '{group_name}'")
        return successful_sends

    def get_connection_count(self) -> int:
        """Get the current number of active connections"""
        return len(self.connections)

    def get_group_count(self, group_name: str) -> int:
        """Get the number of clients in a group"""
        if group_name not in self.groups:
            return 0
        return len(self.groups[group_name])

    async def get_client_metadata(self, client_id: str) -> Optional[Dict[str, Any]]:
        """Get the metadata for a specific client"""
        async with self._lock:
            if client_id not in self.connections:
                return None
            return self.connections[client_id]["metadata"].copy()

    async def update_client_metadata(self, client_id: str, metadata: Dict[str, Any]) -> bool:
        """Update the metadata for a specific client"""
        async with self._lock:
            if client_id not in self.connections:
                return False
            self.connections[client_id]["metadata"].update(metadata)
            return True

    async def get_inactive_connections(self, timeout_seconds: float) -> List[str]:
        """Get connections that have been inactive longer than timeout_seconds"""
        current_time = asyncio.get_event_loop().time()
        inactive_clients = []

        async with self._lock:
            for client_id, conn_data in self.connections.items():
                last_activity = conn_data["last_activity"]
                if current_time - last_activity > timeout_seconds:
                    inactive_clients.append(client_id)

        return inactive_clients

    async def cleanup_inactive_connections(self, timeout_seconds: float) -> int:
        """Remove connections that have been inactive longer than timeout_seconds"""
        inactive_clients = await self.get_inactive_connections(timeout_seconds)

        for client_id in inactive_clients:
            await self.disconnect(client_id)

        if inactive_clients:
            logger.info(f"Cleaned up {len(inactive_clients)} inactive connections")

        return len(inactive_clients)

    @asynccontextmanager
    async def connection_context(self, websocket: WebSocket, client_id: str = None, metadata: Dict[str, Any] = None):
        """
        Context manager for handling a WebSocket connection lifecycle.

        Usage:
            async with manager.connection_context(websocket) as client_id:
                # Connection is established and registered
                # Use client_id for operations
                ...
            # Connection is automatically closed and unregistered when leaving context
        """
        assigned_client_id = await self.connect(websocket, client_id, metadata)
        try:
            yield assigned_client_id
        finally:
            await self.disconnect(assigned_client_id)
