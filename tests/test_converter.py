"""Tests for PDF converter functionality including tagged PDF detection."""

from pathlib import Path
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


def test_needs_ocr_text_pdf(monkeypatch, tmp_path) -> None:
    """needs_ocr should return False for PDFs with searchable text."""
    # Mock pikepdf to simulate a PDF with text content
    mock_page = MagicMock()
    mock_page.__contains__ = Mock(return_value=True)  # Has /Contents

    # Create a mock Contents stream with PDF text operators
    # Simulate text content: (Sample text with more than 50 characters)Tj
    mock_contents = MagicMock()
    text_data = b"(Sample text with more than 50 characters for testing purposes)Tj"
    mock_contents.read_bytes = Mock(return_value=text_data)
    mock_page.Contents = mock_contents

    mock_pdf = MagicMock()
    mock_pdf.pages = [mock_page]
    mock_pdf.__len__ = Mock(return_value=1)

    mock_open = MagicMock()
    mock_open.__enter__ = Mock(return_value=mock_pdf)
    mock_open.__exit__ = Mock(return_value=False)

    mock_pikepdf = Mock()
    mock_pikepdf.open = Mock(return_value=mock_open)

    monkeypatch.setattr(converter, "pikepdf", mock_pikepdf)

    pdf_path = tmp_path / "text.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 test")

    result = converter.needs_ocr(pdf_path)

    assert result["needs_ocr"] is False
    assert "text detected" in result["reason"].lower()
    assert result["text_ratio"] >= 0.66


def test_needs_ocr_scanned_pdf(monkeypatch, tmp_path) -> None:
    """needs_ocr should return True for PDFs without searchable text."""
    # Mock pikepdf to simulate a scanned PDF (no text content)
    mock_page = MagicMock()
    mock_page.__contains__ = Mock(return_value=False)  # No /Contents

    mock_pdf = MagicMock()
    mock_pdf.pages = [mock_page, mock_page, mock_page]
    mock_pdf.__len__ = Mock(return_value=3)

    mock_open = MagicMock()
    mock_open.__enter__ = Mock(return_value=mock_pdf)
    mock_open.__exit__ = Mock(return_value=False)

    mock_pikepdf = Mock()
    mock_pikepdf.open = Mock(return_value=mock_open)

    monkeypatch.setattr(converter, "pikepdf", mock_pikepdf)

    pdf_path = tmp_path / "scanned.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 test")

    result = converter.needs_ocr(pdf_path)

    assert result["needs_ocr"] is True
    assert "needs ocr" in result["reason"].lower()
    assert result["pages_with_text"] == 0


def test_needs_ocr_mixed_content_mostly_scanned(monkeypatch, tmp_path) -> None:
    """needs_ocr should handle mixed content (33% text) correctly."""
    # Mock 3 pages: 1 with text, 2 without (33% text ratio < 66% threshold)
    page_with_text = MagicMock()
    page_with_text.__contains__ = Mock(return_value=True)
    mock_contents = MagicMock()
    text_data = b"(This page has more than 50 characters of text content)Tj"
    mock_contents.read_bytes = Mock(return_value=text_data)
    page_with_text.Contents = mock_contents

    page_without_text = MagicMock()
    page_without_text.__contains__ = Mock(return_value=False)

    mock_pdf = MagicMock()
    mock_pdf.pages = [page_with_text, page_without_text, page_without_text]
    mock_pdf.__len__ = Mock(return_value=3)

    mock_open = MagicMock()
    mock_open.__enter__ = Mock(return_value=mock_pdf)
    mock_open.__exit__ = Mock(return_value=False)

    mock_pikepdf = Mock()
    mock_pikepdf.open = Mock(return_value=mock_open)

    monkeypatch.setattr(converter, "pikepdf", mock_pikepdf)

    pdf_path = tmp_path / "mixed.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 test")

    result = converter.needs_ocr(pdf_path)

    # Should need OCR because only 33% of pages have text
    assert result["needs_ocr"] is True
    assert result["text_ratio"] < 0.66


