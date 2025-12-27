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


class TestJobRepositoryEvents:
    """Test cases for JobRepository event logging methods."""

    @pytest.mark.asyncio
    async def test_add_job_event(self, mock_mongodb):
        """Should add event to job's events array using $push."""
        # Arrange
        from pdfa.models import JobEvent

        repo = JobRepository()
        job_id = "test-job-123"
        event = JobEvent(
            event_type="ocr_decision",
            message="OCR skipped",
            details={"reason": "tagged_pdf", "has_struct_tree_root": True},
        )

        # Act
        await repo.add_job_event(job_id, event)

        # Assert
        mock_mongodb.jobs.update_one.assert_called_once()
        call_args = mock_mongodb.jobs.update_one.call_args
        assert call_args[0][0] == {"job_id": job_id}  # Filter by job_id
        assert "$push" in call_args[0][1]  # Should use $push operator
        assert "events" in call_args[0][1]["$push"]  # Push to events array

        # Verify event data structure
        pushed_event = call_args[0][1]["$push"]["events"]
        assert pushed_event["event_type"] == "ocr_decision"
        assert pushed_event["message"] == "OCR skipped"
        assert pushed_event["details"]["reason"] == "tagged_pdf"

    @pytest.mark.asyncio
    async def test_add_multiple_job_events_in_order(self, mock_mongodb):
        """Should add multiple events in the order they are logged."""
        repo = JobRepository()
        job_id = "test-job-123"

        # Import JobEvent directly to avoid circular import issues
        from pdfa.models import JobEvent

        event1 = JobEvent(
            event_type="format_conversion",
            message="Converted Office to PDF",
            details={"source_format": "docx"},
        )
        event2 = JobEvent(
            event_type="ocr_decision",
            message="OCR decision made",
            details={"decision": "skip"},
        )
        event3 = JobEvent(
            event_type="compression_selected",
            message="Compression profile selected",
            details={"profile": "balanced"},
        )

        # Act
        await repo.add_job_event(job_id, event1)
        await repo.add_job_event(job_id, event2)
        await repo.add_job_event(job_id, event3)

        # Assert
        assert mock_mongodb.jobs.update_one.call_count == 3

        # Verify events were pushed in order
        calls = mock_mongodb.jobs.update_one.call_args_list
        assert calls[0][0][1]["$push"]["events"]["event_type"] == "format_conversion"
        assert calls[1][0][1]["$push"]["events"]["event_type"] == "ocr_decision"
        assert calls[2][0][1]["$push"]["events"]["event_type"] == "compression_selected"

    @pytest.mark.asyncio
    async def test_get_job_with_events(self, mock_mongodb):
        """Should retrieve job with events correctly."""
        repo = JobRepository()

        # Mock MongoDB response with events
        mock_job_data = {
            "job_id": "test-123",
            "user_id": "user-456",
            "status": "completed",
            "filename": "test.pdf",
            "config": {"pdfa_level": "2"},
            "created_at": datetime(2024, 1, 1, 10, 0, 0),
            "completed_at": datetime(2024, 1, 1, 10, 2, 30),
            "events": [
                {
                    "timestamp": datetime(2024, 1, 1, 10, 0, 1),
                    "event_type": "format_conversion",
                    "message": "Converted Office to PDF",
                    "details": {
                        "source_format": "docx",
                        "conversion_time_seconds": 3.2,
                    },
                },
                {
                    "timestamp": datetime(2024, 1, 1, 10, 0, 5),
                    "event_type": "ocr_decision",
                    "message": "OCR skipped due to tagged PDF",
                    "details": {"decision": "skip", "reason": "tagged_pdf"},
                },
                {
                    "timestamp": datetime(2024, 1, 1, 10, 0, 6),
                    "event_type": "compression_selected",
                    "message": "Compression profile auto-switched",
                    "details": {
                        "profile": "preserve",
                        "reason": "auto_switched_for_tagged_pdf",
                    },
                },
            ],
        }
        mock_mongodb.jobs.find_one = AsyncMock(return_value=mock_job_data)

        # Act
        job = await repo.get_job("test-123")

        # Assert
        assert job is not None
        assert len(job.events) == 3
        assert job.events[0].event_type == "format_conversion"
        assert job.events[0].details["source_format"] == "docx"
        assert job.events[1].event_type == "ocr_decision"
        assert job.events[1].details["reason"] == "tagged_pdf"
        assert job.events[2].event_type == "compression_selected"
        assert job.events[2].details["profile"] == "preserve"

    @pytest.mark.asyncio
    async def test_get_job_backward_compatibility_no_events(self, mock_mongodb):
        """Should handle old jobs without events field (backward compatibility)."""
        repo = JobRepository()

        # Mock old job document WITHOUT events field
        mock_job_data = {
            "job_id": "old-job",
            "status": "completed",
            "filename": "old.pdf",
            "config": {},
            "created_at": datetime(2024, 1, 1, 10, 0, 0),
            # NO events field - simulating old document
        }
        mock_mongodb.jobs.find_one = AsyncMock(return_value=mock_job_data)

        # Act
        job = await repo.get_job("old-job")

        # Assert
        assert job is not None
        assert job.events == []  # Should default to empty list
        assert isinstance(job.events, list)

    @pytest.mark.asyncio
    async def test_add_job_event_with_complex_details(self, mock_mongodb):
        """Should handle events with complex nested details."""
        repo = JobRepository()
        job_id = "test-job-123"

        from pdfa.models import JobEvent

        event = JobEvent(
            event_type="fallback_applied",
            message="Fallback tier 2 applied due to Ghostscript error",
            details={
                "tier": 2,
                "reason": "ghostscript_error",
                "original_error": "SubprocessOutputError: ...",
                "safe_mode_config": {
                    "image_dpi": 100,
                    "remove_vectors": False,
                    "optimize": 0,
                    "jbig2_lossy": False,
                },
                "pdfa_level_downgrade": {
                    "original": "3",
                    "fallback": "2",
                },
            },
        )

        # Act
        await repo.add_job_event(job_id, event)

        # Assert
        call_args = mock_mongodb.jobs.update_one.call_args
        pushed_event = call_args[0][1]["$push"]["events"]

        assert pushed_event["details"]["tier"] == 2
        assert pushed_event["details"]["safe_mode_config"]["image_dpi"] == 100
        assert pushed_event["details"]["pdfa_level_downgrade"]["original"] == "3"

    @pytest.mark.asyncio
    async def test_get_user_jobs_returns_events(self, mock_mongodb):
        """Should return events_count but not events array (performance optimization)."""
        repo = JobRepository()

        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(
            return_value=[
                {
                    "job_id": "job-1",
                    "user_id": "user-123",
                    "status": "completed",
                    "filename": "file1.pdf",
                    "config": {},
                    "created_at": datetime(2024, 1, 2),
                    "events": [
                        {
                            "timestamp": datetime(2024, 1, 2, 10, 0, 0),
                            "event_type": "format_conversion",
                            "message": "Direct PDF",
                            "details": {"source_format": "pdf"},
                        }
                    ],
                },
                {
                    "job_id": "job-2",
                    "user_id": "user-123",
                    "status": "completed",
                    "filename": "file2.pdf",
                    "config": {},
                    "created_at": datetime(2024, 1, 1),
                    "events": [],  # Empty events array
                },
            ]
        )

        mock_find = MagicMock(return_value=mock_cursor)
        mock_mongodb.jobs.find = mock_find
        mock_cursor.sort = MagicMock(return_value=mock_cursor)
        mock_cursor.skip = MagicMock(return_value=mock_cursor)
        mock_cursor.limit = MagicMock(return_value=mock_cursor)

        # Act
        result = await repo.get_user_jobs("user-123", limit=2, offset=0)

        # Assert - Performance optimization: events removed, events_count added
        assert len(result) == 2
        assert result[0].events_count == 1  # 1 event in source data
        assert len(result[0].events) == 0  # Events array should be empty (removed)
        assert result[1].events_count == 0  # 0 events in source data
