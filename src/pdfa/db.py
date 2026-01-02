"""MongoDB database connection and management.

This module provides a singleton connection manager for MongoDB using Motor
(async MongoDB driver). The connection is established at application startup
and shared across all requests.

For production deployments with multiple instances, ensure MongoDB is configured
with appropriate connection pooling and replica sets for high availability.
"""

from __future__ import annotations

import logging

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

logger = logging.getLogger(__name__)


class MongoDBConnection:
    """Singleton MongoDB connection manager.

    This class ensures a single MongoDB connection is shared across the application.
    It handles connection initialization, health checks, and graceful shutdown.

    Usage:
        # At startup
        mongo = MongoDBConnection()
        await mongo.connect("mongodb://localhost:27017", "pdfa_service")

        # In application code
        db = get_db()
        await db.users.find_one({"user_id": "123"})

        # At shutdown
        await mongo.disconnect()

    Attributes:
        _instance: Singleton instance of the connection manager
        _client: Motor async MongoDB client
        _database: Motor async database instance

    """

    _instance: MongoDBConnection | None = None
    _client: AsyncIOMotorClient | None = None
    _database: AsyncIOMotorDatabase | None = None

    def __new__(cls) -> MongoDBConnection:
        """Create or return the singleton instance.

        Returns:
            The singleton MongoDBConnection instance

        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def connect(self, uri: str, database: str) -> None:
        """Initialize MongoDB connection.

        This method must be called at application startup before any database
        operations. It will raise an exception if the connection fails, preventing
        the application from starting without a valid database connection.

        Args:
            uri: MongoDB connection URI (e.g., "mongodb://user:pass@host:port/db")
            database: Database name to use

        Raises:
            ConnectionFailure: If unable to connect to MongoDB
            ServerSelectionTimeoutError: If MongoDB is unreachable
            ValueError: If connection parameters are invalid

        """
        if self._client is not None:
            logger.warning("MongoDB connection already established")
            return

        try:
            # Create async MongoDB client with connection pooling
            self._client = AsyncIOMotorClient(
                uri,
                maxPoolSize=100,  # Maximum concurrent connections
                minPoolSize=10,  # Minimum connections to maintain
                serverSelectionTimeoutMS=5000,  # 5 second timeout for server selection
                connectTimeoutMS=10000,  # 10 second timeout for initial connection
            )

            # Verify connection with ping command
            await self._client.admin.command("ping")

            # Set database reference
            self._database = self._client[database]

            logger.info(
                f"MongoDB connection established: database={database}, "
                f"pool_size=100"
            )

        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise RuntimeError(
                f"MongoDB connection failed. Service cannot start without database. "
                f"Error: {e}"
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error during MongoDB connection: {e}")
            raise

    async def disconnect(self) -> None:
        """Close MongoDB connection gracefully.

        Should be called at application shutdown to ensure all connections
        are properly closed and resources are released.

        """
        if self._client:
            self._client.close()
            self._client = None
            self._database = None
            logger.info("MongoDB connection closed")

    @property
    def db(self) -> AsyncIOMotorDatabase:
        """Get the MongoDB database instance.

        Returns:
            Motor async database instance

        Raises:
            RuntimeError: If database connection not established

        """
        if self._database is None:
            raise RuntimeError(
                "Database connection not established. "
                "Call connect() at application startup."
            )
        return self._database

    @property
    def client(self) -> AsyncIOMotorClient:
        """Get the MongoDB client instance.

        Returns:
            Motor async client instance

        Raises:
            RuntimeError: If client connection not established

        """
        if self._client is None:
            raise RuntimeError(
                "MongoDB client not established. "
                "Call connect() at application startup."
            )
        return self._client

    async def health_check(self) -> bool:
        """Check if MongoDB connection is healthy.

        Returns:
            True if connection is healthy, False otherwise

        """
        if self._client is None:
            return False

        try:
            # Ping MongoDB with 1 second timeout
            await self._client.admin.command("ping", maxTimeMS=1000)
            return True
        except Exception as e:
            logger.warning(f"MongoDB health check failed: {e}")
            return False


def get_db() -> AsyncIOMotorDatabase:
    """Get MongoDB database instance.

    This is a convenience function for accessing the database from anywhere
    in the application.

    Returns:
        Motor async database instance

    Raises:
        RuntimeError: If database connection not established

    Example:
        from pdfa.db import get_db

        db = get_db()
        user = await db.users.find_one({"user_id": "123"})

    """
    return MongoDBConnection().db


async def ensure_indexes() -> None:
    """Create all required MongoDB indexes.

    This function should be called once at application startup after the
    database connection is established. It creates all necessary indexes
    for optimal query performance and enforces uniqueness constraints.

    The indexes created are:
    - users: user_id (unique), email, login stats
    - jobs: job_id (unique), user_id+created_at, status, analytics, TTL (90 days)
    - oauth_states: state (unique), TTL (10 minutes)
    - audit_logs: user_id+timestamp, event_type, security, TTL (1 year)

    Note: This function is idempotent - it can be called multiple times safely.
    MongoDB will only create indexes that don't already exist.

    """
    db = get_db()
    logger.info("Creating MongoDB indexes...")

    # Users collection indexes
    await db.users.create_index([("user_id", 1)], unique=True, name="idx_user_id")
    await db.users.create_index([("email", 1)], name="idx_email")
    await db.users.create_index(
        [("last_login_at", -1), ("login_count", -1)], name="idx_login_stats"
    )

    # User preferences collection indexes
    await db.user_preferences.create_index(
        [("user_id", 1)], unique=True, name="idx_user_id"
    )

    # Jobs collection indexes
    await db.jobs.create_index([("job_id", 1)], unique=True, name="idx_job_id")
    await db.jobs.create_index(
        [("user_id", 1), ("created_at", -1)], name="idx_user_jobs"
    )
    await db.jobs.create_index(
        [("status", 1), ("created_at", -1)], name="idx_status_created"
    )
    await db.jobs.create_index(
        [("status", 1), ("completed_at", -1), ("duration_seconds", 1)],
        name="idx_analytics",
    )
    # TTL index: Auto-delete jobs after 90 days (7776000 seconds)
    await db.jobs.create_index(
        [("created_at", 1)], expireAfterSeconds=7776000, name="idx_ttl_90days"
    )

    # OAuth states collection indexes
    await db.oauth_states.create_index([("state", 1)], unique=True, name="idx_state")
    # TTL index: Auto-delete OAuth states after 10 minutes (600 seconds)
    await db.oauth_states.create_index(
        [("created_at", 1)], expireAfterSeconds=600, name="idx_ttl_10min"
    )

    # Audit logs collection indexes
    await db.audit_logs.create_index(
        [("user_id", 1), ("timestamp", -1)], name="idx_user_audit"
    )
    await db.audit_logs.create_index(
        [("event_type", 1), ("timestamp", -1)], name="idx_event_type"
    )
    await db.audit_logs.create_index(
        [("event_type", 1), ("ip_address", 1), ("timestamp", -1)], name="idx_security"
    )
    # TTL index: Auto-delete audit logs after 1 year (31536000 seconds)
    await db.audit_logs.create_index(
        [("timestamp", 1)], expireAfterSeconds=31536000, name="idx_ttl_1year"
    )

    # Pairing sessions collection indexes
    await db.pairing_sessions.create_index(
        [("pairing_code", 1)], unique=True, sparse=True, name="idx_pairing_code"
    )
    await db.pairing_sessions.create_index(
        [("desktop_user_id", 1), ("created_at", -1)], name="idx_user_sessions"
    )
    await db.pairing_sessions.create_index(
        [("status", 1), ("desktop_user_id", 1)], name="idx_status_user"
    )
    # TTL index: Auto-delete pairing sessions after expiration
    # expireAfterSeconds=0 means delete immediately when expires_at is reached
    await db.pairing_sessions.create_index(
        [("expires_at", 1)], expireAfterSeconds=0, name="idx_ttl_expiry"
    )

    logger.info(
        "MongoDB indexes created: "
        "users (3), user_preferences (1), jobs (5), oauth_states (2), audit_logs (4), "
        "pairing_sessions (4)"
    )