def test_needs_ocr_mixed_content_mostly_text(monkeypatch, tmp_path) -> None:
    """needs_ocr should skip OCR when >= 66% pages have text."""
    # Mock 3 pages: 2 with text, 1 without (66% text ratio >= 66% threshold)
    page_with_text = MagicMock()
    page_with_text.__contains__ = Mock(return_value=True)
    mock_contents = MagicMock()
    text_data = b"(This page has more than 50 characters of text content)Tj"
    mock_contents.read_bytes = Mock(return_value=text_data)
    page_with_text.Contents = mock_contents

    page_without_text = MagicMock()
    page_without_text.__contains__ = Mock(return_value=False)

    mock_pdf = MagicMock()
    mock_pdf.pages = [page_with_text, page_with_text, page_without_text]
    mock_pdf.__len__ = Mock(return_value=3)

    mock_open = MagicMock()
    mock_open.__enter__ = Mock(return_value=mock_pdf)
    mock_open.__exit__ = Mock(return_value=False)

    mock_pikepdf = Mock()
    mock_pikepdf.open = Mock(return_value=mock_open)

    monkeypatch.setattr(converter, "pikepdf", mock_pikepdf)

    pdf_path = tmp_path / "mostly_text.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 test")

    result = converter.needs_ocr(pdf_path)

    # Should skip OCR because 66% of pages have text
    assert result["needs_ocr"] is False
    assert result["text_ratio"] >= 0.66


def test_needs_ocr_single_page_text(monkeypatch, tmp_path) -> None:
    """needs_ocr should return False for single-page PDF with text."""
    # Mock single page with sufficient text (>= 50 chars)
    mock_page = MagicMock()
    mock_page.__contains__ = Mock(return_value=True)
    mock_contents = MagicMock()
    text_data = b"(This is a single page with more than 50 characters)Tj"
    mock_contents.read_bytes = Mock(return_value=text_data)
    mock_page.Contents = mock_contents

    mock_pdf = MagicMock()
    mock_pdf.pages = [mock_page]
    mock_pdf.__len__ = Mock(return_value=1)

    mock_open = MagicMock()
    mock_open.__enter__ = Mock(return_value=mock_pdf)
    mock_open.__exit__ = Mock(return_value=False)

    mock_pikepdf = Mock()
    mock_pikepdf.open = Mock(return_value=mock_open)

    monkeypatch.setattr(converter, "pikepdf", mock_pikepdf)

    pdf_path = tmp_path / "single_text.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 test")

    result = converter.needs_ocr(pdf_path)

    assert result["needs_ocr"] is False
    assert "text detected" in result["reason"].lower()
    assert result["total_pages_checked"] == 1


def test_needs_ocr_single_page_minimal_text(monkeypatch, tmp_path) -> None:
    """needs_ocr should return True for single-page PDF with minimal text."""
    # Mock single page with insufficient text (< 50 chars)
    mock_page = MagicMock()
    mock_page.__contains__ = Mock(return_value=True)
    mock_contents = MagicMock()
    text_data = b"(Short)Tj"  # Only 5 chars
    mock_contents.read_bytes = Mock(return_value=text_data)
    mock_page.Contents = mock_contents

    mock_pdf = MagicMock()
    mock_pdf.pages = [mock_page]
    mock_pdf.__len__ = Mock(return_value=1)

    mock_open = MagicMock()
    mock_open.__enter__ = Mock(return_value=mock_pdf)
    mock_open.__exit__ = Mock(return_value=False)

    mock_pikepdf = Mock()
    mock_pikepdf.open = Mock(return_value=mock_open)

    monkeypatch.setattr(converter, "pikepdf", mock_pikepdf)

    pdf_path = tmp_path / "single_minimal.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 test")

    result = converter.needs_ocr(pdf_path)

    assert result["needs_ocr"] is True
    assert "needs ocr" in result["reason"].lower()
    assert result["total_pages_checked"] == 1


