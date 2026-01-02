"""Unit tests for pairing manager."""

import pytest
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from src.pdfa.pairing_manager import PairingManager
from src.pdfa.models import PairingSessionDocument


class TestPairingCodeGeneration:
    """Tests for pairing code generation."""

    def test_generate_code_default_length(self):
        """Pairing code should be 6 characters by default."""
        manager = PairingManager()
        code = manager.generate_pairing_code()
        assert len(code) == 6

    def test_generate_code_custom_length(self):
        """Pairing code should respect custom length."""
        manager = PairingManager()
        code = manager.generate_pairing_code(length=8)
        assert len(code) == 8

    def test_generate_code_no_confusing_chars(self):
        """Should exclude confusing characters: 0, O, 1, I, L."""
        manager = PairingManager()

        # Generate many codes to ensure consistent exclusion
        for _ in range(100):
            code = manager.generate_pairing_code()
            assert "0" not in code, f"Code {code} contains '0'"
            assert "O" not in code, f"Code {code} contains 'O'"
            assert "1" not in code, f"Code {code} contains '1'"
            assert "I" not in code, f"Code {code} contains 'I'"
            assert "L" not in code, f"Code {code} contains 'L'"

    def test_generate_code_alphanumeric(self):
        """Pairing code should only contain alphanumeric characters."""
        manager = PairingManager()
        code = manager.generate_pairing_code()
        assert code.isalnum()

    def test_generate_code_uppercase(self):
        """Pairing code should be uppercase."""
        manager = PairingManager()
        code = manager.generate_pairing_code()
        assert code.isupper()

    def test_generate_code_uniqueness(self):
        """Generated codes should be unique (with high probability)."""
        manager = PairingManager()
        codes = {manager.generate_pairing_code() for _ in range(100)}
        # With 6-character codes from ~32 characters, collisions are very unlikely
        assert len(codes) >= 95  # Allow for rare collisions


@pytest.mark.asyncio
class TestPairingSessionCreation:
    """Tests for pairing session creation."""

    @patch("src.pdfa.pairing_manager.PairingSessionRepository")
    async def test_create_session_generates_uuid(self, mock_repo_class):
        """Should generate valid UUID for session_id."""
        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo

        manager = PairingManager()
        manager.repo = mock_repo

        session = await manager.create_session("user-123")

        # UUID format: 8-4-4-4-12 characters
        assert len(session.session_id) == 36
        assert session.session_id.count("-") == 4

    @patch("src.pdfa.pairing_manager.PairingSessionRepository")
    async def test_create_session_sets_user_id(self, mock_repo_class):
        """Should set desktop_user_id correctly."""
        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo

        manager = PairingManager()
        manager.repo = mock_repo

        session = await manager.create_session("user-123")

        assert session.desktop_user_id == "user-123"
        assert session.mobile_user_id is None

    @patch("src.pdfa.pairing_manager.PairingSessionRepository")
    async def test_create_session_initial_status_pending(self, mock_repo_class):
        """Should create session with 'pending' status."""
        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo

        manager = PairingManager()
        manager.repo = mock_repo

        session = await manager.create_session("user-123")

        assert session.status == "pending"

    @patch("src.pdfa.pairing_manager.PairingSessionRepository")
    async def test_create_session_sets_expiration(self, mock_repo_class):
        """Should set expiration time based on TTL."""
        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo

        manager = PairingManager(ttl_minutes=30)
        manager.repo = mock_repo

        before = datetime.now(UTC)
        session = await manager.create_session("user-123")
        after = datetime.now(UTC)

        expected_min = before + timedelta(minutes=30)
        expected_max = after + timedelta(minutes=30)

        assert expected_min <= session.expires_at <= expected_max

    @patch("src.pdfa.pairing_manager.PairingSessionRepository")
    async def test_create_session_custom_ttl(self, mock_repo_class):
        """Should respect custom TTL."""
        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo

        manager = PairingManager(ttl_minutes=15)
        manager.repo = mock_repo

        before = datetime.now(UTC)
        session = await manager.create_session("user-123")
        after = datetime.now(UTC)

        expected_min = before + timedelta(minutes=15)
        expected_max = after + timedelta(minutes=15)

        assert expected_min <= session.expires_at <= expected_max

    @patch("src.pdfa.pairing_manager.PairingSessionRepository")
    async def test_create_session_zero_images_synced(self, mock_repo_class):
        """Should initialize images_synced to 0."""
        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo

        manager = PairingManager()
        manager.repo = mock_repo

        session = await manager.create_session("user-123")

        assert session.images_synced == 0

    @patch("src.pdfa.pairing_manager.PairingSessionRepository")
    async def test_create_session_persists_to_db(self, mock_repo_class):
        """Should persist session to database."""
        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo

        manager = PairingManager()
        manager.repo = mock_repo

        session = await manager.create_session("user-123")

        mock_repo.create_session.assert_called_once()
        call_args = mock_repo.create_session.call_args[0][0]
        assert call_args.desktop_user_id == "user-123"


