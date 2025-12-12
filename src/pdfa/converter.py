"""Shared utilities to convert PDFs to PDF/A using OCRmyPDF."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from pathlib import Path

import ocrmypdf
import ocrmypdf.pluginspec
import pikepdf

from pdfa.compression_config import PRESETS, CompressionConfig
from pdfa.progress_tracker import ProgressInfo, WebSocketProgressBar

logger = logging.getLogger(__name__)

# OCR detection thresholds
MIN_CHARS_PER_PAGE = 50  # Minimum characters to consider page "has text"
MIN_TEXT_RATIO = 0.66  # Minimum ratio of pages with text to skip OCR
DEFAULT_SAMPLE_PAGES = 3  # Number of pages to sample for detection


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


def needs_ocr(
    pdf_path: Path, sample_pages: int = DEFAULT_SAMPLE_PAGES
) -> tuple[bool, str]:
    """Determine if a PDF needs OCR based on text content analysis.

    Analyzes the first N pages of a PDF to detect existing searchable text.
    Uses character count thresholds to distinguish between text PDFs and
    scanned documents.

    Args:
        pdf_path: Path to the PDF file to analyze.
        sample_pages: Number of pages to sample (default: DEFAULT_SAMPLE_PAGES).

    Returns:
        Tuple of (needs_ocr, reason):
        - needs_ocr: True if OCR should be performed, False if text exists
        - reason: Human-readable explanation for logging

    Detection Logic:
        - Extracts text from first N pages
        - Pages with >= MIN_CHARS_PER_PAGE characters are considered "has text"
        - If >= MIN_TEXT_RATIO of pages have text → skip OCR
        - Otherwise → perform OCR

    Edge Cases:
        - Empty PDFs → needs OCR
        - Very short text → needs OCR (likely metadata/noise)
        - Single page → uses absolute threshold (MIN_CHARS_PER_PAGE)

    """
    try:
        with pikepdf.open(pdf_path) as pdf:
            num_pages = len(pdf.pages)

            if num_pages == 0:
                return True, "PDF has no pages"

            # Sample first N pages (or all pages if fewer)
            pages_to_check = min(sample_pages, num_pages)
            pages_with_text = 0
            total_chars = 0

            for page_num in range(pages_to_check):
                page = pdf.pages[page_num]

                # Extract text content from page
                text = ""
                if "/Contents" in page:
                    try:
                        # Get page content stream
                        contents = page.Contents
                        if isinstance(contents, list):
                            # Multiple content streams
                            for content in contents:
                                text += content.read_bytes().decode(
                                    "latin-1", errors="ignore"
                                )
                        else:
                            text += contents.read_bytes().decode(
                                "latin-1", errors="ignore"
                            )
                    except Exception as e:
                        logger.debug(
                            f"Could not extract text from page {page_num}: {e}"
                        )
                        continue

                # Count actual text characters
                # Simple heuristic: look for Tj, TJ operators (PDF text-showing)
                import re

                # Match text between parentheses (PDF text strings)
                text_matches = re.findall(r"\(([^)]*)\)", text)
                text_content = "".join(text_matches)

                # Count characters (keep spaces, remove only newlines/returns)
                char_count = len(
                    text_content.strip().replace("\n", "").replace("\r", "")
                )
                total_chars += char_count

                if char_count >= MIN_CHARS_PER_PAGE:
                    pages_with_text += 1
                    logger.debug(
                        f"Page {page_num} has {char_count} characters (has text)"
                    )
                else:
                    logger.debug(
                        f"Page {page_num} has {char_count} characters (no text)"
                    )

            # Decision logic
            if pages_to_check == 1:
                # Single page: absolute threshold
                if total_chars >= MIN_CHARS_PER_PAGE:
                    return (
                        False,
                        f"Single page has {total_chars} characters (text detected)",
                    )
                else:
                    return (
                        True,
                        f"Single page has only {total_chars} characters (needs OCR)",
                    )
            else:
                # Multiple pages: ratio-based threshold
                text_ratio = pages_with_text / pages_to_check

                if text_ratio >= MIN_TEXT_RATIO:
                    return False, (
                        f"{pages_with_text}/{pages_to_check} pages have text "
                        f"({text_ratio:.1%}, {total_chars} total chars) - text detected"
                    )
                else:
                    return True, (
                        f"Only {pages_with_text}/{pages_to_check} pages have text "
                        f"({text_ratio:.1%}, {total_chars} total chars) - needs OCR"
                    )

    except Exception as e:
        logger.warning(f"Could not analyze PDF text content for {pdf_path}: {e}")
        # Safe default: perform OCR if we can't determine
        return True, f"Text analysis failed: {e}"


def convert_to_pdfa(
    input_pdf: Path,
    output_pdf: Path,
    *,
    language: str,
    pdfa_level: str,
    ocr_enabled: bool = True,
    skip_ocr_on_tagged_pdfs: bool = True,
    compression_config: CompressionConfig | None = None,
    progress_callback: Callable[[ProgressInfo], None] | None = None,
    cancel_event: asyncio.Event | None = None,
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
        progress_callback: Optional callback for progress updates.
        cancel_event: Optional event to check for cancellation requests.

    """
    if not input_pdf.exists():
        logger.error(f"Input file does not exist: {input_pdf}")
        raise FileNotFoundError(f"Input file does not exist: {input_pdf}")

    # Use provided compression config or load defaults
    if compression_config is None:
        compression_config = CompressionConfig()

    # Validate configuration
    compression_config.validate()

    # Determine if OCR is actually needed
    actual_ocr_enabled = ocr_enabled
    skip_text = False

    if ocr_enabled and skip_ocr_on_tagged_pdfs:
        # First check: Tagged PDFs (Office documents)
        if has_pdf_tags(input_pdf):
            actual_ocr_enabled = False
            skip_text = True
            logger.info(
                f"PDF has structure tags, skipping OCR as requested: {input_pdf}"
            )

            # Preserve vector content for tagged PDFs (office documents)
            if compression_config.remove_vectors:
                logger.info(
                    "Tagged PDF detected - switching to "
                    "vector-preserving compression mode"
                )
                compression_config = PRESETS["preserve"]

        # Second check: Text content detection (for all other PDFs)
        else:
            ocr_needed, reason = needs_ocr(input_pdf)

            if not ocr_needed:
                actual_ocr_enabled = False
                skip_text = True
                logger.info(f"Skipping OCR: {reason} - {input_pdf}")
            else:
                logger.info(f"Performing OCR: {reason} - {input_pdf}")

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

    # Set up progress tracking via OCRmyPDF plugin system
    plugin_manager = None
    if progress_callback:
        # Create a temporary plugin that provides our custom progress bar class
        from ocrmypdf import hookimpl
        from ocrmypdf.api import get_plugin_manager

        # Create a wrapper class that injects callback and cancel_event
        class ConfiguredProgressBar(WebSocketProgressBar):
            """WebSocketProgressBar pre-configured with callback and cancel_event."""

            def __init__(self, *args, **kwargs):
                # Inject our callback and cancel_event into all instances
                super().__init__(
                    *args,
                    **kwargs,
                    callback=progress_callback,
                    cancel_event=cancel_event,
                )

        # Create a plugin that returns our configured progress bar class
        class ProgressPlugin:
            @hookimpl
            def get_progressbar_class(self):
                return ConfiguredProgressBar

        # Get a plugin manager with built-in OCRmyPDF plugins
        plugin_manager = get_plugin_manager([])

        # Register our custom progress plugin
        plugin_manager.register(ProgressPlugin())

        logger.info("Registered custom progress bar plugin")

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
            # Plugin manager for progress tracking
            plugin_manager=plugin_manager,
            # Enable progress bars (our plugin provides the custom implementation)
            progress_bar=True,
        )
        logger.info(f"Successfully converted PDF/A file: {output_pdf}")
    except Exception as e:
        logger.error(f"OCRmyPDF conversion failed: {e}", exc_info=True)
        raise
