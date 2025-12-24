"""Tests for authentication module."""

from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from pdfa.auth_config import AuthConfig

# AuthConfig Tests


def test_auth_config_from_env_disabled(monkeypatch):
    """Auth config loads with auth disabled by default."""
    monkeypatch.delenv("PDFA_ENABLE_AUTH", raising=False)

    config = AuthConfig.from_env()

    assert config.enabled is False


def test_auth_config_from_env_enabled(monkeypatch):
    """Auth config loads with auth enabled when PDFA_ENABLE_AUTH=true."""
    monkeypatch.setenv("PDFA_ENABLE_AUTH", "true")
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "test_client_id")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "test_secret")
    monkeypatch.setenv("JWT_SECRET_KEY", "test_jwt_secret_key_at_least_32_chars")

    config = AuthConfig.from_env()

    assert config.enabled is True
    assert config.google_client_id == "test_client_id"
    assert config.google_client_secret == "test_secret"
    assert config.jwt_secret_key == "test_jwt_secret_key_at_least_32_chars"


def test_auth_config_validation_succeeds_when_disabled():
    """Validation succeeds when auth is disabled even without credentials."""
    config = AuthConfig(
        enabled=False,
        google_client_id="",
        google_client_secret="",
        jwt_secret_key="",
    )

    config.validate()  # Should not raise


def test_auth_config_validation_requires_google_client_id():
    """Validation fails when auth enabled but GOOGLE_CLIENT_ID missing."""
    config = AuthConfig(
        enabled=True,
        google_client_id="",
        google_client_secret="secret",
        jwt_secret_key="a" * 32,
    )

    with pytest.raises(ValueError, match="GOOGLE_CLIENT_ID is required"):
        config.validate()


def test_auth_config_validation_requires_jwt_secret_min_length():
    """Validation fails when JWT_SECRET_KEY is too short."""
    config = AuthConfig(
        enabled=True,
        google_client_id="client_id",
        google_client_secret="secret",
        jwt_secret_key="short",  # Less than 32 chars
    )

    with pytest.raises(ValueError, match="at least 32 characters"):
        config.validate()


def test_auth_config_validation_unsupported_algorithm():
    """Validation fails with unsupported JWT algorithm."""
    config = AuthConfig(
        enabled=True,
        google_client_id="client_id",
        google_client_secret="secret",
        jwt_secret_key="a" * 32,
        jwt_algorithm="RS256",  # Unsupported
    )

    with pytest.raises(ValueError, match="Unsupported JWT algorithm"):
        config.validate()


# JWT Token Tests


def test_create_jwt_token(auth_config_enabled, test_user):
    """JWT token is created with correct payload."""
    import jose.jwt

    from pdfa.auth import create_jwt_token

    token = create_jwt_token(test_user, auth_config_enabled)

    # Decode without verification to inspect payload
    payload = jose.jwt.decode(
        token,
        auth_config_enabled.jwt_secret_key,
        algorithms=[auth_config_enabled.jwt_algorithm],
    )

    assert payload["sub"] == test_user.user_id
    assert payload["email"] == test_user.email
    assert payload["name"] == test_user.name
    assert payload["picture"] == test_user.picture
    assert "iat" in payload
    assert "exp" in payload


def test_decode_jwt_token_valid(auth_config_enabled, valid_jwt_token, test_user):
    """Valid JWT token is decoded successfully."""
    from pdfa.auth import decode_jwt_token

    user = decode_jwt_token(valid_jwt_token, auth_config_enabled)

    assert user.user_id == test_user.user_id
    assert user.email == test_user.email
    assert user.name == test_user.name


def test_decode_jwt_token_expired(auth_config_enabled, expired_jwt_token):
    """Expired JWT token raises HTTPException."""
    from pdfa.auth import decode_jwt_token

    with pytest.raises(HTTPException) as exc_info:
        decode_jwt_token(expired_jwt_token, auth_config_enabled)

    assert exc_info.value.status_code == 401
    assert "expired" in exc_info.value.detail.lower()


