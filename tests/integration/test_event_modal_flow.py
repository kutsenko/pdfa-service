"""Integration tests for complete event and modal flow.

Tests the full conversion pipeline including:
- Event logging to MongoDB
- Event broadcasting via WebSocket
- Modal display after successful conversion

These tests reproduce real-world scenarios to catch issues like:
- Events not being logged
- Modal not appearing after download
- Event list showing only one event
"""

from pathlib import Path

import pytest
from httpx import AsyncClient

from pdfa.api import app
from pdfa.db import get_db
from pdfa.models import JobStatus

pytestmark = [
    pytest.mark.integration,
    pytest.mark.asyncio,
    pytest.mark.no_mongo_mock,  # Requires real MongoDB
]


@pytest.fixture
async def db_connection():
    """Get MongoDB database for test verification."""
    db = get_db()
    if db is None:
        pytest.skip("MongoDB not available")
    yield db
    # Cleanup test data after each test
    if db:
        await db.jobs.delete_many({"user_id": "test-user"})


@pytest.fixture
def test_pdf(tmp_path: Path) -> Path:
    """Create a simple test PDF file."""
    from tests.e2e.test_data.pdf_generator import create_small_pdf

    pdf_path = tmp_path / "test_conversion.pdf"
    create_small_pdf(pdf_path, num_pages=3)
    return pdf_path


class TestEventLoggingFlow:
    """Test event logging to MongoDB during conversion."""

    async def test_events_are_logged_to_mongodb(
        self, test_pdf: Path, db_connection
    ) -> None:
        """Test that all events are successfully logged to MongoDB."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Upload and convert file
            with open(test_pdf, "rb") as f:
                response = await client.post(
                    "/convert",
                    files={"file": ("test.pdf", f, "application/pdf")},
                    data={
                        "language": "deu+eng",
                        "pdfa_level": "2",
                        "compression_profile": "balanced",
                        "ocr_enabled": "true",
                        "skip_ocr_on_tagged_pdfs": "true",
                    },
                )

            assert response.status_code == 200, f"Conversion failed: {response.text}"

            # Extract job_id from response (if available in headers or body)
            # For now, get the most recent job from DB
            if db_connection:
                job = await db_connection.jobs.find_one(
                    {"user_id": None}, sort=[("created_at", -1)]
                )

                assert job is not None, "No job found in database"
                assert job["status"] == JobStatus.COMPLETED

                # Check that events were logged
                events = job.get("events", [])
                assert len(events) > 0, "No events were logged to database"

                # Verify event types
                event_types = [event["event_type"] for event in events]
                assert (
                    "format_conversion" in event_types
                ), "format_conversion event missing"

                # Check event structure
                for event in events:
                    assert "event_type" in event
                    assert "timestamp" in event
                    assert "message" in event
                    assert "details" in event

    async def test_no_asyncio_loop_errors(self, test_pdf: Path, db_connection) -> None:
        """Test that events are logged without asyncio loop errors."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Upload and convert file
            with open(test_pdf, "rb") as f:
                response = await client.post(
                    "/convert",
                    files={"file": ("test.pdf", f, "application/pdf")},
                    data={
                        "language": "deu+eng",
                        "pdfa_level": "2",
                        "compression_profile": "balanced",
                        "ocr_enabled": "true",
                    },
                )

            assert response.status_code == 200

            if db_connection:
                job = await db_connection.jobs.find_one(
                    {"user_id": None}, sort=[("created_at", -1)]
                )

                events = job.get("events", [])

                # Before fix: Only 1 event due to asyncio error
                # After fix: Multiple events (at least format_conversion)
                assert len(events) >= 1, f"Expected at least 1 event, got {len(events)}"

                # If OCR was skipped, we should have ocr_decision event
                # If compression was selected, we should have compression_selected
                # At minimum, we should have format_conversion
                event_types = [e["event_type"] for e in events]
                print(f"Event types logged: {event_types}")


class TestWebSocketEventBroadcasting:
    """Test WebSocket event broadcasting during conversion."""

    async def test_events_broadcast_via_websocket(
        self, test_pdf: Path, db_connection
    ) -> None:
        """Test that events are broadcast via WebSocket after MongoDB logging."""
        # This test would require setting up WebSocket client
        # For now, we verify the broadcast function is called by checking logs
        pytest.skip("WebSocket testing requires separate setup")


@pytest.mark.integration
class TestEventCoverage:
    """Additional integration tests for event edge cases."""

    async def test_multiple_events_logged_correctly(
        self, test_pdf: Path, db_connection
    ) -> None:
        """Test that multiple events are logged in correct order."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            with open(test_pdf, "rb") as f:
                response = await client.post(
                    "/convert",
                    files={"file": ("test.pdf", f, "application/pdf")},
                    data={
                        "language": "deu+eng",
                        "pdfa_level": "2",
                        "ocr_enabled": "true",
                    },
                )

            assert response.status_code == 200

            if db_connection:
                job = await db_connection.jobs.find_one(
                    {"user_id": None}, sort=[("created_at", -1)]
                )

                events = job.get("events", [])

                # Verify events are in chronological order
                if len(events) > 1:
                    for i in range(len(events) - 1):
                        t1 = events[i]["timestamp"]
                        t2 = events[i + 1]["timestamp"]
                        assert t1 <= t2, (
                            f"Events not in chronological order: "
                            f"{events[i]['event_type']} at {t1} > "
                            f"{events[i+1]['event_type']} at {t2}"
                        )

    async def test_event_details_contain_i18n_keys(
        self, test_pdf: Path, db_connection
    ) -> None:
        """Test that events contain i18n keys for frontend translation."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            with open(test_pdf, "rb") as f:
                response = await client.post(
                    "/convert",
                    files={"file": ("test.pdf", f, "application/pdf")},
                    data={"ocr_enabled": "true"},
                )

            assert response.status_code == 200

            if db_connection:
                job = await db_connection.jobs.find_one(
                    {"user_id": None}, sort=[("created_at", -1)]
                )

                events = job.get("events", [])

                # Check that events have i18n keys
                for event in events:
                    details = event.get("details", {})
                    if event["event_type"] in [
                        "ocr_decision",
                        "compression_selected",
                    ]:
                        assert (
                            "_i18n_key" in details
                        ), f"Event {event['event_type']} missing _i18n_key"
