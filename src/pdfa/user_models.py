"""User data models for authentication."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class User:
    """Authenticated user information from Google OAuth.

    Attributes:
        user_id: Unique user identifier (Google user ID)
        email: User email address
        name: User display name
        picture: Profile picture URL (optional)

    """

    user_id: str
    email: str
    name: str
    picture: str | None = None

    def to_dict(self) -> dict[str, str | None]:
        """Convert user to dictionary for JSON serialization.

        Returns:
            Dictionary with user data.

        """
        return {
            "user_id": self.user_id,
            "email": self.email,
            "name": self.name,
            "picture": self.picture,
        }

    @classmethod
    def from_google_userinfo(cls, userinfo: dict) -> User:
        """Create User from Google OAuth userinfo response.

        Args:
            userinfo: User info dict from Google OAuth.

        Returns:
            User instance.

        Example userinfo:
            {
                "sub": "1234567890",
                "email": "user@example.com",
                "name": "John Doe",
                "picture": "https://lh3.googleusercontent.com/..."
            }

        """
        return cls(
            user_id=userinfo["sub"],
            email=userinfo["email"],
            name=userinfo.get("name", userinfo["email"]),
            picture=userinfo.get("picture"),
        )
