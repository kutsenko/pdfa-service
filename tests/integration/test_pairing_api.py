"""Integration tests for pairing API endpoints."""

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
        yield mock_manager


class TestCreatePairingSessionEndpoint:
    """Tests for POST /api/v1/camera/pairing/create."""

    def test_create_pairing_session_success(self, client, mock_pairing_manager):
        """Should create pairing session and return QR data."""
        # Mock session creation
        mock_session = PairingSessionDocument(
            session_id="test-session-id",
            pairing_code="ABC123",
            desktop_user_id="anonymous",
            status="pending",
            created_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(minutes=30),
            last_activity_at=datetime.now(UTC),
        )
        mock_pairing_manager.create_session = AsyncMock(return_value=mock_session)

        # Make request
        response = client.post("/api/v1/camera/pairing/create")

        # Assertions
        assert response.status_code == 200
        data = response.json()

        assert data["session_id"] == "test-session-id"
        assert data["pairing_code"] == "ABC123"
        assert "qr_data" in data
        assert "/mobile/camera?code=ABC123" in data["qr_data"]
        assert data["ttl_seconds"] == 1800  # 30 minutes

    def test_create_pairing_session_includes_base_url(
        self, client, mock_pairing_manager
    ):
        """Should include correct base URL in QR data."""
        mock_session = PairingSessionDocument(
            session_id="test-session-id",
            pairing_code="XYZ789",
            desktop_user_id="anonymous",
            status="pending",
            created_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(minutes=30),
            last_activity_at=datetime.now(UTC),
        )
        mock_pairing_manager.create_session = AsyncMock(return_value=mock_session)

        response = client.post("/api/v1/camera/pairing/create")

        data = response.json()
        assert data["qr_data"].startswith("http")
        assert "XYZ789" in data["qr_data"]


class TestJoinPairingSessionEndpoint:
    """Tests for POST /api/v1/camera/pairing/join."""

    def test_join_pairing_session_success(self, client, mock_pairing_manager):
        """Should join session with valid code."""
        # Mock session join
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
        mock_pairing_manager.join_session = AsyncMock(return_value=mock_session)

        # Make request
        response = client.post(
            "/api/v1/camera/pairing/join", data={"pairing_code": "ABC123"}
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()

        assert data["session_id"] == "test-session-id"
        assert data["status"] == "active"

    def test_join_pairing_session_invalid_code(self, client, mock_pairing_manager):
        """Should reject invalid pairing code."""
        mock_pairing_manager.join_session = AsyncMock(
            side_effect=ValueError("Invalid pairing code")
        )

        response = client.post(
            "/api/v1/camera/pairing/join", data={"pairing_code": "INVALID"}
        )

        assert response.status_code == 400
        assert "Invalid pairing code" in response.json()["detail"]

    def test_join_pairing_session_different_user(self, client, mock_pairing_manager):
        """Should reject different user."""
        mock_pairing_manager.join_session = AsyncMock(
            side_effect=ValueError("Must use same account on both devices")
        )

        response = client.post(
            "/api/v1/camera/pairing/join", data={"pairing_code": "ABC123"}
        )

        assert response.status_code == 400
        assert "same account" in response.json()["detail"]

    def test_join_pairing_session_expired(self, client, mock_pairing_manager):
        """Should reject expired session."""
        mock_pairing_manager.join_session = AsyncMock(
            side_effect=ValueError("Pairing session expired")
        )

        response = client.post(
            "/api/v1/camera/pairing/join", data={"pairing_code": "ABC123"}
        )

        assert response.status_code == 400
        assert "expired" in response.json()["detail"]


class TestGetPairingStatusEndpoint:
    """Tests for GET /api/v1/camera/pairing/status/{session_id}."""

    def test_get_pairing_status_success(self, mock_pairing_manager):
        """Should return session status."""
        from fastapi.testclient import TestClient

        from src.pdfa.api import app, get_current_user_optional

        # Override dependency
        async def override_get_current_user():
            return None

        app.dependency_overrides[get_current_user_optional] = override_get_current_user
        client = TestClient(app)

        try:
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
                images_synced=3,
            )
            mock_repo.get_session.return_value = mock_session
            mock_pairing_manager.repo = mock_repo

            response = client.get("/api/v1/camera/pairing/status/test-session-id")

            assert response.status_code == 200
            data = response.json()

            assert data["session_id"] == "test-session-id"
            assert data["status"] == "active"
            assert data["images_synced"] == 3
        finally:
            app.dependency_overrides.clear()

    def test_get_pairing_status_not_found(self, client, mock_pairing_manager):
        """Should return 404 for non-existent session."""
        mock_repo = AsyncMock()
        mock_repo.get_session.return_value = None
        mock_pairing_manager.repo = mock_repo

        response = client.get("/api/v1/camera/pairing/status/non-existent")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


class TestCancelPairingSessionEndpoint:
    """Tests for POST /api/v1/camera/pairing/cancel/{session_id}."""

    def test_cancel_pairing_session_success(self, mock_pairing_manager):
        """Should cancel active session."""
        from fastapi.testclient import TestClient

        from src.pdfa.api import app, get_current_user_optional

        # Override dependency
        async def override_get_current_user():
            return None

        app.dependency_overrides[get_current_user_optional] = override_get_current_user
        client = TestClient(app)

        try:
            # Mock repository
            mock_repo = AsyncMock()
            mock_session = PairingSessionDocument(
                session_id="test-session-id",
                pairing_code="ABC123",
                desktop_user_id="anonymous",
                status="active",
                created_at=datetime.now(UTC),
                expires_at=datetime.now(UTC) + timedelta(minutes=30),
                last_activity_at=datetime.now(UTC),
            )
            mock_repo.get_session.return_value = mock_session
            mock_pairing_manager.repo = mock_repo
            mock_pairing_manager.active_connections = {}

            response = client.post("/api/v1/camera/pairing/cancel/test-session-id")

            assert response.status_code == 200
            assert response.json()["status"] == "cancelled"

            # Verify session was updated
            mock_repo.update_session.assert_called_once()
        finally:
            app.dependency_overrides.clear()

    def test_cancel_pairing_session_not_found(self, client, mock_pairing_manager):
        """Should return 404 for non-existent session."""
        mock_repo = AsyncMock()
        mock_repo.get_session.return_value = None
        mock_pairing_manager.repo = mock_repo

        response = client.post("/api/v1/camera/pairing/cancel/non-existent")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


class TestMobileCameraPageEndpoint:
    """Tests for GET /mobile/camera."""

    def test_mobile_camera_page_returns_html(self, client):
        """Should return HTML page."""
        response = client.get("/mobile/camera")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert b"Mobile Camera" in response.content

    def test_mobile_camera_page_with_code_param(self, client):
        """Should accept code parameter."""
        response = client.get("/mobile/camera?code=ABC123")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]


class TestPairingRateLimiting:
    """Tests for rate limiting on pairing endpoints."""

    def test_create_session_rate_limit(self, client, mock_pairing_manager):
        """Should rate limit session creation (10/minute)."""
        # Skip rate limiting test in unit tests as it requires Redis/state
        # and is better tested in E2E or manual testing
        pytest.skip("Rate limiting requires Redis and is tested in E2E")
