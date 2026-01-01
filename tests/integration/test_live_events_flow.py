"""Integration test for live event display via WebSocket (US-004).

This module tests the complete event broadcasting flow:
- Job submission and acceptance
- Job events broadcast via WebSocket
- Job completion with download URL
- Event message structure and i18n keys
"""

from __future__ import annotations

import base64
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from pdfa import api
from pdfa.progress_tracker import ProgressInfo


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


class TestLiveEventBroadcasting:
    """Test that job events are broadcast via WebSocket in real-time."""

    @pytest.mark.asyncio
    async def test_job_events_are_broadcast_via_websocket(
        self, client: TestClient, sample_pdf: bytes, tmp_path: Path
    ) -> None:
        """Verify that job events are broadcast to WebSocket clients."""
        # Track all WebSocket messages received
        messages_received = []
        job_events_received = []

        # Mock the conversion function
        def mock_convert(
            input_pdf: Path,
            output_pdf: Path,
            *args,
            event_callback=None,
            progress_callback=None,
            **kwargs,
        ) -> None:
            # Create output file
            output_pdf.write_bytes(b"%PDF-1.4 converted")

            # Simulate event logging if callback provided
            if event_callback:
                # event_callback is a synchronous wrapper, call it directly
                event_callback(
                    "ocr_decision",
                    decision="skip",
                    reason="tagged_pdf",
                    has_struct_tree_root=True,
                )

                event_callback(
                    "passthrough_mode",
                    mode="pdf_output_no_ocr",
                    tags_preserved=True,
                )

            # Simulate progress if callback provided
            if progress_callback:
                progress_callback(
                    ProgressInfo(
                        step="pdfa",
                        current=1,
                        total=1,
                        percentage=100.0,
                        message="Conversion complete",
                    )
                )

        with patch("pdfa.api.convert_to_pdfa", side_effect=mock_convert):
            # Connect to WebSocket
            with client.websocket_connect("/ws") as websocket:
                # Submit job
                websocket.send_json(
                    {
                        "type": "submit",
                        "filename": "test.pdf",
                        "fileData": base64.b64encode(sample_pdf).decode(),
                        "config": {
                            "language": "eng",
                            "pdfa_level": "2",
                            "ocr_enabled": True,
                        },
                    }
                )

                # Collect all messages until completed or error
                job_id = None
                completed = False
                max_messages = 50

                for _ in range(max_messages):
                    msg = websocket.receive_json()
                    messages_received.append(msg)
                    print(f"[TEST] Received message: {msg['type']}")

                    # Extract job_id from first message
                    if msg["type"] == "job_accepted":
                        job_id = msg["job_id"]
                        print(f"[TEST] Job accepted: {job_id}")

                    # Collect job_event messages
                    elif msg["type"] == "job_event":
                        job_events_received.append(msg)
                        print(f"[TEST] Job event: {msg['event_type']}")

                    # Check for completion
                    elif msg["type"] == "completed":
                        completed = True
                        print("[TEST] Job completed")
                        print(f"[TEST] Download URL: {msg.get('download_url')}")
                        break

                    elif msg["type"] == "error":
                        print(f"[TEST] Error: {msg.get('message')}")
                        pytest.fail(f"Job failed: {msg.get('message')}")
                        break

        # Print summary
        print("\n[TEST SUMMARY]")
        print(f"Total messages received: {len(messages_received)}")
        print(f"Job events received: {len(job_events_received)}")
        print(f"Message types: {[m['type'] for m in messages_received]}")

        # Assertions
        assert job_id is not None, "Should receive job_accepted message"
        assert len(job_events_received) >= 1, "Should receive at least one job_event"
        assert completed, "Should receive completed message"

        # Verify job_event message structure
        for event in job_events_received:
            assert event["type"] == "job_event"
            assert "job_id" in event
            assert "event_type" in event
            assert "timestamp" in event
            assert "message" in event
            assert "details" in event

            # Verify i18n keys are present
            details = event["details"]
            assert (
                "_i18n_key" in details
            ), f"Event {event['event_type']} missing _i18n_key"
            assert (
                "_i18n_params" in details
            ), f"Event {event['event_type']} missing _i18n_params"

            print(
                f"[TEST] Event {event['event_type']}: i18n_key = {details['_i18n_key']}"
            )

        # Verify completed message has download_url
        completed_msg = next(
            (m for m in messages_received if m["type"] == "completed"), None
        )
        assert completed_msg is not None
        assert "download_url" in completed_msg
        assert "filename" in completed_msg
        print(f"[TEST] Completed message: {completed_msg}")

    @pytest.mark.asyncio
    async def test_event_message_structure(self) -> None:
        """Test that JobEventMessage has correct structure for frontend."""
        from datetime import datetime

        from pdfa.websocket_protocol import JobEventMessage

        # Create a sample event message
        msg = JobEventMessage(
            job_id="test-job-123",
            event_type="ocr_decision",
            timestamp=datetime.now(UTC).isoformat(),
            message="OCR skipped: tagged PDF detected",
            details={
                "decision": "skip",
                "reason": "tagged_pdf",
                "_i18n_key": "ocr_decision.skip.tagged_pdf",
                "_i18n_params": {"decision": "skip", "reason": "tagged_pdf"},
            },
        )

        # Convert to dict (as sent over WebSocket)
        data = msg.to_dict()

        # Verify structure
        assert data["type"] == "job_event"
        assert data["job_id"] == "test-job-123"
        assert data["event_type"] == "ocr_decision"
        assert "timestamp" in data
        assert data["message"] == "OCR skipped: tagged PDF detected"
        assert data["details"]["_i18n_key"] == "ocr_decision.skip.tagged_pdf"
        assert data["details"]["_i18n_params"]["decision"] == "skip"

        # Verify it's JSON serializable
        json_str = json.dumps(data)
        assert json_str is not None

        # Verify it can be parsed back
        parsed = json.loads(json_str)
        assert parsed["type"] == "job_event"

    @pytest.mark.asyncio
    async def test_broadcast_failure_does_not_block_mongodb(
        self, tmp_path: Path
    ) -> None:
        """Verify that WebSocket broadcast failures don't prevent MongoDB persistence.

        This test ensures that event logging is resilient to WebSocket failures.
        """
        from pdfa.event_logger import log_ocr_decision_event

        job_id = "test-job-broadcast-fail"

        # Mock job_manager to raise exception on broadcast
        mock_job_manager = MagicMock()
        mock_job_manager.broadcast_to_job = AsyncMock(
            side_effect=Exception("WebSocket broadcast failed")
        )

        # Mock the repository at the class level
        mock_repo_instance = AsyncMock()
        mock_repo_class = MagicMock(return_value=mock_repo_instance)

        with patch("pdfa.job_manager.get_job_manager", return_value=mock_job_manager):
            with patch("pdfa.event_logger.JobRepository", mock_repo_class):
                # This should NOT raise an exception even though broadcast fails
                await log_ocr_decision_event(
                    job_id=job_id,
                    decision="skip",
                    reason="tagged_pdf",
                    has_struct_tree_root=True,
                )

                # Verify MongoDB persistence was attempted
                # (even though broadcast failed)
                mock_repo_instance.add_job_event.assert_called_once()


