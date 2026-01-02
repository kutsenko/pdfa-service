"""Test-wide fixtures and stubs."""

from __future__ import annotations

import importlib.util
import os
import sys
import types

# Disable rate limiting for all tests
os.environ["PDFA_DISABLE_RATE_LIMITING"] = "true"

if importlib.util.find_spec("ocrmypdf") is None:
    exceptions_module = types.ModuleType("ocrmypdf.exceptions")

    class ExitCodeException(Exception):
        """Fallback ExitCodeException used when OCRmyPDF is absent."""

        exit_code = 1

    class OCRmyPDFError(ExitCodeException):
        """Backward-compatible alias matching older OCRmyPDF documentation."""

        pass

    exceptions_module.ExitCodeException = ExitCodeException
    exceptions_module.OCRmyPDFError = OCRmyPDFError

    ocrmypdf_stub = types.ModuleType("ocrmypdf")
    ocrmypdf_stub.ocr = lambda *args, **kwargs: None  # type: ignore[assignment]
    ocrmypdf_stub.exceptions = exceptions_module

    sys.modules["ocrmypdf"] = ocrmypdf_stub
    sys.modules["ocrmypdf.exceptions"] = exceptions_module


# Authentication fixtures
import pytest


@pytest.fixture
def auth_config_disabled():
    """Auth config with authentication disabled."""
    from pdfa.auth_config import AuthConfig

    return AuthConfig(
        enabled=False,
        google_client_id="",
        google_client_secret="",
        jwt_secret_key="",
    )


@pytest.fixture
def auth_config_enabled():
    """Auth config with authentication enabled."""
    from pdfa.auth_config import AuthConfig

    return AuthConfig(
        enabled=True,
        google_client_id="test_client_id_12345",
        google_client_secret="test_client_secret_67890",
        jwt_secret_key="test_secret_key_at_least_32_characters_long_for_security",
        redirect_uri="http://testserver/auth/callback",
    )


@pytest.fixture
def test_user():
    """Test user fixture."""
    from pdfa.user_models import User

    return User(
        user_id="google_user_123456",
        email="test@example.com",
        name="Test User",
        picture="https://example.com/picture.jpg",
    )


@pytest.fixture
def valid_jwt_token(auth_config_enabled, test_user):
    """Generate a valid JWT token for testing."""
    from pdfa.auth import create_jwt_token

    return create_jwt_token(test_user, auth_config_enabled)


@pytest.fixture
def expired_jwt_token(auth_config_enabled, test_user):
    """Generate an expired JWT token for testing."""
    from datetime import UTC, datetime, timedelta

    # Create token with past expiry
    import jose.jwt

    payload = {
        "sub": test_user.user_id,
        "email": test_user.email,
        "name": test_user.name,
        "picture": test_user.picture,
        "iat": int((datetime.now(UTC) - timedelta(days=2)).timestamp()),
        "exp": int((datetime.now(UTC) - timedelta(days=1)).timestamp()),  # Expired
    }

    return jose.jwt.encode(
        payload,
        auth_config_enabled.jwt_secret_key,
        algorithm=auth_config_enabled.jwt_algorithm,
    )


@pytest.fixture
def auth_headers(valid_jwt_token):
    """Generate authorization headers for testing."""
    return {"Authorization": f"Bearer {valid_jwt_token}"}


@pytest.fixture(autouse=True)
def mock_mongodb(monkeypatch, auth_config_disabled, auth_config_enabled, request):
    """Auto-mock MongoDB for all unit tests.

    This fixture automatically mocks MongoDB database operations so unit tests
    can run without a real MongoDB instance. It provides AsyncMock objects for
    all collection operations.

    By default, authentication is DISABLED for tests. Tests that need
    authentication should use the auth_headers fixture and mark themselves
    with @pytest.mark.enable_auth.

    The mock is applied globally and automatically to all tests unless
    explicitly disabled with the marker: @pytest.mark.no_mongo_mock
    """
    from unittest.mock import AsyncMock, MagicMock

    # Create mock database
    mock_db = MagicMock()

    # Mock collections with AsyncMock for async operations
    mock_db.users = MagicMock()
    mock_db.jobs = MagicMock()
    mock_db.oauth_states = MagicMock()
    mock_db.audit_logs = MagicMock()

    # Mock common collection methods
    for collection in [
        mock_db.users,
        mock_db.jobs,
        mock_db.oauth_states,
        mock_db.audit_logs,
    ]:
        collection.insert_one = AsyncMock()
        collection.update_one = AsyncMock()
        collection.find_one = AsyncMock(return_value=None)
        collection.find_one_and_delete = AsyncMock(return_value=None)
        collection.delete_one = AsyncMock()
        collection.find = MagicMock()
        collection.aggregate = MagicMock()
        collection.create_index = AsyncMock()

    # Mock get_db to return our mock database
    def mock_get_db():
        return mock_db

    monkeypatch.setattr("pdfa.db.get_db", mock_get_db)
    monkeypatch.setattr("pdfa.repositories.get_db", mock_get_db)

    # Mock MongoDB health check to always return True
    async def mock_health_check(self):
        return True

    monkeypatch.setattr("pdfa.db.MongoDBConnection.health_check", mock_health_check)

    # Set auth config: use enabled config only for tests that use auth_headers fixture
    # Check if test uses auth_headers fixture by looking at the test function
    auth_config = auth_config_disabled
    if hasattr(request, "fixturenames") and "auth_headers" in request.fixturenames:
        auth_config = auth_config_enabled

    monkeypatch.setattr("pdfa.auth.auth_config", auth_config)

    return mock_db
