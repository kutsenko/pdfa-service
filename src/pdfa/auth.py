"""Authentication module for Google OAuth and JWT handling."""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta
from typing import Any

from authlib.integrations.starlette_client import OAuth
from fastapi import HTTPException, Request, WebSocket
from jose import JWTError, jwt

from pdfa.auth_config import AuthConfig
from pdfa.logging_config import get_logger
from pdfa.user_models import User

logger = get_logger(__name__)

# Global auth config (loaded at startup)
auth_config: AuthConfig | None = None


def create_jwt_token(user: User, config: AuthConfig) -> str:
    """Create a JWT token for authenticated user.

    Args:
        user: Authenticated user
        config: Auth configuration

    Returns:
        Signed JWT token string
    """
    now = datetime.utcnow()
    expires_at = now + timedelta(hours=config.jwt_expiry_hours)

    payload = {
        "sub": user.user_id,
        "email": user.email,
        "name": user.name,
        "picture": user.picture,
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
    }

    token = jwt.encode(payload, config.jwt_secret_key, algorithm=config.jwt_algorithm)
    return token


def decode_jwt_token(token: str, config: AuthConfig) -> User:
    """Decode and validate JWT token.

    Args:
        token: JWT token string
        config: Auth configuration

    Returns:
        User object from token payload

    Raises:
        HTTPException: If token is invalid or expired (401)
    """
    try:
        payload = jwt.decode(
            token, config.jwt_secret_key, algorithms=[config.jwt_algorithm]
        )

        user = User(
            user_id=payload["sub"],
            email=payload["email"],
            name=payload["name"],
            picture=payload.get("picture"),
        )

        return user

    except jwt.ExpiredSignatureError:
        logger.warning("JWT token expired")
        raise HTTPException(status_code=401, detail="Token has expired")
    except JWTError as e:
        logger.warning(f"Invalid JWT token: {e}")
        raise HTTPException(status_code=401, detail="Invalid authentication token")


