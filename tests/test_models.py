"""Unit tests for data models.

Following TDD principles, these tests verify model behavior before implementation.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from pdfa.models import JobDocument, JobEvent


class TestJobEvent:
    """Test cases for JobEvent model."""

    def test_job_event_creation_with_defaults(self):
        """JobEvent should auto-populate timestamp."""
        event = JobEvent(
            event_type="ocr_decision",
            message="OCR skipped due to tagged PDF",
            details={"reason": "tagged_pdf"},
        )

        assert event.timestamp is not None
        assert isinstance(event.timestamp, datetime)
        assert event.event_type == "ocr_decision"
        assert event.message == "OCR skipped due to tagged PDF"
        assert event.details["reason"] == "tagged_pdf"

    def test_job_event_creation_with_explicit_timestamp(self):
        """JobEvent should accept explicit timestamp."""
        explicit_time = datetime(2024, 1, 1, 12, 0, 0)
        event = JobEvent(
            timestamp=explicit_time,
            event_type="format_conversion",
            message="Converted Office to PDF",
            details={"source_format": "docx"},
        )

        assert event.timestamp == explicit_time
        assert event.event_type == "format_conversion"

    def test_job_event_invalid_type(self):
        """JobEvent should reject invalid event_type."""
        with pytest.raises(ValidationError) as exc_info:
            JobEvent(
                event_type="invalid_type",  # Not in Literal
                message="Test",
                details={},
            )

        # Check that the error mentions the invalid value
        assert "invalid_type" in str(exc_info.value)

    def test_job_event_all_valid_event_types(self):
        """JobEvent should accept all defined event types."""
        valid_types = [
            "format_conversion",
            "ocr_decision",
            "compression_selected",
            "passthrough_mode",
            "fallback_applied",
            "job_timeout",
            "job_cleanup",
        ]

        for event_type in valid_types:
            event = JobEvent(
                event_type=event_type,
                message=f"Test {event_type}",
                details={},
            )
            assert event.event_type == event_type

    def test_job_event_serialization(self):
        """JobEvent should serialize to dict correctly."""
        event = JobEvent(
            timestamp=datetime(2024, 1, 1, 12, 0, 0),
            event_type="format_conversion",
            message="Converted Office to PDF",
            details={"source_format": "docx", "conversion_time_seconds": 3.2},
        )

        data = event.model_dump()

        assert data["event_type"] == "format_conversion"
        assert data["message"] == "Converted Office to PDF"
        assert data["details"]["source_format"] == "docx"
        assert data["details"]["conversion_time_seconds"] == 3.2
        assert isinstance(data["timestamp"], datetime)

    def test_job_event_empty_details(self):
        """JobEvent should allow empty details dict."""
        event = JobEvent(
            event_type="job_cleanup",
            message="Job cleaned up",
            details={},
        )

        assert event.details == {}

    def test_job_event_complex_details(self):
        """JobEvent should handle complex nested details."""
        event = JobEvent(
            event_type="fallback_applied",
            message="Fallback tier 2 applied",
            details={
                "tier": 2,
                "reason": "ghostscript_error",
                "safe_mode_config": {
                    "image_dpi": 100,
                    "remove_vectors": False,
                    "optimize": 0,
                },
                "pdfa_level_downgrade": {"original": "3", "fallback": "2"},
            },
        )

        assert event.details["tier"] == 2
        assert event.details["safe_mode_config"]["image_dpi"] == 100
        assert event.details["pdfa_level_downgrade"]["original"] == "3"


class TestJobDocumentWithEvents:
    """Test cases for JobDocument with events field."""

    def test_job_document_default_empty_events(self):
        """JobDocument should have empty events list by default."""
        job = JobDocument(
            job_id="test-123",
            status="queued",
            filename="test.pdf",
            config={},
            created_at=datetime.now(UTC),
        )

        assert job.events == []
        assert isinstance(job.events, list)

    def test_job_document_with_single_event(self):
        """JobDocument should store a single event correctly."""
        event = JobEvent(
            event_type="format_conversion",
            message="Test conversion",
            details={"source_format": "pdf"},
        )

        job = JobDocument(
            job_id="test-123",
            status="processing",
            filename="test.pdf",
            config={},
            created_at=datetime.now(UTC),
            events=[event],
        )

        assert len(job.events) == 1
        assert job.events[0].event_type == "format_conversion"
        assert job.events[0].message == "Test conversion"

    def test_job_document_with_multiple_events(self):
        """JobDocument should store multiple events in order."""
        event1 = JobEvent(
            event_type="format_conversion",
            message="Converted to PDF",
            details={},
        )
        event2 = JobEvent(
            event_type="ocr_decision",
            message="OCR skipped",
            details={"reason": "tagged_pdf"},
        )
        event3 = JobEvent(
            event_type="compression_selected",
            message="Compression profile selected",
            details={"profile": "balanced"},
        )

        job = JobDocument(
            job_id="test-123",
            status="processing",
            filename="test.pdf",
            config={},
            created_at=datetime.now(UTC),
            events=[event1, event2, event3],
        )

        assert len(job.events) == 3
        assert job.events[0].event_type == "format_conversion"
        assert job.events[1].event_type == "ocr_decision"
        assert job.events[2].event_type == "compression_selected"

    def test_job_document_backward_compatibility_no_events_field(self):
        """JobDocument should work without events field (old documents from MongoDB)."""
        # Simulate old document from MongoDB (no events field)
        job_data = {
            "job_id": "old-job",
            "status": "completed",
            "filename": "old.pdf",
            "config": {},
            "created_at": datetime.now(UTC),
            # NO events field - this is the key test for backward compatibility
        }

        job = JobDocument(**job_data)

        assert job.events == []  # Should default to empty list
        assert hasattr(job, "events")

    def test_job_document_serialization_with_events(self):
        """JobDocument should serialize events correctly."""
        event = JobEvent(
            timestamp=datetime(2024, 1, 1, 12, 0, 0),
            event_type="ocr_decision",
            message="OCR decision made",
            details={"decision": "skip", "reason": "has_text"},
        )

        job = JobDocument(
            job_id="test-123",
            status="completed",
            filename="test.pdf",
            config={},
            created_at=datetime(2024, 1, 1, 10, 0, 0),
            events=[event],
        )

        data = job.model_dump()

        assert "events" in data
        assert len(data["events"]) == 1
        assert data["events"][0]["event_type"] == "ocr_decision"
        assert data["events"][0]["details"]["reason"] == "has_text"

    def test_job_document_with_events_and_other_fields(self):
        """JobDocument should work with events alongside all other fields."""
        event = JobEvent(
            event_type="job_cleanup",
            message="Job cleaned up",
            details={"trigger": "age_exceeded"},
        )

        job = JobDocument(
            job_id="test-123",
            user_id="user-456",
            status="completed",
            filename="test.pdf",
            config={"pdfa_level": "2"},
            created_at=datetime(2024, 1, 1, 10, 0, 0),
            started_at=datetime(2024, 1, 1, 10, 0, 5),
            completed_at=datetime(2024, 1, 1, 10, 2, 30),
            duration_seconds=145.0,
            file_size_input=1048576,
            file_size_output=524288,
            compression_ratio=0.5,
            events=[event],
        )

        assert job.job_id == "test-123"
        assert job.user_id == "user-456"
        assert job.compression_ratio == 0.5
        assert len(job.events) == 1
        assert job.events[0].event_type == "job_cleanup"
