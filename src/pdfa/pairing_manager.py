"""Pairing session management for mobile-desktop camera sync.

This module provides the core logic for managing temporary pairing sessions
that link desktop and mobile devices for real-time image transfer during
camera workflows.

The PairingManager handles:
- Generating unique pairing codes
- Creating and managing pairing sessions
- Registering WebSocket connections for paired devices
- Syncing images from mobile to desktop
- Notifying devices of peer status changes
"""

from __future__ import annotations

import secrets
import string
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import WebSocket

from pdfa.logging_config import get_logger
from pdfa.models import PairingSessionDocument
from pdfa.repositories import PairingSessionRepository

logger = get_logger(__name__)


class PairingManager:
    """Manages mobile-desktop camera pairing sessions.

    This class handles the lifecycle of pairing sessions, from creation to expiration,
    including WebSocket connection management and image synchronization.

    Attributes:
        ttl_minutes: Time-to-live for pairing sessions in minutes (default: 30)
        repo: Repository for pairing session persistence
        active_connections: Dictionary mapping session_id to device WebSockets

    """

    def __init__(self, ttl_minutes: int = 30):
        """Initialize the pairing manager.

        Args:
            ttl_minutes: Session expiration time in minutes (default: 30)

        """
        self.ttl_minutes = ttl_minutes
        self.repo = PairingSessionRepository()
        # Structure: {session_id: {"desktop": WebSocket, "mobile": WebSocket}}
        self.active_connections: dict[str, dict[str, WebSocket]] = {}

    def generate_pairing_code(self, length: int = 6) -> str:
        """Generate random alphanumeric pairing code.

        Excludes confusing characters (0, O, 1, I, L) for better usability.

        Args:
            length: Code length (default: 6 characters)

        Returns:
            Random uppercase alphanumeric code

        Example:
            >>> manager = PairingManager()
            >>> code = manager.generate_pairing_code()
            >>> len(code)
            6
            >>> '0' not in code and 'O' not in code
            True

        """
        alphabet = string.ascii_uppercase + string.digits
        # Remove confusing characters
        alphabet = alphabet.replace("0", "").replace("O", "")
        alphabet = alphabet.replace("1", "").replace("I", "").replace("L", "")
        return "".join(secrets.choice(alphabet) for _ in range(length))

    async def create_session(self, user_id: str) -> PairingSessionDocument:
        """Create new pairing session.

        Generates a unique session ID and pairing code, then persists the session
        to the database with pending status.

        Args:
            user_id: User identifier who is creating the session (desktop)

        Returns:
            Created pairing session document

        Example:
            >>> manager = PairingManager()
            >>> session = await manager.create_session("user-123")
            >>> session.status
            'pending'

        """
        now = datetime.now(UTC)
        code = self.generate_pairing_code()

        session = PairingSessionDocument(
            session_id=str(uuid.uuid4()),
            pairing_code=code,
            desktop_user_id=user_id,
            status="pending",
            created_at=now,
            expires_at=now + timedelta(minutes=self.ttl_minutes),
            last_activity_at=now,
            images_synced=0,
        )

        await self.repo.create_session(session)
        logger.info(f"Created pairing session {session.session_id} with code {code}")
        return session

    async def join_session(self, code: str, user_id: str) -> PairingSessionDocument:
        """Join existing pairing session from mobile device.

        Validates the pairing code, checks expiration, and enforces same-user
        authentication before activating the session.

        Args:
            code: Pairing code (6-8 alphanumeric characters)
            user_id: User identifier attempting to join (mobile)

        Returns:
            Updated pairing session document with active status

        Raises:
            ValueError: If code is invalid, session expired, different user,
                       or session already active

        Example:
            >>> manager = PairingManager()
            >>> session = await manager.create_session("user-123")
            >>> joined = await manager.join_session(session.pairing_code, "user-123")
            >>> joined.status
            'active'

        """
        session = await self.repo.find_by_code(code)

        if not session:
            raise ValueError("Invalid pairing code")

        if session.expires_at < datetime.now(UTC):
            raise ValueError("Pairing session expired")

        if session.desktop_user_id != user_id:
            raise ValueError("Must use same account on both devices")

        if session.status != "pending":
            raise ValueError(f"Session already {session.status}")

        session.mobile_user_id = user_id
        session.status = "active"
        session.joined_at = datetime.now(UTC)

        await self.repo.update_session(session)
        logger.info(f"User joined pairing session {session.session_id}")
        return session

    async def register_websocket(
        self, session_id: str, role: str, websocket: WebSocket
    ) -> None:
        """Register WebSocket connection for a device in the pairing session.

        Associates a WebSocket connection with either the desktop or mobile role
        for the specified session, enabling real-time communication.

        Args:
            session_id: Pairing session UUID
            role: Device role ("desktop" or "mobile")
            websocket: WebSocket connection to register

        Example:
            >>> await manager.register_websocket(
            ...     session_id="uuid",
            ...     role="desktop",
            ...     websocket=ws
            ... )

        """
        if session_id not in self.active_connections:
            self.active_connections[session_id] = {}

        self.active_connections[session_id][role] = websocket
        logger.info(f"Registered {role} WebSocket for session {session_id}")

        # Notify peer that this device connected
        await self._notify_peer_status(session_id, role, connected=True)

    async def unregister_websocket(self, session_id: str, role: str) -> None:
        """Unregister WebSocket connection for a device.

        Removes the WebSocket connection and notifies the peer device of
        the disconnection.

        Args:
            session_id: Pairing session UUID
            role: Device role ("desktop" or "mobile")

        """
        if session_id in self.active_connections:
            self.active_connections[session_id].pop(role, None)
            logger.info(f"Unregistered {role} WebSocket for session {session_id}")

            # Notify peer that this device disconnected
            await self._notify_peer_status(session_id, role, connected=False)

            # Clean up empty session connections
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]

    async def _notify_peer_status(
        self, session_id: str, role: str, connected: bool
    ) -> None:
        """Notify peer device of connection status change.

        Sends a pairing_peer_status message to the other device in the pair.

        Args:
            session_id: Pairing session UUID
            role: Role of the device that changed status
            connected: True if device connected, False if disconnected

        """
        connections = self.active_connections.get(session_id, {})
        peer_role = "mobile" if role == "desktop" else "desktop"
        peer_ws = connections.get(peer_role)

        if peer_ws:
            try:
                await peer_ws.send_json(
                    {
                        "type": "pairing_peer_status",
                        "session_id": session_id,
                        "peer_role": role,
                        "connected": connected,
                    }
                )
                logger.debug(
                    f"Notified {peer_role} of {role} "
                    f"status: {'connected' if connected else 'disconnected'}"
                )
            except Exception as e:
                logger.warning(f"Failed to notify peer: {e}")

    async def sync_image(
        self,
        session_id: str,
        image_data: str,
        image_index: int,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Sync image from mobile to desktop.

        Transfers a captured image from mobile device to desktop by broadcasting
        an image_synced message through the desktop's WebSocket connection.

        Args:
            session_id: Pairing session UUID
            image_data: Base64-encoded JPEG image data
            image_index: Sequential image number
            metadata: Optional image metadata (timestamp, dimensions, etc.)

        Raises:
            ValueError: If desktop WebSocket not connected

        Example:
            >>> await manager.sync_image(
            ...     session_id="uuid",
            ...     image_data="base64_jpeg_data",
            ...     image_index=0,
            ...     metadata={"timestamp": "2024-01-01T12:00:00Z"}
            ... )

        """
        connections = self.active_connections.get(session_id, {})
        desktop_ws = connections.get("desktop")

        if not desktop_ws:
            logger.warning(f"No desktop connection for session {session_id}")
            raise ValueError("Desktop not connected")

        message = {
            "type": "image_synced",
            "session_id": session_id,
            "image_data": image_data,
            "image_index": image_index,
            "metadata": metadata or {},
        }

        try:
            await desktop_ws.send_json(message)
            await self.repo.increment_images_synced(session_id)
            logger.info(f"Synced image {image_index} to desktop (session {session_id})")
        except Exception as e:
            logger.error(f"Failed to sync image: {e}")
            raise


# Global instance
pairing_manager = PairingManager()
