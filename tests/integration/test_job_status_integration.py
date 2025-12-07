"""Integration tests for job status management and file download.

This module tests the complete job lifecycle including:
- Job creation and status transitions
- Job-to-document mapping
- Download endpoint after job completion
- Error handling and status updates
- Edge cases and race conditions
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from pdfa import api
from pdfa.exceptions import JobNotFoundException
from pdfa.job_manager import get_job_manager


@pytest.fixture()
def client() -> TestClient:
    """Return a test client bound to the FastAPI app."""
    return TestClient(api.app)


@pytest.fixture()
def sample_pdf() -> bytes:
    """Return a minimal PDF for testing."""
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


class TestJobStatusTransitions:
    """Test job status state transitions."""

    @pytest.mark.asyncio
    async def test_job_status_queued_to_processing_to_completed(
        self, sample_pdf: bytes
    ) -> None:
        """Test job transitions from queued -> processing -> completed."""
        job_manager = get_job_manager()

        # Mock conversion that succeeds (must be sync, not async)
        def mock_convert(
            input_pdf: Path,
            output_pdf: Path,
            *args,
            progress_callback=None,
            **kwargs,
        ) -> None:
            # Create output file
            output_pdf.write_bytes(b"%PDF-1.4 converted")

        with patch("pdfa.api.convert_to_pdfa", new=mock_convert):
            # Create job
            job = job_manager.create_job(
                filename="test.pdf",
                file_data=sample_pdf,
                config={"language": "deu+eng"},
            )

            # Initial status should be queued
            assert job.status == "queued"
            assert job.started_at is None
            assert job.completed_at is None

            # Process job
            await api.process_conversion_job(job.job_id)

            # Wait a bit for async processing
            await asyncio.sleep(0.05)

            # Get updated job
            updated_job = job_manager.get_job(job.job_id)

            # Status should be completed
            assert updated_job.status == "completed"
            assert updated_job.started_at is not None
            assert updated_job.completed_at is not None
            assert updated_job.output_path is not None
            assert updated_job.output_path.exists()
            assert updated_job.error is None

    @pytest.mark.asyncio
    async def test_job_status_processing_to_failed_on_error(
        self, sample_pdf: bytes
    ) -> None:
        """Test job transitions to failed status on conversion error."""
        job_manager = get_job_manager()

        # Mock conversion that fails (must be sync, not async)
        def mock_convert_error(
            input_pdf: Path, output_pdf: Path, *args, **kwargs
        ) -> None:
            raise ValueError("Simulated conversion error")

        with patch("pdfa.api.convert_to_pdfa", new=mock_convert_error):
            # Create job
            job = job_manager.create_job(
                filename="test.pdf",
                file_data=sample_pdf,
                config={},
            )

            # Process job
            await api.process_conversion_job(job.job_id)

            # Wait for async processing
            await asyncio.sleep(0.05)

            # Get updated job
            updated_job = job_manager.get_job(job.job_id)

            # Status should be failed
            assert updated_job.status == "failed"
            assert updated_job.started_at is not None
            assert updated_job.completed_at is not None
            assert updated_job.error is not None
            assert "Simulated conversion error" in updated_job.error
            assert updated_job.output_path is None

    @pytest.mark.asyncio
    async def test_job_status_with_nonexistent_job(self) -> None:
        """Test process_conversion_job with non-existent job ID."""
        # This should not crash and should handle the error gracefully
        await api.process_conversion_job("nonexistent-job-id")

        # Job manager should not have this job
        job_manager = get_job_manager()
        with pytest.raises(JobNotFoundException):
            job_manager.get_job("nonexistent-job-id")

    @pytest.mark.asyncio
    async def test_job_status_update_failure_handling(self, sample_pdf: bytes) -> None:
        """Test error handling when status update itself fails."""
        job_manager = get_job_manager()

        # Create job
        job = job_manager.create_job(
            filename="test.pdf",
            file_data=sample_pdf,
            config={},
        )

        # Mock conversion (must be sync, not async)
        def mock_convert(input_pdf: Path, output_pdf: Path, *args, **kwargs) -> None:
            output_pdf.write_bytes(b"%PDF-1.4 converted")

        # Mock update_job_status to fail on first call (processing), succeed on others
        original_update = job_manager.update_job_status
        call_count = [0]

        async def mock_update_status(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:  # First call (to "processing")
                raise RuntimeError("Simulated status update failure")
            return await original_update(*args, **kwargs)

        with patch("pdfa.api.convert_to_pdfa", new=mock_convert):
            with patch.object(
                job_manager, "update_job_status", side_effect=mock_update_status
            ):
                # Process job - should handle the status update failure
                await api.process_conversion_job(job.job_id)

                await asyncio.sleep(0.05)

                # Job should still be marked as failed due to status update error
                updated_job = job_manager.get_job(job.job_id)
                assert updated_job.status == "failed"


class TestJobToDocumentMapping:
    """Test job-to-document mapping and download functionality."""

    @pytest.mark.asyncio
    async def test_download_completed_job(
        self, client: TestClient, sample_pdf: bytes
    ) -> None:
        """Test downloading a file after job completion."""
        job_manager = get_job_manager()

        # Mock conversion (must be sync, not async)
        def mock_convert(input_pdf: Path, output_pdf: Path, *args, **kwargs) -> None:
            output_pdf.write_bytes(b"%PDF-1.4 converted output")

        with patch("pdfa.api.convert_to_pdfa", new=mock_convert):
            # Create and process job
            job = job_manager.create_job(
                filename="document.pdf",
                file_data=sample_pdf,
                config={},
            )

            await api.process_conversion_job(job.job_id)
            await asyncio.sleep(0.05)

            # Verify job is completed
            updated_job = job_manager.get_job(job.job_id)
            assert updated_job.status == "completed"
            assert updated_job.output_path is not None

            # Download the file
            response = client.get(f"/download/{job.job_id}")
            assert response.status_code == 200
            assert response.headers["content-type"] == "application/pdf"
            assert b"%PDF-1.4 converted output" in response.content

    def test_download_nonexistent_job(self, client: TestClient) -> None:
        """Test downloading with non-existent job ID."""
        response = client.get("/download/nonexistent-job-id")
        assert response.status_code == 404
        assert "Job not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_download_incomplete_job(
        self, client: TestClient, sample_pdf: bytes
    ) -> None:
        """Test downloading before job is completed."""
        job_manager = get_job_manager()

        # Create job but don't process it
        job = job_manager.create_job(
            filename="test.pdf",
            file_data=sample_pdf,
            config={},
        )

        # Try to download
        response = client.get(f"/download/{job.job_id}")
        assert response.status_code == 400
        assert "not completed" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_download_after_file_deletion(
        self, client: TestClient, sample_pdf: bytes
    ) -> None:
        """Test downloading after output file has been deleted (race condition)."""
        job_manager = get_job_manager()

        # Mock conversion (must be sync, not async)
        def mock_convert(input_pdf: Path, output_pdf: Path, *args, **kwargs) -> None:
            output_pdf.write_bytes(b"%PDF-1.4 converted")

        with patch("pdfa.api.convert_to_pdfa", new=mock_convert):
            # Create and process job
            job = job_manager.create_job(
                filename="test.pdf",
                file_data=sample_pdf,
                config={},
            )

            await api.process_conversion_job(job.job_id)
            await asyncio.sleep(0.05)

            # Verify job completed
            updated_job = job_manager.get_job(job.job_id)
            assert updated_job.status == "completed"
            assert updated_job.output_path is not None

            # Delete the output file (simulate cleanup or race condition)
            updated_job.output_path.unlink()

            # Try to download
            response = client.get(f"/download/{job.job_id}")
            assert response.status_code == 404
            assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_completed_job_without_output_path(
        self, client: TestClient, sample_pdf: bytes
    ) -> None:
        """Test edge case where job is marked completed but has no output_path."""
        job_manager = get_job_manager()

        # Create job
        job = job_manager.create_job(
            filename="test.pdf",
            file_data=sample_pdf,
            config={},
        )

        # Manually set status to completed without output_path
        # (shouldn't happen, but test it)
        await job_manager.update_job_status(job.job_id, "completed")

        # Try to download
        response = client.get(f"/download/{job.job_id}")
        assert response.status_code == 500
        assert "output file path is missing" in response.json()["detail"].lower()


class TestJobStatusWebSocketIntegration:
    """Test job status updates via WebSocket messages."""

    @pytest.mark.asyncio
    async def test_broadcast_on_completion(self, sample_pdf: bytes) -> None:
        """Test that completion message is broadcast to WebSocket clients."""
        job_manager = get_job_manager()

        # Track broadcast calls
        broadcast_calls = []
        original_broadcast = job_manager.broadcast_to_job

        async def mock_broadcast(job_id: str, message: dict) -> None:
            broadcast_calls.append({"job_id": job_id, "message": message})
            await original_broadcast(job_id, message)

        # Mock conversion (must be sync, not async)
        def mock_convert(input_pdf: Path, output_pdf: Path, *args, **kwargs) -> None:
            output_pdf.write_bytes(b"%PDF-1.4 converted")

        with patch("pdfa.api.convert_to_pdfa", new=mock_convert):
            with patch.object(
                job_manager, "broadcast_to_job", side_effect=mock_broadcast
            ):
                # Create and process job
                job = job_manager.create_job(
                    filename="test.pdf",
                    file_data=sample_pdf,
                    config={},
                )

                await api.process_conversion_job(job.job_id)
                await asyncio.sleep(0.05)

                # Verify broadcast was called with completion message
                assert len(broadcast_calls) > 0
                completion_messages = [
                    call
                    for call in broadcast_calls
                    if call["message"].get("type") == "completed"
                ]
                assert len(completion_messages) == 1
                assert completion_messages[0]["job_id"] == job.job_id
                assert "download_url" in completion_messages[0]["message"]

    @pytest.mark.asyncio
    async def test_broadcast_on_error(self, sample_pdf: bytes) -> None:
        """Test that error message is broadcast on job failure."""
        job_manager = get_job_manager()

        # Track broadcast calls
        broadcast_calls = []
        original_broadcast = job_manager.broadcast_to_job

        async def mock_broadcast(job_id: str, message: dict) -> None:
            broadcast_calls.append({"job_id": job_id, "message": message})
            await original_broadcast(job_id, message)

        # Mock conversion that fails (must be sync, not async)
        def mock_convert_error(
            input_pdf: Path, output_pdf: Path, *args, **kwargs
        ) -> None:
            raise ValueError("Test error")

        with patch("pdfa.api.convert_to_pdfa", new=mock_convert_error):
            with patch.object(
                job_manager, "broadcast_to_job", side_effect=mock_broadcast
            ):
                # Create and process job
                job = job_manager.create_job(
                    filename="test.pdf",
                    file_data=sample_pdf,
                    config={},
                )

                await api.process_conversion_job(job.job_id)
                await asyncio.sleep(0.05)

                # Verify broadcast was called with error message
                error_messages = [
                    call
                    for call in broadcast_calls
                    if call["message"].get("type") == "error"
                ]
                assert len(error_messages) == 1
                assert error_messages[0]["job_id"] == job.job_id
                assert "Test error" in error_messages[0]["message"]["message"]

    @pytest.mark.asyncio
    async def test_broadcast_even_if_status_update_fails(
        self, sample_pdf: bytes
    ) -> None:
        """Test that error broadcast happens even if final status update fails."""
        job_manager = get_job_manager()

        # Track broadcast calls
        broadcast_calls = []

        async def mock_broadcast(job_id: str, message: dict) -> None:
            broadcast_calls.append({"job_id": job_id, "message": message})
            # Don't call original to avoid errors
            pass

        # Mock conversion that fails (must be sync, not async)
        def mock_convert_error(
            input_pdf: Path, output_pdf: Path, *args, **kwargs
        ) -> None:
            raise ValueError("Conversion error")

        # Mock status update to succeed for "processing" but fail for "failed"
        original_update = job_manager.update_job_status
        call_count = [0]

        async def mock_update_status_selective(*args, **kwargs) -> None:
            call_count[0] += 1
            if call_count[0] == 1:  # First call ("processing")
                await original_update(*args, **kwargs)
            else:  # Second call ("failed")
                raise RuntimeError("Status update to failed failed")

        with patch("pdfa.api.convert_to_pdfa", new=mock_convert_error):
            with patch.object(
                job_manager,
                "update_job_status",
                side_effect=mock_update_status_selective,
            ):
                with patch.object(
                    job_manager, "broadcast_to_job", side_effect=mock_broadcast
                ):
                    # Create and process job
                    job = job_manager.create_job(
                        filename="test.pdf",
                        file_data=sample_pdf,
                        config={},
                    )

                    await api.process_conversion_job(job.job_id)
                    await asyncio.sleep(0.05)

                    # Verify broadcast was still called even though final
                    # status update failed
                    error_messages = [
                        call
                        for call in broadcast_calls
                        if call["message"].get("type") == "error"
                    ]
                    assert len(error_messages) == 1
                    assert "Conversion error" in error_messages[0]["message"]["message"]
