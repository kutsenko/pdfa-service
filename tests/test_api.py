"""Tests for the FastAPI PDF/A conversion service."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from ocrmypdf import exceptions as ocrmypdf_exceptions

from pdfa import api


@pytest.fixture()
def client() -> TestClient:
    """Return a test client bound to the FastAPI app."""
    return TestClient(api.app)


def test_convert_endpoint_success(monkeypatch, client: TestClient) -> None:
    """The endpoint should convert files and return a PDF response."""

    def fake_convert(
        input_pdf,
        output_pdf,
        *,
        language,
        pdfa_level,
        ocr_enabled,
        skip_ocr_on_tagged_pdfs=True,
        compression_config=None,
    ) -> None:
        output_pdf.write_bytes(b"%PDF-1.4 converted")
        fake_convert.called_with = {  # type: ignore[attr-defined]
            "input": input_pdf,
            "output": output_pdf,
            "language": language,
            "pdfa_level": pdfa_level,
            "ocr_enabled": ocr_enabled,
        }

    monkeypatch.setattr(api, "convert_to_pdfa", fake_convert)

    response = client.post(
        "/convert",
        data={"language": "eng", "pdfa_level": "1"},
        files={"file": ("sample.pdf", b"%PDF-1.4 fake", "application/pdf")},
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "content-disposition" in response.headers
    assert response.content.startswith(b"%PDF-1.4")
    assert fake_convert.called_with["language"] == "eng"  # type: ignore[attr-defined]
    assert fake_convert.called_with["pdfa_level"] == "1"  # type: ignore[attr-defined]
    assert fake_convert.called_with["ocr_enabled"] is True  # type: ignore[attr-defined]


def test_convert_endpoint_with_ocr_disabled(monkeypatch, client: TestClient) -> None:
    """The endpoint should pass ocr_enabled=False when requested."""

    def fake_convert(
        input_pdf,
        output_pdf,
        *,
        language,
        pdfa_level,
        ocr_enabled,
        skip_ocr_on_tagged_pdfs=True,
        compression_config=None,
    ) -> None:
        output_pdf.write_bytes(b"%PDF-1.4 converted")
        fake_convert.called_with = {  # type: ignore[attr-defined]
            "ocr_enabled": ocr_enabled,
        }

    monkeypatch.setattr(api, "convert_to_pdfa", fake_convert)

    response = client.post(
        "/convert",
        data={"ocr_enabled": False},
        files={"file": ("sample.pdf", b"%PDF-1.4 fake", "application/pdf")},
    )

    assert response.status_code == 200
    assert fake_convert.called_with["ocr_enabled"] is False  # type: ignore[attr-defined]


def test_convert_endpoint_rejects_non_pdf(client: TestClient) -> None:
    """Non-PDF uploads should be rejected with HTTP 400."""
    response = client.post(
        "/convert",
        files={"file": ("notes.txt", b"text", "text/plain")},
    )

    assert response.status_code == 400
    assert "Supported formats" in response.json()["detail"]


def test_convert_endpoint_handles_conversion_failure(
    monkeypatch, client: TestClient
) -> None:
    """OCRmyPDF failures should surface as HTTP 500 errors."""

    class FakeError(ocrmypdf_exceptions.ExitCodeException):  # type: ignore[misc]
        """Stub exception with a fixed message for testing."""

        def __str__(self) -> str:
            return "ocr failure"

    def raise_error(*_: Any, **__: Any) -> None:
        raise FakeError()

    monkeypatch.setattr(api, "convert_to_pdfa", raise_error)

    response = client.post(
        "/convert",
        files={"file": ("sample.pdf", b"%PDF-1.4 fake", "application/pdf")},
    )

    assert response.status_code == 500
    assert response.json()["detail"] == "OCRmyPDF failed: ocr failure"


def test_convert_endpoint_unicode_filename(monkeypatch, client: TestClient) -> None:
    """Unicode filenames (umlauts, accents) should be properly encoded in headers."""

    def fake_convert(
        input_pdf: Path,
        output_pdf: Path,
        *_: Any,
        **__: Any,
    ) -> None:
        # Create a fake output PDF
        output_pdf.write_bytes(b"%PDF-1.4 converted")

    monkeypatch.setattr(api, "convert_to_pdfa", fake_convert)

    # Test with German umlauts, French accents, and combining characters
    unicode_filename = "Testdokumént_mit_Ümlauten_und_Akzénten.pdf"
    response = client.post(
        "/convert",
        files={"file": (unicode_filename, b"%PDF-1.4 fake", "application/pdf")},
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"

    # Check that Content-Disposition header uses RFC 5987 encoding
    content_disposition = response.headers.get("content-disposition", "")
    assert "filename*=UTF-8''" in content_disposition
    # The filename should be URL-encoded in the header
    assert (
        "Testdokum" in content_disposition or "Testdokum%C3%A9nt" in content_disposition
    )


def test_web_ui_root_path(client: TestClient) -> None:
    """Root path should serve the web UI with auto language detection."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    # Should have auto language detection enabled
    assert 'data-lang="auto"' in response.text


