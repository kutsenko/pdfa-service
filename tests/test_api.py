"""Tests for the FastAPI PDF/A conversion service."""

from __future__ import annotations

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

    def fake_convert(input_pdf, output_pdf, *, language, pdfa_level) -> None:
        output_pdf.write_bytes(b"%PDF-1.4 converted")
        fake_convert.called_with = {  # type: ignore[attr-defined]
            "input": input_pdf,
            "output": output_pdf,
            "language": language,
            "pdfa_level": pdfa_level,
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


def test_convert_endpoint_rejects_non_pdf(client: TestClient) -> None:
    """Non-PDF uploads should be rejected with HTTP 400."""
    response = client.post(
        "/convert",
        files={"file": ("notes.txt", b"text", "text/plain")},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Only PDF uploads are supported."


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
