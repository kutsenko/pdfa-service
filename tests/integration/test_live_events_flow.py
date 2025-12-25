"""Integration test for live event display via WebSocket (US-004).

This module tests the complete event broadcasting flow:
- Job submission and acceptance
- Job events broadcast via WebSocket
- Job completion with download URL
- Event message structure and i18n keys
"""

from __future__ import annotations

import asyncio
import base64
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from pdfa import api
from pdfa.job_manager import get_job_manager
from pdfa.models import JobDocument, JobEvent
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
                # Simulate OCR decision event
                asyncio.run(
                    event_callback(
                        "ocr_decision",
                        decision="skip",
                        reason="tagged_pdf",
                        has_struct_tree_root=True,
                    )
                )

                # Simulate passthrough mode event
                asyncio.run(
                    event_callback(
                        "passthrough_mode",
                        mode="pdf_output_no_ocr",
                        tags_preserved=True,
                    )
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

        with patch("pdfa.converter.convert_to_pdfa", side_effect=mock_convert):
            # Connect to WebSocket
            with client.websocket_connect("/ws") as websocket:
                # Submit job
                websocket.send_json({
                    "type": "submit",
                    "filename": "test.pdf",
                    "fileData": base64.b64encode(sample_pdf).decode(),
                    "config": {
                        "language": "eng",
                        "pdfa_level": "2b",
                        "ocr_enabled": True,
                    },
                })

                # Collect all messages until completed or error
                job_id = None
                completed = False
                timeout_count = 0
                max_timeout = 50  # 5 seconds total (50 * 100ms)

                while not completed and timeout_count < max_timeout:
                    try:
                        msg = websocket.receive_json(timeout=0.1)
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
                            print(f"[TEST] Job completed")
                            print(f"[TEST] Download URL: {msg.get('download_url')}")

                        elif msg["type"] == "error":
                            print(f"[TEST] Error: {msg.get('message')}")
                            break

                    except Exception:
                        timeout_count += 1
                        await asyncio.sleep(0.1)

        # Print summary
        print(f"\n[TEST SUMMARY]")
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
            assert "_i18n_key" in details, f"Event {event['event_type']} missing _i18n_key"
            assert "_i18n_params" in details, f"Event {event['event_type']} missing _i18n_params"

            print(f"[TEST] Event {event['event_type']}: i18n_key = {details['_i18n_key']}")

        # Verify completed message has download_url
        completed_msg = next((m for m in messages_received if m["type"] == "completed"), None)
        assert completed_msg is not None
        assert "download_url" in completed_msg
        assert "filename" in completed_msg
        print(f"[TEST] Completed message: {completed_msg}")


    @pytest.mark.asyncio
    async def test_event_message_structure(self) -> None:
        """Test that JobEventMessage has correct structure for frontend."""
        from pdfa.websocket_protocol import JobEventMessage
        from datetime import datetime

        # Create a sample event message
        msg = JobEventMessage(
            job_id="test-job-123",
            event_type="ocr_decision",
            timestamp=datetime.utcnow().isoformat(),
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
    async def test_broadcast_failure_does_not_block_mongodb(self, tmp_path: Path) -> None:
        """Verify that WebSocket broadcast failures don't prevent MongoDB persistence."""
        from pdfa.event_logger import log_ocr_decision_event
        from pdfa.repositories import JobRepository

        job_id = "test-job-broadcast-fail"

        # Mock job_manager to raise exception on broadcast
        mock_job_manager = MagicMock()
        mock_job_manager.broadcast_to_job = AsyncMock(
            side_effect=Exception("WebSocket broadcast failed")
        )

        # Mock repository to verify add_job_event is called
        mock_repo = AsyncMock()

        with patch("pdfa.event_logger.get_job_manager", return_value=mock_job_manager):
            with patch("pdfa.event_logger.JobRepository", return_value=mock_repo):
                # This should NOT raise an exception even though broadcast fails
                await log_ocr_decision_event(
                    job_id=job_id,
                    decision="skip",
                    reason="tagged_pdf",
                    has_struct_tree_root=True,
                )

                # Verify MongoDB persistence was called
                mock_repo.add_job_event.assert_called_once()

                # Verify broadcast was attempted
                mock_job_manager.broadcast_to_job.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
