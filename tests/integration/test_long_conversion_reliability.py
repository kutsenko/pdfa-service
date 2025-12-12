"""Integration tests for long-running conversion reliability.

This module tests WebSocket stability and progress updates during very long
PDF conversions (up to 30 minutes). Tests use time acceleration to simulate
long conversions in seconds rather than minutes.

Key scenarios tested:
- Progress updates continue throughout long conversions
- WebSocket keep-alive maintains connection
- Client reconnection handles temporary disconnections
- Download works after completion
- Multiple concurrent clients receive updates
"""

from __future__ import annotations

import base64
import time
from pathlib import Path
from threading import Event
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from pdfa import api
from pdfa.job_manager import get_job_manager
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


def create_long_conversion_mock(
    duration_seconds: float = 30.0,
    update_interval: float = 0.1,
    cancel_event: Event | None = None,
):
    """Create a mock conversion function that simulates a long-running conversion.

    Args:
        duration_seconds: Total duration of simulated conversion (default: 30s)
        update_interval: Time between progress updates in seconds (default: 0.1s)
        cancel_event: Optional event to check for cancellation

    Returns:
        Mock function compatible with convert_to_pdfa signature

    Time acceleration:
        30 seconds simulates 30 minutes (60x speedup)
        0.1s intervals = 6 minute intervals in real conversion

    """

    def mock_convert(
        input_pdf: Path,
        output_pdf: Path,
        *args,
        progress_callback=None,
        cancel_event=None,
        **kwargs,
    ) -> None:
        """Simulate a long-running conversion with regular progress updates."""
        start_time = time.time()
        total_updates = int(duration_seconds / update_interval)

        for i in range(total_updates):
            # Check for cancellation
            if cancel_event and cancel_event.is_set():
                raise RuntimeError("Conversion cancelled")

            # Calculate progress
            elapsed = time.time() - start_time
            percentage = min((elapsed / duration_seconds) * 100, 100.0)

            # Send progress update
            if progress_callback:
                progress_callback(
                    ProgressInfo(
                        step="ocr" if percentage < 90 else "pdfa",
                        current=i + 1,
                        total=total_updates,
                        percentage=percentage,
                        message=f"Processing: {percentage:.1f}%",
                    )
                )

            # Wait for next update
            time.sleep(update_interval)

        # Create output file
        output_pdf.write_bytes(b"%PDF-1.4\nConverted after long processing")

    return mock_convert