def test_needs_ocr_error_handling(monkeypatch, tmp_path) -> None:
    """needs_ocr should return True (safe default) on errors."""
    mock_pikepdf = Mock()
    mock_pikepdf.open = Mock(side_effect=Exception("Read error"))

    monkeypatch.setattr(converter, "pikepdf", mock_pikepdf)

    pdf_path = tmp_path / "error.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 test")

    result = converter.needs_ocr(pdf_path)

    # Should default to OCR on error
    assert result["needs_ocr"] is True
    assert "failed" in result["reason"].lower() or "error" in result["reason"].lower()


def test_needs_ocr_empty_pdf(monkeypatch, tmp_path) -> None:
    """needs_ocr should return True for PDFs with no pages."""
    # Mock PDF with 0 pages
    mock_pdf = MagicMock()
    mock_pdf.pages = []
    mock_pdf.__len__ = Mock(return_value=0)

    mock_open = MagicMock()
    mock_open.__enter__ = Mock(return_value=mock_pdf)
    mock_open.__exit__ = Mock(return_value=False)

    mock_pikepdf = Mock()
    mock_pikepdf.open = Mock(return_value=mock_open)

    monkeypatch.setattr(converter, "pikepdf", mock_pikepdf)

    pdf_path = tmp_path / "empty.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 test")

    result = converter.needs_ocr(pdf_path)

    assert result["needs_ocr"] is True
    assert result["total_pages_checked"] == 0
    assert "no pages" in result["reason"].lower()


def test_convert_to_pdfa_auto_skip_ocr_text_pdf(monkeypatch, tmp_path) -> None:
    """convert_to_pdfa should automatically skip OCR for text PDFs."""
    calls: dict[str, Any] = {}

    def fake_ocr(input_file: str, output_file: str, **kwargs: Any) -> None:
        calls["kwargs"] = kwargs

    # Mock has_pdf_tags to return False (not a tagged PDF)
    monkeypatch.setattr(converter, "has_pdf_tags", Mock(return_value=False))

    # Mock needs_ocr to return False (text detected)
    monkeypatch.setattr(
        converter,
        "needs_ocr",
        Mock(
            return_value={
                "needs_ocr": False,
                "reason": "Text detected",
                "pages_with_text": 3,
                "total_pages_checked": 3,
                "text_ratio": 1.0,
                "total_characters": 500,
            }
        ),
    )

    monkeypatch.setattr(converter.ocrmypdf, "ocr", fake_ocr)

    input_pdf = tmp_path / "text.pdf"
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

    # OCR should be disabled (force_ocr=False)
    assert calls["kwargs"]["force_ocr"] is False
    assert calls["kwargs"]["skip_text"] is True


def test_convert_to_pdfa_auto_run_ocr_scanned_pdf(monkeypatch, tmp_path) -> None:
    """convert_to_pdfa should automatically run OCR for scanned PDFs."""
    calls: dict[str, Any] = {}

    def fake_ocr(input_file: str, output_file: str, **kwargs: Any) -> None:
        calls["kwargs"] = kwargs

    # Mock has_pdf_tags to return False (not a tagged PDF)
    monkeypatch.setattr(converter, "has_pdf_tags", Mock(return_value=False))

    # Mock needs_ocr to return True (needs OCR)
    monkeypatch.setattr(
        converter,
        "needs_ocr",
        Mock(
            return_value={
                "needs_ocr": True,
                "reason": "No text detected",
                "pages_with_text": 0,
                "total_pages_checked": 3,
                "text_ratio": 0.0,
                "total_characters": 0,
            }
        ),
    )

    monkeypatch.setattr(converter.ocrmypdf, "ocr", fake_ocr)

    input_pdf = tmp_path / "scanned.pdf"
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

    # OCR should be enabled (force_ocr=True)
    assert calls["kwargs"]["force_ocr"] is True
    assert calls["kwargs"]["skip_text"] is False