def test_web_ui_english(client: TestClient) -> None:
    """English web UI should have correct language attribute."""
    response = client.get("/en")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    # Should have English language set
    assert 'lang="en"' in response.text
    assert 'data-lang="en"' in response.text
    # Should NOT have auto detection
    assert 'data-lang="auto"' not in response.text


def test_web_ui_german(client: TestClient) -> None:
    """German web UI should have correct language attribute."""
    response = client.get("/de")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    # Should have German language set
    assert 'lang="de"' in response.text
    assert 'data-lang="de"' in response.text


def test_web_ui_spanish(client: TestClient) -> None:
    """Spanish web UI should have correct language attribute."""
    response = client.get("/es")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    # Should have Spanish language set
    assert 'lang="es"' in response.text
    assert 'data-lang="es"' in response.text


def test_web_ui_french(client: TestClient) -> None:
    """French web UI should have correct language attribute."""
    response = client.get("/fr")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    # Should have French language set
    assert 'lang="fr"' in response.text
    assert 'data-lang="fr"' in response.text


def test_web_ui_unsupported_language(client: TestClient) -> None:
    """Unsupported language should return 404."""
    response = client.get("/xx")
    assert response.status_code == 404
    assert "not supported" in response.json()["detail"]


def test_web_ui_language_switcher_links(client: TestClient) -> None:
    """Web UI should contain language switcher links."""
    response = client.get("/en")
    assert response.status_code == 200
    # Check for language switcher links
    assert 'href="/en"' in response.text
    assert 'href="/de"' in response.text
    assert 'href="/es"' in response.text
    assert 'href="/fr"' in response.text


def test_convert_with_compression_profile_balanced(
    monkeypatch, client: TestClient
) -> None:
    """Test conversion with balanced compression profile."""
    compression_config_used = {}

    def fake_convert(
        input_pdf,
        output_pdf,
        *,
        language,
        pdfa_level,
        ocr_enabled,
        skip_ocr_on_tagged_pdfs=True,
        compression_config=None,
    ) -> None:
        output_pdf.write_bytes(b"%PDF-1.4 converted")
        # Capture the compression config that was used
        compression_config_used["config"] = compression_config

    monkeypatch.setattr(api, "convert_to_pdfa", fake_convert)

    response = client.post(
        "/convert",
        data={"language": "eng", "pdfa_level": "2", "compression_profile": "balanced"},
        files={"file": ("sample.pdf", b"%PDF-1.4 fake", "application/pdf")},
    )

    assert response.status_code == 200
    # Verify balanced profile was used (150 DPI, quality 85)
    assert compression_config_used["config"].image_dpi == 150
    assert compression_config_used["config"].jpg_quality == 85


