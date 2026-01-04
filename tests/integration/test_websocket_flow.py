"""Integration tests for WebSocket-based conversion flow.

This module tests the complete end-to-end WebSocket flow including:
- Job submission
- Progress updates
- Job completion
- File download
- UI state management
"""

from __future__ import annotations

import base64
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from pdfa import api
from pdfa.job_manager import get_job_manager
from pdfa.progress_tracker import ProgressInfo


# Client fixture now provided by conftest.py (integration_client)


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


@pytest.mark.skip(
    reason="TestClient does not properly handle async lifespan events. "
    "WebSocket functionality is thoroughly tested via E2E tests with Playwright. "
    "TODO: Migrate to httpx.AsyncClient or Starlette TestClient with lifespan support."
)
@pytest.mark.integration
class TestWebSocketConversionFlow:
    """Test complete WebSocket conversion workflow.

    NOTE: Currently skipped due to TestClient limitations with async startup/shutdown.
    WebSocket functionality IS tested via:
    - tests/e2e/test_event_display_and_modal.py (real browser WebSocket)
    - tests/e2e/test_progress_updates_real.py (real browser WebSocket)

    Future improvement: Use httpx.AsyncClient instead of TestClient.
    """

    def test_complete_conversion_flow(
        self, integration_client: TestClient, sample_pdf: bytes
    ) -> None:
        """Test complete conversion flow from submission to download."""
        messages_received = []

        # Mock the conversion function to simulate progress
        def mock_convert(
            input_pdf: Path,
            output_pdf: Path,
            *args,
            progress_callback=None,
            **kwargs,
        ) -> None:
            # Create output file
            output_pdf.write_bytes(b"%PDF-1.4 converted")

            # Simulate progress updates if callback provided
            if progress_callback:
                # Only send a few progress updates to speed up test
                progress_callback(
                    ProgressInfo(
                        step="ocr",
                        current=1,
                        total=3,
                        percentage=33.0,
                        message="Processing page 1 of 3",
                    )
                )

                progress_callback(
                    ProgressInfo(
                        step="ocr",
                        current=2,
                        total=3,
                        percentage=66.0,
                        message="Processing page 2 of 3",
                    )
                )

                progress_callback(
                    ProgressInfo(
                        step="pdfa",
                        current=3,
                        total=3,
                        percentage=100.0,
                        message="Finishing conversion...",
                    )
                )

        with patch.object(api, "convert_to_pdfa", side_effect=mock_convert):
            # Connect to WebSocket
            with integration_client.websocket_connect("/ws") as websocket:
                # Should receive pong for connection
                data = websocket.receive_json()
                assert data is not None

                # Submit job
                file_data = base64.b64encode(sample_pdf).decode("utf-8")
                websocket.send_json(
                    {
                        "type": "submit",
                        "filename": "test.pdf",
                        "fileData": file_data,
                        "config": {
                            "language": "deu+eng",
                            "pdfa_level": "2",
                            "compression_profile": "balanced",
                            "ocr_enabled": True,
                            "skip_ocr_on_tagged_pdfs": True,
                        },
                    }
                )

                # Receive job_accepted message
                msg = websocket.receive_json()
                messages_received.append(msg)
                assert msg["type"] == "job_accepted"
                assert "job_id" in msg
                job_id = msg["job_id"]

                # Receive progress messages
                progress_messages = []
                while True:
                    try:
                        msg = websocket.receive_json()
                        messages_received.append(msg)

                        if msg["type"] == "progress":
                            progress_messages.append(msg)
                            # Verify progress message structure
                            assert "percentage" in msg
                            assert "step" in msg
                            assert 0 <= msg["percentage"] <= 100

                        elif msg["type"] == "completed":
                            # Verify completion message
                            assert "download_url" in msg
                            assert "filename" in msg
                            assert msg["job_id"] == job_id
                            break

                        elif msg["type"] == "error":
                            pytest.fail(f"Unexpected error: {msg}")

                    except Exception:
                        break

                # Verify we received progress updates
                assert len(progress_messages) > 0, "Should receive progress updates"

                # Verify progress percentages are increasing
                percentages = [m["percentage"] for m in progress_messages]
                assert percentages == sorted(
                    percentages
                ), "Percentages should be monotonically increasing"

                # Verify we got different steps
                steps = {m["step"] for m in progress_messages}
                assert len(steps) > 0, "Should have at least one progress step"

                # Test download endpoint
                download_url = msg["download_url"]
                assert download_url.startswith("/download/")

                # Download the file
                download_response = integration_client.get(download_url)
                assert download_response.status_code == 200
                assert download_response.headers["content-type"] == "application/pdf"
                assert len(download_response.content) > 0

    def test_progress_percentage_updates(
        self, integration_client: TestClient, sample_pdf: bytes
    ) -> None:
        """Test that progress percentages are correctly updated."""
        expected_percentages = [10.0, 20.0, 30.0, 50.0, 75.0, 90.0, 100.0]

        def mock_convert(
            input_pdf: Path,
            output_pdf: Path,
            *args,
            progress_callback=None,
            **kwargs,
        ) -> None:
            output_pdf.write_bytes(b"%PDF-1.4 converted")

            if progress_callback:
                for pct in expected_percentages:
                    progress_callback(
                        ProgressInfo(
                            step="ocr",
                            current=int(pct),
                            total=100,
                            percentage=pct,
                            message=f"Processing {pct}%",
                        )
                    )

        with patch.object(api, "convert_to_pdfa", side_effect=mock_convert):
            with integration_client.websocket_connect("/ws") as websocket:
                # Wait for connection
                websocket.receive_json()

                # Submit job
                file_data = base64.b64encode(sample_pdf).decode("utf-8")
                websocket.send_json(
                    {
                        "type": "submit",
                        "filename": "test.pdf",
                        "fileData": file_data,
                        "config": {},
                    }
                )

                # Receive job_accepted
                msg = websocket.receive_json()
                assert msg["type"] == "job_accepted"

                # Collect all progress messages
                received_percentages = []
                while True:
                    msg = websocket.receive_json()

                    if msg["type"] == "progress":
                        received_percentages.append(msg["percentage"])
                    elif msg["type"] == "completed":
                        break
                    elif msg["type"] == "error":
                        pytest.fail(f"Unexpected error: {msg}")

                # Verify we received percentage updates
                assert len(received_percentages) > 0
                # Verify percentages are in valid range
                assert all(0 <= p <= 100 for p in received_percentages)
                # Verify progress is monotonically increasing
                assert received_percentages == sorted(received_percentages)

    def test_ui_state_after_completion(
        self, integration_client: TestClient, sample_pdf: bytes
    ) -> None:
        """Test that UI state is properly reset after job completion."""

        def mock_convert(input_pdf: Path, output_pdf: Path, *args, **kwargs) -> None:
            output_pdf.write_bytes(b"%PDF-1.4 converted")

        with patch.object(api, "convert_to_pdfa", side_effect=mock_convert):
            with integration_client.websocket_connect("/ws") as websocket:
                # Wait for connection
                websocket.receive_json()

                # Submit job
                file_data = base64.b64encode(sample_pdf).decode("utf-8")
                websocket.send_json(
                    {
                        "type": "submit",
                        "filename": "test.pdf",
                        "fileData": file_data,
                        "config": {},
                    }
                )

                # Receive job_accepted
                msg = websocket.receive_json()
                assert msg["type"] == "job_accepted"
                job_id = msg["job_id"]

                # Wait for completion
                while True:
                    msg = websocket.receive_json()
                    if msg["type"] == "completed":
                        break

                # Verify job manager state
                job_manager = get_job_manager()
                job = job_manager.get_job(job_id)

                # Job should exist and be completed
                assert job is not None
                assert job.status == "completed"
                assert job.output_path is not None
                assert job.output_path.exists()

    def test_error_handling_ui_state(
        self, integration_client: TestClient, sample_pdf: bytes
    ) -> None:
        """Test that UI state is properly reset after errors."""

        def mock_convert_with_error(
            input_pdf: Path, output_pdf: Path, *args, **kwargs
        ) -> None:
            raise Exception("Simulated conversion error")

        with patch.object(api, "convert_to_pdfa", side_effect=mock_convert_with_error):
            with integration_client.websocket_connect("/ws") as websocket:
                # Wait for connection
                websocket.receive_json()

                # Submit job
                file_data = base64.b64encode(sample_pdf).decode("utf-8")
                websocket.send_json(
                    {
                        "type": "submit",
                        "filename": "test.pdf",
                        "fileData": file_data,
                        "config": {},
                    }
                )

                # Receive job_accepted
                msg = websocket.receive_json()
                assert msg["type"] == "job_accepted"
                job_id = msg["job_id"]

                # Wait for error message
                while True:
                    msg = websocket.receive_json()
                    if msg["type"] == "error":
                        assert "message" in msg
                        assert msg["job_id"] == job_id
                        break

                # Verify job manager state
                job_manager = get_job_manager()
                job = job_manager.get_job(job_id)

                # Job should exist and be failed
                assert job is not None
                assert job.status == "failed"