def test_convert_to_pdfa_tagged_pdf_takes_priority(monkeypatch, tmp_path) -> None:
    """Tagged PDF detection should take priority over text detection."""
    calls: dict[str, Any] = {}

    def fake_ocr(input_file: str, output_file: str, **kwargs: Any) -> None:
        calls["kwargs"] = kwargs

    # Mock has_pdf_tags to return True (tagged PDF)
    monkeypatch.setattr(converter, "has_pdf_tags", Mock(return_value=True))

    # Mock needs_ocr - should NOT be called for tagged PDFs
    needs_ocr_mock = Mock(
        return_value={
            "needs_ocr": False,
            "reason": "Text detected",
            "pages_with_text": 3,
            "total_pages_checked": 3,
            "text_ratio": 1.0,
            "total_characters": 500,
        }
    )
    monkeypatch.setattr(converter, "needs_ocr", needs_ocr_mock)

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

    # needs_ocr should NOT have been called (tagged PDFs take priority)
    needs_ocr_mock.assert_not_called()

    # OCR should be disabled
    assert calls["kwargs"]["force_ocr"] is False
    assert calls["kwargs"]["skip_text"] is True


# ============================================================================
# PDF Pass-Through Tests (TDD - Phase 1: RED)
# ============================================================================


def test_convert_to_pdfa_pdf_passthrough_office_with_tags(
    monkeypatch, tmp_path
) -> None:
    """PDF pass-through mode: Office document with tags skips OCRmyPDF."""
    # Mock has_pdf_tags to return True
    monkeypatch.setattr(converter, "has_pdf_tags", Mock(return_value=True))

    # OCRmyPDF should NOT be called
    ocr_called = {"called": False}

    def fake_ocr(input_file: str, output_file: str, **kwargs: Any) -> None:
        ocr_called["called"] = True

    monkeypatch.setattr(converter.ocrmypdf, "ocr", fake_ocr)

    input_pdf = tmp_path / "input.pdf"
    input_pdf.write_bytes(b"%PDF-1.4 test with tags")
    output_pdf = tmp_path / "output.pdf"

    converter.convert_to_pdfa(
        input_pdf,
        output_pdf,
        language="eng",
        pdfa_level="pdf",
        ocr_enabled=False,  # Disable OCR for pass-through
        is_office_source=True,
    )

    assert output_pdf.exists()
    assert output_pdf.read_bytes() == b"%PDF-1.4 test with tags"
    assert not ocr_called[
        "called"
    ], "OCRmyPDF should not be called in pass-through mode"


def test_convert_to_pdfa_pdf_passthrough_office_without_tags(
    monkeypatch, tmp_path
) -> None:
    """PDF pass-through mode: Office document without tags still skips OCRmyPDF."""
    # Mock has_pdf_tags to return False
    monkeypatch.setattr(converter, "has_pdf_tags", Mock(return_value=False))

    # OCRmyPDF should NOT be called
    ocr_called = {"called": False}

    def fake_ocr(input_file: str, output_file: str, **kwargs: Any) -> None:
        ocr_called["called"] = True

    monkeypatch.setattr(converter.ocrmypdf, "ocr", fake_ocr)

    input_pdf = tmp_path / "input.pdf"
    input_pdf.write_bytes(b"%PDF-1.4 test no tags")
    output_pdf = tmp_path / "output.pdf"

    converter.convert_to_pdfa(
        input_pdf,
        output_pdf,
        language="eng",
        pdfa_level="pdf",
        ocr_enabled=False,  # Disable OCR for pass-through
        is_office_source=True,
    )

    assert output_pdf.exists()
    assert output_pdf.read_bytes() == b"%PDF-1.4 test no tags"
    assert not ocr_called["called"]


