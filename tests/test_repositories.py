"""Unit tests for MongoDB repositories.

Following TDD principles, these tests verify repository behavior with mocked MongoDB.
All tests use the auto-mock from conftest.py and do not require a real database.
"""

from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from pdfa.models import AuditLogDocument, JobDocument, OAuthStateDocument, UserDocument
from pdfa.repositories import (
    AuditLogRepository,
    JobRepository,
    OAuthStateRepository,
    UserRepository,
)


class TestUserRepository:
    """Test cases for UserRepository."""

    @pytest.mark.asyncio
    async def test_create_or_update_user_new_user(self, mock_mongodb):
        """Test creating a new user."""
        # Arrange
        repo = UserRepository()
        user = UserDocument(
            user_id="google_123",
            email="newuser@example.com",
            name="New User",
            picture="https://example.com/pic.jpg",
            created_at=datetime(2024, 1, 1),
            last_login_at=datetime(2024, 1, 1),
            login_count=1,
        )

        # Act
        result = await repo.create_or_update_user(user)

        # Assert
        assert result == user
        mock_mongodb.users.update_one.assert_called_once()
        call_args = mock_mongodb.users.update_one.call_args
        assert call_args[0][0] == {"user_id": "google_123"}  # Filter
        assert "$set" in call_args[0][1]  # Update operation
        assert "$inc" in call_args[0][1]  # Increment login_count
        assert call_args[1]["upsert"] is True

    @pytest.mark.asyncio
    async def test_get_user_found(self, mock_mongodb):
        """Test getting an existing user."""
        # Arrange
        repo = UserRepository()
        mock_user_data = {
            "user_id": "google_123",
            "email": "user@example.com",
            "name": "Test User",
            "picture": None,
            "created_at": datetime(2024, 1, 1),
            "last_login_at": datetime(2024, 1, 2),
            "login_count": 5,
        }
        mock_mongodb.users.find_one = AsyncMock(return_value=mock_user_data)

        # Act
        result = await repo.get_user("google_123")

        # Assert
        assert result is not None
        assert result.user_id == "google_123"
        assert result.email == "user@example.com"
        assert result.login_count == 5
        mock_mongodb.users.find_one.assert_called_once_with({"user_id": "google_123"})

    @pytest.mark.asyncio
    async def test_get_user_not_found(self, mock_mongodb):
        """Test getting a non-existent user."""
        # Arrange
        repo = UserRepository()
        mock_mongodb.users.find_one = AsyncMock(return_value=None)

        # Act
        result = await repo.get_user("nonexistent_user")

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_get_user_by_email_found(self, mock_mongodb):
        """Test getting user by email."""
        # Arrange
        repo = UserRepository()
        mock_user_data = {
            "user_id": "google_123",
            "email": "user@example.com",
            "name": "Test User",
            "picture": None,
            "created_at": datetime(2024, 1, 1),
            "last_login_at": datetime(2024, 1, 2),
            "login_count": 3,
        }
        mock_mongodb.users.find_one = AsyncMock(return_value=mock_user_data)

        # Act
        result = await repo.get_user_by_email("user@example.com")

        # Assert
        assert result is not None
        assert result.email == "user@example.com"
        mock_mongodb.users.find_one.assert_called_once_with(
            {"email": "user@example.com"}
        )


