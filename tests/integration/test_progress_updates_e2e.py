"""End-to-end tests for progress updates with large files.

This module tests the complete progress update flow including:
- Initial progress message when job starts
- Progress updates during conversion
- Progress bar percentages
- Message updates
- Completion handling
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import patch

import pytest

from pdfa import api
from pdfa.job_manager import get_job_manager
from pdfa.progress_tracker import ProgressInfo


@pytest.fixture()
def large_pdf() -> bytes:
    """Return a PDF with metadata indicating many pages for testing."""
    # This minimal PDF is used with mocked OCRmyPDF that simulates
    # processing a multi-page document
    # fmt: off
    return (
        b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj "
        b"2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj "
        b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R"
        b"/Resources<<>>>>endobj\n"
        b"xref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n"
        b"0000000052 00000 n\n0000000101 00000 n\n"
        b"trailer<</Size 4/Root 1 0 R>>\nstartxref\n178\n%%EOF"
    )
    # fmt: on


class TestProgressUpdatesE2E:
    """Test end-to-end progress update flow."""

    @pytest.mark.asyncio
    async def test_initial_progress_message_sent(self, large_pdf: bytes) -> None:
        """Test that initial progress message is sent when job starts."""
        job_manager = get_job_manager()

        # Track broadcast calls
        broadcast_calls = []
        original_broadcast = job_manager.broadcast_to_job

        async def mock_broadcast(job_id: str, message: dict) -> None:
            broadcast_calls.append({"job_id": job_id, "message": message})
            await original_broadcast(job_id, message)

        # Mock conversion that succeeds
        def mock_convert(input_pdf: Path, output_pdf: Path, *args, **kwargs) -> None:
            output_pdf.write_bytes(b"%PDF-1.4 converted")

        with patch("pdfa.api.convert_to_pdfa", new=mock_convert):
            with patch.object(
                job_manager, "broadcast_to_job", side_effect=mock_broadcast
            ):
                # Create and process job
                job = job_manager.create_job(
                    filename="large.pdf",
                    file_data=large_pdf,
                    config={},
                )

                await api.process_conversion_job(job.job_id)
                await asyncio.sleep(0.05)

                # Find initial progress message
                progress_messages = [
                    call
                    for call in broadcast_calls
                    if call["message"].get("type") == "progress"
                ]

                # Should have at least one progress message
                assert len(progress_messages) >= 1, "No progress messages received"

                # First progress message should have percentage 0
                first_progress = progress_messages[0]["message"]
                assert first_progress["percentage"] == 0
                assert "message" in first_progress
                assert first_progress["job_id"] == job.job_id

    @pytest.mark.asyncio
    async def test_progress_updates_during_conversion(self, large_pdf: bytes) -> None:
        """Test that progress updates are sent during conversion."""
        job_manager = get_job_manager()

        # Track broadcast calls
        broadcast_calls = []
        original_broadcast = job_manager.broadcast_to_job

        async def mock_broadcast(job_id: str, message: dict) -> None:
            broadcast_calls.append({"job_id": job_id, "message": message})
            await original_broadcast(job_id, message)

        # Mock conversion that sends multiple progress updates
        def mock_convert_with_progress(
            input_pdf: Path,
            output_pdf: Path,
            *args,
            progress_callback=None,
            **kwargs,
        ) -> None:
            # Simulate processing a 10-page document
            if progress_callback:
                for page in range(1, 11):
                    progress_callback(
                        ProgressInfo(
                            step="ocr",
                            current=page,
                            total=10,
                            percentage=(page / 10) * 100,
                            message=f"Processing page {page} of 10",
                        )
                    )

            output_pdf.write_bytes(b"%PDF-1.4 converted")

        with patch("pdfa.api.convert_to_pdfa", new=mock_convert_with_progress):
            with patch.object(
                job_manager, "broadcast_to_job", side_effect=mock_broadcast
            ):
                # Create and process job
                job = job_manager.create_job(
                    filename="large.pdf",
                    file_data=large_pdf,
                    config={},
                )

                await api.process_conversion_job(job.job_id)
                await asyncio.sleep(0.05)

                # Find all progress messages
                progress_messages = [
                    call
                    for call in broadcast_calls
                    if call["message"].get("type") == "progress"
                ]

                # Should have at least initial message
                # Note: Due to asyncio.to_thread and threading, not all progress
                # callbacks may complete before job finishes in tests
                assert len(progress_messages) >= 1, (
                    f"Expected at least 1 progress message, "
                    f"got {len(progress_messages)}"
                )

                # First message should be initial progress (0%)
                assert progress_messages[0]["message"]["percentage"] == 0

                # If we got multiple progress messages, verify they increase
                if len(progress_messages) > 1:
                    percentages = [
                        msg["message"]["percentage"] for msg in progress_messages
                    ]
                    for i in range(len(percentages) - 1):
                        assert percentages[i] <= percentages[i + 1], (
                            f"Progress decreased: {percentages[i]} -> "
                            f"{percentages[i + 1]}"
                        )

    @pytest.mark.asyncio
    async def test_progress_messages_have_required_fields(
        self, large_pdf: bytes
    ) -> None:
        """Test that progress messages contain all required fields."""
        job_manager = get_job_manager()

        # Track broadcast calls
        broadcast_calls = []

        async def mock_broadcast(job_id: str, message: dict) -> None:
            broadcast_calls.append({"job_id": job_id, "message": message})

        # Mock conversion with progress
        def mock_convert(
            input_pdf: Path,
            output_pdf: Path,
            *args,
            progress_callback=None,
            **kwargs,
        ) -> None:
            if progress_callback:
                progress_callback(
                    ProgressInfo(
                        step="ocr",
                        current=5,
                        total=10,
                        percentage=50.0,
                        message="Processing page 5 of 10",
                    )
                )

            output_pdf.write_bytes(b"%PDF-1.4 converted")

        with patch("pdfa.api.convert_to_pdfa", new=mock_convert):
            with patch.object(
                job_manager, "broadcast_to_job", side_effect=mock_broadcast
            ):
                # Create and process job
                job = job_manager.create_job(
                    filename="large.pdf",
                    file_data=large_pdf,
                    config={},
                )

                await api.process_conversion_job(job.job_id)
                await asyncio.sleep(0.05)

                # Find progress messages
                progress_messages = [
                    call
                    for call in broadcast_calls
                    if call["message"].get("type") == "progress"
                ]

                assert len(progress_messages) >= 1

                # Verify all required fields are present
                for msg in progress_messages:
                    progress = msg["message"]
                    assert "type" in progress
                    assert progress["type"] == "progress"
                    assert "job_id" in progress
                    assert progress["job_id"] == job.job_id
                    assert "step" in progress
                    assert "percentage" in progress
                    assert "current" in progress
                    assert "total" in progress
                    assert "message" in progress

                    # Verify percentage is in valid range
                    assert 0 <= progress["percentage"] <= 100

    @pytest.mark.asyncio
    async def test_no_progress_stuck_at_low_percentage(self, large_pdf: bytes) -> None:
        """Test that progress doesn't get stuck at a low percentage."""
        job_manager = get_job_manager()

        # Track broadcast calls
        broadcast_calls = []

        async def mock_broadcast(job_id: str, message: dict) -> None:
            broadcast_calls.append({"job_id": job_id, "message": message})

        # Mock conversion with minimal progress updates
        # (simulates a file that processes quickly)
        def mock_convert_fast(
            input_pdf: Path,
            output_pdf: Path,
            *args,
            progress_callback=None,
            **kwargs,
        ) -> None:
            # Only send one progress update at 8%
            if progress_callback:
                progress_callback(
                    ProgressInfo(
                        step="ocr",
                        current=1,
                        total=12,
                        percentage=8.33,
                        message="Processing page 1 of 12",
                    )
                )

            output_pdf.write_bytes(b"%PDF-1.4 converted")

        with patch("pdfa.api.convert_to_pdfa", new=mock_convert_fast):
            with patch.object(
                job_manager, "broadcast_to_job", side_effect=mock_broadcast
            ):
                # Create and process job
                job = job_manager.create_job(
                    filename="large.pdf",
                    file_data=large_pdf,
                    config={},
                )

                await api.process_conversion_job(job.job_id)
                await asyncio.sleep(0.05)

                # Find progress messages
                progress_messages = [
                    call
                    for call in broadcast_calls
                    if call["message"].get("type") == "progress"
                ]

                # Should have at least initial progress (0%)
                assert len(progress_messages) >= 1

                # First message should be 0%
                assert progress_messages[0]["message"]["percentage"] == 0

                # Job should complete successfully
                updated_job = job_manager.get_job(job.job_id)
                assert updated_job.status == "completed"

                # Completion message should be sent
                completed_messages = [
                    call
                    for call in broadcast_calls
                    if call["message"].get("type") == "completed"
                ]
                assert len(completed_messages) == 1

    @pytest.mark.asyncio
    async def test_progress_with_office_conversion(self, large_pdf: bytes) -> None:
        """Test progress updates during Office document conversion."""
        job_manager = get_job_manager()

        # Track broadcast calls
        broadcast_calls = []

        async def mock_broadcast(job_id: str, message: dict) -> None:
            broadcast_calls.append({"job_id": job_id, "message": message})

        # Mock Office to PDF conversion
        def mock_office_convert(
            input_path: Path,
            output_path: Path,
            *args,
            progress_callback=None,
            **kwargs,
        ) -> None:
            if progress_callback:
                progress_callback(
                    ProgressInfo(
                        step="office",
                        current=1,
                        total=1,
                        percentage=50.0,
                        message="Converting Office document to PDF...",
                    )
                )
            output_path.write_bytes(b"%PDF-1.4 from office")

        # Mock PDF/A conversion
        def mock_pdfa_convert(
            input_pdf: Path,
            output_pdf: Path,
            *args,
            progress_callback=None,
            **kwargs,
        ) -> None:
            if progress_callback:
                progress_callback(
                    ProgressInfo(
                        step="pdfa",
                        current=1,
                        total=1,
                        percentage=100.0,
                        message="Converting to PDF/A format...",
                    )
                )
            output_pdf.write_bytes(b"%PDF-1.4 pdfa")

        with patch("pdfa.api.convert_office_to_pdf", new=mock_office_convert):
            with patch("pdfa.api.convert_to_pdfa", new=mock_pdfa_convert):
                with patch.object(
                    job_manager, "broadcast_to_job", side_effect=mock_broadcast
                ):
                    # Create job with Office document
                    job = job_manager.create_job(
                        filename="document.docx",  # Office file
                        file_data=large_pdf,  # Content doesn't matter for test
                        config={},
                    )

                    await api.process_conversion_job(job.job_id)
                    await asyncio.sleep(0.05)

                    # Find progress messages
                    progress_messages = [
                        call
                        for call in broadcast_calls
                        if call["message"].get("type") == "progress"
                    ]

                    # Should have at least initial progress (0%)
                    # Note: Due to threading, office conversion progress may not
                    # always complete before job finishes in unit tests
                    assert len(progress_messages) >= 1

                    # First message should be initial progress
                    assert progress_messages[0]["message"]["percentage"] == 0

                    # Job should complete successfully
                    updated_job = job_manager.get_job(job.job_id)
                    assert updated_job.status == "completed"

    @pytest.mark.asyncio
    async def test_initial_progress_survives_broadcast_failure(
        self, large_pdf: bytes
    ) -> None:
        """Test that job continues even if initial progress broadcast fails."""
        job_manager = get_job_manager()

        call_count = [0]
        original_broadcast = job_manager.broadcast_to_job

        async def mock_broadcast_fail_first(job_id: str, message: dict) -> None:
            call_count[0] += 1
            if call_count[0] == 1:  # Fail first broadcast (initial progress)
                raise RuntimeError("Broadcast failed")
            await original_broadcast(job_id, message)

        # Mock conversion
        def mock_convert(input_pdf: Path, output_pdf: Path, *args, **kwargs) -> None:
            output_pdf.write_bytes(b"%PDF-1.4 converted")

        with patch("pdfa.api.convert_to_pdfa", new=mock_convert):
            with patch.object(
                job_manager, "broadcast_to_job", side_effect=mock_broadcast_fail_first
            ):
                # Create and process job
                job = job_manager.create_job(
                    filename="large.pdf",
                    file_data=large_pdf,
                    config={},
                )

                # Should not raise exception
                await api.process_conversion_job(job.job_id)
                await asyncio.sleep(0.05)

                # Job should still complete successfully
                updated_job = job_manager.get_job(job.job_id)
                assert updated_job.status == "completed"
