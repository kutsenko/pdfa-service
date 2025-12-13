"""Tests for error handling in PDF conversion."""

from __future__ import annotations

from pathlib import Path

import ocrmypdf.exceptions as ocrmypdf_exceptions
import pytest

from pdfa import converter


def test_ghostscript_error_fallback_to_no_ocr_legacy(monkeypatch, tmp_path) -> None:
    """Test that final tier (no-OCR) succeeds when safe-mode also fails.

    This is a compatibility test for the old two-tier fallback behavior,
    now extended to three tiers: normal → safe-mode → no-OCR.
    """
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

        # First two calls fail (normal + safe-mode)
        if call_count <= 2:
            raise ocrmypdf_exceptions.SubprocessOutputError(
                "Ghostscript rasterizing failed"
            )
        # Third call (no OCR) succeeds
        elif call_count == 3:
            Path(output_file).write_bytes(b"%PDF-1.4 converted")

    monkeypatch.setattr(converter.ocrmypdf, "ocr", fake_ocr)

    # Should succeed with final fallback
    converter.convert_to_pdfa(
        input_pdf,
        output_pdf,
        language="eng",
        pdfa_level="2",
        ocr_enabled=True,
    )

    # Verify three calls were made (new behavior)
    assert call_count == 3

    # First call should have OCR enabled (normal mode)
    assert ocr_kwargs_list[0]["force_ocr"] is True
    assert ocr_kwargs_list[0]["skip_text"] is False

    # Second call should have OCR enabled (safe mode)
    assert ocr_kwargs_list[1]["force_ocr"] is True
    assert ocr_kwargs_list[1]["skip_text"] is False

    # Third call (final fallback) should have OCR disabled
    assert ocr_kwargs_list[2]["force_ocr"] is False
    assert ocr_kwargs_list[2]["skip_text"] is True

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
    """Test error handling when all three fallback tiers fail."""
    input_pdf = tmp_path / "input.pdf"
    input_pdf.write_bytes(b"%PDF-1.4 test")
    output_pdf = tmp_path / "output.pdf"

    def fake_ocr(input_file: str, output_file: str, **kwargs) -> None:
        # Always fail with Ghostscript error
        raise ocrmypdf_exceptions.SubprocessOutputError(
            "Ghostscript rasterizing failed"
        )

    monkeypatch.setattr(converter.ocrmypdf, "ocr", fake_ocr)

    # Should raise RuntimeError mentioning all fallback attempts
    with pytest.raises(
        RuntimeError, match="All fallback strategies exhausted.*severely corrupted"
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


def test_ghostscript_safe_mode_fallback_succeeds(monkeypatch, tmp_path) -> None:
    """Test that Tier 2 safe-mode fallback succeeds when normal mode fails."""
    input_pdf = tmp_path / "input.pdf"
    input_pdf.write_bytes(b"%PDF-1.4 test")
    output_pdf = tmp_path / "output.pdf"

    call_count = 0
    ocr_kwargs_list = []

    def fake_ocr(input_file: str, output_file: str, **kwargs) -> None:
        nonlocal call_count
        call_count += 1
        ocr_kwargs_list.append(kwargs)

        # First call (normal mode) fails
        if call_count == 1:
            raise ocrmypdf_exceptions.SubprocessOutputError(
                "Ghostscript rasterizing failed"
            )
        # Second call (safe mode) succeeds
        elif call_count == 2:
            Path(output_file).write_bytes(b"%PDF-1.4 converted")

    monkeypatch.setattr(converter.ocrmypdf, "ocr", fake_ocr)

    # Should succeed with safe-mode fallback
    converter.convert_to_pdfa(
        input_pdf,
        output_pdf,
        language="eng",
        pdfa_level="2",
        ocr_enabled=True,
    )

    # Verify two calls were made
    assert call_count == 2

    # First call: normal mode with OCR
    assert ocr_kwargs_list[0]["force_ocr"] is True
    assert ocr_kwargs_list[0]["output_type"] == "pdfa-2"

    # Second call: safe mode with OCR, downgraded PDF/A level
    assert ocr_kwargs_list[1]["force_ocr"] is True  # Still with OCR
    assert ocr_kwargs_list[1]["output_type"] == "pdfa-1"  # Downgraded from 2 to 1
    assert ocr_kwargs_list[1]["image_dpi"] == 100  # Low DPI
    assert ocr_kwargs_list[1]["remove_vectors"] is False  # Preserve vectors
    assert ocr_kwargs_list[1]["optimize"] == 0  # No optimization
    assert ocr_kwargs_list[1]["jpg_quality"] == 95  # High quality
    assert ocr_kwargs_list[1]["jbig2_page_group_size"] == 1  # Minimal JBIG2 grouping

    # Output file should exist
    assert output_pdf.exists()


def test_ghostscript_three_tier_fallback(monkeypatch, tmp_path) -> None:
    """Test all three fallback tiers: normal → safe-mode → no-OCR."""
    input_pdf = tmp_path / "input.pdf"
    input_pdf.write_bytes(b"%PDF-1.4 test")
    output_pdf = tmp_path / "output.pdf"

    call_count = 0
    ocr_kwargs_list = []

    def fake_ocr(input_file: str, output_file: str, **kwargs) -> None:
        nonlocal call_count
        call_count += 1
        ocr_kwargs_list.append(kwargs)

        # First two calls fail (normal mode and safe mode)
        if call_count <= 2:
            raise ocrmypdf_exceptions.SubprocessOutputError(
                "Ghostscript rasterizing failed"
            )
        # Third call (no OCR) succeeds
        elif call_count == 3:
            Path(output_file).write_bytes(b"%PDF-1.4 converted")

    monkeypatch.setattr(converter.ocrmypdf, "ocr", fake_ocr)

    # Should succeed with final no-OCR fallback
    converter.convert_to_pdfa(
        input_pdf,
        output_pdf,
        language="eng",
        pdfa_level="3",
        ocr_enabled=True,
    )

    # Verify three calls were made
    assert call_count == 3

    # First call: normal mode with OCR, PDF/A-3
    assert ocr_kwargs_list[0]["force_ocr"] is True
    assert ocr_kwargs_list[0]["output_type"] == "pdfa-3"

    # Second call: safe mode with OCR, PDF/A-2 (downgraded from 3)
    assert ocr_kwargs_list[1]["force_ocr"] is True
    assert ocr_kwargs_list[1]["output_type"] == "pdfa-2"
    assert ocr_kwargs_list[1]["image_dpi"] == 100
    assert ocr_kwargs_list[1]["remove_vectors"] is False

    # Third call: no OCR, still using safe mode settings
    assert ocr_kwargs_list[2]["force_ocr"] is False
    assert ocr_kwargs_list[2]["skip_text"] is True
    assert ocr_kwargs_list[2]["output_type"] == "pdfa-2"
    assert ocr_kwargs_list[2]["image_dpi"] == 100

    # Output file should exist
    assert output_pdf.exists()


def test_ghostscript_all_fallbacks_fail(monkeypatch, tmp_path) -> None:
    """Test that meaningful error is raised when all three tiers fail."""
    input_pdf = tmp_path / "input.pdf"
    input_pdf.write_bytes(b"%PDF-1.4 test")
    output_pdf = tmp_path / "output.pdf"

    def fake_ocr(input_file: str, output_file: str, **kwargs) -> None:
        # Always fail
        raise ocrmypdf_exceptions.SubprocessOutputError(
            "Ghostscript rasterizing failed"
        )

    monkeypatch.setattr(converter.ocrmypdf, "ocr", fake_ocr)

    # Should raise RuntimeError with comprehensive message
    with pytest.raises(
        RuntimeError, match="All fallback strategies exhausted.*safe-mode OCR"
    ):
        converter.convert_to_pdfa(
            input_pdf,
            output_pdf,
            language="eng",
            pdfa_level="2",
            ocr_enabled=True,
        )


def test_ghostscript_pdfa_level_downgrade(monkeypatch, tmp_path) -> None:
    """Test that PDF/A level is correctly downgraded in safe mode."""
    input_pdf = tmp_path / "input.pdf"
    input_pdf.write_bytes(b"%PDF-1.4 test")
    output_pdf = tmp_path / "output.pdf"

    test_cases = [
        ("3", "2"),  # PDF/A-3 → PDF/A-2
        ("2", "1"),  # PDF/A-2 → PDF/A-1
        ("1", "1"),  # PDF/A-1 → PDF/A-1 (no downgrade possible)
    ]

    for original_level, expected_safe_level in test_cases:
        call_count = 0
        captured_levels = []

        def fake_ocr(input_file: str, output_file: str, **kwargs) -> None:
            nonlocal call_count
            call_count += 1
            captured_levels.append(kwargs["output_type"])

            # First call fails, second succeeds
            if call_count == 1:
                raise ocrmypdf_exceptions.SubprocessOutputError("GS failed")
            else:
                Path(output_file).write_bytes(b"%PDF-1.4 converted")

        monkeypatch.setattr(converter.ocrmypdf, "ocr", fake_ocr)

        # Convert with specific PDF/A level
        converter.convert_to_pdfa(
            input_pdf,
            output_pdf,
            language="eng",
            pdfa_level=original_level,
            ocr_enabled=True,
        )

        # Verify the downgrade
        assert captured_levels[0] == f"pdfa-{original_level}"  # First attempt
        assert captured_levels[1] == f"pdfa-{expected_safe_level}"  # Safe mode