@pytest.mark.asyncio
class TestPairingSessionJoining:
    """Tests for joining pairing sessions."""

    @patch("src.pdfa.pairing_manager.PairingSessionRepository")
    async def test_join_session_same_user_succeeds(self, mock_repo_class):
        """Should allow same user to join from mobile."""
        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo

        # Mock existing session
        existing_session = PairingSessionDocument(
            session_id="test-session",
            pairing_code="ABC123",
            desktop_user_id="user-123",
            status="pending",
            created_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(minutes=30),
            last_activity_at=datetime.now(UTC),
        )
        mock_repo.find_by_code.return_value = existing_session

        manager = PairingManager()
        manager.repo = mock_repo

        joined = await manager.join_session("ABC123", "user-123")

        assert joined.status == "active"
        assert joined.mobile_user_id == "user-123"
        assert joined.joined_at is not None
        mock_repo.update_session.assert_called_once()

    @patch("src.pdfa.pairing_manager.PairingSessionRepository")
    async def test_join_session_different_user_fails(self, mock_repo_class):
        """Should reject different user."""
        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo

        # Mock existing session
        existing_session = PairingSessionDocument(
            session_id="test-session",
            pairing_code="ABC123",
            desktop_user_id="user-123",
            status="pending",
            created_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(minutes=30),
            last_activity_at=datetime.now(UTC),
        )
        mock_repo.find_by_code.return_value = existing_session

        manager = PairingManager()
        manager.repo = mock_repo

        with pytest.raises(ValueError, match="Must use same account"):
            await manager.join_session("ABC123", "user-456")

    @patch("src.pdfa.pairing_manager.PairingSessionRepository")
    async def test_join_session_invalid_code_fails(self, mock_repo_class):
        """Should reject invalid pairing code."""
        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo

        mock_repo.find_by_code.return_value = None

        manager = PairingManager()
        manager.repo = mock_repo

        with pytest.raises(ValueError, match="Invalid pairing code"):
            await manager.join_session("INVALID", "user-123")

    @patch("src.pdfa.pairing_manager.PairingSessionRepository")
    async def test_join_session_expired_fails(self, mock_repo_class):
        """Should reject expired session."""
        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo

        # Mock expired session
        existing_session = PairingSessionDocument(
            session_id="test-session",
            pairing_code="ABC123",
            desktop_user_id="user-123",
            status="pending",
            created_at=datetime.now(UTC) - timedelta(hours=1),
            expires_at=datetime.now(UTC) - timedelta(minutes=1),
            last_activity_at=datetime.now(UTC),
        )
        mock_repo.find_by_code.return_value = existing_session

        manager = PairingManager()
        manager.repo = mock_repo

        with pytest.raises(ValueError, match="expired"):
            await manager.join_session("ABC123", "user-123")

    @patch("src.pdfa.pairing_manager.PairingSessionRepository")
    async def test_join_session_already_active_fails(self, mock_repo_class):
        """Should reject session that is already active."""
        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo

        # Mock already active session
        existing_session = PairingSessionDocument(
            session_id="test-session",
            pairing_code="ABC123",
            desktop_user_id="user-123",
            mobile_user_id="user-123",
            status="active",
            created_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(minutes=30),
            joined_at=datetime.now(UTC),
            last_activity_at=datetime.now(UTC),
        )
        mock_repo.find_by_code.return_value = existing_session

        manager = PairingManager()
        manager.repo = mock_repo

        with pytest.raises(ValueError, match="already active"):
            await manager.join_session("ABC123", "user-123")


