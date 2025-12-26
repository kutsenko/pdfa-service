"""Tests for WebSocket protocol message schemas."""

from __future__ import annotations

import base64

import pytest

from pdfa.websocket_protocol import (
    CancelJobMessage,
    CancelledMessage,
    CompletedMessage,
    ErrorMessage,
    JobAcceptedMessage,
    JobEventMessage,
    PingMessage,
    PongMessage,
    ProgressMessage,
    SubmitJobMessage,
    parse_client_message,
)


class TestSubmitJobMessage:
    """Tests for SubmitJobMessage."""

    def test_valid_message(self):
        """Test valid submit message."""
        file_content = b"test content"
        msg = SubmitJobMessage(
            filename="test.pdf",
            fileData=base64.b64encode(file_content).decode(),
            config={"language": "eng"},
        )
        msg.validate()

        assert msg.filename == "test.pdf"
        assert msg.get_file_bytes() == file_content

    def test_missing_filename(self):
        """Test validation fails without filename."""
        msg = SubmitJobMessage(
            filename="",
            fileData=base64.b64encode(b"test").decode(),
        )

        with pytest.raises(ValueError, match="filename is required"):
            msg.validate()

    def test_missing_file_data(self):
        """Test validation fails without file data."""
        msg = SubmitJobMessage(
            filename="test.pdf",
            fileData="",
        )

        with pytest.raises(ValueError, match="fileData is required"):
            msg.validate()

    def test_invalid_base64(self):
        """Test validation fails with invalid base64."""
        msg = SubmitJobMessage(
            filename="test.pdf",
            fileData="not-valid-base64!!!",
        )

        with pytest.raises(ValueError, match="Invalid base64 encoding"):
            msg.validate()

    def test_default_config(self):
        """Test default config is empty dict."""
        msg = SubmitJobMessage(
            filename="test.pdf",
            fileData=base64.b64encode(b"test").decode(),
        )
        msg.validate()

        assert msg.config == {}


class TestCancelJobMessage:
    """Tests for CancelJobMessage."""

    def test_valid_message(self):
        """Test valid cancel message."""
        msg = CancelJobMessage(job_id="550e8400-e29b-41d4-a716-446655440000")
        msg.validate()

        assert msg.job_id == "550e8400-e29b-41d4-a716-446655440000"

    def test_missing_job_id(self):
        """Test validation fails without job_id."""
        msg = CancelJobMessage(job_id="")

        with pytest.raises(ValueError, match="job_id is required"):
            msg.validate()


class TestPingMessage:
    """Tests for PingMessage."""

    def test_ping_message(self):
        """Test ping message."""
        msg = PingMessage()
        assert msg.type == "ping"