def test_convert_with_compression_profile_quality(
    monkeypatch, client: TestClient
) -> None:
    """Test conversion with quality compression profile."""
    compression_config_used = {}

    def fake_convert(
        input_pdf,
        output_pdf,
        *,
        language,
        pdfa_level,
        ocr_enabled,
        skip_ocr_on_tagged_pdfs=True,
        compression_config=None,
    ) -> None:
        output_pdf.write_bytes(b"%PDF-1.4 converted")
        compression_config_used["config"] = compression_config

    monkeypatch.setattr(api, "convert_to_pdfa", fake_convert)

    response = client.post(
        "/convert",
        data={"language": "eng", "pdfa_level": "2", "compression_profile": "quality"},
        files={"file": ("sample.pdf", b"%PDF-1.4 fake", "application/pdf")},
    )

    assert response.status_code == 200
    # Verify quality profile was used (300 DPI, quality 95)
    assert compression_config_used["config"].image_dpi == 300
    assert compression_config_used["config"].jpg_quality == 95


def test_convert_with_compression_profile_aggressive(
    monkeypatch, client: TestClient
) -> None:
    """Test conversion with aggressive compression profile."""
    compression_config_used = {}

    def fake_convert(
        input_pdf,
        output_pdf,
        *,
        language,
        pdfa_level,
        ocr_enabled,
        skip_ocr_on_tagged_pdfs=True,
        compression_config=None,
    ) -> None:
        output_pdf.write_bytes(b"%PDF-1.4 converted")
        compression_config_used["config"] = compression_config

    monkeypatch.setattr(api, "convert_to_pdfa", fake_convert)

    response = client.post(
        "/convert",
        data={
            "language": "eng",
            "pdfa_level": "2",
            "compression_profile": "aggressive",
        },
        files={"file": ("sample.pdf", b"%PDF-1.4 fake", "application/pdf")},
    )

    assert response.status_code == 200
    # Verify aggressive profile was used (100 DPI, quality 75)
    assert compression_config_used["config"].image_dpi == 100
    assert compression_config_used["config"].jpg_quality == 75


def test_convert_with_compression_profile_minimal(
    monkeypatch, client: TestClient
) -> None:
    """Test conversion with minimal compression profile."""
    compression_config_used = {}

    def fake_convert(
        input_pdf,
        output_pdf,
        *,
        language,
        pdfa_level,
        ocr_enabled,
        skip_ocr_on_tagged_pdfs=True,
        compression_config=None,
    ) -> None:
        output_pdf.write_bytes(b"%PDF-1.4 converted")
        compression_config_used["config"] = compression_config

    monkeypatch.setattr(api, "convert_to_pdfa", fake_convert)

    response = client.post(
        "/convert",
        data={"language": "eng", "pdfa_level": "2", "compression_profile": "minimal"},
        files={"file": ("sample.pdf", b"%PDF-1.4 fake", "application/pdf")},
    )

    assert response.status_code == 200
    # Verify minimal profile was used (72 DPI, quality 70)
    assert compression_config_used["config"].image_dpi == 72
    assert compression_config_used["config"].jpg_quality == 70


def test_web_ui_has_compression_profile_selector(client: TestClient) -> None:
    """Web UI should contain compression profile selector."""
    response = client.get("/en")
    assert response.status_code == 200
    # Check for compression profile selector
    assert 'id="compression_profile"' in response.text
    assert 'value="balanced"' in response.text
    assert 'value="quality"' in response.text
    assert 'value="aggressive"' in response.text
    assert 'value="minimal"' in response.text


# WebSocket Integration Tests


def test_websocket_connection(client: TestClient) -> None:
    """Test WebSocket connection can be established."""
    with client.websocket_connect("/ws") as websocket:
        # Connection established successfully
        assert websocket is not None


def test_websocket_ping_pong(client: TestClient) -> None:
    """Test WebSocket ping/pong mechanism."""
    with client.websocket_connect("/ws") as websocket:
        # Send ping message
        websocket.send_json({"type": "ping"})

        # Receive pong response
        response = websocket.receive_json()
        assert response["type"] == "pong"


