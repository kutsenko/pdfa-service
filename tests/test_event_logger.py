"""Unit tests for event logger helper functions.

Following TDD principles, these tests verify event logger behavior before
implementation.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from pdfa.event_logger import (
    log_compression_selected_event,
    log_fallback_applied_event,
    log_format_conversion_event,
    log_job_cleanup_event,
    log_job_timeout_event,
    log_ocr_decision_event,
    log_passthrough_mode_event,
)
from pdfa.models import JobEvent


class TestLogFormatConversionEvent:
    """Test cases for log_format_conversion_event()."""

    @pytest.mark.asyncio
    async def test_office_to_pdf_conversion(self):
        """Should log Office→PDF conversion with conversion time."""
        with patch("pdfa.event_logger.JobRepository") as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo_class.return_value = mock_repo

            await log_format_conversion_event(
                job_id="test-123",
                source_format="docx",
                target_format="pdf",
                conversion_required=True,
                converter="office_to_pdf",
                conversion_time_seconds=3.2,
            )

            # Assert add_job_event was called
            mock_repo.add_job_event.assert_called_once()
            call_args = mock_repo.add_job_event.call_args
            assert call_args[0][0] == "test-123"  # job_id

            # Verify event structure
            event: JobEvent = call_args[0][1]
            assert event.event_type == "format_conversion"
            assert "docx" in event.message.lower()
            assert event.details["source_format"] == "docx"
            assert event.details["target_format"] == "pdf"
            assert event.details["conversion_required"] is True
            assert event.details["converter"] == "office_to_pdf"
            assert event.details["conversion_time_seconds"] == 3.2

    @pytest.mark.asyncio
    async def test_direct_pdf_no_conversion(self):
        """Should log PDF with no conversion required."""
        with patch("pdfa.event_logger.JobRepository") as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo_class.return_value = mock_repo

            await log_format_conversion_event(
                job_id="test-456",
                source_format="pdf",
                target_format="pdf",
                conversion_required=False,
            )

            mock_repo.add_job_event.assert_called_once()
            event: JobEvent = mock_repo.add_job_event.call_args[0][1]
            assert event.event_type == "format_conversion"
            assert event.details["conversion_required"] is False


class TestLogOcrDecisionEvent:
    """Test cases for log_ocr_decision_event()."""

    @pytest.mark.asyncio
    async def test_ocr_skipped_tagged_pdf(self):
        """Should log OCR skipped for tagged PDF."""
        with patch("pdfa.event_logger.JobRepository") as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo_class.return_value = mock_repo

            await log_ocr_decision_event(
                job_id="test-123",
                decision="skip",
                reason="tagged_pdf",
                has_struct_tree_root=True,
            )

            event: JobEvent = mock_repo.add_job_event.call_args[0][1]
            assert event.event_type == "ocr_decision"
            assert "skip" in event.message.lower()
            assert event.details["decision"] == "skip"
            assert event.details["reason"] == "tagged_pdf"
            assert event.details["has_struct_tree_root"] is True

    @pytest.mark.asyncio
    async def test_ocr_skipped_has_text(self):
        """Should log OCR skipped due to existing text."""
        with patch("pdfa.event_logger.JobRepository") as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo_class.return_value = mock_repo

            await log_ocr_decision_event(
                job_id="test-123",
                decision="skip",
                reason="has_text",
                pages_with_text=3,
                total_pages_checked=3,
                text_ratio=1.0,
                total_characters=1523,
            )

            event: JobEvent = mock_repo.add_job_event.call_args[0][1]
            assert event.details["decision"] == "skip"
            assert event.details["reason"] == "has_text"
            assert event.details["pages_with_text"] == 3
            assert event.details["total_pages_checked"] == 3
            assert event.details["text_ratio"] == 1.0
            assert event.details["total_characters"] == 1523

    @pytest.mark.asyncio
    async def test_ocr_perform_no_text(self):
        """Should log OCR performed due to missing text."""
        with patch("pdfa.event_logger.JobRepository") as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo_class.return_value = mock_repo

            await log_ocr_decision_event(
                job_id="test-123",
                decision="perform",
                reason="no_text",
                pages_with_text=0,
                total_pages_checked=3,
                text_ratio=0.0,
                total_characters=8,
            )

            event: JobEvent = mock_repo.add_job_event.call_args[0][1]
            assert event.details["decision"] == "perform"
            assert event.details["reason"] == "no_text"


class TestLogCompressionSelectedEvent:
    """Test cases for log_compression_selected_event()."""

    @pytest.mark.asyncio
    async def test_user_selected_quality(self):
        """Should log user-selected quality profile."""
        with patch("pdfa.event_logger.JobRepository") as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo_class.return_value = mock_repo

            await log_compression_selected_event(
                job_id="test-123",
                profile="quality",
                reason="user_selected",
                settings={
                    "image_dpi": 300,
                    "jpg_quality": 95,
                    "optimize": 1,
                    "remove_vectors": False,
                },
            )

            event: JobEvent = mock_repo.add_job_event.call_args[0][1]
            assert event.event_type == "compression_selected"
            assert event.details["profile"] == "quality"
            assert event.details["reason"] == "user_selected"
            assert event.details["settings"]["image_dpi"] == 300

    @pytest.mark.asyncio
    async def test_auto_switched_for_tagged_pdf(self):
        """Should log auto-switch to preserve profile for tagged PDF."""
        with patch("pdfa.event_logger.JobRepository") as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo_class.return_value = mock_repo

            await log_compression_selected_event(
                job_id="test-123",
                profile="preserve",
                reason="auto_switched_for_tagged_pdf",
                original_profile="balanced",
                settings={"image_dpi": 300, "remove_vectors": False},
            )

            event: JobEvent = mock_repo.add_job_event.call_args[0][1]
            assert event.details["profile"] == "preserve"
            assert event.details["reason"] == "auto_switched_for_tagged_pdf"
            assert event.details["original_profile"] == "balanced"


class TestLogPassthroughModeEvent:
    """Test cases for log_passthrough_mode_event()."""

    @pytest.mark.asyncio
    async def test_passthrough_enabled_pdf_output_no_ocr(self):
        """Should log pass-through mode enabled."""
        with patch("pdfa.event_logger.JobRepository") as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo_class.return_value = mock_repo

            await log_passthrough_mode_event(
                job_id="test-123",
                enabled=True,
                reason="pdf_output_no_ocr",
                pdfa_level="pdf",
                ocr_enabled=False,
                has_tags=True,
                tags_preserved=True,
            )

            event: JobEvent = mock_repo.add_job_event.call_args[0][1]
            assert event.event_type == "passthrough_mode"
            assert event.details["enabled"] is True
            assert event.details["reason"] == "pdf_output_no_ocr"
            assert event.details["pdfa_level"] == "pdf"
            assert event.details["ocr_enabled"] is False
            assert event.details["has_tags"] is True
            assert event.details["tags_preserved"] is True


class TestLogFallbackAppliedEvent:
    """Test cases for log_fallback_applied_event()."""

    @pytest.mark.asyncio
    async def test_fallback_tier_2_ghostscript_error(self):
        """Should log fallback to tier 2 due to Ghostscript error."""
        with patch("pdfa.event_logger.JobRepository") as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo_class.return_value = mock_repo

            await log_fallback_applied_event(
                job_id="test-123",
                tier=2,
                reason="ghostscript_error",
                original_error="SubprocessOutputError: Ghostscript failed",
                safe_mode_config={
                    "image_dpi": 100,
                    "remove_vectors": False,
                    "optimize": 0,
                    "jbig2_lossy": False,
                },
                pdfa_level_downgrade={"original": "3", "fallback": "2"},
            )

            event: JobEvent = mock_repo.add_job_event.call_args[0][1]
            assert event.event_type == "fallback_applied"
            assert event.details["tier"] == 2
            assert event.details["reason"] == "ghostscript_error"
            assert "SubprocessOutputError" in event.details["original_error"]
            assert event.details["safe_mode_config"]["image_dpi"] == 100
            assert event.details["pdfa_level_downgrade"]["original"] == "3"

    @pytest.mark.asyncio
    async def test_fallback_tier_3_no_ocr(self):
        """Should log fallback to tier 3 (no OCR)."""
        with patch("pdfa.event_logger.JobRepository") as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo_class.return_value = mock_repo

            await log_fallback_applied_event(
                job_id="test-123",
                tier=3,
                reason="tier2_failed",
                tier2_error="SubprocessOutputError: Tier 2 failed",
                ocr_disabled=True,
                safe_mode_config={
                    "image_dpi": 100,
                    "remove_vectors": False,
                    "optimize": 0,
                },
            )

            event: JobEvent = mock_repo.add_job_event.call_args[0][1]
            assert event.details["tier"] == 3
            assert event.details["reason"] == "tier2_failed"
            assert event.details["ocr_disabled"] is True


class TestLogJobTimeoutEvent:
    """Test cases for log_job_timeout_event()."""

    @pytest.mark.asyncio
    async def test_job_timeout(self):
        """Should log job timeout event."""
        with patch("pdfa.event_logger.JobRepository") as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo_class.return_value = mock_repo

            await log_job_timeout_event(
                job_id="test-123", timeout_seconds=7200, runtime_seconds=7305
            )

            event: JobEvent = mock_repo.add_job_event.call_args[0][1]
            assert event.event_type == "job_timeout"
            assert "timeout" in event.message.lower()
            assert event.details["timeout_seconds"] == 7200
            assert event.details["runtime_seconds"] == 7305
            assert event.details["job_cancelled"] is True


class TestLogJobCleanupEvent:
    """Test cases for log_job_cleanup_event()."""

    @pytest.mark.asyncio
    async def test_cleanup_age_exceeded(self):
        """Should log cleanup due to age exceeded."""
        with patch("pdfa.event_logger.JobRepository") as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo_class.return_value = mock_repo

            await log_job_cleanup_event(
                job_id="test-123",
                trigger="age_exceeded",
                ttl_seconds=3600,
                age_seconds=3720,
                files_deleted={
                    "input_file": "/tmp/input.pdf",
                    "output_file": "/tmp/output.pdf",
                    "temp_directory": "/tmp/job-123",
                },
                total_size_bytes=2048576,
            )

            event: JobEvent = mock_repo.add_job_event.call_args[0][1]
            assert event.event_type == "job_cleanup"
            assert event.details["trigger"] == "age_exceeded"
            assert event.details["ttl_seconds"] == 3600
            assert event.details["age_seconds"] == 3720
            assert event.details["total_size_bytes"] == 2048576

    @pytest.mark.asyncio
    async def test_cleanup_timeout(self):
        """Should log cleanup due to timeout."""
        with patch("pdfa.event_logger.JobRepository") as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo_class.return_value = mock_repo

            await log_job_cleanup_event(
                job_id="test-123",
                trigger="timeout",
                ttl_seconds=7200,
                age_seconds=7350,
            )

            event: JobEvent = mock_repo.add_job_event.call_args[0][1]
            assert event.details["trigger"] == "timeout"
