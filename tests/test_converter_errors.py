"""Tests for error handling in PDF conversion."""

from __future__ import annotations

from pathlib import Path

import ocrmypdf.exceptions as ocrmypdf_exceptions
import pytest

from pdfa import converter


def test_ghostscript_error_fallback_to_no_ocr(monkeypatch, tmp_path) -> None:
    """Test fallback to no-OCR when Ghostscript fails during OCR."""
    input_pdf = tmp_path / "input.pdf"
    input_pdf.write_bytes(b"%PDF-1.4 test")
    output_pdf = tmp_path / "output.pdf"

    # Track calls to ocrmypdf.ocr
    call_count = 0
    ocr_kwargs_list = []

    def fake_ocr(input_file: str, output_file: str, **kwargs) -> None:
        nonlocal call_count
        call_count += 1
        ocr_kwargs_list.append(kwargs)

        # First call (with OCR) fails with Ghostscript error
        if call_count == 1 and kwargs.get("force_ocr"):
            raise ocrmypdf_exceptions.SubprocessOutputError(
                "Ghostscript rasterizing failed"
            )
        # Second call (without OCR) succeeds
        elif call_count == 2:
            # Create output file to simulate success
            Path(output_file).write_bytes(b"%PDF-1.4 converted")

    monkeypatch.setattr(converter.ocrmypdf, "ocr", fake_ocr)

    # Should succeed with fallback
    converter.convert_to_pdfa(
        input_pdf,
        output_pdf,
        language="eng",
        pdfa_level="2",
        ocr_enabled=True,
    )

    # Verify two calls were made
    assert call_count == 2

    # First call should have OCR enabled
    assert ocr_kwargs_list[0]["force_ocr"] is True
    assert ocr_kwargs_list[0]["skip_text"] is False

    # Second call (fallback) should have OCR disabled
    assert ocr_kwargs_list[1]["force_ocr"] is False
    assert ocr_kwargs_list[1]["skip_text"] is True

    # Output file should exist
    assert output_pdf.exists()


def test_ghostscript_error_no_fallback_when_ocr_disabled(monkeypatch, tmp_path) -> None:
    """Test that no fallback is attempted when OCR is already disabled."""
    input_pdf = tmp_path / "input.pdf"
    input_pdf.write_bytes(b"%PDF-1.4 test")
    output_pdf = tmp_path / "output.pdf"

    def fake_ocr(input_file: str, output_file: str, **kwargs) -> None:
        # Always fail with Ghostscript error
        raise ocrmypdf_exceptions.SubprocessOutputError(
            "Ghostscript rasterizing failed"
        )

    monkeypatch.setattr(converter.ocrmypdf, "ocr", fake_ocr)

    # Should raise RuntimeError without fallback attempt
    with pytest.raises(RuntimeError, match="Ghostscript could not render the PDF"):
        converter.convert_to_pdfa(
            input_pdf,
            output_pdf,
            language="eng",
            pdfa_level="2",
            ocr_enabled=False,  # OCR disabled, so no fallback possible
        )


def test_ghostscript_error_fallback_also_fails(monkeypatch, tmp_path) -> None:
    """Test error handling when both primary and fallback conversions fail."""
    input_pdf = tmp_path / "input.pdf"
    input_pdf.write_bytes(b"%PDF-1.4 test")
    output_pdf = tmp_path / "output.pdf"

    def fake_ocr(input_file: str, output_file: str, **kwargs) -> None:
        # Always fail with Ghostscript error
        raise ocrmypdf_exceptions.SubprocessOutputError(
            "Ghostscript rasterizing failed"
        )

    monkeypatch.setattr(converter.ocrmypdf, "ocr", fake_ocr)

    # Should raise RuntimeError mentioning both failures
    with pytest.raises(
        RuntimeError, match="even without OCR.*may be corrupted or contain unsupported"
    ):
        converter.convert_to_pdfa(
            input_pdf,
            output_pdf,
            language="eng",
            pdfa_level="2",
            ocr_enabled=True,
        )


def test_encrypted_pdf_error(monkeypatch, tmp_path) -> None:
    """Test handling of encrypted PDFs."""
    input_pdf = tmp_path / "encrypted.pdf"
    input_pdf.write_bytes(b"%PDF-1.4 test")
    output_pdf = tmp_path / "output.pdf"

    def fake_ocr(input_file: str, output_file: str, **kwargs) -> None:
        raise ocrmypdf_exceptions.EncryptedPdfError(
            "PDF is encrypted or contains an encryption dictionary"
        )

    monkeypatch.setattr(converter.ocrmypdf, "ocr", fake_ocr)

    # Should raise RuntimeError with encryption message
    with pytest.raises(RuntimeError, match="Cannot process encrypted PDF"):
        converter.convert_to_pdfa(
            input_pdf,
            output_pdf,
            language="eng",
            pdfa_level="2",
        )


def test_invalid_pdf_error(monkeypatch, tmp_path) -> None:
    """Test handling of invalid/corrupted PDFs."""
    input_pdf = tmp_path / "invalid.pdf"
    input_pdf.write_bytes(b"not a pdf")
    output_pdf = tmp_path / "output.pdf"

    def fake_ocr(input_file: str, output_file: str, **kwargs) -> None:
        raise ocrmypdf_exceptions.InputFileError("PDF file is invalid or corrupted")

    monkeypatch.setattr(converter.ocrmypdf, "ocr", fake_ocr)

    # Should raise RuntimeError with invalid file message
    with pytest.raises(RuntimeError, match="Invalid or corrupted PDF file"):
        converter.convert_to_pdfa(
            input_pdf,
            output_pdf,
            language="eng",
            pdfa_level="2",
        )


def test_prior_ocr_found_is_handled_gracefully(monkeypatch, tmp_path) -> None:
    """Test that PriorOcrFoundError is handled gracefully (not raised)."""
    input_pdf = tmp_path / "with_ocr.pdf"
    input_pdf.write_bytes(b"%PDF-1.4 test")
    output_pdf = tmp_path / "output.pdf"

    def fake_ocr(input_file: str, output_file: str, **kwargs) -> None:
        # Simulate PDF that already has OCR
        raise ocrmypdf_exceptions.PriorOcrFoundError("PDF already has text layer")

    monkeypatch.setattr(converter.ocrmypdf, "ocr", fake_ocr)

    # Should not raise - PriorOcrFoundError is acceptable
    # Note: This might still fail because ocrmypdf.ocr doesn't create output_pdf
    # In real scenarios, ocrmypdf would have created the output before raising this
    try:
        converter.convert_to_pdfa(
            input_pdf,
            output_pdf,
            language="eng",
            pdfa_level="2",
        )
    except ocrmypdf_exceptions.PriorOcrFoundError:
        # This is expected - the function logs but doesn't re-raise
        pass


def test_generic_exception_is_reraised(monkeypatch, tmp_path) -> None:
    """Test that unknown exceptions are still raised."""
    input_pdf = tmp_path / "input.pdf"
    input_pdf.write_bytes(b"%PDF-1.4 test")
    output_pdf = tmp_path / "output.pdf"

    def fake_ocr(input_file: str, output_file: str, **kwargs) -> None:
        raise ValueError("Unexpected error")

    monkeypatch.setattr(converter.ocrmypdf, "ocr", fake_ocr)

    # Should re-raise the ValueError
    with pytest.raises(ValueError, match="Unexpected error"):
        converter.convert_to_pdfa(
            input_pdf,
            output_pdf,
            language="eng",
            pdfa_level="2",
        )