def test_convert_to_pdfa_pdf_level_without_office_source(monkeypatch, tmp_path) -> None:
    """pdfa_level='pdf' for regular PDF now works (universal PDF output)."""
    # Mock has_pdf_tags
    monkeypatch.setattr(converter, "has_pdf_tags", Mock(return_value=False))

    # Mock needs_ocr
    monkeypatch.setattr(
        converter,
        "needs_ocr",
        Mock(
            return_value={
                "needs_ocr": True,
                "reason": "No text, needs OCR",
                "pages_with_text": 0,
                "total_pages_checked": 1,
                "text_ratio": 0.0,
                "total_characters": 0,
            }
        ),
    )

    calls: dict[str, Any] = {}

    def fake_ocr(input_file: str, output_file: str, **kwargs: Any) -> None:
        calls["input"] = input_file
        calls["kwargs"] = kwargs
        Path(output_file).write_bytes(b"%PDF-1.4 with ocr")

    monkeypatch.setattr(converter.ocrmypdf, "ocr", fake_ocr)

    input_pdf = tmp_path / "input.pdf"
    input_pdf.write_bytes(b"%PDF-1.4 regular")
    output_pdf = tmp_path / "output.pdf"

    # Should now work for non-Office documents with pdfa_level='pdf'
    converter.convert_to_pdfa(
        input_pdf,
        output_pdf,
        language="eng",
        pdfa_level="pdf",
        is_office_source=False,  # Not from Office - but now allowed!
    )

    # Verify OCR was called with output_type='pdf'
    assert "kwargs" in calls
    assert calls["kwargs"]["output_type"] == "pdf"
    assert output_pdf.exists()


def test_convert_to_pdfa_pdfa2_office_source(monkeypatch, tmp_path) -> None:
    """pdfa_level='2' for Office document should still use OCRmyPDF."""
    calls: dict[str, Any] = {}

    def fake_ocr(input_file: str, output_file: str, **kwargs: Any) -> None:
        calls["kwargs"] = kwargs

    monkeypatch.setattr(converter.ocrmypdf, "ocr", fake_ocr)
    # Mock has_pdf_tags to avoid tag detection logic
    monkeypatch.setattr(converter, "has_pdf_tags", Mock(return_value=False))
    # Mock needs_ocr to avoid text detection logic
    monkeypatch.setattr(
        converter,
        "needs_ocr",
        Mock(
            return_value={
                "needs_ocr": True,
                "reason": "Needs OCR",
                "pages_with_text": 0,
                "total_pages_checked": 3,
                "text_ratio": 0.0,
                "total_characters": 0,
            }
        ),
    )

    input_pdf = tmp_path / "input.pdf"
    input_pdf.write_bytes(b"%PDF-1.4 office")
    output_pdf = tmp_path / "output.pdf"

    converter.convert_to_pdfa(
        input_pdf,
        output_pdf,
        language="eng",
        pdfa_level="2",
        is_office_source=True,
    )

    assert "kwargs" in calls
    assert calls["kwargs"]["output_type"] == "pdfa-2"


def test_convert_to_pdfa_invalid_pdfa_level(tmp_path) -> None:
    """Invalid pdfa_level should raise ValueError."""
    input_pdf = tmp_path / "input.pdf"
    input_pdf.write_bytes(b"%PDF-1.4 test")
    output_pdf = tmp_path / "output.pdf"

    try:
        converter.convert_to_pdfa(
            input_pdf,
            output_pdf,
            language="eng",
            pdfa_level="invalid",
            is_office_source=False,
        )
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "Invalid pdfa_level" in str(e)


# ============================================================================
# Universal PDF Output Tests (TDD - Phase 1: RED)
# ============================================================================


def test_convert_universal_pdf_output_no_ocr(monkeypatch, tmp_path) -> None:
    """Universal PDF output: pdfa_level='pdf' + ocr_enabled=False copies file."""
    # Mock has_pdf_tags
    monkeypatch.setattr(converter, "has_pdf_tags", Mock(return_value=False))

    # OCRmyPDF should NOT be called
    ocr_called = {"called": False}

    def fake_ocr(input_file: str, output_file: str, **kwargs: Any) -> None:
        ocr_called["called"] = True

    monkeypatch.setattr(converter.ocrmypdf, "ocr", fake_ocr)

    input_pdf = tmp_path / "input.pdf"
    input_pdf.write_bytes(b"%PDF-1.4 universal test")
    output_pdf = tmp_path / "output.pdf"

    # Should work for ANY PDF (not just Office)
    converter.convert_to_pdfa(
        input_pdf,
        output_pdf,
        language="eng",
        pdfa_level="pdf",
        ocr_enabled=False,  # Explicitly disable OCR
    )

    assert output_pdf.exists()
    assert output_pdf.read_bytes() == b"%PDF-1.4 universal test"
    assert not ocr_called[
        "called"
    ], "OCRmyPDF should not be called when ocr_enabled=False"