class TestJobCompletionAndDownload:
    """Test that job completion and download flow works correctly."""

    @pytest.mark.asyncio
    async def test_completed_message_contains_download_url(
        self, client: TestClient, sample_pdf: bytes
    ) -> None:
        """Verify that completed message includes download_url and filename.

        This test catches the bug where downloads are not offered after completion.
        """

        # Mock the conversion function
        def mock_convert(
            input_pdf: Path,
            output_pdf: Path,
            *args,
            **kwargs,
        ) -> None:
            # Create output file
            output_pdf.write_bytes(b"%PDF-1.4 converted to PDF/A")

        with patch("pdfa.api.convert_to_pdfa", side_effect=mock_convert):
            # Connect to WebSocket
            with client.websocket_connect("/ws") as websocket:
                # Submit job
                websocket.send_json(
                    {
                        "type": "submit",
                        "filename": "test.pdf",
                        "fileData": base64.b64encode(sample_pdf).decode(),
                        "config": {
                            "language": "eng",
                            "pdfa_level": "2",
                        },
                    }
                )

                # Collect messages until completed
                completed_message = None

                while True:
                    msg = websocket.receive_json()
                    print(f"[TEST] Received: {msg['type']}")

                    if msg["type"] == "completed":
                        completed_message = msg
                        print(f"[TEST] Completed message: {msg}")
                        break
                    elif msg["type"] == "error":
                        pytest.fail(f"Job failed: {msg.get('message')}")
                        break

        # CRITICAL ASSERTIONS - These catch the download bug
        assert completed_message is not None, "Should receive completed message"
        assert (
            "download_url" in completed_message
        ), "Completed message must have download_url"
        assert "filename" in completed_message, "Completed message must have filename"

        # Verify download_url format
        assert completed_message["download_url"].startswith("/download/"), (
            f"download_url should start with /download/, "
            f"got: {completed_message['download_url']}"
        )

        # Verify filename has _pdfa suffix
        assert completed_message["filename"].endswith(
            "_pdfa.pdf"
        ), f"filename should end with _pdfa.pdf, got: {completed_message['filename']}"

        print(f"[TEST] ✓ Download URL: {completed_message['download_url']}")
        print(f"[TEST] ✓ Filename: {completed_message['filename']}")

    @pytest.mark.asyncio
    async def test_download_endpoint_returns_file(
        self, client: TestClient, sample_pdf: bytes
    ) -> None:
        """Verify that /download/{job_id} endpoint returns the converted file.

        This test ensures the download actually works after completion.
        """
        job_id = None

        # Mock the conversion function
        def mock_convert(
            input_pdf: Path,
            output_pdf: Path,
            *args,
            **kwargs,
        ) -> None:
            # Create output file
            output_pdf.write_bytes(b"%PDF-1.4 converted to PDF/A")

        with patch("pdfa.api.convert_to_pdfa", side_effect=mock_convert):
            # Connect to WebSocket
            with client.websocket_connect("/ws") as websocket:
                # Submit job
                websocket.send_json(
                    {
                        "type": "submit",
                        "filename": "test.pdf",
                        "fileData": base64.b64encode(sample_pdf).decode(),
                        "config": {},
                    }
                )

                # Collect all messages until completed
                messages = []
                max_messages = 50  # Safety limit

                for _ in range(max_messages):
                    msg = websocket.receive_json()
                    messages.append(msg)
                    print(f"[TEST] Received: {msg['type']}")

                    if msg["type"] == "job_accepted":
                        job_id = msg["job_id"]
                        print(f"[TEST] Job ID: {job_id}")
                    elif msg["type"] == "completed":
                        download_url = msg["download_url"]
                        print(f"[TEST] Download URL: {download_url}")
                        break
                    elif msg["type"] == "error":
                        pytest.fail(f"Job failed: {msg.get('message')}")

                assert job_id is not None, "Should receive job_accepted message"

        # Now test the download endpoint
        assert job_id is not None

        # Make GET request to download endpoint
        response = client.get(f"/download/{job_id}")

        # CRITICAL ASSERTIONS - These verify download works
        assert (
            response.status_code == 200
        ), f"Download should return 200, got: {response.status_code}"

        assert response.headers["content-type"] == "application/pdf", (
            f"Should return PDF content-type, "
            f"got: {response.headers.get('content-type')}"
        )

        # Verify we got the converted file
        content = response.content
        assert len(content) > 0, "Downloaded file should not be empty"
        assert content.startswith(b"%PDF"), "Downloaded content should be a PDF"

        print(f"[TEST] ✓ Downloaded {len(content)} bytes")
        print(f"[TEST] ✓ Content-Type: {response.headers['content-type']}")

    @pytest.mark.asyncio
    async def test_complete_conversion_and_download_flow(
        self, client: TestClient, sample_pdf: bytes
    ) -> None:
        """End-to-end test: Submit job, receive events, get completion, download file.

        This is a comprehensive test that catches any breaks in the download flow.
        """

        # Mock the conversion function with events
        def mock_convert(
            input_pdf: Path,
            output_pdf: Path,
            *args,
            event_callback=None,
            progress_callback=None,
            **kwargs,
        ) -> None:
            # Create output file
            output_pdf.write_bytes(b"%PDF-1.4 converted to PDF/A-2b")

            # Simulate progress
            if progress_callback:
                from pdfa.progress_tracker import ProgressInfo

                progress_callback(
                    ProgressInfo(
                        step="pdfa",
                        current=1,
                        total=1,
                        percentage=100.0,
                        message="Conversion complete",
                    )
                )

            # Simulate an event
            if event_callback:
                # event_callback is a synchronous wrapper, call it directly
                event_callback(
                    "ocr_decision",
                    decision="skip",
                    reason="tagged_pdf",
                )

        with patch("pdfa.api.convert_to_pdfa", side_effect=mock_convert):
            # Connect to WebSocket
            with client.websocket_connect("/ws") as websocket:
                # Submit job
                websocket.send_json(
                    {
                        "type": "submit",
                        "filename": "complete_test.pdf",
                        "fileData": base64.b64encode(sample_pdf).decode(),
                        "config": {
                            "language": "eng",
                            "pdfa_level": "2",
                        },
                    }
                )

                # Track what we received
                job_id = None
                received_job_accepted = False
                received_progress = False
                received_job_event = False
                received_completed = False
                download_url = None
                filename = None

                while True:
                    msg = websocket.receive_json()
                    msg_type = msg["type"]
                    print(f"[TEST] Received: {msg_type}")

                    if msg_type == "job_accepted":
                        job_id = msg["job_id"]
                        received_job_accepted = True
                        print(f"[TEST] Job accepted: {job_id}")

                    elif msg_type == "progress":
                        received_progress = True
                        print(f"[TEST] Progress: {msg.get('percentage', 0)}%")

                    elif msg_type == "job_event":
                        received_job_event = True
                        print(f"[TEST] Event: {msg.get('event_type')}")

                    elif msg_type == "completed":
                        received_completed = True
                        download_url = msg.get("download_url")
                        filename = msg.get("filename")
                        print(f"[TEST] Completed: {download_url}")
                        break

                    elif msg_type == "error":
                        pytest.fail(f"Job failed with error: {msg.get('message')}")

        # COMPREHENSIVE ASSERTIONS
        print("\n[TEST] Verifying complete flow...")

        assert received_job_accepted, "Should receive job_accepted message"
        assert job_id is not None, "Should have job_id"

        assert received_progress, "Should receive at least one progress message"
        assert received_job_event, "Should receive at least one job_event message"

        # CRITICAL: These assertions catch the download bug
        assert received_completed, "Should receive completed message"
        assert download_url is not None, "Completed message should have download_url"
        assert filename is not None, "Completed message should have filename"
        assert download_url.startswith(
            "/download/"
        ), f"Invalid download_url: {download_url}"
        assert filename == "complete_test_pdfa.pdf", f"Unexpected filename: {filename}"

        # Test the download endpoint actually works
        response = client.get(download_url)
        assert (
            response.status_code == 200
        ), f"Download failed with status {response.status_code}"
        assert response.headers["content-type"] == "application/pdf"
        assert len(response.content) > 0, "Downloaded file is empty"

        print("[TEST] ✓ Complete flow verified successfully!")
        print(f"[TEST] ✓ Job ID: {job_id}")
        print(f"[TEST] ✓ Download URL: {download_url}")
        print(f"[TEST] ✓ Filename: {filename}")
        print(f"[TEST] ✓ Downloaded: {len(response.content)} bytes")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
