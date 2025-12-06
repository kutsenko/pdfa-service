"""Shared utilities to convert PDFs to PDF/A using OCRmyPDF."""

from __future__ import annotations

import logging
from pathlib import Path

import ocrmypdf
import pikepdf

from pdfa.compression_config import CompressionConfig

logger = logging.getLogger(__name__)


def has_pdf_tags(pdf_path: Path) -> bool:
    """Check if a PDF has structure tags (is tagged).

    Args:
        pdf_path: Path to the PDF file to check.

    Returns:
        True if the PDF has structure tags, False otherwise.

    """
    try:
        with pikepdf.open(pdf_path) as pdf:
            # Check if StructTreeRoot exists in the document catalog
            # This indicates the PDF has structure tags
            if "/StructTreeRoot" in pdf.Root:
                logger.debug(f"PDF has structure tags: {pdf_path}")
                return True
            logger.debug(f"PDF does not have structure tags: {pdf_path}")
            return False
    except Exception as e:
        logger.warning(f"Could not check PDF tags for {pdf_path}: {e}")
        # If we can't check, assume it doesn't have tags (safe default)
        return False


def convert_to_pdfa(
    input_pdf: Path,
    output_pdf: Path,
    *,
    language: str,
    pdfa_level: str,
    ocr_enabled: bool = True,
    skip_ocr_on_tagged_pdfs: bool = True,
    compression_config: CompressionConfig | None = None,
) -> None:
    """Convert a PDF to PDF/A using OCRmyPDF.

    Args:
        input_pdf: Path to the input PDF file.
        output_pdf: Path for the output PDF/A file.
        language: Tesseract language codes for OCR (e.g., 'eng', 'deu+eng').
        pdfa_level: PDF/A compliance level ('1', '2', or '3').
        ocr_enabled: Whether to perform OCR on the PDF (default: True).
        skip_ocr_on_tagged_pdfs: Skip OCR for PDFs with structure tags (default: True).
        compression_config: Compression settings (default: None, uses defaults).

    """
    if not input_pdf.exists():
        logger.error(f"Input file does not exist: {input_pdf}")
        raise FileNotFoundError(f"Input file does not exist: {input_pdf}")

    # Use provided compression config or load defaults
    if compression_config is None:
        compression_config = CompressionConfig()

    # Validate configuration
    compression_config.validate()

    # Check if we should skip OCR for tagged PDFs
    actual_ocr_enabled = ocr_enabled
    skip_text = False
    if ocr_enabled and skip_ocr_on_tagged_pdfs:
        if has_pdf_tags(input_pdf):
            actual_ocr_enabled = False
            skip_text = True
            logger.info(
                f"PDF has structure tags, skipping OCR as requested: {input_pdf}"
            )

    logger.info(
        f"Converting PDF to PDF/A-{pdfa_level}: {input_pdf} -> {output_pdf}",
    )
    logger.debug(
        f"OCR enabled: {actual_ocr_enabled}, Skip text: {skip_text}, "
        f"Languages: {language}, Skip OCR on tagged PDFs: {skip_ocr_on_tagged_pdfs}"
    )
    logger.debug(
        f"Compression: DPI={compression_config.image_dpi}, "
        f"JPG quality={compression_config.jpg_quality}, "
        f"Optimize={compression_config.optimize}"
    )

    output_pdf.parent.mkdir(parents=True, exist_ok=True)
    output_type = f"pdfa-{pdfa_level}"

    try:
        ocrmypdf.ocr(
            str(input_pdf),
            str(output_pdf),
            language=language,
            output_type=output_type,
            force_ocr=actual_ocr_enabled,
            skip_text=skip_text,
            # Compression settings (configurable via environment variables)
            image_dpi=compression_config.image_dpi,
            remove_vectors=compression_config.remove_vectors,
            optimize=compression_config.optimize,
            jpg_quality=compression_config.jpg_quality,
            jbig2_lossy=compression_config.jbig2_lossy,
            jbig2_page_group_size=compression_config.jbig2_page_group_size,
        )
        logger.info(f"Successfully converted PDF/A file: {output_pdf}")
    except Exception as e:
        logger.error(f"OCRmyPDF conversion failed: {e}", exc_info=True)
        raise