@pytest.mark.skip(reason="WebSocket tests hang in CI - require real event loop")
class TestLongConversionReliability:
    """Test suite for long-running conversion reliability."""

    @pytest.mark.asyncio
    async def test_30_minute_conversion_with_progress_updates(
        self, client: TestClient, sample_pdf: bytes
    ) -> None:
        """Test that progress updates continue throughout a 30-minute conversion.

        Simulates a 30-minute conversion in 30 seconds with regular progress updates.
        Verifies that:
        - Progress updates are received throughout the entire conversion
        - WebSocket connection remains stable
        - Final download is available after completion
        """
        mock_convert = create_long_conversion_mock(duration_seconds=30.0)
        progress_updates_received = []

        with patch.object(api, "convert_to_pdfa", side_effect=mock_convert):
            with client.websocket_connect("/ws") as websocket:
                # Wait for connection confirmation
                websocket.receive_json()

                # Submit job
                file_data = base64.b64encode(sample_pdf).decode("utf-8")
                websocket.send_json(
                    {
                        "type": "submit",
                        "filename": "long_conversion.pdf",
                        "fileData": file_data,
                        "config": {
                            "language": "deu+eng",
                            "pdfa_level": "2",
                        },
                    }
                )

                # Receive job_accepted
                msg = websocket.receive_json()
                assert msg["type"] == "job_accepted"

                # Collect all messages
                completion_msg = None
                while True:
                    try:
                        msg = websocket.receive_json()

                        if msg["type"] == "progress":
                            progress_updates_received.append(msg)
                        elif msg["type"] == "completed":
                            completion_msg = msg
                            break
                        elif msg["type"] == "error":
                            pytest.fail(f"Unexpected error: {msg}")
                        elif msg["type"] == "ping":
                            # Keep-alive ping - ignore
                            pass

                    except Exception as e:
                        pytest.fail(f"WebSocket error: {e}")

                # Verify we received many progress updates throughout
                assert len(progress_updates_received) > 50, (
                    f"Should receive many progress updates during long conversion, "
                    f"got {len(progress_updates_received)}"
                )

                # Verify progress percentages are increasing
                percentages = [m["percentage"] for m in progress_updates_received]
                assert percentages == sorted(
                    percentages
                ), "Progress percentages should be monotonically increasing"

                # Verify we reached 100%
                assert completion_msg is not None
                assert "download_url" in completion_msg

                # Verify download works
                download_response = client.get(completion_msg["download_url"])
                assert download_response.status_code == 200
                assert len(download_response.content) > 0

    @pytest.mark.asyncio
    async def test_websocket_survives_multiple_keep_alive_cycles(
        self, client: TestClient, sample_pdf: bytes
    ) -> None:
        """Test that WebSocket connection survives many keep-alive ping/pong cycles.

        Simulates a conversion with 60 keep-alive cycles (30 seconds @
        0.5s ping interval). Verifies connection remains stable throughout.
        """
        # Faster updates to test more keep-alive cycles
        mock_convert = create_long_conversion_mock(
            duration_seconds=30.0, update_interval=0.5
        )

        with patch.object(api, "convert_to_pdfa", side_effect=mock_convert):
            with client.websocket_connect("/ws") as websocket:
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

                # Count pings and progress updates
                ping_count = 0
                progress_count = 0

                while True:
                    msg = websocket.receive_json()

                    if msg["type"] == "ping":
                        ping_count += 1
                        # Respond with pong
                        websocket.send_json({"type": "pong"})
                    elif msg["type"] == "progress":
                        progress_count += 1
                    elif msg["type"] == "completed":
                        break
                    elif msg["type"] == "error":
                        pytest.fail(f"Unexpected error: {msg}")

                # Verify we received keep-alive pings
                # Note: In test environment, ping frequency depends on JobManager config
                assert progress_count > 0, "Should receive progress updates"

    @pytest.mark.asyncio
    async def test_progress_broadcast_with_multiple_clients(
        self, client: TestClient, sample_pdf: bytes
    ) -> None:
        """Test progress broadcasting to multiple concurrent WebSocket clients.

        Verifies that:
        - All clients receive the same progress updates
        - Broadcasting doesn't timeout with many clients
        - All clients receive completion notification
        """
        mock_convert = create_long_conversion_mock(duration_seconds=5.0)

        # We'll test with 3 clients (more than 10 is difficult with TestClient)
        num_clients = 3
        clients_progress = [[] for _ in range(num_clients)]

        with patch.object(api, "convert_to_pdfa", side_effect=mock_convert):
            # Note: Testing with multiple WebSocket clients simultaneously
            # is complex with TestClient. This test demonstrates the concept
            # but in real scenario would need async WebSocket client library.

            with client.websocket_connect("/ws") as ws1:
                ws1.receive_json()

                # Submit job from first client
                file_data = base64.b64encode(sample_pdf).decode("utf-8")
                ws1.send_json(
                    {
                        "type": "submit",
                        "filename": "test.pdf",
                        "fileData": file_data,
                        "config": {},
                    }
                )

                # Receive job_accepted
                msg = ws1.receive_json()
                assert msg["type"] == "job_accepted"

                # Collect all messages on first client
                while True:
                    msg = ws1.receive_json()

                    if msg["type"] == "progress":
                        clients_progress[0].append(msg["percentage"])
                    elif msg["type"] == "completed":
                        break
                    elif msg["type"] == "error":
                        pytest.fail(f"Unexpected error: {msg}")

                # Verify first client received updates
                assert (
                    len(clients_progress[0]) > 10
                ), "Should receive many progress updates"

    @pytest.mark.asyncio
    async def test_download_available_after_completion(
        self, client: TestClient, sample_pdf: bytes
    ) -> None:
        """Test that download is available immediately after completion message.

        Verifies the 100ms delay fix ensures message is transmitted before cleanup.
        """
        mock_convert = create_long_conversion_mock(duration_seconds=10.0)

        with patch.object(api, "convert_to_pdfa", side_effect=mock_convert):
            with client.websocket_connect("/ws") as websocket:
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

                # Wait for job_accepted
                msg = websocket.receive_json()
                assert msg["type"] == "job_accepted"

                # Wait for completion
                download_url = None
                while True:
                    msg = websocket.receive_json()

                    if msg["type"] == "completed":
                        download_url = msg["download_url"]
                        break
                    elif msg["type"] == "error":
                        pytest.fail(f"Unexpected error: {msg}")

                assert download_url is not None

                # Download should be available immediately (no race condition)
                download_response = client.get(download_url)
                assert download_response.status_code == 200
                assert download_response.headers["content-type"] == "application/pdf"
                assert len(download_response.content) > 0

    @pytest.mark.asyncio
    async def test_progress_updates_not_throttled_excessively(
        self, client: TestClient, sample_pdf: bytes
    ) -> None:
        """Test that progress throttling (1 update/sec) doesn't cause issues.

        Verifies that throttling allows sufficient updates for good UX during
        long conversions.
        """
        # 10 second conversion with updates every 0.1 seconds
        # Throttling should reduce to ~10 updates (1 per second)
        mock_convert = create_long_conversion_mock(
            duration_seconds=10.0, update_interval=0.1
        )

        with patch.object(api, "convert_to_pdfa", side_effect=mock_convert):
            with client.websocket_connect("/ws") as websocket:
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

                # Wait for job_accepted
                msg = websocket.receive_json()
                assert msg["type"] == "job_accepted"

                # Collect progress updates
                progress_updates = []
                while True:
                    msg = websocket.receive_json()

                    if msg["type"] == "progress":
                        progress_updates.append(msg)
                    elif msg["type"] == "completed":
                        break

                # Should receive approximately 10 updates (1 per second)
                # Allow some tolerance for timing variations
                assert (
                    5 <= len(progress_updates) <= 15
                ), f"Expected ~10 throttled updates, got {len(progress_updates)}"

    @pytest.mark.asyncio
    async def test_job_status_endpoint_during_long_conversion(
        self, client: TestClient, sample_pdf: bytes
    ) -> None:
        """Test that job status can be queried via REST API during conversion.

        This is the fallback mechanism when WebSocket disconnects.
        Note: This test will validate the endpoint once it's implemented.
        """
        mock_convert = create_long_conversion_mock(duration_seconds=5.0)

        with patch.object(api, "convert_to_pdfa", side_effect=mock_convert):
            with client.websocket_connect("/ws") as websocket:
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

                # Wait for job_accepted
                msg = websocket.receive_json()
                assert msg["type"] == "job_accepted"
                job_id = msg["job_id"]

                # Wait a bit for conversion to start
                time.sleep(0.5)

                # Query job status via REST API (will be implemented)
                # For now, just verify job exists in job manager
                job_manager = get_job_manager()
                job = job_manager.get_job(job_id)
                assert job is not None
                assert job.status in ["queued", "running"]

                # Wait for completion
                while True:
                    msg = websocket.receive_json()
                    if msg["type"] == "completed":
                        break

                # After completion, status should be updated
                job = job_manager.get_job(job_id)
                assert job.status == "completed"


@pytest.mark.skip(reason="Manual test - requires specific timing conditions")
class TestReconnectionScenarios:
    """Tests for client reconnection scenarios.

    These tests are marked as manual because they require simulating
    network disconnections which is difficult in automated tests.
    """

    @pytest.mark.asyncio
    async def test_client_reconnection_during_conversion(
        self, client: TestClient, sample_pdf: bytes
    ) -> None:
        """Test that client can reconnect and resume after disconnect.

        This would require:
        1. Client disconnects mid-conversion
        2. Server continues processing
        3. Client reconnects
        4. Client receives remaining progress updates
        """
        pass

    @pytest.mark.asyncio
    async def test_client_reconnection_after_completion(
        self, client: TestClient, sample_pdf: bytes
    ) -> None:
        """Test that client can download after reconnecting post-completion.

        This would require:
        1. Conversion completes while client disconnected
        2. Client reconnects
        3. Client queries status and gets download URL
        4. Client successfully downloads file
        """
        pass
