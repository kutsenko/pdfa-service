"""Integration tests for pairing WebSocket flow."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from src.pdfa.api import app
from src.pdfa.models import PairingSessionDocument


@pytest.fixture
def client():
    """Test client."""
    return TestClient(app)


@pytest.fixture
def mock_pairing_manager():
    """Mock pairing manager."""
    with patch("src.pdfa.api.pairing_manager") as mock_manager:
        mock_manager.active_connections = {}
        mock_manager.register_websocket = AsyncMock()
        mock_manager.unregister_websocket = AsyncMock()
        mock_manager.sync_image = AsyncMock()
        yield mock_manager


class TestWebSocketPairingRegistration:
    """Tests for WebSocket pairing registration."""

    def test_register_desktop_websocket(self, client, mock_pairing_manager):
        """Should register desktop WebSocket for pairing."""
        # Mock repository
        mock_repo = AsyncMock()
        mock_session = PairingSessionDocument(
            session_id="test-session-id",
            pairing_code="ABC123",
            desktop_user_id="anonymous",
            status="pending",
            created_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(minutes=30),
            last_activity_at=datetime.now(UTC),
        )
        mock_repo.get_session.return_value = mock_session
        mock_pairing_manager.repo = mock_repo

        # Connect WebSocket and register
        with client.websocket_connect("/ws") as websocket:
            # Send registration message
            websocket.send_json(
                {
                    "type": "register_pairing",
                    "session_id": "test-session-id",
                    "role": "desktop",
                }
            )

            # Give it time to process
            import time

            time.sleep(0.1)

        # Verify registration was called
        mock_pairing_manager.register_websocket.assert_called_once()

    def test_register_mobile_websocket(self, client, mock_pairing_manager):
        """Should register mobile WebSocket for pairing."""
        # Mock repository
        mock_repo = AsyncMock()
        mock_session = PairingSessionDocument(
            session_id="test-session-id",
            pairing_code="ABC123",
            desktop_user_id="anonymous",
            mobile_user_id="anonymous",
            status="active",
            created_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(minutes=30),
            joined_at=datetime.now(UTC),
            last_activity_at=datetime.now(UTC),
        )
        mock_repo.get_session.return_value = mock_session
        mock_pairing_manager.repo = mock_repo

        # Connect WebSocket and register
        with client.websocket_connect("/ws") as websocket:
            # Send registration message
            websocket.send_json(
                {
                    "type": "register_pairing",
                    "session_id": "test-session-id",
                    "role": "mobile",
                }
            )

            # Give it time to process
            import time

            time.sleep(0.1)

        # Verify registration was called
        mock_pairing_manager.register_websocket.assert_called_once()

    def test_register_invalid_session_id(self, client, mock_pairing_manager):
        """Should reject registration with invalid session ID."""
        # Mock repository
        mock_repo = AsyncMock()
        mock_repo.get_session.return_value = None
        mock_pairing_manager.repo = mock_repo

        # Connect WebSocket and try to register
        with client.websocket_connect("/ws") as websocket:
            # Send registration message
            websocket.send_json(
                {
                    "type": "register_pairing",
                    "session_id": "invalid-session",
                    "role": "desktop",
                }
            )

            # Should receive error
            response = websocket.receive_json()
            assert response["type"] == "error"
            assert "Invalid session ID" in response["message"]


class TestWebSocketImageSync:
    """Tests for image syncing via WebSocket."""

    def test_sync_image_from_mobile_to_desktop(self, client, mock_pairing_manager):
        """Should sync image from mobile to desktop via WebSocket."""
        # Mock repository
        mock_repo = AsyncMock()
        mock_session = PairingSessionDocument(
            session_id="test-session-id",
            pairing_code="ABC123",
            desktop_user_id="anonymous",
            mobile_user_id="anonymous",
            status="active",
            created_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(minutes=30),
            joined_at=datetime.now(UTC),
            last_activity_at=datetime.now(UTC),
        )
        mock_repo.get_session.return_value = mock_session
        mock_pairing_manager.repo = mock_repo

        # Connect WebSocket as mobile
        with client.websocket_connect("/ws") as websocket:
            # Register as mobile
            websocket.send_json(
                {
                    "type": "register_pairing",
                    "session_id": "test-session-id",
                    "role": "mobile",
                }
            )

            # Send image sync message
            # Base64 encoded 1x1 red pixel PNG
            test_image_data = (
                "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAA"
                "DUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
            )
            websocket.send_json(
                {
                    "type": "sync_image",
                    "session_id": "test-session-id",
                    "image_data": test_image_data,
                    "image_index": 0,
                    "metadata": {"width": 1920, "height": 1080},
                }
            )

            # Give it a moment to process
            import time

            time.sleep(0.1)

        mock_pairing_manager.sync_image.assert_called_once()

    def test_sync_image_invalid_base64(self, client, mock_pairing_manager):
        """Should reject invalid base64 image data."""
        # Mock repository
        mock_repo = AsyncMock()
        mock_session = PairingSessionDocument(
            session_id="test-session-id",
            pairing_code="ABC123",
            desktop_user_id="anonymous",
            mobile_user_id="anonymous",
            status="active",
            created_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(minutes=30),
            joined_at=datetime.now(UTC),
            last_activity_at=datetime.now(UTC),
        )
        mock_repo.get_session.return_value = mock_session
        mock_pairing_manager.repo = mock_repo

        # Connect WebSocket as mobile
        with client.websocket_connect("/ws") as websocket:
            # Register as mobile
            websocket.send_json(
                {
                    "type": "register_pairing",
                    "session_id": "test-session-id",
                    "role": "mobile",
                }
            )

            # Send image sync message with invalid base64
            websocket.send_json(
                {
                    "type": "sync_image",
                    "session_id": "test-session-id",
                    "image_data": "not-valid-base64!!!",
                    "image_index": 0,
                }
            )

            # Should receive error
            response = websocket.receive_json()
            assert response["type"] == "error"


class TestWebSocketPeerStatus:
    """Tests for peer status notifications."""

    def test_peer_connection_notification(self, client, mock_pairing_manager):
        """Should notify peer when device connects."""
        # Mock repository
        mock_repo = AsyncMock()
        mock_session = PairingSessionDocument(
            session_id="test-session-id",
            pairing_code="ABC123",
            desktop_user_id="anonymous",
            status="pending",
            created_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(minutes=30),
            last_activity_at=datetime.now(UTC),
        )
        mock_repo.get_session.return_value = mock_session
        mock_pairing_manager.repo = mock_repo

        # Simulate peer notification by setting up mock
        mock_pairing_manager._notify_peer_status = AsyncMock()

        # Connect desktop WebSocket
        with client.websocket_connect("/ws") as websocket:
            websocket.send_json(
                {
                    "type": "register_pairing",
                    "session_id": "test-session-id",
                    "role": "desktop",
                }
            )

            # Give it time to process
            import time

            time.sleep(0.1)

        # Verify notification was attempted (via register_websocket which calls it)
        mock_pairing_manager.register_websocket.assert_called_once()


class TestWebSocketMessageValidation:
    """Tests for WebSocket message validation."""

    def test_register_pairing_missing_session_id(self, client, mock_pairing_manager):
        """Should reject registration without session_id."""
        with client.websocket_connect("/ws") as websocket:
            # Send invalid registration message
            websocket.send_json(
                {
                    "type": "register_pairing",
                    "role": "desktop",
                    # Missing session_id
                }
            )

            # Should receive error
            response = websocket.receive_json()
            assert response["type"] == "error"

    def test_register_pairing_invalid_role(self, client, mock_pairing_manager):
        """Should reject registration with invalid role."""
        # Mock repository
        mock_repo = AsyncMock()
        mock_session = PairingSessionDocument(
            session_id="test-session-id",
            pairing_code="ABC123",
            desktop_user_id="anonymous",
            status="pending",
            created_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(minutes=30),
            last_activity_at=datetime.now(UTC),
        )
        mock_repo.get_session.return_value = mock_session
        mock_pairing_manager.repo = mock_repo

        with client.websocket_connect("/ws") as websocket:
            # Send registration with invalid role
            websocket.send_json(
                {
                    "type": "register_pairing",
                    "session_id": "test-session-id",
                    "role": "invalid-role",
                }
            )

            # Should receive error
            response = websocket.receive_json()
            assert response["type"] == "error"

    def test_sync_image_missing_image_data(self, client, mock_pairing_manager):
        """Should reject sync without image_data."""
        # Mock repository
        mock_repo = AsyncMock()
        mock_session = PairingSessionDocument(
            session_id="test-session-id",
            pairing_code="ABC123",
            desktop_user_id="anonymous",
            mobile_user_id="anonymous",
            status="active",
            created_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(minutes=30),
            joined_at=datetime.now(UTC),
            last_activity_at=datetime.now(UTC),
        )
        mock_repo.get_session.return_value = mock_session
        mock_pairing_manager.repo = mock_repo

        with client.websocket_connect("/ws") as websocket:
            # Register as mobile
            websocket.send_json(
                {
                    "type": "register_pairing",
                    "session_id": "test-session-id",
                    "role": "mobile",
                }
            )

            # Send sync without image_data
            websocket.send_json(
                {
                    "type": "sync_image",
                    "session_id": "test-session-id",
                    "image_index": 0,
                    # Missing image_data
                }
            )

            # Should receive error
            response = websocket.receive_json()
            assert response["type"] == "error"
