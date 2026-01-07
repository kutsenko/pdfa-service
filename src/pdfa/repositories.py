"""Repository pattern for MongoDB data access.

This module provides the data access layer for all MongoDB collections.
Each repository encapsulates database operations for a specific collection,
providing a clean interface for the application layer.

The repository pattern offers several benefits:
- Abstraction over database implementation
- Easier testing with mocked repositories
- Centralized query logic
- Type-safe database operations
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from pdfa.db import get_db
from pdfa.models import (
    AuditLogDocument,
    JobDocument,
    JobEvent,
    OAuthStateDocument,
    PairingSessionDocument,
    UserDocument,
    UserPreferencesDocument,
)

logger = logging.getLogger(__name__)


class UserRepository:
    """Repository for user collection operations.

    Provides methods for creating, updating, and querying user profiles.
    Users are typically created or updated on each successful login.

    """

    async def create_or_update_user(self, user: UserDocument) -> UserDocument:
        """Create a new user or update existing user on login.

        This method performs an upsert operation: if the user exists (by user_id),
        it updates the profile and increments the login count. Otherwise, it creates
        a new user document.

        Args:
            user: User document to create or update

        Returns:
            The created or updated user document

        Example:
            user = UserDocument(
                user_id="google_123",
                email="user@example.com",
                name="John Doe",
                picture="https://...",
                created_at=datetime.now(UTC),
                last_login_at=datetime.now(UTC),
                login_count=1
            )
            await user_repo.create_or_update_user(user)

        """
        db = get_db()

        # Upsert: update if exists, insert if new
        # Also increment login_count on each login
        await db.users.update_one(
            {"user_id": user.user_id},
            {
                "$set": {
                    "email": user.email,
                    "name": user.name,
                    "picture": user.picture,
                    "last_login_at": user.last_login_at,
                },
                "$setOnInsert": {
                    "user_id": user.user_id,
                    "created_at": user.created_at,
                },
                "$inc": {"login_count": 1},
            },
            upsert=True,
        )

        logger.debug(
            f"User profile updated: user_id={user.user_id}, email={user.email}"
        )
        return user

    async def get_user(self, user_id: str) -> UserDocument | None:
        """Get user by user_id.

        Args:
            user_id: Google user ID

        Returns:
            User document if found, None otherwise

        """
        db = get_db()
        user_data = await db.users.find_one({"user_id": user_id})
        if user_data:
            return UserDocument(**user_data)
        return None

    async def get_user_by_email(self, email: str) -> UserDocument | None:
        """Get user by email address.

        Args:
            email: User email address

        Returns:
            User document if found, None otherwise

        """
        db = get_db()
        user_data = await db.users.find_one({"email": email})
        if user_data:
            return UserDocument(**user_data)
        return None


class UserPreferencesRepository:
    """Repository for user preferences collection operations.

    Provides methods for creating, updating, and querying user preferences
    for default conversion parameters.

    """

    async def get_preferences(self, user_id: str) -> UserPreferencesDocument | None:
        """Get user preferences by user_id.

        Args:
            user_id: User identifier

        Returns:
            UserPreferencesDocument if found, None otherwise

        Example:
            prefs = await user_prefs_repo.get_preferences("google_123")
            if prefs:
                print(f"Default PDF type: {prefs.default_pdfa_level}")

        """
        db = get_db()
        doc = await db.user_preferences.find_one({"user_id": user_id})
        return UserPreferencesDocument(**doc) if doc else None

    async def create_or_update_preferences(
        self, prefs: UserPreferencesDocument
    ) -> UserPreferencesDocument:
        """Create or update user preferences.

        Performs an upsert operation: if preferences exist for this user,
        they are updated. Otherwise, new preferences are created.

        Args:
            prefs: Preferences document to save

        Returns:
            Updated preferences document

        Example:
            prefs = UserPreferencesDocument(
                user_id="google_123",
                default_pdfa_level="standard",
                default_ocr_language="eng"
            )
            updated = await user_prefs_repo.create_or_update_preferences(prefs)

        """
        db = get_db()
        prefs.updated_at = datetime.now(UTC)

        await db.user_preferences.update_one(
            {"user_id": prefs.user_id}, {"$set": prefs.model_dump()}, upsert=True
        )

        logger.debug(
            f"User preferences updated: user_id={prefs.user_id}, "
            f"pdfa_level={prefs.default_pdfa_level}"
        )
        return prefs

    async def delete_preferences(self, user_id: str) -> bool:
        """Delete user preferences.

        Args:
            user_id: User identifier

        Returns:
            True if deleted, False if not found

        Example:
            deleted = await user_prefs_repo.delete_preferences("google_123")
            if deleted:
                print("Preferences removed successfully")

        """
        db = get_db()
        result = await db.user_preferences.delete_one({"user_id": user_id})
        deleted = result.deleted_count > 0

        if deleted:
            logger.debug(f"User preferences deleted: user_id={user_id}")

        return deleted


class JobRepository:
    """Repository for job collection operations.

    Provides methods for creating, updating, and querying conversion jobs.
    Jobs persist conversion history and enable analytics.

    """

    async def create_job(self, job: JobDocument) -> None:
        """Create a new job document.

        Args:
            job: Job document to create

        Example:
            job = JobDocument(
                job_id="uuid-123",
                user_id="google_123",
                status="queued",
                filename="document.pdf",
                config={"pdfa_level": "2"},
                created_at=datetime.now(UTC)
            )
            await job_repo.create_job(job)

        """
        db = get_db()
        job_dict = job.model_dump()
        await db.jobs.insert_one(job_dict)
        logger.debug(f"Job created: job_id={job.job_id}, user_id={job.user_id}")

    async def update_job_status(
        self,
        job_id: str,
        status: str,
        **kwargs: Any,
    ) -> None:
        """Update job status and optionally other fields.

        Args:
            job_id: Job identifier
            status: New status value
            **kwargs: Additional fields to update (e.g., error,
                     completed_at, duration_seconds)

        Example:
            await job_repo.update_job_status(
                "uuid-123",
                "completed",
                completed_at=datetime.now(UTC),
                duration_seconds=45.2,
                file_size_output=524288
            )

        """
        db = get_db()
        update_fields = {"status": status, **kwargs}
        await db.jobs.update_one({"job_id": job_id}, {"$set": update_fields})
        logger.debug(f"Job updated: job_id={job_id}, status={status}")

    async def get_job(self, job_id: str) -> JobDocument | None:
        """Get job by job_id.

        Args:
            job_id: Job identifier

        Returns:
            Job document if found, None otherwise

        """
        db = get_db()
        job_data = await db.jobs.find_one({"job_id": job_id})
        if job_data:
            return JobDocument(**job_data)
        return None

    async def get_user_jobs(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
        status: str | None = None,
    ) -> list[JobDocument]:
        """Get jobs for a specific user with pagination.

        Args:
            user_id: User identifier
            limit: Maximum number of jobs to return (default: 50)
            offset: Number of jobs to skip (default: 0)
            status: Filter by status (optional)

        Returns:
            List of job documents sorted by created_at (newest first)

        Example:
            # Get latest 50 jobs for user
            jobs = await job_repo.get_user_jobs("google_123")

            # Get completed jobs only
            completed = await job_repo.get_user_jobs("google_123", status="completed")

            # Pagination: get next 50 jobs
            next_page = await job_repo.get_user_jobs("google_123", offset=50)

        """
        db = get_db()

        # Build query filter
        query_filter: dict[str, Any] = {"user_id": user_id}
        if status:
            query_filter["status"] = status

        # Execute query with pagination and sorting
        cursor = (
            db.jobs.find(query_filter)
            .sort("created_at", -1)  # Newest first
            .skip(offset)
            .limit(limit)
        )

        jobs_data = await cursor.to_list(length=limit)

        # Performance optimization: Add events_count, remove events array
        # This significantly reduces response size for job lists
        # (20 jobs × 10 events = 200 events = ~50KB)
        for job_data in jobs_data:
            job_data["events_count"] = len(job_data.get("events", []))
            job_data.pop("events", None)

        return [JobDocument(**job_data) for job_data in jobs_data]

    async def get_job_stats(self, user_id: str) -> dict[str, Any]:
        """Get job statistics for a user.

        Args:
            user_id: User identifier

        Returns:
            Dictionary with job statistics:
            - total_jobs: Total number of jobs
            - completed_jobs: Number of completed jobs
            - failed_jobs: Number of failed jobs
            - avg_duration_seconds: Average processing duration
            - total_input_bytes: Total input file size
            - total_output_bytes: Total output file size
            - avg_compression_ratio: Average compression ratio

        """
        db = get_db()

        # Aggregation pipeline for statistics
        pipeline = [
            {"$match": {"user_id": user_id}},
            {
                "$group": {
                    "_id": None,
                    "total_jobs": {"$sum": 1},
                    "completed_jobs": {
                        "$sum": {"$cond": [{"$eq": ["$status", "completed"]}, 1, 0]}
                    },
                    "failed_jobs": {
                        "$sum": {"$cond": [{"$eq": ["$status", "failed"]}, 1, 0]}
                    },
                    "avg_duration_seconds": {"$avg": "$duration_seconds"},
                    "total_input_bytes": {"$sum": "$file_size_input"},
                    "total_output_bytes": {"$sum": "$file_size_output"},
                    "avg_compression_ratio": {"$avg": "$compression_ratio"},
                }
            },
        ]

        result = await db.jobs.aggregate(pipeline).to_list(length=1)
        if result:
            stats = result[0]
            stats.pop("_id", None)  # Remove MongoDB _id field
            return stats
        return {
            "total_jobs": 0,
            "completed_jobs": 0,
            "failed_jobs": 0,
            "avg_duration_seconds": 0,
            "total_input_bytes": 0,
            "total_output_bytes": 0,
            "avg_compression_ratio": 0,
        }

    async def add_job_event(
        self,
        job_id: str,
        event: JobEvent,
    ) -> None:
        """Add an event to a job's event log.

        Uses MongoDB's $push operator to atomically append the event to the
        job's events array. This operation is thread-safe and does not require
        reading the document first.

        Args:
            job_id: Job identifier
            event: Event to add to the job's history

        Example:
            event = JobEvent(
                event_type="ocr_decision",
                message="OCR skipped due to tagged PDF",
                details={"reason": "tagged_pdf", "has_struct_tree_root": True}
            )
            await job_repo.add_job_event("uuid-123", event)

        """
        db = get_db()
        event_dict = event.model_dump()

        # Use upsert to handle race condition where events are logged
        # before job document is created in MongoDB
        result = await db.jobs.update_one(
            {"job_id": job_id},
            {"$push": {"events": event_dict}},
            upsert=False,  # Don't create new doc, just update if exists
        )

        if result.matched_count == 0:
            # Job document doesn't exist yet - this can happen due to race condition
            # between async job creation and event logging
            logger.warning(
                f"Event logged for non-existent job {job_id} (race condition): "
                f"{event.event_type}"
            )
        else:
            logger.debug(
                f"Event logged for job {job_id}: {event.event_type} - {event.message}"
            )


class OAuthStateRepository:
    """Repository for OAuth state token operations.

    Provides methods for creating and validating OAuth state tokens
    used in CSRF protection during OAuth authorization flow.

    State tokens have a 10-minute TTL and are automatically cleaned up by MongoDB.

    """

    async def create_state(self, state_doc: OAuthStateDocument) -> None:
        """Create a new OAuth state token.

        Args:
            state_doc: OAuth state document to create

        Example:
            state = OAuthStateDocument(
                state="random-token",
                created_at=datetime.now(UTC),
                ip_address="192.168.1.100",
                user_agent="Mozilla/5.0..."
            )
            await oauth_repo.create_state(state)

        """
        db = get_db()
        state_dict = state_doc.model_dump()
        await db.oauth_states.insert_one(state_dict)
        logger.debug(f"OAuth state created: state={state_doc.state[:16]}...")

    async def validate_and_delete_state(self, state_token: str) -> bool:
        """Validate OAuth state token and delete if valid.

        This is an atomic operation that validates the state exists and
        deletes it in one database call to prevent replay attacks.

        Args:
            state_token: State token to validate

        Returns:
            True if state was valid and deleted, False if not found or expired

        """
        db = get_db()
        result = await db.oauth_states.find_one_and_delete({"state": state_token})

        if result:
            logger.debug(
                f"OAuth state validated and deleted: state={state_token[:16]}..."
            )
            return True

        logger.warning(f"OAuth state validation failed: state={state_token[:16]}...")
        return False


class AuditLogRepository:
    """Repository for audit log operations.

    Provides methods for creating and querying audit logs for security,
    compliance, and analytics purposes.

    Audit logs have a 1-year TTL and are automatically cleaned up by MongoDB.

    """

    async def log_event(self, event: AuditLogDocument) -> None:
        """Log an audit event.

        Args:
            event: Audit log document to create

        Example:
            event = AuditLogDocument(
                event_type="user_login",
                user_id="google_123",
                timestamp=datetime.now(UTC),
                ip_address="192.168.1.100",
                user_agent="Mozilla/5.0...",
                details={"method": "google_oauth"}
            )
            await audit_repo.log_event(event)

        """
        db = get_db()
        event_dict = event.model_dump()
        await db.audit_logs.insert_one(event_dict)
        logger.debug(
            f"Audit event logged: type={event.event_type}, user_id={event.user_id}"
        )

    async def get_user_events(
        self,
        user_id: str,
        event_type: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditLogDocument]:
        """Get audit events for a specific user.

        Args:
            user_id: User identifier
            event_type: Filter by event type (optional)
            limit: Maximum number of events to return (default: 100)
            offset: Number of events to skip (default: 0)

        Returns:
            List of audit log documents sorted by timestamp (newest first)

        """
        db = get_db()

        # Build query filter
        query_filter: dict[str, Any] = {"user_id": user_id}
        if event_type:
            query_filter["event_type"] = event_type

        cursor = (
            db.audit_logs.find(query_filter)
            .sort("timestamp", -1)
            .skip(offset)
            .limit(limit)
        )

        events_data = await cursor.to_list(length=limit)
        return [AuditLogDocument(**event_data) for event_data in events_data]

    async def get_security_events(
        self,
        event_types: list[str],
        hours: int = 24,
        limit: int = 1000,
    ) -> list[AuditLogDocument]:
        """Get recent security-related events.

        Args:
            event_types: List of event types to query
                        (e.g., ["auth_failure", "user_login"])
            hours: Number of hours to look back (default: 24)
            limit: Maximum number of events to return (default: 1000)

        Returns:
            List of audit log documents sorted by timestamp (newest first)

        """
        db = get_db()

        # Calculate timestamp threshold
        threshold = datetime.now(UTC).timestamp() - (hours * 3600)
        threshold_dt = datetime.fromtimestamp(threshold)

        query_filter = {
            "event_type": {"$in": event_types},
            "timestamp": {"$gte": threshold_dt},
        }

        cursor = db.audit_logs.find(query_filter).sort("timestamp", -1).limit(limit)

        events_data = await cursor.to_list(length=limit)
        return [AuditLogDocument(**event_data) for event_data in events_data]


class PairingSessionRepository:
    """Repository for mobile-desktop camera pairing sessions.

    Manages temporary pairing sessions that link desktop and mobile devices
    for real-time image transfer during camera workflows.

    """

    async def create_session(self, session: PairingSessionDocument) -> None:
        """Create new pairing session.

        Args:
            session: Pairing session document to create

        Example:
            >>> session = PairingSessionDocument(
            ...     session_id=str(uuid.uuid4()),
            ...     pairing_code="ABC123",
            ...     desktop_user_id="user-123",
            ...     status="pending",
            ...     created_at=datetime.now(UTC),
            ...     expires_at=datetime.now(UTC) + timedelta(minutes=30),
            ...     last_activity_at=datetime.now(UTC)
            ... )
            >>> await repo.create_session(session)

        """
        db = get_db()
        await db.pairing_sessions.insert_one(session.model_dump())
        logger.debug(f"Created pairing session: {session.session_id}")

    async def get_session(self, session_id: str) -> PairingSessionDocument | None:
        """Get pairing session by ID.

        Args:
            session_id: Session identifier (UUID)

        Returns:
            Pairing session document if found, None otherwise

        """
        db = get_db()
        doc = await db.pairing_sessions.find_one({"session_id": session_id})
        return PairingSessionDocument(**doc) if doc else None

    async def find_by_code(self, code: str) -> PairingSessionDocument | None:
        """Find active pairing session by pairing code.

        Only returns sessions with status 'pending' or 'active'.

        Args:
            code: Pairing code (6-8 alphanumeric characters)

        Returns:
            Active pairing session if found, None otherwise

        """
        db = get_db()
        doc = await db.pairing_sessions.find_one(
            {"pairing_code": code, "status": {"$in": ["pending", "active"]}}
        )
        return PairingSessionDocument(**doc) if doc else None

    async def update_session(self, session: PairingSessionDocument) -> None:
        """Update existing pairing session.

        Args:
            session: Updated pairing session document

        """
        db = get_db()
        await db.pairing_sessions.update_one(
            {"session_id": session.session_id}, {"$set": session.model_dump()}
        )
        logger.debug(f"Updated pairing session: {session.session_id}")

    async def increment_images_synced(self, session_id: str) -> None:
        """Increment the images synced counter for a session.

        Args:
            session_id: Session identifier (UUID)

        """
        db = get_db()
        await db.pairing_sessions.update_one(
            {"session_id": session_id},
            {
                "$inc": {"images_synced": 1},
                "$set": {"last_activity_at": datetime.now(UTC)},
            },
        )
        logger.debug(f"Incremented images_synced for session: {session_id}")
