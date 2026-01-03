"""Authentication module for Google OAuth and JWT handling."""

from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

from authlib.integrations.starlette_client import OAuth
from fastapi import HTTPException, Request, WebSocket
from jose import JWTError, jwt

from pdfa.auth_config import AuthConfig
from pdfa.logging_config import get_logger
from pdfa.models import AuditLogDocument, OAuthStateDocument, UserDocument
from pdfa.repositories import AuditLogRepository, OAuthStateRepository, UserRepository
from pdfa.user_models import User

logger = get_logger(__name__)

# Global auth config (loaded at startup)
auth_config: AuthConfig | None = None

# OAuth state tokens are now stored in MongoDB for CSRF protection
# This enables distributed deployments with multiple service instances


def get_client_ip(request: Request) -> str:
    """Extract client IP address from request.

    Checks X-Forwarded-For header first (for requests behind proxy),
    then falls back to direct client IP.

    Args:
        request: FastAPI/Starlette request object

    Returns:
        Client IP address or "unknown" if unavailable

    """
    # Check X-Forwarded-For header (for reverse proxy/load balancer)
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        # X-Forwarded-For can contain multiple IPs (client, proxy1, proxy2, ...)
        # The first one is the original client IP
        return forwarded_for.split(",")[0].strip()

    # Fall back to direct client IP
    if request.client:
        return request.client.host

    return "unknown"


def create_jwt_token(user: User, config: AuthConfig) -> str:
    """Create a JWT token for authenticated user.

    Args:
        user: Authenticated user
        config: Auth configuration

    Returns:
        Signed JWT token string

    """
    now = datetime.now(UTC)
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
        raise HTTPException(status_code=500, detail="Authentication not configured")

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


