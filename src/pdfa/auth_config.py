"""Authentication configuration for the PDF/A service."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class AuthConfig:
    """Authentication configuration loaded from environment variables.

    Attributes:
        enabled: Enable/disable authentication (PDFA_ENABLE_AUTH)
        google_client_id: Google OAuth 2.0 client ID
        google_client_secret: Google OAuth 2.0 client secret
        jwt_secret_key: Secret key for JWT signing (min 32 characters)
        jwt_algorithm: Algorithm for JWT signing (default: HS256)
        jwt_expiry_hours: JWT token expiry in hours (default: 24)
        redirect_uri: OAuth callback URL
        default_user_id: Default user ID when auth disabled
                         (default: local-default)
        default_user_email: Default user email when auth disabled
                            (default: local@localhost)
        default_user_name: Default user name when auth disabled
                           (default: Local User)

    """

    enabled: bool
    google_client_id: str
    google_client_secret: str
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expiry_hours: int = 24
    redirect_uri: str = "http://localhost:8000/auth/callback"
    default_user_id: str = "local-default"
    default_user_email: str = "local@localhost"
    default_user_name: str = "Local User"

    @classmethod
    def from_env(cls) -> AuthConfig:
        """Load authentication configuration from environment variables.

        Returns:
            AuthConfig instance with values from environment variables.

        Environment Variables:
            PDFA_ENABLE_AUTH: Enable authentication (true/false, default: false)
            GOOGLE_CLIENT_ID: Google OAuth client ID
            GOOGLE_CLIENT_SECRET: Google OAuth client secret
            JWT_SECRET_KEY: Secret key for JWT signing
            JWT_ALGORITHM: JWT signing algorithm (default: HS256)
            JWT_EXPIRY_HOURS: JWT expiry in hours (default: 24)
            OAUTH_REDIRECT_URI: OAuth callback URL
            DEFAULT_USER_ID: Default user ID when auth disabled
                             (default: local-default)
            DEFAULT_USER_EMAIL: Default user email when auth disabled
                                (default: local@localhost)
            DEFAULT_USER_NAME: Default user name when auth disabled
                               (default: Local User)

        """
        enabled_val = os.getenv("PDFA_ENABLE_AUTH", "false").lower()
        enabled = enabled_val in ("true", "1", "yes")

        return cls(
            enabled=enabled,
            google_client_id=os.getenv("GOOGLE_CLIENT_ID", ""),
            google_client_secret=os.getenv("GOOGLE_CLIENT_SECRET", ""),
            jwt_secret_key=os.getenv("JWT_SECRET_KEY", ""),
            jwt_algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
            jwt_expiry_hours=int(os.getenv("JWT_EXPIRY_HOURS", "24")),
            redirect_uri=os.getenv(
                "OAUTH_REDIRECT_URI", "http://localhost:8000/auth/callback"
            ),
            default_user_id=os.getenv("DEFAULT_USER_ID", "local-default"),
            default_user_email=os.getenv("DEFAULT_USER_EMAIL", "local@localhost"),
            default_user_name=os.getenv("DEFAULT_USER_NAME", "Local User"),
        )

    def validate(self) -> None:
        """Validate authentication configuration when auth is enabled.

        Raises:
            ValueError: If required configuration is missing when auth is enabled.

        """
        if not self.enabled:
            return

        if not self.google_client_id:
            raise ValueError(
                "GOOGLE_CLIENT_ID is required when authentication is enabled"
            )

        if not self.google_client_secret:
            raise ValueError(
                "GOOGLE_CLIENT_SECRET is required when authentication is enabled"
            )

        if not self.jwt_secret_key:
            raise ValueError(
                "JWT_SECRET_KEY is required when authentication is enabled"
            )

        if len(self.jwt_secret_key) < 32:
            raise ValueError(
                "JWT_SECRET_KEY must be at least 32 characters long for security"
            )

        if self.jwt_algorithm not in ("HS256", "HS384", "HS512"):
            raise ValueError(
                f"Unsupported JWT algorithm: {self.jwt_algorithm}. "
                f"Supported: HS256, HS384, HS512"
            )

        if self.jwt_expiry_hours < 1:
            raise ValueError("JWT_EXPIRY_HOURS must be at least 1 hour")