@pytest.mark.asyncio
class TestWebSocketRegistration:
    """Tests for WebSocket registration."""

    @patch("src.pdfa.pairing_manager.PairingSessionRepository")
    async def test_register_websocket_desktop(self, mock_repo_class):
        """Should register desktop WebSocket."""
        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo

        manager = PairingManager()
        manager.repo = mock_repo

        mock_websocket = MagicMock()

        await manager.register_websocket("session-123", "desktop", mock_websocket)

        assert "session-123" in manager.active_connections
        assert manager.active_connections["session-123"]["desktop"] == mock_websocket

    @patch("src.pdfa.pairing_manager.PairingSessionRepository")
    async def test_register_websocket_mobile(self, mock_repo_class):
        """Should register mobile WebSocket."""
        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo

        manager = PairingManager()
        manager.repo = mock_repo

        mock_websocket = MagicMock()

        await manager.register_websocket("session-123", "mobile", mock_websocket)

        assert "session-123" in manager.active_connections
        assert manager.active_connections["session-123"]["mobile"] == mock_websocket

    @patch("src.pdfa.pairing_manager.PairingSessionRepository")
    async def test_register_both_websockets(self, mock_repo_class):
        """Should register both desktop and mobile WebSockets."""
        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo

        manager = PairingManager()
        manager.repo = mock_repo

        mock_desktop_ws = MagicMock()
        mock_mobile_ws = MagicMock()

        await manager.register_websocket("session-123", "desktop", mock_desktop_ws)
        await manager.register_websocket("session-123", "mobile", mock_mobile_ws)

        assert manager.active_connections["session-123"]["desktop"] == mock_desktop_ws
        assert manager.active_connections["session-123"]["mobile"] == mock_mobile_ws

    @patch("src.pdfa.pairing_manager.PairingSessionRepository")
    async def test_unregister_websocket(self, mock_repo_class):
        """Should unregister WebSocket."""
        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo

        manager = PairingManager()
        manager.repo = mock_repo

        mock_websocket = MagicMock()

        await manager.register_websocket("session-123", "desktop", mock_websocket)
        await manager.unregister_websocket("session-123", "desktop")

        assert "desktop" not in manager.active_connections.get("session-123", {})


@pytest.mark.asyncio
class TestImageSyncing:
    """Tests for image syncing from mobile to desktop."""

    @patch("src.pdfa.pairing_manager.PairingSessionRepository")
    async def test_sync_image_to_desktop(self, mock_repo_class):
        """Should sync image to desktop WebSocket."""
        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo

        manager = PairingManager()
        manager.repo = mock_repo

        # Register desktop WebSocket
        mock_desktop_ws = AsyncMock()
        manager.active_connections["session-123"] = {"desktop": mock_desktop_ws}

        # Sync image
        await manager.sync_image(
            "session-123",
            "base64imagedata",
            0,
            {"width": 1920, "height": 1080}
        )

        # Verify WebSocket send
        mock_desktop_ws.send_json.assert_called_once()
        call_args = mock_desktop_ws.send_json.call_args[0][0]
        assert call_args["type"] == "image_synced"
        assert call_args["session_id"] == "session-123"
        assert call_args["image_data"] == "base64imagedata"
        assert call_args["image_index"] == 0

        # Verify counter increment
        mock_repo.increment_images_synced.assert_called_once_with("session-123")

    @patch("src.pdfa.pairing_manager.PairingSessionRepository")
    async def test_sync_image_desktop_not_connected_fails(self, mock_repo_class):
        """Should fail if desktop not connected."""
        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo

        manager = PairingManager()
        manager.repo = mock_repo

        # No desktop WebSocket registered
        manager.active_connections["session-123"] = {}

        with pytest.raises(ValueError, match="Desktop not connected"):
            await manager.sync_image("session-123", "base64imagedata", 0)