async def get_current_user_optional(
    request: Request,
) -> User | None:
    """FastAPI dependency to get current user.

    Returns default user when auth disabled, authenticated user when enabled.

    Args:
        request: FastAPI request object

    Returns:
        - Authenticated OAuth user if auth is enabled and valid token provided
        - Default user object if auth is disabled (uses DEFAULT_USER_* env vars)
        - Default user object with hardcoded values if auth_config is None

    The default user values are configurable via environment variables:
        - DEFAULT_USER_ID (default: "local-default")
        - DEFAULT_USER_EMAIL (default: "local@localhost")
        - DEFAULT_USER_NAME (default: "Local User")

    """
    global auth_config

    if auth_config is None or not auth_config.enabled:
        # Auth disabled - return default user
        return User(
            user_id=auth_config.default_user_id if auth_config else "local-default",
            email=auth_config.default_user_email if auth_config else "local@localhost",
            name=auth_config.default_user_name if auth_config else "Local User",
            picture=None,
        )

    # Auth enabled - try to authenticate, but don't require it
    # This allows endpoints to decide whether to require auth
    try:
        return await get_current_user(request)
    except HTTPException:
        # No valid token provided - return None to let endpoint decide
        return None


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

    async def _get_authorization_url(self, request: Request) -> str:
        """Generate OAuth authorization URL with state parameter.

        Stores state token in MongoDB for CSRF protection across distributed instances.

        Args:
            request: FastAPI request

        Returns:
            Google OAuth authorization URL

        """
        # Generate CSRF state token
        state = secrets.token_urlsafe(32)

        # Store state in MongoDB for validation during callback
        oauth_repo = OAuthStateRepository()
        state_doc = OAuthStateDocument(
            state=state,
            created_at=datetime.now(UTC),
            ip_address=get_client_ip(request),
            user_agent=request.headers.get("user-agent"),
        )
        await oauth_repo.create_state(state_doc)

        # Build authorization URL
        # Security: URL-encode redirect_uri to prevent OAuth errors
        from urllib.parse import quote

        redirect_uri = quote(self.config.redirect_uri, safe="")
        client_id = quote(self.config.google_client_id, safe="")
        state_encoded = quote(state, safe="")

        authorize_url = (
            f"https://accounts.google.com/o/oauth2/v2/auth?"
            f"client_id={client_id}&"
            f"response_type=code&"
            f"scope=openid%20email%20profile&"
            f"redirect_uri={redirect_uri}&"
            f"state={state_encoded}"
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

        authorize_url = await self._get_authorization_url(request)
        logger.info("Initiating Google OAuth login")

        return RedirectResponse(url=authorize_url, status_code=302)

    async def _exchange_code_for_token(self, code: str) -> dict[str, Any]:
        """Exchange authorization code for access token.

        Args:
            code: Authorization code from Google

        Returns:
            Token response dict with access_token

        Raises:
            HTTPException: If token exchange fails

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

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(token_url, data=data)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            error_body = e.response.text
            status_code = e.response.status_code
            logger.error(
                f"Google token exchange failed " f"(HTTP {status_code}): {error_body}"
            )
            raise HTTPException(
                status_code=500,
                detail=f"OAuth token exchange failed: {error_body}",
            )

    async def _get_user_info(self, access_token: str) -> dict[str, Any]:
        """Get user info from Google using access token.

        Args:
            access_token: Google access token

        Returns:
            User info dict (sub, email, name, picture)

        Raises:
            HTTPException: If user info retrieval fails

        """
        import httpx

        # Use v3 endpoint for OpenID Connect which guarantees 'sub' field
        userinfo_url = "https://www.googleapis.com/oauth2/v3/userinfo"

        headers = {"Authorization": f"Bearer {access_token}"}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(userinfo_url, headers=headers)
                response.raise_for_status()
                userinfo = response.json()
                logger.debug(f"Google userinfo response: {userinfo}")
                return userinfo
        except httpx.HTTPStatusError as e:
            error_body = e.response.text
            status_code = e.response.status_code
            logger.error(
                f"Google userinfo request failed " f"(HTTP {status_code}): {error_body}"
            )
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get user info: {error_body}",
            )

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
            raise HTTPException(status_code=400, detail="Missing authorization code")

        if not state:
            raise HTTPException(status_code=400, detail="Missing state parameter")

        # Validate state (CSRF protection) and delete from MongoDB
        oauth_repo = OAuthStateRepository()
        state_valid = await oauth_repo.validate_and_delete_state(state)

        if not state_valid:
            # Log failed authentication attempt
            audit_repo = AuditLogRepository()
            await audit_repo.log_event(
                AuditLogDocument(
                    event_type="auth_failure",
                    user_id=None,
                    timestamp=datetime.now(UTC),
                    ip_address=get_client_ip(request),
                    user_agent=request.headers.get("user-agent"),
                    details={"reason": "invalid_state", "state": state[:16] + "..."},
                )
            )
            raise HTTPException(status_code=400, detail="Invalid state parameter")

        try:
            # Exchange code for token
            token_response = await self._exchange_code_for_token(code)
            access_token = token_response["access_token"]

            # Get user info from Google
            userinfo = await self._get_user_info(access_token)

            # Create User object
            user = User.from_google_userinfo(userinfo)

            # Persist user profile to MongoDB (upsert)
            user_repo = UserRepository()
            user_doc = UserDocument(
                user_id=user.user_id,
                email=user.email,
                name=user.name,
                picture=user.picture,
                created_at=datetime.now(UTC),
                last_login_at=datetime.now(UTC),
                login_count=1,  # Will be incremented by repository
            )
            await user_repo.create_or_update_user(user_doc)

            # Create JWT token for our application
            jwt_token = create_jwt_token(user, self.config)

            # Log successful authentication
            audit_repo = AuditLogRepository()
            await audit_repo.log_event(
                AuditLogDocument(
                    event_type="user_login",
                    user_id=user.user_id,
                    timestamp=datetime.now(UTC),
                    ip_address=get_client_ip(request),
                    user_agent=request.headers.get("user-agent"),
                    details={"email": user.email, "method": "google_oauth"},
                )
            )

            logger.info(f"User authenticated: {user.email}")

            return user, jwt_token

        except HTTPException:
            # Re-raise HTTPExceptions (like validation errors)
            raise
        except KeyError as e:
            logger.error(f"Missing field in OAuth response: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Invalid OAuth response: missing {e}",
            )
        except Exception as e:
            logger.error(
                f"OAuth callback error: {type(e).__name__}: {e}", exc_info=True
            )
            # Provide more specific error message if it's an HTTP error
            error_detail = "Authentication failed"
            if hasattr(e, "response") and hasattr(e.response, "text"):
                logger.error(f"Google OAuth error response: {e.response.text}")
                error_detail = f"Authentication failed: {str(e)}"
            raise HTTPException(status_code=500, detail=error_detail)


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
