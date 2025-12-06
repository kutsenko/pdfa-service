"""Tests for PDF converter functionality including tagged PDF detection."""

from typing import Any
from unittest.mock import MagicMock, Mock

from pdfa import converter


def test_has_pdf_tags_with_tagged_pdf(monkeypatch, tmp_path) -> None:
    """has_pdf_tags should return True for PDFs with structure tags."""
    # Mock pikepdf to simulate a tagged PDF
    mock_pdf = MagicMock()
    mock_pdf.Root = {"/StructTreeRoot": Mock()}

    mock_open = MagicMock()
    mock_open.__enter__ = Mock(return_value=mock_pdf)
    mock_open.__exit__ = Mock(return_value=False)

    mock_pikepdf = Mock()
    mock_pikepdf.open = Mock(return_value=mock_open)

    monkeypatch.setattr(converter, "pikepdf", mock_pikepdf)

    pdf_path = tmp_path / "tagged.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 test")

    result = converter.has_pdf_tags(pdf_path)

    assert result is True


def test_has_pdf_tags_without_tags(monkeypatch, tmp_path) -> None:
    """has_pdf_tags should return False for PDFs without structure tags."""
    # Mock pikepdf to simulate an untagged PDF
    mock_pdf = MagicMock()
    mock_pdf.Root = {}  # No StructTreeRoot

    mock_open = MagicMock()
    mock_open.__enter__ = Mock(return_value=mock_pdf)
    mock_open.__exit__ = Mock(return_value=False)

    mock_pikepdf = Mock()
    mock_pikepdf.open = Mock(return_value=mock_open)

    monkeypatch.setattr(converter, "pikepdf", mock_pikepdf)

    pdf_path = tmp_path / "untagged.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 test")

    result = converter.has_pdf_tags(pdf_path)

    assert result is False


def test_has_pdf_tags_error_returns_false(monkeypatch, tmp_path) -> None:
    """has_pdf_tags should return False if an error occurs."""
    mock_pikepdf = Mock()
    mock_pikepdf.open = Mock(side_effect=Exception("Read error"))

    monkeypatch.setattr(converter, "pikepdf", mock_pikepdf)

    pdf_path = tmp_path / "error.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 test")

    result = converter.has_pdf_tags(pdf_path)

    assert result is False


def test_convert_to_pdfa_skip_ocr_on_tagged_pdf(monkeypatch, tmp_path) -> None:
    """Skip OCR for tagged PDFs when skip_ocr_on_tagged_pdfs=True."""
    calls: dict[str, Any] = {}

    def fake_ocr(input_file: str, output_file: str, **kwargs: Any) -> None:
        calls["input"] = input_file
        calls["output"] = output_file
        calls["kwargs"] = kwargs

    # Mock pikepdf to return True for has_pdf_tags
    mock_pdf = MagicMock()
    mock_pdf.Root = {"/StructTreeRoot": Mock()}

    mock_open = MagicMock()
    mock_open.__enter__ = Mock(return_value=mock_pdf)
    mock_open.__exit__ = Mock(return_value=False)

    mock_pikepdf = Mock()
    mock_pikepdf.open = Mock(return_value=mock_open)

    monkeypatch.setattr(converter, "pikepdf", mock_pikepdf)
    monkeypatch.setattr(converter.ocrmypdf, "ocr", fake_ocr)

    input_pdf = tmp_path / "tagged.pdf"
    input_pdf.write_bytes(b"%PDF-1.4 test")
    output_pdf = tmp_path / "output.pdf"

    converter.convert_to_pdfa(
        input_pdf,
        output_pdf,
        language="eng",
        pdfa_level="2",
        ocr_enabled=True,
        skip_ocr_on_tagged_pdfs=True,
    )

    # OCR should be disabled (force_ocr=False) because PDF has tags
    assert calls["kwargs"]["force_ocr"] is False


def test_convert_to_pdfa_force_ocr_on_tagged_pdf(monkeypatch, tmp_path) -> None:
    """Perform OCR on tagged PDFs when skip_ocr_on_tagged_pdfs=False."""
    calls: dict[str, Any] = {}

    def fake_ocr(input_file: str, output_file: str, **kwargs: Any) -> None:
        calls["input"] = input_file
        calls["output"] = output_file
        calls["kwargs"] = kwargs

    # Mock pikepdf to return True for has_pdf_tags
    mock_pdf = MagicMock()
    mock_pdf.Root = {"/StructTreeRoot": Mock()}

    mock_open = MagicMock()
    mock_open.__enter__ = Mock(return_value=mock_pdf)
    mock_open.__exit__ = Mock(return_value=False)

    mock_pikepdf = Mock()
    mock_pikepdf.open = Mock(return_value=mock_open)

    monkeypatch.setattr(converter, "pikepdf", mock_pikepdf)
    monkeypatch.setattr(converter.ocrmypdf, "ocr", fake_ocr)

    input_pdf = tmp_path / "tagged.pdf"
    input_pdf.write_bytes(b"%PDF-1.4 test")
    output_pdf = tmp_path / "output.pdf"

    converter.convert_to_pdfa(
        input_pdf,
        output_pdf,
        language="eng",
        pdfa_level="2",
        ocr_enabled=True,
        skip_ocr_on_tagged_pdfs=False,  # Force OCR even on tagged PDFs
    )

    # OCR should be enabled (force_ocr=True) because we're forcing it
    assert calls["kwargs"]["force_ocr"] is True


def test_convert_to_pdfa_ocr_on_untagged_pdf(monkeypatch, tmp_path) -> None:
    """Perform OCR on untagged PDFs regardless of skip setting."""
    calls: dict[str, Any] = {}

    def fake_ocr(input_file: str, output_file: str, **kwargs: Any) -> None:
        calls["input"] = input_file
        calls["output"] = output_file
        calls["kwargs"] = kwargs

    # Mock pikepdf to return False for has_pdf_tags
    mock_pdf = MagicMock()
    mock_pdf.Root = {}  # No StructTreeRoot

    mock_open = MagicMock()
    mock_open.__enter__ = Mock(return_value=mock_pdf)
    mock_open.__exit__ = Mock(return_value=False)

    mock_pikepdf = Mock()
    mock_pikepdf.open = Mock(return_value=mock_open)

    monkeypatch.setattr(converter, "pikepdf", mock_pikepdf)
    monkeypatch.setattr(converter.ocrmypdf, "ocr", fake_ocr)

    input_pdf = tmp_path / "untagged.pdf"
    input_pdf.write_bytes(b"%PDF-1.4 test")
    output_pdf = tmp_path / "output.pdf"

    converter.convert_to_pdfa(
        input_pdf,
        output_pdf,
        language="eng",
        pdfa_level="2",
        ocr_enabled=True,
        skip_ocr_on_tagged_pdfs=True,
    )

    # OCR should be enabled (force_ocr=True) because PDF has no tags
    assert calls["kwargs"]["force_ocr"] is True