async def get_current_user(request: Request) -> User:
    """FastAPI dependency to get current authenticated user (required).

    Args:
        request: FastAPI request object

    Returns:
        Authenticated user

    Raises:
        HTTPException: If authentication fails (401)
    """
    global auth_config

    if auth_config is None:
        raise HTTPException(
            status_code=500, detail="Authentication not configured"
        )

    # Extract token from Authorization header
    auth_header = request.headers.get("Authorization")

    if not auth_header:
        raise HTTPException(
            status_code=401,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Parse Bearer token
    parts = auth_header.split()

    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication header format",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = parts[1]

    # Decode and validate token
    user = decode_jwt_token(token, auth_config)

    logger.debug(f"Authenticated user: {user.email}")
    return user


async def get_current_user_optional(request: Request) -> User | None:
    """FastAPI dependency to get current user (optional, bypasses when auth disabled).

    Args:
        request: FastAPI request object

    Returns:
        Authenticated user or None if auth is disabled
    """
    global auth_config

    if auth_config is None or not auth_config.enabled:
        # Auth disabled - return None
        return None

    # Auth enabled - require authentication
    return await get_current_user(request)


class GoogleOAuthClient:
    """Google OAuth 2.0 client for authentication flow."""

    def __init__(self, config: AuthConfig):
        """Initialize Google OAuth client.

        Args:
            config: Auth configuration
        """
        self.config = config
        self.oauth = OAuth()
        self.oauth.register(
            name="google",
            client_id=config.google_client_id,
            client_secret=config.google_client_secret,
            server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
            client_kwargs={"scope": "openid email profile"},
        )

        # State storage for CSRF protection (in-memory, use Redis in production)
        self._state_storage: dict[str, str] = {}

    def _get_authorization_url(self, request: Request) -> str:
        """Generate OAuth authorization URL with state parameter.

        Args:
            request: FastAPI request

        Returns:
            Google OAuth authorization URL
        """
        # Generate CSRF state token
        state = secrets.token_urlsafe(32)
        self._state_storage[state] = datetime.utcnow().isoformat()

        # Build authorization URL
        redirect_uri = self.config.redirect_uri
        authorize_url = (
            f"https://accounts.google.com/o/oauth2/v2/auth?"
            f"client_id={self.config.google_client_id}&"
            f"response_type=code&"
            f"scope=openid%20email%20profile&"
            f"redirect_uri={redirect_uri}&"
            f"state={state}"
        )

        return authorize_url

    async def initiate_login(self, request: Request):
        """Initiate Google OAuth login flow.

        Args:
            request: FastAPI request

        Returns:
            RedirectResponse to Google OAuth
        """
        from fastapi.responses import RedirectResponse

        authorize_url = self._get_authorization_url(request)
        logger.info("Initiating Google OAuth login")

        return RedirectResponse(url=authorize_url, status_code=302)

    async def _exchange_code_for_token(self, code: str) -> dict[str, Any]:
        """Exchange authorization code for access token.

        Args:
            code: Authorization code from Google

        Returns:
            Token response dict with access_token
        """
        import httpx

        token_url = "https://oauth2.googleapis.com/token"

        data = {
            "code": code,
            "client_id": self.config.google_client_id,
            "client_secret": self.config.google_client_secret,
            "redirect_uri": self.config.redirect_uri,
            "grant_type": "authorization_code",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(token_url, data=data)
            response.raise_for_status()
            return response.json()

    async def _get_user_info(self, access_token: str) -> dict[str, Any]:
        """Get user info from Google using access token.

        Args:
            access_token: Google access token

        Returns:
            User info dict (sub, email, name, picture)
        """
        import httpx

        userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"

        headers = {"Authorization": f"Bearer {access_token}"}

        async with httpx.AsyncClient() as client:
            response = await client.get(userinfo_url, headers=headers)
            response.raise_for_status()
            return response.json()

    async def handle_callback(self, request: Request) -> tuple[User, str]:
        """Handle OAuth callback and issue JWT token.

        Args:
            request: FastAPI request with code and state

        Returns:
            Tuple of (User, JWT token)

        Raises:
            HTTPException: If callback validation fails
        """
        # Extract code and state from query params
        code = request.query_params.get("code")
        state = request.query_params.get("state")

        if not code:
            raise HTTPException(
                status_code=400, detail="Missing authorization code"
            )

        if not state:
            raise HTTPException(status_code=400, detail="Missing state parameter")

        # Validate state (CSRF protection)
        if state not in self._state_storage:
            raise HTTPException(status_code=400, detail="Invalid state parameter")

        # Remove used state
        del self._state_storage[state]

        try:
            # Exchange code for token
            token_response = await self._exchange_code_for_token(code)
            access_token = token_response["access_token"]

            # Get user info from Google
            userinfo = await self._get_user_info(access_token)

            # Create User object
            user = User.from_google_userinfo(userinfo)

            # Create JWT token for our application
            jwt_token = create_jwt_token(user, self.config)

            logger.info(f"User authenticated: {user.email}")

            return user, jwt_token

        except Exception as e:
            logger.error(f"OAuth callback error: {e}")
            raise HTTPException(
                status_code=500, detail="Authentication failed"
            )


class WebSocketAuthenticator:
    """Authenticates WebSocket connections using JWT tokens."""

    def __init__(self, config: AuthConfig):
        """Initialize WebSocket authenticator.

        Args:
            config: Auth configuration
        """
        self.config = config

    async def authenticate_websocket(self, websocket: WebSocket) -> User:
        """Authenticate WebSocket connection from token in query params.

        Args:
            websocket: FastAPI WebSocket connection

        Returns:
            Authenticated user

        Raises:
            HTTPException: If authentication fails (401)
        """
        # Extract token from query params (WebSocket doesn't support headers in browser)
        token = websocket.query_params.get("token")

        if not token:
            raise HTTPException(
                status_code=401,
                detail="Missing authentication token in WebSocket connection",
            )

        # Validate and decode token
        user = decode_jwt_token(token, self.config)

        logger.debug(f"WebSocket authenticated for user: {user.email}")
        return user
