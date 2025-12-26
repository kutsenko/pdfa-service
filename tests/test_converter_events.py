"""Tests for converter event logging integration.

Following TDD principles, these tests verify that the converter properly logs
events at key decision points during PDF conversion.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, Mock

import pytest

from pdfa import converter


class TestNeedsOcrRefactored:
    """Test cases for refactored needs_ocr() function."""

    def test_needs_ocr_returns_stats_dict_with_text(self, monkeypatch, tmp_path):
        """needs_ocr should return dict with stats when text is detected."""
        # Mock pikepdf to simulate PDF with text
        mock_pdf = MagicMock()
        mock_pdf.pages = [MagicMock() for _ in range(3)]

        # Simulate pages with sufficient text
        for i, page in enumerate(mock_pdf.pages):
            page.__contains__ = Mock(return_value=True)
            # Create content with text (simulate PDF text operators)
            text_content = "(This is a test page with sufficient text content)" * 5
            page.Contents.read_bytes = Mock(return_value=text_content.encode("latin-1"))

        mock_open = MagicMock()
        mock_open.__enter__ = Mock(return_value=mock_pdf)
        mock_open.__exit__ = Mock(return_value=False)

        mock_pikepdf = Mock()
        mock_pikepdf.open = Mock(return_value=mock_open)

        monkeypatch.setattr(converter, "pikepdf", mock_pikepdf)

        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF-1.4 test")

        result = converter.needs_ocr(pdf_path)

        # Should return dict with stats
        assert isinstance(result, dict)
        assert "needs_ocr" in result
        assert "reason" in result
        assert "pages_with_text" in result
        assert "total_pages_checked" in result
        assert "text_ratio" in result
        assert "total_characters" in result

        # Should detect text and skip OCR
        assert result["needs_ocr"] is False
        assert result["pages_with_text"] >= 2
        assert result["text_ratio"] >= 0.66

    def test_needs_ocr_returns_stats_dict_no_text(self, monkeypatch, tmp_path):
        """needs_ocr should return dict with stats when no text detected."""
        # Mock pikepdf to simulate PDF without text
        mock_pdf = MagicMock()
        mock_pdf.pages = [MagicMock() for _ in range(3)]

        # Simulate pages with minimal/no text
        for page in mock_pdf.pages:
            page.__contains__ = Mock(return_value=True)
            # Very little text content
            page.Contents.read_bytes = Mock(return_value=b"(X)")

        mock_open = MagicMock()
        mock_open.__enter__ = Mock(return_value=mock_pdf)
        mock_open.__exit__ = Mock(return_value=False)

        mock_pikepdf = Mock()
        mock_pikepdf.open = Mock(return_value=mock_open)

        monkeypatch.setattr(converter, "pikepdf", mock_pikepdf)

        pdf_path = tmp_path / "scan.pdf"
        pdf_path.write_bytes(b"%PDF-1.4 test")

        result = converter.needs_ocr(pdf_path)

        # Should return dict indicating OCR is needed
        assert isinstance(result, dict)
        assert result["needs_ocr"] is True
        assert result["pages_with_text"] == 0
        assert result["text_ratio"] == 0.0
        assert result["total_characters"] < 50


class TestConvertToPdfaEventLogging:
    """Test cases for event logging in convert_to_pdfa()."""

    def test_convert_accepts_event_callback_parameter(self, monkeypatch, tmp_path):
        """convert_to_pdfa should accept event_callback parameter."""
        # Mock OCRmyPDF
        mock_ocr = Mock()
        monkeypatch.setattr(converter.ocrmypdf, "ocr", mock_ocr)

        # Mock pikepdf
        mock_pdf = MagicMock()
        mock_pdf.pages = []
        mock_pdf.Root = {}

        mock_open = MagicMock()
        mock_open.__enter__ = Mock(return_value=mock_pdf)
        mock_open.__exit__ = Mock(return_value=False)

        mock_pikepdf = Mock()
        mock_pikepdf.open = Mock(return_value=mock_open)
        monkeypatch.setattr(converter, "pikepdf", mock_pikepdf)

        input_pdf = tmp_path / "input.pdf"
        input_pdf.write_bytes(b"%PDF-1.4 test")
        output_pdf = tmp_path / "output.pdf"

        event_callback = AsyncMock()

        # Should not raise error
        converter.convert_to_pdfa(
            input_pdf,
            output_pdf,
            language="eng",
            pdfa_level="2",
            event_callback=event_callback,
        )

    @pytest.mark.asyncio
    async def test_passthrough_mode_logs_event(self, monkeypatch, tmp_path):
        """Pass-through mode should log passthrough_mode event."""
        # Mock pikepdf for tagged PDF
        mock_pdf = MagicMock()
        mock_pdf.Root = {"/StructTreeRoot": Mock()}

        mock_open = MagicMock()
        mock_open.__enter__ = Mock(return_value=mock_pdf)
        mock_open.__exit__ = Mock(return_value=False)

        mock_pikepdf = Mock()
        mock_pikepdf.open = Mock(return_value=mock_open)
        monkeypatch.setattr(converter, "pikepdf", mock_pikepdf)

        input_pdf = tmp_path / "input.pdf"
        input_pdf.write_bytes(b"%PDF-1.4 test")
        output_pdf = tmp_path / "output.pdf"

        event_callback = AsyncMock()

        converter.convert_to_pdfa(
            input_pdf,
            output_pdf,
            language="eng",
            pdfa_level="pdf",
            ocr_enabled=False,
            event_callback=event_callback,
        )

        # Should have logged passthrough_mode event
        assert event_callback.call_count >= 1
        # Find the passthrough_mode event call
        passthrough_calls = [
            c for c in event_callback.call_args_list if c[0][0] == "passthrough_mode"
        ]
        assert len(passthrough_calls) == 1

    @pytest.mark.asyncio
    async def test_tagged_pdf_logs_ocr_decision_event(self, monkeypatch, tmp_path):
        """Tagged PDF detection should log ocr_decision event."""
        # Mock pikepdf for tagged PDF
        mock_pdf = MagicMock()
        mock_pdf.Root = {"/StructTreeRoot": Mock()}
        mock_pdf.pages = []

        mock_open = MagicMock()
        mock_open.__enter__ = Mock(return_value=mock_pdf)
        mock_open.__exit__ = Mock(return_value=False)

        mock_pikepdf = Mock()
        mock_pikepdf.open = Mock(return_value=mock_open)
        monkeypatch.setattr(converter, "pikepdf", mock_pikepdf)

        # Mock OCRmyPDF
        mock_ocr = Mock()
        monkeypatch.setattr(converter.ocrmypdf, "ocr", mock_ocr)

        input_pdf = tmp_path / "tagged.pdf"
        input_pdf.write_bytes(b"%PDF-1.4 test")
        output_pdf = tmp_path / "output.pdf"

        event_callback = AsyncMock()

        converter.convert_to_pdfa(
            input_pdf,
            output_pdf,
            language="eng",
            pdfa_level="2",
            skip_ocr_on_tagged_pdfs=True,
            event_callback=event_callback,
        )

        # Should have logged ocr_decision event with reason=tagged_pdf
        ocr_decision_calls = [
            c for c in event_callback.call_args_list if c[0][0] == "ocr_decision"
        ]
        assert len(ocr_decision_calls) == 1
        assert ocr_decision_calls[0][1]["reason"] == "tagged_pdf"

    @pytest.mark.asyncio
    async def test_text_detection_logs_ocr_decision_event(self, monkeypatch, tmp_path):
        """Text detection should log ocr_decision event with stats."""
        # Mock pikepdf for untagged PDF with text
        mock_pdf = MagicMock()
        mock_pdf.Root = {}  # No tags
        mock_pdf.pages = [MagicMock() for _ in range(3)]

        # Simulate pages with text
        for page in mock_pdf.pages:
            page.__contains__ = Mock(return_value=True)
            text_content = "(This is a test page with text)" * 10
            page.Contents.read_bytes = Mock(return_value=text_content.encode("latin-1"))

        mock_open = MagicMock()
        mock_open.__enter__ = Mock(return_value=mock_pdf)
        mock_open.__exit__ = Mock(return_value=False)

        mock_pikepdf = Mock()
        mock_pikepdf.open = Mock(return_value=mock_open)
        monkeypatch.setattr(converter, "pikepdf", mock_pikepdf)

        # Mock OCRmyPDF
        mock_ocr = Mock()
        monkeypatch.setattr(converter.ocrmypdf, "ocr", mock_ocr)

        input_pdf = tmp_path / "text.pdf"
        input_pdf.write_bytes(b"%PDF-1.4 test")
        output_pdf = tmp_path / "output.pdf"

        event_callback = AsyncMock()

        converter.convert_to_pdfa(
            input_pdf,
            output_pdf,
            language="eng",
            pdfa_level="2",
            skip_ocr_on_tagged_pdfs=True,
            event_callback=event_callback,
        )

        # Should have logged ocr_decision event with stats
        ocr_decision_calls = [
            c for c in event_callback.call_args_list if c[0][0] == "ocr_decision"
        ]
        assert len(ocr_decision_calls) == 1
        event_kwargs = ocr_decision_calls[0][1]
        assert event_kwargs["reason"] == "has_text"
        assert "pages_with_text" in event_kwargs
        assert "text_ratio" in event_kwargs

    @pytest.mark.asyncio
    async def test_compression_auto_switch_logs_event(self, monkeypatch, tmp_path):
        """Compression auto-switch for tagged PDF should log event."""
        # Mock pikepdf for tagged PDF
        mock_pdf = MagicMock()
        mock_pdf.Root = {"/StructTreeRoot": Mock()}
        mock_pdf.pages = []

        mock_open = MagicMock()
        mock_open.__enter__ = Mock(return_value=mock_pdf)
        mock_open.__exit__ = Mock(return_value=False)

        mock_pikepdf = Mock()
        mock_pikepdf.open = Mock(return_value=mock_open)
        monkeypatch.setattr(converter, "pikepdf", mock_pikepdf)

        # Mock OCRmyPDF
        mock_ocr = Mock()
        monkeypatch.setattr(converter.ocrmypdf, "ocr", mock_ocr)

        # Import PRESETS to create compression config with remove_vectors=True
        from pdfa.compression_config import CompressionConfig

        input_pdf = tmp_path / "tagged.pdf"
        input_pdf.write_bytes(b"%PDF-1.4 test")
        output_pdf = tmp_path / "output.pdf"

        event_callback = AsyncMock()

        # Use compression config that would normally remove vectors
        compression_config = CompressionConfig(remove_vectors=True)

        converter.convert_to_pdfa(
            input_pdf,
            output_pdf,
            language="eng",
            pdfa_level="2",
            skip_ocr_on_tagged_pdfs=True,
            compression_config=compression_config,
            event_callback=event_callback,
        )

        # Should have logged compression_selected event
        compression_calls = [
            c
            for c in event_callback.call_args_list
            if c[0][0] == "compression_selected"
        ]
        assert len(compression_calls) == 1
        assert compression_calls[0][1]["reason"] == "auto_switched_for_tagged_pdf"

    @pytest.mark.asyncio
    async def test_fallback_tier_2_logs_event(self, monkeypatch, tmp_path):
        """Fallback to tier 2 should log fallback_applied event."""
        # Mock pikepdf
        mock_pdf = MagicMock()
        mock_pdf.Root = {}
        mock_pdf.pages = [MagicMock()]
        mock_pdf.pages[0].__contains__ = Mock(return_value=False)

        mock_open = MagicMock()
        mock_open.__enter__ = Mock(return_value=mock_pdf)
        mock_open.__exit__ = Mock(return_value=False)

        mock_pikepdf = Mock()
        mock_pikepdf.open = Mock(return_value=mock_open)
        monkeypatch.setattr(converter, "pikepdf", mock_pikepdf)

        # Mock OCRmyPDF to fail first, succeed second
        from ocrmypdf.exceptions import SubprocessOutputError

        call_count = {"count": 0}

        def mock_ocr(*args, **kwargs):
            call_count["count"] += 1
            if call_count["count"] == 1:
                # First call fails (tier 1)
                raise SubprocessOutputError("Ghostscript error")
            # Second call succeeds (tier 2)
            return None

        monkeypatch.setattr(converter.ocrmypdf, "ocr", mock_ocr)

        input_pdf = tmp_path / "problematic.pdf"
        input_pdf.write_bytes(b"%PDF-1.4 test")
        output_pdf = tmp_path / "output.pdf"

        event_callback = AsyncMock()

        converter.convert_to_pdfa(
            input_pdf,
            output_pdf,
            language="eng",
            pdfa_level="3",
            event_callback=event_callback,
        )

        # Should have logged fallback_applied event for tier 2
        fallback_calls = [
            c for c in event_callback.call_args_list if c[0][0] == "fallback_applied"
        ]
        assert len(fallback_calls) == 1
        assert fallback_calls[0][1]["tier"] == 2
        assert fallback_calls[0][1]["reason"] == "ghostscript_error"