def test_decode_jwt_token_invalid_signature(auth_config_enabled, test_user):
    """JWT with invalid signature raises HTTPException."""
    from pdfa.auth import create_jwt_token, decode_jwt_token

    # Create token with one secret
    token = create_jwt_token(test_user, auth_config_enabled)

    # Try to decode with different secret
    wrong_config = AuthConfig(
        enabled=True,
        google_client_id="test",
        google_client_secret="test",
        jwt_secret_key="different_secret_key_32_chars_long",
    )

    with pytest.raises(HTTPException) as exc_info:
        decode_jwt_token(token, wrong_config)

    assert exc_info.value.status_code == 401


def test_decode_jwt_token_malformed(auth_config_enabled):
    """Malformed JWT token raises HTTPException."""
    from pdfa.auth import decode_jwt_token

    with pytest.raises(HTTPException) as exc_info:
        decode_jwt_token("not.a.valid.jwt.token", auth_config_enabled)

    assert exc_info.value.status_code == 401


def test_jwt_token_expiry_time(auth_config_enabled, test_user):
    """JWT token expires at correct time."""
    import jose.jwt

    from pdfa.auth import create_jwt_token

    token = create_jwt_token(test_user, auth_config_enabled)

    payload = jose.jwt.decode(
        token,
        auth_config_enabled.jwt_secret_key,
        algorithms=[auth_config_enabled.jwt_algorithm],
    )

    iat = datetime.utcfromtimestamp(payload["iat"])
    exp = datetime.utcfromtimestamp(payload["exp"])

    # Should expire after configured hours
    expected_expiry = iat + timedelta(hours=auth_config_enabled.jwt_expiry_hours)

    # Allow 1 second tolerance for test execution time
    assert abs((exp - expected_expiry).total_seconds()) < 1


# FastAPI Dependency Tests


@pytest.mark.asyncio
async def test_get_current_user_with_valid_token(
    auth_config_enabled, valid_jwt_token, test_user
):
    """get_current_user returns user with valid token."""
    from fastapi import Request

    from pdfa.auth import get_current_user

    # Mock request with Authorization header
    request = MagicMock(spec=Request)
    request.headers = {"Authorization": f"Bearer {valid_jwt_token}"}

    # Mock auth_config in the module
    with patch("pdfa.auth.auth_config", auth_config_enabled):
        user = await get_current_user(request)

    assert user.user_id == test_user.user_id
    assert user.email == test_user.email


@pytest.mark.asyncio
async def test_get_current_user_missing_token(auth_config_enabled):
    """get_current_user raises 401 when token is missing."""
    from fastapi import Request

    from pdfa.auth import get_current_user

    request = MagicMock(spec=Request)
    request.headers = {}

    with patch("pdfa.auth.auth_config", auth_config_enabled):
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(request)

    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_invalid_token_format(auth_config_enabled):
    """get_current_user raises 401 with invalid token format."""
    from fastapi import Request

    from pdfa.auth import get_current_user

    request = MagicMock(spec=Request)
    request.headers = {"Authorization": "InvalidFormat token"}

    with patch("pdfa.auth.auth_config", auth_config_enabled):
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(request)

    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_optional_with_auth_disabled(auth_config_disabled):
    """get_current_user_optional returns None when auth disabled."""
    from fastapi import Request

    from pdfa.auth import get_current_user_optional

    request = MagicMock(spec=Request)
    request.headers = {}

    with patch("pdfa.auth.auth_config", auth_config_disabled):
        user = await get_current_user_optional(request)

    assert user is None


@pytest.mark.asyncio
async def test_get_current_user_optional_with_auth_enabled(
    auth_config_enabled, valid_jwt_token, test_user
):
    """get_current_user_optional returns user when auth enabled and token valid."""
    from fastapi import Request

    from pdfa.auth import get_current_user_optional

    request = MagicMock(spec=Request)
    request.headers = {"Authorization": f"Bearer {valid_jwt_token}"}

    with patch("pdfa.auth.auth_config", auth_config_enabled):
        user = await get_current_user_optional(request)

    assert user is not None
    assert user.user_id == test_user.user_id


# Google OAuth Tests