class TestJobRepository:
    """Test cases for JobRepository."""

    @pytest.mark.asyncio
    async def test_create_job(self, mock_mongodb):
        """Test creating a new job."""
        # Arrange
        repo = JobRepository()
        job = JobDocument(
            job_id="job-123",
            user_id="google_123",
            status="queued",
            filename="test.pdf",
            config={"pdfa_level": "2"},
            created_at=datetime(2024, 1, 1),
        )

        # Act
        await repo.create_job(job)

        # Assert
        mock_mongodb.jobs.insert_one.assert_called_once()
        call_args = mock_mongodb.jobs.insert_one.call_args[0][0]
        assert call_args["job_id"] == "job-123"
        assert call_args["status"] == "queued"

    @pytest.mark.asyncio
    async def test_update_job_status(self, mock_mongodb):
        """Test updating job status."""
        # Arrange
        repo = JobRepository()

        # Act
        await repo.update_job_status(
            "job-123",
            "completed",
            completed_at=datetime(2024, 1, 1, 10, 30),
            duration_seconds=45.5,
        )

        # Assert
        mock_mongodb.jobs.update_one.assert_called_once()
        call_args = mock_mongodb.jobs.update_one.call_args
        assert call_args[0][0] == {"job_id": "job-123"}
        update_fields = call_args[0][1]["$set"]
        assert update_fields["status"] == "completed"
        assert update_fields["duration_seconds"] == 45.5

    @pytest.mark.asyncio
    async def test_get_job_found(self, mock_mongodb):
        """Test getting an existing job."""
        # Arrange
        repo = JobRepository()
        mock_job_data = {
            "job_id": "job-123",
            "user_id": "google_123",
            "status": "completed",
            "filename": "test.pdf",
            "config": {"pdfa_level": "2"},
            "created_at": datetime(2024, 1, 1),
            "started_at": datetime(2024, 1, 1, 10, 0),
            "completed_at": datetime(2024, 1, 1, 10, 30),
            "duration_seconds": 30.0,
            "file_size_input": 1024,
            "file_size_output": 512,
            "compression_ratio": 0.5,
            "error": None,
        }
        mock_mongodb.jobs.find_one = AsyncMock(return_value=mock_job_data)

        # Act
        result = await repo.get_job("job-123")

        # Assert
        assert result is not None
        assert result.job_id == "job-123"
        assert result.status == "completed"
        assert result.duration_seconds == 30.0

    @pytest.mark.asyncio
    async def test_get_user_jobs_with_pagination(self, mock_mongodb):
        """Test getting user jobs with pagination."""
        # Arrange
        repo = JobRepository()
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(
            return_value=[
                {
                    "job_id": "job-1",
                    "user_id": "google_123",
                    "status": "completed",
                    "filename": "file1.pdf",
                    "config": {},
                    "created_at": datetime(2024, 1, 2),
                },
                {
                    "job_id": "job-2",
                    "user_id": "google_123",
                    "status": "completed",
                    "filename": "file2.pdf",
                    "config": {},
                    "created_at": datetime(2024, 1, 1),
                },
            ]
        )

        mock_find = MagicMock(return_value=mock_cursor)
        mock_mongodb.jobs.find = mock_find
        mock_cursor.sort = MagicMock(return_value=mock_cursor)
        mock_cursor.skip = MagicMock(return_value=mock_cursor)
        mock_cursor.limit = MagicMock(return_value=mock_cursor)

        # Act
        result = await repo.get_user_jobs("google_123", limit=2, offset=0)

        # Assert
        assert len(result) == 2
        assert result[0].job_id == "job-1"
        mock_cursor.sort.assert_called_once_with("created_at", -1)
        mock_cursor.skip.assert_called_once_with(0)
        mock_cursor.limit.assert_called_once_with(2)

    @pytest.mark.asyncio
    async def test_get_user_jobs_with_status_filter(self, mock_mongodb):
        """Test getting user jobs filtered by status."""
        # Arrange
        repo = JobRepository()
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=[])
        mock_find = MagicMock(return_value=mock_cursor)
        mock_mongodb.jobs.find = mock_find
        mock_cursor.sort = MagicMock(return_value=mock_cursor)
        mock_cursor.skip = MagicMock(return_value=mock_cursor)
        mock_cursor.limit = MagicMock(return_value=mock_cursor)

        # Act
        await repo.get_user_jobs("google_123", status="completed")

        # Assert
        # Verify filter includes status
        call_args = mock_find.call_args[0][0]
        assert call_args["user_id"] == "google_123"
        assert call_args["status"] == "completed"

    @pytest.mark.asyncio
    async def test_get_job_stats(self, mock_mongodb):
        """Test getting job statistics for a user."""
        # Arrange
        repo = JobRepository()
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(
            return_value=[
                {
                    "total_jobs": 10,
                    "completed_jobs": 8,
                    "failed_jobs": 2,
                    "avg_duration_seconds": 45.5,
                    "total_input_bytes": 10485760,
                    "total_output_bytes": 5242880,
                    "avg_compression_ratio": 0.5,
                }
            ]
        )
        mock_mongodb.jobs.aggregate = MagicMock(return_value=mock_cursor)

        # Act
        result = await repo.get_job_stats("google_123")

        # Assert
        assert result["total_jobs"] == 10
        assert result["completed_jobs"] == 8
        assert result["failed_jobs"] == 2
        assert result["avg_duration_seconds"] == 45.5
        mock_mongodb.jobs.aggregate.assert_called_once()