def test_convert_universal_pdf_output_with_tags_auto_skip(
    monkeypatch, tmp_path
) -> None:
    """Universal PDF output: pdfa_level='pdf' with tags should auto-skip OCR."""
    # Mock has_pdf_tags to return True
    monkeypatch.setattr(converter, "has_pdf_tags", Mock(return_value=True))

    # Track OCR calls
    ocr_calls: list[dict[str, Any]] = []

    def fake_ocr(input_file: str, output_file: str, **kwargs: Any) -> None:
        ocr_calls.append({"input": input_file, "output": output_file, "kwargs": kwargs})
        Path(output_file).write_bytes(b"%PDF-1.4 with ocr")

    monkeypatch.setattr(converter.ocrmypdf, "ocr", fake_ocr)

    input_pdf = tmp_path / "input.pdf"
    input_pdf.write_bytes(b"%PDF-1.4 has tags")
    output_pdf = tmp_path / "output.pdf"

    converter.convert_to_pdfa(
        input_pdf,
        output_pdf,
        language="eng",
        pdfa_level="pdf",
        ocr_enabled=True,  # OCR enabled but should be skipped
        skip_ocr_on_tagged_pdfs=True,  # Auto-skip on tags
    )

    assert output_pdf.exists()
    # Should call OCR with force_ocr=False and skip_text=True
    assert len(ocr_calls) == 1
    assert ocr_calls[0]["kwargs"]["output_type"] == "pdf"
    assert ocr_calls[0]["kwargs"]["force_ocr"] is False
    assert ocr_calls[0]["kwargs"]["skip_text"] is True


def test_convert_universal_pdf_output_with_text_auto_skip(
    monkeypatch, tmp_path
) -> None:
    """Universal PDF output: pdfa_level='pdf' with text should auto-skip OCR."""
    # Mock has_pdf_tags to return False (no tags)
    monkeypatch.setattr(converter, "has_pdf_tags", Mock(return_value=False))

    # Mock needs_ocr to return False (has text)
    monkeypatch.setattr(
        converter,
        "needs_ocr",
        Mock(
            return_value={
                "needs_ocr": False,
                "reason": "Has sufficient text content",
                "pages_with_text": 3,
                "total_pages_checked": 3,
                "text_ratio": 1.0,
                "total_characters": 500,
            }
        ),
    )

    # Track OCR calls
    ocr_calls: list[dict[str, Any]] = []

    def fake_ocr(input_file: str, output_file: str, **kwargs: Any) -> None:
        ocr_calls.append({"kwargs": kwargs})
        Path(output_file).write_bytes(b"%PDF-1.4 with text")

    monkeypatch.setattr(converter.ocrmypdf, "ocr", fake_ocr)

    input_pdf = tmp_path / "input.pdf"
    input_pdf.write_bytes(b"%PDF-1.4 has text content")
    output_pdf = tmp_path / "output.pdf"

    converter.convert_to_pdfa(
        input_pdf,
        output_pdf,
        language="eng",
        pdfa_level="pdf",
        ocr_enabled=True,
        skip_ocr_on_tagged_pdfs=True,
    )

    assert output_pdf.exists()
    # Should call OCR with force_ocr=False and skip_text=True
    assert len(ocr_calls) == 1
    assert ocr_calls[0]["kwargs"]["output_type"] == "pdf"
    assert ocr_calls[0]["kwargs"]["force_ocr"] is False