def test_websocket_submit_job(monkeypatch, client: TestClient) -> None:
    """Test job submission via WebSocket."""
    import base64

    def fake_convert(
        input_pdf,
        output_pdf,
        *,
        language,
        pdfa_level,
        ocr_enabled,
        skip_ocr_on_tagged_pdfs=True,
        compression_config=None,
        progress_callback=None,
        cancel_event=None,
    ) -> None:
        # Simulate conversion
        output_pdf.write_bytes(b"%PDF-1.4 converted")

    monkeypatch.setattr(api, "convert_to_pdfa", fake_convert)

    with client.websocket_connect("/ws") as websocket:
        # Encode sample PDF
        pdf_data = base64.b64encode(b"%PDF-1.4 test").decode()

        # Submit job
        websocket.send_json(
            {
                "type": "submit",
                "filename": "test.pdf",
                "fileData": pdf_data,
                "config": {
                    "language": "eng",
                    "pdfa_level": "2",
                    "compression_profile": "balanced",
                    "ocr_enabled": True,
                    "skip_ocr_on_tagged_pdfs": True,
                },
            }
        )

        # Receive job_accepted message
        response = websocket.receive_json()
        assert response["type"] == "job_accepted"
        assert "job_id" in response
        job_id = response["job_id"]

        # Receive completion message (job processes quickly with mock)
        messages = []
        while True:
            try:
                msg = websocket.receive_json()
                messages.append(msg)
                if msg["type"] == "completed":
                    break
            except Exception:
                break

        # Verify we got completion
        completed_messages = [m for m in messages if m["type"] == "completed"]
        assert len(completed_messages) == 1

        completed = completed_messages[0]
        assert completed["job_id"] == job_id
        assert "download_url" in completed
        assert completed["download_url"].startswith("/download/")


def test_websocket_cancel_message(client: TestClient) -> None:
    """Test WebSocket accepts cancel messages."""
    import base64

    with client.websocket_connect("/ws") as websocket:
        # Submit a job first
        pdf_data = base64.b64encode(b"%PDF-1.4 test").decode()
        websocket.send_json(
            {
                "type": "submit",
                "filename": "test.pdf",
                "fileData": pdf_data,
                "config": {},
            }
        )

        # Get job_id
        response = websocket.receive_json()
        job_id = response["job_id"]

        # Send cancel message immediately
        websocket.send_json({"type": "cancel", "job_id": job_id})

        # WebSocket should remain open - send ping
        websocket.send_json({"type": "ping"})

        # Drain messages until we get pong (may receive progress, cancelled, etc.)
        for _ in range(5):  # Safety limit
            response = websocket.receive_json()
            if response.get("type") == "pong":
                break
        else:
            # If we didn't break, we didn't get pong
            assert False, f"Expected pong message, got: {response}"

        assert response["type"] == "pong"


def test_websocket_invalid_message_type(client: TestClient) -> None:
    """Test WebSocket handles invalid message types gracefully."""
    with client.websocket_connect("/ws") as websocket:
        # Send invalid message type
        websocket.send_json({"type": "invalid_type"})

        # Should receive an error message
        response = websocket.receive_json()
        assert response["type"] == "error"

        # Connection should still work
        websocket.send_json({"type": "ping"})
        pong = websocket.receive_json()
        assert pong["type"] == "pong"


def test_websocket_missing_filename(client: TestClient) -> None:
    """Test WebSocket rejects job submission without filename."""
    import base64

    with client.websocket_connect("/ws") as websocket:
        pdf_data = base64.b64encode(b"%PDF-1.4 test").decode()

        # Submit job without filename
        websocket.send_json(
            {
                "type": "submit",
                "fileData": pdf_data,
                "config": {},
            }
        )

        # Should receive error
        response = websocket.receive_json()
        assert response["type"] == "error"


def test_websocket_invalid_base64(client: TestClient) -> None:
    """Test WebSocket rejects invalid base64 data."""
    with client.websocket_connect("/ws") as websocket:
        # Submit job with invalid base64
        websocket.send_json(
            {
                "type": "submit",
                "filename": "test.pdf",
                "fileData": "not-valid-base64!!!",
                "config": {},
            }
        )

        # Should receive error
        response = websocket.receive_json()
        assert response["type"] == "error"