class TestServerMessages:
    """Tests for server-to-client messages."""

    def test_job_accepted_message(self):
        """Test JobAcceptedMessage."""
        msg = JobAcceptedMessage(
            job_id="test-job-123",
            status="queued",
        )

        data = msg.to_dict()
        assert data["type"] == "job_accepted"
        assert data["job_id"] == "test-job-123"
        assert data["status"] == "queued"

    def test_progress_message(self):
        """Test ProgressMessage."""
        msg = ProgressMessage(
            job_id="test-job-123",
            step="OCR",
            current=15,
            total=100,
            percentage=15.0,
            message="Processing page 15 of 100",
        )

        data = msg.to_dict()
        assert data["type"] == "progress"
        assert data["job_id"] == "test-job-123"
        assert data["step"] == "OCR"
        assert data["current"] == 15
        assert data["total"] == 100
        assert data["percentage"] == 15.0
        assert "Processing page 15" in data["message"]

    def test_completed_message(self):
        """Test CompletedMessage."""
        msg = CompletedMessage(
            job_id="test-job-123",
            download_url="/download/test-job-123",
            filename="test_pdfa.pdf",
            size_bytes=12345,
        )

        data = msg.to_dict()
        assert data["type"] == "completed"
        assert data["download_url"] == "/download/test-job-123"
        assert data["size_bytes"] == 12345

    def test_error_message(self):
        """Test ErrorMessage."""
        msg = ErrorMessage(
            job_id="test-job-123",
            error_code="CONVERSION_FAILED",
            message="OCRmyPDF failed",
        )

        data = msg.to_dict()
        assert data["type"] == "error"
        assert data["error_code"] == "CONVERSION_FAILED"
        assert "OCRmyPDF failed" in data["message"]

    def test_cancelled_message(self):
        """Test CancelledMessage."""
        msg = CancelledMessage(job_id="test-job-123")

        data = msg.to_dict()
        assert data["type"] == "cancelled"
        assert data["job_id"] == "test-job-123"

    def test_pong_message(self):
        """Test PongMessage."""
        msg = PongMessage()

        data = msg.to_dict()
        assert data["type"] == "pong"

    def test_job_event_message_with_details(self):
        """Test JobEventMessage with details."""
        msg = JobEventMessage(
            job_id="test-job-123",
            event_type="ocr_decision",
            timestamp="2025-12-25T10:30:15.123Z",
            message="OCR skipped: tagged PDF detected",
            details={
                "decision": "skip",
                "reason": "tagged_pdf",
                "_i18n_key": "ocr_decision.skip.tagged_pdf",
                "_i18n_params": {"decision": "skip", "reason": "tagged_pdf"},
            },
        )

        data = msg.to_dict()
        assert data["type"] == "job_event"
        assert data["job_id"] == "test-job-123"
        assert data["event_type"] == "ocr_decision"
        assert data["timestamp"] == "2025-12-25T10:30:15.123Z"
        assert "OCR skipped" in data["message"]
        assert data["details"]["decision"] == "skip"
        assert data["details"]["_i18n_key"] == "ocr_decision.skip.tagged_pdf"

    def test_job_event_message_without_details(self):
        """Test JobEventMessage without details."""
        msg = JobEventMessage(
            job_id="test-job-456",
            event_type="job_cleanup",
            timestamp="2025-12-25T10:35:00.000Z",
            message="Temporary files cleaned",
            details=None,
        )

        data = msg.to_dict()
        assert data["type"] == "job_event"
        assert data["job_id"] == "test-job-456"
        assert data["event_type"] == "job_cleanup"
        assert "Temporary files" in data["message"]
        # details should not be in dict when None (filtered by to_dict())
        assert "details" not in data or data.get("details") is None

    def test_job_event_message_format_conversion(self):
        """Test JobEventMessage for format conversion."""
        msg = JobEventMessage(
            job_id="test-job-789",
            event_type="format_conversion",
            timestamp="2025-12-25T10:32:00.000Z",
            message="DOCX converted to PDF",
            details={
                "input_format": "docx",
                "pages": 5,
                "_i18n_key": "format_conversion.docx.success",
                "_i18n_params": {"pages": 5},
            },
        )

        data = msg.to_dict()
        assert data["type"] == "job_event"
        assert data["event_type"] == "format_conversion"
        assert data["details"]["input_format"] == "docx"
        assert data["details"]["pages"] == 5


class TestParseClientMessage:
    """Tests for parse_client_message function."""

    def test_parse_submit_message(self):
        """Test parsing submit message."""
        data = {
            "type": "submit",
            "filename": "test.pdf",
            "fileData": base64.b64encode(b"content").decode(),
            "config": {"language": "eng"},
        }

        msg = parse_client_message(data)

        assert isinstance(msg, SubmitJobMessage)
        assert msg.filename == "test.pdf"
        assert msg.get_file_bytes() == b"content"

    def test_parse_cancel_message(self):
        """Test parsing cancel message."""
        data = {
            "type": "cancel",
            "job_id": "test-job-123",
        }

        msg = parse_client_message(data)

        assert isinstance(msg, CancelJobMessage)
        assert msg.job_id == "test-job-123"

    def test_parse_ping_message(self):
        """Test parsing ping message."""
        data = {"type": "ping"}

        msg = parse_client_message(data)

        assert isinstance(msg, PingMessage)

    def test_parse_unknown_type(self):
        """Test parsing unknown message type."""
        data = {"type": "unknown"}

        with pytest.raises(ValueError, match="Unknown message type"):
            parse_client_message(data)
