"""Shared utilities to convert PDFs to PDF/A using OCRmyPDF."""

from __future__ import annotations

import logging
from pathlib import Path

import ocrmypdf

logger = logging.getLogger(__name__)


def convert_to_pdfa(
    input_pdf: Path,
    output_pdf: Path,
    *,
    language: str,
    pdfa_level: str,
    ocr_enabled: bool = True,
) -> None:
    """Convert a PDF to PDF/A using OCRmyPDF.

    Args:
        input_pdf: Path to the input PDF file.
        output_pdf: Path for the output PDF/A file.
        language: Tesseract language codes for OCR (e.g., 'eng', 'deu+eng').
        pdfa_level: PDF/A compliance level ('1', '2', or '3').
        ocr_enabled: Whether to perform OCR on the PDF (default: True).

    """
    if not input_pdf.exists():
        logger.error(f"Input file does not exist: {input_pdf}")
        raise FileNotFoundError(f"Input file does not exist: {input_pdf}")

    logger.info(
        f"Converting PDF to PDF/A-{pdfa_level}: {input_pdf} -> {output_pdf}",
    )
    logger.debug(f"OCR enabled: {ocr_enabled}, Languages: {language}")

    output_pdf.parent.mkdir(parents=True, exist_ok=True)
    output_type = f"pdfa-{pdfa_level}"

    try:
        ocrmypdf.ocr(
            str(input_pdf),
            str(output_pdf),
            language=language,
            output_type=output_type,
            force_ocr=ocr_enabled,
        )
        logger.info(f"Successfully converted PDF/A file: {output_pdf}")
    except Exception as e:
        logger.error(f"OCRmyPDF conversion failed: {e}", exc_info=True)
        raise
