"""Database configuration from environment variables.

This module handles loading and validating MongoDB configuration from
environment variables. It enforces a hard migration strategy where MongoDB
is required for the service to operate.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class DatabaseConfig:
    """MongoDB configuration loaded from environment variables.

    This configuration enforces a hard migration strategy: if MONGODB_URI
    is not provided, the service will fail to start. This ensures data
    persistence and multi-instance deployment support.

    Attributes:
        mongodb_uri: MongoDB connection URI (required)
        mongodb_database: Database name to use (default: pdfa_service)
        mongodb_max_pool_size: Maximum connection pool size (default: 100)
        mongodb_min_pool_size: Minimum connection pool size (default: 10)
        job_ttl_days: Number of days to retain job history (default: 90)

    """

    mongodb_uri: str
    mongodb_database: str = "pdfa_service"
    mongodb_max_pool_size: int = 100
    mongodb_min_pool_size: int = 10
    job_ttl_days: int = 90

    @classmethod
    def from_env(cls) -> DatabaseConfig:
        """Load database configuration from environment variables.

        Environment variables:
            MONGODB_URI: MongoDB connection URI (REQUIRED)
            MONGODB_DATABASE: Database name (default: pdfa_service)
            MONGODB_MAX_POOL_SIZE: Max connection pool size (default: 100)
            MONGODB_MIN_POOL_SIZE: Min connection pool size (default: 10)
            MONGODB_JOB_TTL_DAYS: Job retention in days (default: 90)

        Returns:
            DatabaseConfig instance with values from environment

        Raises:
            ValueError: If MONGODB_URI is not set (hard migration enforcement)

        Example:
            # .env file
            MONGODB_URI=mongodb://pdfa_user:password@mongodb:27017/pdfa_service?authSource=admin
            MONGODB_DATABASE=pdfa_service
            MONGODB_JOB_TTL_DAYS=90

            # In code
            db_config = DatabaseConfig.from_env()

        """
        mongodb_uri = os.getenv("MONGODB_URI")
        if not mongodb_uri:
            raise ValueError(
                "MONGODB_URI environment variable is required. "
                "Service cannot start without database connection. "
                "Please set MONGODB_URI in your environment or .env file."
            )

        return cls(
            mongodb_uri=mongodb_uri,
            mongodb_database=os.getenv("MONGODB_DATABASE", "pdfa_service"),
            mongodb_max_pool_size=int(os.getenv("MONGODB_MAX_POOL_SIZE", "100")),
            mongodb_min_pool_size=int(os.getenv("MONGODB_MIN_POOL_SIZE", "10")),
            job_ttl_days=int(os.getenv("MONGODB_JOB_TTL_DAYS", "90")),
        )

    def get_safe_uri_for_logging(self) -> str:
        """Get MongoDB URI with password redacted for logging.

        Returns:
            MongoDB URI with password replaced by '***'

        Example:
            >>> config = DatabaseConfig.from_env()
            >>> config.get_safe_uri_for_logging()
            'mongodb://pdfa_user:***@mongodb:27017/pdfa_service?authSource=admin'

        """
        # Replace password in URI with *** for safe logging
        uri = self.mongodb_uri
        if "@" in uri and "://" in uri:
            # Format: mongodb://user:password@host:port/db
            protocol, rest = uri.split("://", 1)
            if "@" in rest:
                credentials, host_part = rest.split("@", 1)
                if ":" in credentials:
                    username, _ = credentials.split(":", 1)
                    return f"{protocol}://{username}:***@{host_part}"
        return uri
