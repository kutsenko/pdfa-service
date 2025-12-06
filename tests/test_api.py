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