def test_convert_universal_pdf_output_needs_ocr(monkeypatch, tmp_path) -> None:
    """Universal PDF output: pdfa_level='pdf' without text should run OCR."""
    # Mock has_pdf_tags to return False
    monkeypatch.setattr(converter, "has_pdf_tags", Mock(return_value=False))

    # Mock needs_ocr to return True (no text, needs OCR)
    monkeypatch.setattr(
        converter,
        "needs_ocr",
        Mock(
            return_value={
                "needs_ocr": True,
                "reason": "No text detected, needs OCR",
                "pages_with_text": 0,
                "total_pages_checked": 3,
                "text_ratio": 0.0,
                "total_characters": 8,
            }
        ),
    )

    # Track OCR calls
    ocr_calls: list[dict[str, Any]] = []

    def fake_ocr(input_file: str, output_file: str, **kwargs: Any) -> None:
        ocr_calls.append({"kwargs": kwargs})
        Path(output_file).write_bytes(b"%PDF-1.4 after ocr")

    monkeypatch.setattr(converter.ocrmypdf, "ocr", fake_ocr)

    input_pdf = tmp_path / "input.pdf"
    input_pdf.write_bytes(b"%PDF-1.4 no text")
    output_pdf = tmp_path / "output.pdf"

    converter.convert_to_pdfa(
        input_pdf,
        output_pdf,
        language="eng",
        pdfa_level="pdf",
        ocr_enabled=True,
        skip_ocr_on_tagged_pdfs=True,
    )

    assert output_pdf.exists()
    # Should call OCR with force_ocr=True
    assert len(ocr_calls) == 1
    assert ocr_calls[0]["kwargs"]["output_type"] == "pdf"
    assert ocr_calls[0]["kwargs"]["force_ocr"] is True


def test_convert_universal_pdf_output_force_ocr(monkeypatch, tmp_path) -> None:
    """Universal PDF output: Force OCR even when tags present."""
    # Mock has_pdf_tags to return True
    monkeypatch.setattr(converter, "has_pdf_tags", Mock(return_value=True))

    # Track OCR calls
    ocr_calls: list[dict[str, Any]] = []

    def fake_ocr(input_file: str, output_file: str, **kwargs: Any) -> None:
        ocr_calls.append({"kwargs": kwargs})
        Path(output_file).write_bytes(b"%PDF-1.4 forced ocr")

    monkeypatch.setattr(converter.ocrmypdf, "ocr", fake_ocr)

    input_pdf = tmp_path / "input.pdf"
    input_pdf.write_bytes(b"%PDF-1.4 with tags")
    output_pdf = tmp_path / "output.pdf"

    converter.convert_to_pdfa(
        input_pdf,
        output_pdf,
        language="eng",
        pdfa_level="pdf",
        ocr_enabled=True,
        skip_ocr_on_tagged_pdfs=False,  # Force OCR even with tags
    )

    assert output_pdf.exists()
    # Should call OCR with force_ocr=True (tags present but forced)
    assert len(ocr_calls) == 1
    assert ocr_calls[0]["kwargs"]["output_type"] == "pdf"
    assert ocr_calls[0]["kwargs"]["force_ocr"] is True


def test_convert_universal_pdf_output_backward_compat(monkeypatch, tmp_path) -> None:
    """Backward compatibility: is_office_source parameter should still work."""
    # Mock has_pdf_tags
    monkeypatch.setattr(converter, "has_pdf_tags", Mock(return_value=True))

    # OCRmyPDF should NOT be called
    ocr_called = {"called": False}

    def fake_ocr(input_file: str, output_file: str, **kwargs: Any) -> None:
        ocr_called["called"] = True

    monkeypatch.setattr(converter.ocrmypdf, "ocr", fake_ocr)

    input_pdf = tmp_path / "input.pdf"
    input_pdf.write_bytes(b"%PDF-1.4 office doc")
    output_pdf = tmp_path / "output.pdf"

    # Old code with is_office_source should still work
    converter.convert_to_pdfa(
        input_pdf,
        output_pdf,
        language="eng",
        pdfa_level="pdf",
        is_office_source=True,  # Old parameter - should be ignored but not break
        ocr_enabled=False,
    )

    assert output_pdf.exists()
    assert output_pdf.read_bytes() == b"%PDF-1.4 office doc"
    assert not ocr_called["called"]