def test_download_endpoint_success(monkeypatch, client: TestClient) -> None:
    """Test download endpoint returns converted file."""
    import tempfile
    import uuid
    from pathlib import Path

    from pdfa.job_manager import Job, get_job_manager

    job_manager = get_job_manager()

    # Create a temporary file to serve
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "output.pdf"
        output_path.write_bytes(b"%PDF-1.4 converted")

        # Create a job in completed state
        job_id = str(uuid.uuid4())
        import asyncio

        job = Job(
            job_id=job_id,
            status="completed",
            filename="test.pdf",
            input_path=Path(tmpdir) / "input.pdf",
            output_path=output_path,
            config={},
            progress=None,
            created_at=0,
            cancel_event=asyncio.Event(),
            websockets=set(),
        )

        # Add job to manager
        job_manager.jobs[job_id] = job

        try:
            # Request download
            response = client.get(f"/download/{job_id}")

            assert response.status_code == 200
            assert response.headers["content-type"] == "application/pdf"
            assert response.content == b"%PDF-1.4 converted"
        finally:
            # Cleanup
            if job_id in job_manager.jobs:
                del job_manager.jobs[job_id]


def test_download_endpoint_not_found(client: TestClient) -> None:
    """Test download endpoint returns 404 for unknown job."""
    response = client.get("/download/unknown-job-id")
    assert response.status_code == 404


def test_download_endpoint_not_completed(client: TestClient) -> None:
    """Test download endpoint returns 400 for non-completed job."""
    import asyncio
    import uuid
    from pathlib import Path

    from pdfa.job_manager import Job, get_job_manager

    job_manager = get_job_manager()

    job_id = str(uuid.uuid4())
    job = Job(
        job_id=job_id,
        status="processing",
        filename="test.pdf",
        input_path=Path("/tmp/input.pdf"),
        output_path=None,
        config={},
        progress=None,
        created_at=0,
        cancel_event=asyncio.Event(),
        websockets=set(),
    )

    job_manager.jobs[job_id] = job

    try:
        response = client.get(f"/download/{job_id}")
        assert response.status_code == 400
        assert "not completed" in response.json()["detail"]
    finally:
        if job_id in job_manager.jobs:
            del job_manager.jobs[job_id]


def test_head_request_root_endpoint(client: TestClient) -> None:
    """HEAD request to root endpoint should return 200 with appropriate headers."""
    response = client.head("/")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    # HEAD should not return a body
    assert response.content == b""


def test_head_request_health_endpoint(client: TestClient) -> None:
    """HEAD request to health endpoint should return 200 with appropriate headers."""
    response = client.head("/health")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    # HEAD should not return a body
    assert response.content == b""


def test_head_request_language_endpoint(client: TestClient) -> None:
    """HEAD request to language endpoint should return 200 with appropriate headers."""
    response = client.head("/en")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    # HEAD should not return a body
    assert response.content == b""


# Tests for /jobs/history endpoint


def test_jobs_history_requires_authentication(client: TestClient) -> None:
    """GET /api/v1/jobs/history should require authentication."""
    response = client.get("/api/v1/jobs/history")
    assert response.status_code == 401