class TestOAuthStateRepository:
    """Test cases for OAuthStateRepository."""

    @pytest.mark.asyncio
    async def test_create_state(self, mock_mongodb):
        """Test creating an OAuth state token."""
        # Arrange
        repo = OAuthStateRepository()
        state = OAuthStateDocument(
            state="random-state-token-12345",
            created_at=datetime(2024, 1, 1, 10, 0),
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0",
        )

        # Act
        await repo.create_state(state)

        # Assert
        mock_mongodb.oauth_states.insert_one.assert_called_once()
        call_args = mock_mongodb.oauth_states.insert_one.call_args[0][0]
        assert call_args["state"] == "random-state-token-12345"

    @pytest.mark.asyncio
    async def test_validate_and_delete_state_valid(self, mock_mongodb):
        """Test validating and deleting a valid state token."""
        # Arrange
        repo = OAuthStateRepository()
        mock_mongodb.oauth_states.find_one_and_delete = AsyncMock(
            return_value={
                "state": "valid-token",
                "created_at": datetime(2024, 1, 1),
            }
        )

        # Act
        result = await repo.validate_and_delete_state("valid-token")

        # Assert
        assert result is True
        mock_mongodb.oauth_states.find_one_and_delete.assert_called_once_with(
            {"state": "valid-token"}
        )

    @pytest.mark.asyncio
    async def test_validate_and_delete_state_invalid(self, mock_mongodb):
        """Test validating an invalid/expired state token."""
        # Arrange
        repo = OAuthStateRepository()
        mock_mongodb.oauth_states.find_one_and_delete = AsyncMock(return_value=None)

        # Act
        result = await repo.validate_and_delete_state("invalid-token")

        # Assert
        assert result is False


class TestAuditLogRepository:
    """Test cases for AuditLogRepository."""

    @pytest.mark.asyncio
    async def test_log_event(self, mock_mongodb):
        """Test logging an audit event."""
        # Arrange
        repo = AuditLogRepository()
        event = AuditLogDocument(
            event_type="user_login",
            user_id="google_123",
            timestamp=datetime(2024, 1, 1, 10, 0),
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0",
            details={"method": "google_oauth"},
        )

        # Act
        await repo.log_event(event)

        # Assert
        mock_mongodb.audit_logs.insert_one.assert_called_once()
        call_args = mock_mongodb.audit_logs.insert_one.call_args[0][0]
        assert call_args["event_type"] == "user_login"
        assert call_args["user_id"] == "google_123"

    @pytest.mark.asyncio
    async def test_get_user_events(self, mock_mongodb):
        """Test getting audit events for a user."""
        # Arrange
        repo = AuditLogRepository()
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(
            return_value=[
                {
                    "event_type": "user_login",
                    "user_id": "google_123",
                    "timestamp": datetime(2024, 1, 1, 10, 0),
                    "ip_address": "192.168.1.100",
                    "user_agent": "Mozilla/5.0",
                    "details": {},
                }
            ]
        )
        mock_find = MagicMock(return_value=mock_cursor)
        mock_mongodb.audit_logs.find = mock_find
        mock_cursor.sort = MagicMock(return_value=mock_cursor)
        mock_cursor.skip = MagicMock(return_value=mock_cursor)
        mock_cursor.limit = MagicMock(return_value=mock_cursor)

        # Act
        result = await repo.get_user_events("google_123", limit=10)

        # Assert
        assert len(result) == 1
        assert result[0].event_type == "user_login"
        mock_cursor.sort.assert_called_once_with("timestamp", -1)

    @pytest.mark.asyncio
    async def test_get_user_events_with_type_filter(self, mock_mongodb):
        """Test getting audit events filtered by event type."""
        # Arrange
        repo = AuditLogRepository()
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=[])
        mock_find = MagicMock(return_value=mock_cursor)
        mock_mongodb.audit_logs.find = mock_find
        mock_cursor.sort = MagicMock(return_value=mock_cursor)
        mock_cursor.skip = MagicMock(return_value=mock_cursor)
        mock_cursor.limit = MagicMock(return_value=mock_cursor)

        # Act
        await repo.get_user_events("google_123", event_type="user_login")

        # Assert
        call_args = mock_find.call_args[0][0]
        assert call_args["user_id"] == "google_123"
        assert call_args["event_type"] == "user_login"

    @pytest.mark.asyncio
    async def test_get_security_events(self, mock_mongodb):
        """Test getting recent security-related events."""
        # Arrange
        repo = AuditLogRepository()
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(
            return_value=[
                {
                    "event_type": "auth_failure",
                    "user_id": None,
                    "timestamp": datetime(2024, 1, 1, 10, 0),
                    "ip_address": "192.168.1.100",
                    "user_agent": None,
                    "details": {"reason": "invalid_state"},
                }
            ]
        )
        mock_find = MagicMock(return_value=mock_cursor)
        mock_mongodb.audit_logs.find = mock_find
        mock_cursor.sort = MagicMock(return_value=mock_cursor)
        mock_cursor.limit = MagicMock(return_value=mock_cursor)

        # Act
        result = await repo.get_security_events(
            event_types=["auth_failure", "user_login"], hours=24
        )

        # Assert
        assert len(result) == 1
        assert result[0].event_type == "auth_failure"
        # Verify query includes event_type filter and timestamp threshold
        call_args = mock_find.call_args[0][0]
        assert "$in" in call_args["event_type"]
        assert "$gte" in call_args["timestamp"]