@pytest.mark.asyncio
async def test_google_oauth_initiate_login(auth_config_enabled):
    """GoogleOAuthClient initiates login redirect."""
    from fastapi import Request
    from fastapi.responses import RedirectResponse

    from pdfa.auth import GoogleOAuthClient

    request = MagicMock(spec=Request)
    client = GoogleOAuthClient(auth_config_enabled)

    with patch.object(
        client,
        "_get_authorization_url",
        return_value="https://accounts.google.com/o/oauth2/auth?...",
    ):
        response = await client.initiate_login(request)

    assert isinstance(response, RedirectResponse)
    assert response.status_code == 302


@pytest.mark.asyncio
async def test_google_oauth_callback_success(auth_config_enabled, test_user):
    """GoogleOAuthClient handles callback and returns user + token."""
    from fastapi import Request

    from pdfa.auth import GoogleOAuthClient, _oauth_state_storage

    request = MagicMock(spec=Request)
    request.query_params = {"code": "auth_code_123", "state": "state_123"}

    client = GoogleOAuthClient(auth_config_enabled)

    # Add state to storage (simulating initiate_login was called)
    _oauth_state_storage["state_123"] = datetime.utcnow().isoformat()

    # Mock OAuth token exchange
    mock_token_response = {"access_token": "access_token_123"}
    mock_userinfo = {
        "sub": test_user.user_id,
        "email": test_user.email,
        "name": test_user.name,
        "picture": test_user.picture,
    }

    with (
        patch.object(
            client, "_exchange_code_for_token", return_value=mock_token_response
        ),
        patch.object(client, "_get_user_info", return_value=mock_userinfo),
    ):
        user, token = await client.handle_callback(request)

    assert user.user_id == test_user.user_id
    assert user.email == test_user.email
    assert isinstance(token, str)
    assert len(token) > 0


@pytest.mark.asyncio
async def test_google_oauth_callback_missing_code(auth_config_enabled):
    """GoogleOAuthClient raises error when code is missing."""
    from fastapi import Request

    from pdfa.auth import GoogleOAuthClient

    request = MagicMock(spec=Request)
    request.query_params = {}

    client = GoogleOAuthClient(auth_config_enabled)

    with pytest.raises(HTTPException) as exc_info:
        await client.handle_callback(request)

    assert exc_info.value.status_code == 400


# WebSocket Authentication Tests


@pytest.mark.asyncio
async def test_websocket_authenticator_valid_token(
    auth_config_enabled, valid_jwt_token, test_user
):
    """WebSocketAuthenticator validates token from query params."""
    from fastapi import WebSocket

    from pdfa.auth import WebSocketAuthenticator

    websocket = MagicMock(spec=WebSocket)
    websocket.query_params = {"token": valid_jwt_token}

    authenticator = WebSocketAuthenticator(auth_config_enabled)
    user = await authenticator.authenticate_websocket(websocket)

    assert user.user_id == test_user.user_id
    assert user.email == test_user.email


@pytest.mark.asyncio
async def test_websocket_authenticator_missing_token(auth_config_enabled):
    """WebSocketAuthenticator raises 401 when token is missing."""
    from fastapi import WebSocket

    from pdfa.auth import WebSocketAuthenticator

    websocket = MagicMock(spec=WebSocket)
    websocket.query_params = {}

    authenticator = WebSocketAuthenticator(auth_config_enabled)

    with pytest.raises(HTTPException) as exc_info:
        await authenticator.authenticate_websocket(websocket)

    assert exc_info.value.status_code == 401
    assert "missing" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_websocket_authenticator_invalid_token(auth_config_enabled):
    """WebSocketAuthenticator raises 401 with invalid token."""
    from fastapi import WebSocket

    from pdfa.auth import WebSocketAuthenticator

    websocket = MagicMock(spec=WebSocket)
    websocket.query_params = {"token": "invalid.token.here"}

    authenticator = WebSocketAuthenticator(auth_config_enabled)

    with pytest.raises(HTTPException) as exc_info:
        await authenticator.authenticate_websocket(websocket)

    assert exc_info.value.status_code == 401