def test_jobs_history_success(
    client: TestClient, auth_headers: dict, mock_mongodb
) -> None:
    """GET /api/v1/jobs/history should return user jobs with authentication."""
    from datetime import datetime
    from unittest.mock import AsyncMock, MagicMock

    # Mock repository to return jobs
    mock_cursor = AsyncMock()
    mock_cursor.to_list = AsyncMock(
        return_value=[
            {
                "job_id": "job-1",
                "user_id": "google_user_123456",
                "status": "completed",
                "filename": "test1.pdf",
                "config": {"pdfa_level": "2"},
                "created_at": datetime(2024, 1, 2, 10, 0),
                "started_at": datetime(2024, 1, 2, 10, 0, 5),
                "completed_at": datetime(2024, 1, 2, 10, 2, 30),
                "duration_seconds": 145.0,
                "file_size_input": 1048576,
                "file_size_output": 524288,
                "compression_ratio": 0.5,
                "error": None,
            },
            {
                "job_id": "job-2",
                "user_id": "google_user_123456",
                "status": "completed",
                "filename": "test2.pdf",
                "config": {"pdfa_level": "3"},
                "created_at": datetime(2024, 1, 1, 10, 0),
                "started_at": datetime(2024, 1, 1, 10, 0, 5),
                "completed_at": datetime(2024, 1, 1, 10, 1, 0),
                "duration_seconds": 55.0,
                "file_size_input": 2097152,
                "file_size_output": 1048576,
                "compression_ratio": 0.5,
                "error": None,
            },
        ]
    )

    mock_find = MagicMock(return_value=mock_cursor)
    mock_mongodb.jobs.find = mock_find
    mock_cursor.sort = MagicMock(return_value=mock_cursor)
    mock_cursor.skip = MagicMock(return_value=mock_cursor)
    mock_cursor.limit = MagicMock(return_value=mock_cursor)

    response = client.get("/api/v1/jobs/history", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert "jobs" in data
    assert "total" in data
    assert "limit" in data
    assert "offset" in data
    assert len(data["jobs"]) == 2
    assert data["jobs"][0]["job_id"] == "job-1"
    assert data["jobs"][0]["filename"] == "test1.pdf"
    assert data["jobs"][0]["status"] == "completed"
    assert data["jobs"][0]["duration_seconds"] == 145.0


def test_jobs_history_with_pagination(
    client: TestClient, auth_headers: dict, mock_mongodb
) -> None:
    """GET /api/v1/jobs/history should support pagination."""
    from unittest.mock import AsyncMock, MagicMock

    mock_cursor = AsyncMock()
    mock_cursor.to_list = AsyncMock(return_value=[])
    mock_find = MagicMock(return_value=mock_cursor)
    mock_mongodb.jobs.find = mock_find
    mock_cursor.sort = MagicMock(return_value=mock_cursor)
    mock_cursor.skip = MagicMock(return_value=mock_cursor)
    mock_cursor.limit = MagicMock(return_value=mock_cursor)

    response = client.get(
        "/api/v1/jobs/history?limit=10&offset=20", headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["limit"] == 10
    assert data["offset"] == 20


def test_jobs_history_with_status_filter(
    client: TestClient, auth_headers: dict, mock_mongodb
) -> None:
    """GET /api/v1/jobs/history should support status filtering."""
    from unittest.mock import AsyncMock, MagicMock

    mock_cursor = AsyncMock()
    mock_cursor.to_list = AsyncMock(return_value=[])
    mock_find = MagicMock(return_value=mock_cursor)
    mock_mongodb.jobs.find = mock_find
    mock_cursor.sort = MagicMock(return_value=mock_cursor)
    mock_cursor.skip = MagicMock(return_value=mock_cursor)
    mock_cursor.limit = MagicMock(return_value=mock_cursor)

    response = client.get(
        "/api/v1/jobs/history?status=completed", headers=auth_headers
    )

    assert response.status_code == 200


def test_jobs_history_invalid_limit(client: TestClient, auth_headers: dict) -> None:
    """GET /api/v1/jobs/history should reject invalid limit values."""
    # Limit too low
    response = client.get("/api/v1/jobs/history?limit=0", headers=auth_headers)
    assert response.status_code == 400
    assert "must be between 1 and 100" in response.json()["detail"]

    # Limit too high
    response = client.get("/api/v1/jobs/history?limit=101", headers=auth_headers)
    assert response.status_code == 400
    assert "must be between 1 and 100" in response.json()["detail"]


def test_jobs_history_invalid_offset(client: TestClient, auth_headers: dict) -> None:
    """GET /api/v1/jobs/history should reject negative offset."""
    response = client.get("/api/v1/jobs/history?offset=-1", headers=auth_headers)
    assert response.status_code == 400
    assert "must be non-negative" in response.json()["detail"]


def test_jobs_history_invalid_status(client: TestClient, auth_headers: dict) -> None:
    """GET /api/v1/jobs/history should reject invalid status values."""
    response = client.get(
        "/api/v1/jobs/history?status=invalid_status", headers=auth_headers
    )
    assert response.status_code == 400
    assert "Invalid status" in response.json()["detail"]
