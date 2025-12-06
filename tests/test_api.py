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

    def fake_convert(
        input_pdf,
        output_pdf,
        *,
        language,
        pdfa_level,
        ocr_enabled,
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
