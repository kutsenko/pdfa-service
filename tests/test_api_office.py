"""Tests for Office document conversion in the REST API."""

from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient

from pdfa import api
from pdfa.exceptions import OfficeConversionError


@pytest.fixture()
def client() -> TestClient:
    """Return a test client bound to the FastAPI app."""
    return TestClient(api.app)


class TestConvertOfficeDocuments:
    """Tests for Office document conversion endpoints."""

    def test_convert_docx_endpoint(self, monkeypatch, client: TestClient) -> None:
        """The endpoint should convert DOCX files."""

        def fake_convert_office(input_file, output_file) -> None:
            output_file.write_bytes(b"%PDF-1.4 converted")

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
            output_pdf.write_bytes(b"%PDF-1.4 pdfa")

        monkeypatch.setattr(api, "convert_office_to_pdf", fake_convert_office)
        monkeypatch.setattr(api, "convert_to_pdfa", fake_convert)

        response = client.post(
            "/convert",
            data={"language": "eng"},
            files={
                "file": (
                    "document.docx",
                    b"PK\x03\x04dummy",
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
            },
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert response.content == b"%PDF-1.4 pdfa"
        assert "content-disposition" in response.headers
        assert "document.pdf" in response.headers["content-disposition"]

    def test_convert_pptx_endpoint(self, monkeypatch, client: TestClient) -> None:
        """The endpoint should convert PPTX files."""

        def fake_convert_office(input_file, output_file) -> None:
            output_file.write_bytes(b"%PDF-1.4 converted")

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
            output_pdf.write_bytes(b"%PDF-1.4 pdfa")

        monkeypatch.setattr(api, "convert_office_to_pdf", fake_convert_office)
        monkeypatch.setattr(api, "convert_to_pdfa", fake_convert)

        response = client.post(
            "/convert",
            data={},
            files={
                "file": (
                    "presentation.pptx",
                    b"PK\x03\x04dummy",
                    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
                )
            },
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert "presentation.pdf" in response.headers["content-disposition"]

    def test_convert_xlsx_endpoint(self, monkeypatch, client: TestClient) -> None:
        """The endpoint should convert XLSX files."""

        def fake_convert_office(input_file, output_file) -> None:
            output_file.write_bytes(b"%PDF-1.4 converted")

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
            output_pdf.write_bytes(b"%PDF-1.4 pdfa")

        monkeypatch.setattr(api, "convert_office_to_pdf", fake_convert_office)
        monkeypatch.setattr(api, "convert_to_pdfa", fake_convert)

        response = client.post(
            "/convert",
            data={},
            files={
                "file": (
                    "spreadsheet.xlsx",
                    b"PK\x03\x04dummy",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            },
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert "spreadsheet.pdf" in response.headers["content-disposition"]

    def test_rejects_unsupported_format(self, client: TestClient) -> None:
        """The endpoint should reject unsupported file formats."""
        response = client.post(
            "/convert",
            files={"file": ("document.doc", b"dummy content", "application/msword")},
        )

        assert response.status_code == 400
        assert "Supported formats" in response.json()["detail"]

    def test_office_conversion_failure(self, monkeypatch, client: TestClient) -> None:
        """The endpoint should return HTTP 500 on Office conversion failure."""

        def raise_error(*_: Any, **__: Any) -> None:
            raise OfficeConversionError("LibreOffice failed")

        monkeypatch.setattr(api, "convert_office_to_pdf", raise_error)

        response = client.post(
            "/convert",
            files={
                "file": (
                    "document.docx",
                    b"PK\x03\x04dummy",
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
            },
        )

        assert response.status_code == 500
        assert "LibreOffice failed" in response.json()["detail"]

    # ========================================================================
    # PDF Pass-Through Tests (TDD - Phase 1: RED)
    # ========================================================================

    def test_api_office_pdf_passthrough(self, monkeypatch, client: TestClient) -> None:
        """API with pdfa_level='pdf' should skip OCRmyPDF for Office docs."""

        def fake_convert_office(input_file, output_file) -> None:
            output_file.write_bytes(b"%PDF-1.4 converted")

        ocr_called = {"called": False}

        def fake_convert(
            input_pdf,
            output_pdf,
            *,
            language,
            pdfa_level,
            ocr_enabled,
            skip_ocr_on_tagged_pdfs=True,
            is_office_source=False,
            compression_config=None,
        ) -> None:
            ocr_called["called"] = True
            output_pdf.write_bytes(input_pdf.read_bytes())

        monkeypatch.setattr(api, "convert_office_to_pdf", fake_convert_office)
        monkeypatch.setattr(api, "convert_to_pdfa", fake_convert)

        response = client.post(
            "/convert",
            data={"pdfa_level": "pdf", "language": "eng"},
            files={
                "file": (
                    "document.docx",
                    b"PK\x03\x04dummy",
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
            },
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"

    def test_api_office_pdfa2_still_converts(
        self, monkeypatch, client: TestClient
    ) -> None:
        """API with pdfa_level='2' should still use OCRmyPDF for Office docs."""

        def fake_convert_office(input_file, output_file) -> None:
            output_file.write_bytes(b"%PDF-1.4 converted")

        ocr_called = {"called": False}

        def fake_convert(
            input_pdf,
            output_pdf,
            *,
            language,
            pdfa_level,
            ocr_enabled,
            skip_ocr_on_tagged_pdfs=True,
            is_office_source=False,
            compression_config=None,
        ) -> None:
            ocr_called["called"] = True
            output_pdf.write_bytes(b"%PDF-1.4 pdfa-2")

        monkeypatch.setattr(api, "convert_office_to_pdf", fake_convert_office)
        monkeypatch.setattr(api, "convert_to_pdfa", fake_convert)

        response = client.post(
            "/convert",
            data={"pdfa_level": "2"},
            files={
                "file": (
                    "document.docx",
                    b"PK\x03\x04dummy",
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
            },
        )

        assert response.status_code == 200
        assert ocr_called["called"], "OCRmyPDF should be called"
