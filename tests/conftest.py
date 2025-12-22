"""Test-wide fixtures and stubs."""

from __future__ import annotations

import importlib.util
import sys
import types

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
    from pdfa.auth import create_jwt_token
    from datetime import datetime, timedelta

    # Create token with past expiry
    import jose.jwt

    payload = {
        "sub": test_user.user_id,
        "email": test_user.email,
        "name": test_user.name,
        "picture": test_user.picture,
        "iat": int((datetime.utcnow() - timedelta(days=2)).timestamp()),
        "exp": int((datetime.utcnow() - timedelta(days=1)).timestamp()),  # Expired
    }

    return jose.jwt.encode(
        payload, auth_config_enabled.jwt_secret_key, algorithm=auth_config_enabled.jwt_algorithm
    )


@pytest.fixture
def auth_headers(valid_jwt_token):
    """Generate authorization headers for testing."""
    return {"Authorization": f"Bearer {valid_jwt_token}"}
