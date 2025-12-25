"""Shared utilities to convert PDFs to PDF/A using OCRmyPDF."""

from __future__ import annotations

import asyncio
import logging
import shutil
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any

import ocrmypdf
import ocrmypdf.exceptions as ocrmypdf_exceptions
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
) -> dict[str, Any]:
    """Determine if a PDF needs OCR based on text content analysis.

    Analyzes the first N pages of a PDF to detect existing searchable text.
    Uses character count thresholds to distinguish between text PDFs and
    scanned documents.

    Args:
        pdf_path: Path to the PDF file to analyze.
        sample_pages: Number of pages to sample (default: DEFAULT_SAMPLE_PAGES).

    Returns:
        Dict with OCR decision and statistics:
        - needs_ocr: True if OCR should be performed, False if text exists
        - reason: Human-readable explanation for logging
        - pages_with_text: Number of pages containing text
        - total_pages_checked: Total pages analyzed
        - text_ratio: Ratio of pages with text (0.0-1.0)
        - total_characters: Total characters found across all pages

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
                return {
                    "needs_ocr": True,
                    "reason": "PDF has no pages",
                    "pages_with_text": 0,
                    "total_pages_checked": 0,
                    "text_ratio": 0.0,
                    "total_characters": 0,
                }

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
                text_ratio = 1.0 if total_chars >= MIN_CHARS_PER_PAGE else 0.0
                if total_chars >= MIN_CHARS_PER_PAGE:
                    return {
                        "needs_ocr": False,
                        "reason": (
                            f"Single page has {total_chars} characters "
                            f"(text detected)"
                        ),
                        "pages_with_text": 1,
                        "total_pages_checked": 1,
                        "text_ratio": text_ratio,
                        "total_characters": total_chars,
                    }
                else:
                    return {
                        "needs_ocr": True,
                        "reason": (
                            f"Single page has only {total_chars} characters "
                            f"(needs OCR)"
                        ),
                        "pages_with_text": 0,
                        "total_pages_checked": 1,
                        "text_ratio": text_ratio,
                        "total_characters": total_chars,
                    }
            else:
                # Multiple pages: ratio-based threshold
                text_ratio = pages_with_text / pages_to_check

                if text_ratio >= MIN_TEXT_RATIO:
                    return {
                        "needs_ocr": False,
                        "reason": (
                            f"{pages_with_text}/{pages_to_check} pages have "
                            f"text ({text_ratio:.1%}, {total_chars} total "
                            f"chars) - text detected"
                        ),
                        "pages_with_text": pages_with_text,
                        "total_pages_checked": pages_to_check,
                        "text_ratio": text_ratio,
                        "total_characters": total_chars,
                    }
                else:
                    return {
                        "needs_ocr": True,
                        "reason": (
                            f"Only {pages_with_text}/{pages_to_check} pages have text "
                            f"({text_ratio:.1%}, {total_chars} total chars) - needs OCR"
                        ),
                        "pages_with_text": pages_with_text,
                        "total_pages_checked": pages_to_check,
                        "text_ratio": text_ratio,
                        "total_characters": total_chars,
                    }

    except Exception as e:
        logger.warning(f"Could not analyze PDF text content for {pdf_path}: {e}")
        # Safe default: perform OCR if we can't determine
        return {
            "needs_ocr": True,
            "reason": f"Text analysis failed: {e}",
            "pages_with_text": 0,
            "total_pages_checked": 0,
            "text_ratio": 0.0,
            "total_characters": 0,
        }


def convert_to_pdfa(
    input_pdf: Path,
    output_pdf: Path,
    *,
    language: str,
    pdfa_level: str,
    ocr_enabled: bool = True,
    skip_ocr_on_tagged_pdfs: bool = True,
    is_office_source: bool = False,
    compression_config: CompressionConfig | None = None,
    progress_callback: Callable[[ProgressInfo], None] | None = None,
    cancel_event: asyncio.Event | None = None,
    event_callback: Callable[..., Awaitable[None]] | None = None,
) -> None:
    """Convert a PDF to PDF/A using OCRmyPDF, or pass through for plain PDF output.

    Args:
        input_pdf: Path to the input PDF file.
        output_pdf: Path for the output PDF/A file.
        language: Tesseract language codes for OCR (e.g., 'eng', 'deu+eng').
        pdfa_level: PDF/A compliance level ('1', '2', '3') or 'pdf' for
                    plain PDF output.
        ocr_enabled: Whether to perform OCR on the PDF (default: True).
        skip_ocr_on_tagged_pdfs: Skip OCR for PDFs with structure tags
                                 (default: True).
        is_office_source: Whether the PDF originated from an Office document
                          (default: False). When True with pdfa_level='pdf',
                          enables pass-through mode.
        compression_config: Compression settings (default: None, uses defaults).
        progress_callback: Optional callback for progress updates.
        cancel_event: Optional event to check for cancellation requests.
        event_callback: Optional async callback for logging job events.
                       Called with (event_type: str, **kwargs: Any).

    """

    # Helper to call async event_callback from sync context
    def log_event(event_type: str, **kwargs: Any) -> None:
        """Log event if callback is provided."""
        if event_callback:
            # Run the async callback in a new event loop if needed
            try:
                loop = asyncio.get_running_loop()
                # We're in an event loop, schedule the callback
                loop.create_task(event_callback(event_type, **kwargs))
            except RuntimeError:
                # No event loop running, run callback synchronously
                asyncio.run(event_callback(event_type, **kwargs))

    if not input_pdf.exists():
        logger.error(f"Input file does not exist: {input_pdf}")
        raise FileNotFoundError(f"Input file does not exist: {input_pdf}")

    # Universal PDF pass-through mode (for all input types)
    if pdfa_level == "pdf" and not ocr_enabled:
        logger.info(f"PDF output mode: No OCR, copying file: {input_pdf}")

        # Check for tags (informational only)
        has_tags = has_pdf_tags(input_pdf)
        if has_tags:
            logger.info(f"PDF has structure tags (preserved): {input_pdf}")
        else:
            logger.debug(f"PDF has no structure tags: {input_pdf}")

        # Log passthrough mode event
        log_event(
            "passthrough_mode",
            enabled=True,
            reason="pdf_output_no_ocr",
            pdfa_level=pdfa_level,
            ocr_enabled=ocr_enabled,
            has_tags=has_tags,
            tags_preserved=has_tags,
        )

        # Copy directly to output
        output_pdf.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(input_pdf, output_pdf)
        logger.info(f"Successfully created PDF file (pass-through): {output_pdf}")
        return

    # Determine output type based on pdfa_level
    if pdfa_level == "pdf":
        output_type = "pdf"
    elif pdfa_level in ["1", "2", "3"]:
        output_type = f"pdfa-{pdfa_level}"
    else:
        raise ValueError(
            f"Invalid pdfa_level: '{pdfa_level}'. " f"Expected 'pdf', '1', '2', or '3'."
        )

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

            # Log OCR decision event for tagged PDF
            log_event(
                "ocr_decision",
                decision="skip",
                reason="tagged_pdf",
                has_struct_tree_root=True,
            )

            # Preserve vector content for tagged PDFs (office documents)
            original_profile = None
            if compression_config.remove_vectors:
                logger.info(
                    "Tagged PDF detected - switching to "
                    "vector-preserving compression mode"
                )
                original_profile = "custom" if compression_config else "default"
                compression_config = PRESETS["preserve"]

                # Log compression profile auto-switch
                log_event(
                    "compression_selected",
                    profile="preserve",
                    reason="auto_switched_for_tagged_pdf",
                    original_profile=original_profile,
                    settings={
                        "image_dpi": compression_config.image_dpi,
                        "remove_vectors": compression_config.remove_vectors,
                    },
                )

        # Second check: Text content detection (for all other PDFs)
        else:
            ocr_stats = needs_ocr(input_pdf)

            if not ocr_stats["needs_ocr"]:
                actual_ocr_enabled = False
                skip_text = True
                logger.info(f"Skipping OCR: {ocr_stats['reason']} - {input_pdf}")

                # Log OCR decision event with stats
                log_event(
                    "ocr_decision",
                    decision="skip",
                    reason="has_text",
                    pages_with_text=ocr_stats["pages_with_text"],
                    total_pages_checked=ocr_stats["total_pages_checked"],
                    text_ratio=ocr_stats["text_ratio"],
                    total_characters=ocr_stats["total_characters"],
                )
            else:
                logger.info(f"Performing OCR: {ocr_stats['reason']} - {input_pdf}")

                # Log OCR decision event
                log_event(
                    "ocr_decision",
                    decision="perform",
                    reason="no_text",
                    pages_with_text=ocr_stats["pages_with_text"],
                    total_pages_checked=ocr_stats["total_pages_checked"],
                    text_ratio=ocr_stats["text_ratio"],
                    total_characters=ocr_stats["total_characters"],
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
    # Note: output_type is already set above based on pdfa_level

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
    except ocrmypdf_exceptions.SubprocessOutputError as e:
        # Ghostscript or other subprocess failed (e.g., rendering error)
        # This often happens with problematic PDFs that Ghostscript can't handle
        logger.warning(
            f"Ghostscript rendering failed for {input_pdf}: {e}. "
            "Attempting fallback strategies..."
        )

        # Three-tier fallback strategy
        if actual_ocr_enabled:
            # TIER 2: Try with Ghostscript-safe parameters (still with OCR)
            # Use conservative settings that are less likely to trigger GS errors
            logger.info(
                "Tier 2 fallback: Retrying with Ghostscript-safe parameters "
                "(low DPI, preserved vectors, minimal compression)"
            )

            # Use ghostscript_safe preset: low DPI, no vector removal, no JBIG2
            safe_config = PRESETS["ghostscript_safe"]

            # Try a simpler PDF/A level for better compatibility
            # PDF/A-1 is most restrictive but most compatible
            safe_pdfa_level = pdfa_level
            pdfa_downgrade = None
            if pdfa_level == "3":
                safe_pdfa_level = "2"  # PDF/A-3 → PDF/A-2
                pdfa_downgrade = {"original": "3", "fallback": "2"}
                logger.debug("Downgrading PDF/A-3 to PDF/A-2 for better compatibility")
            elif pdfa_level == "2":
                safe_pdfa_level = "1"  # PDF/A-2 → PDF/A-1
                pdfa_downgrade = {"original": "2", "fallback": "1"}
                logger.debug("Downgrading PDF/A-2 to PDF/A-1 for better compatibility")

            # Log fallback tier 2 event
            log_event(
                "fallback_applied",
                tier=2,
                reason="ghostscript_error",
                original_error=str(e),
                safe_mode_config={
                    "image_dpi": safe_config.image_dpi,
                    "remove_vectors": safe_config.remove_vectors,
                    "optimize": safe_config.optimize,
                    "jbig2_lossy": safe_config.jbig2_lossy,
                },
                pdfa_level_downgrade=pdfa_downgrade,
            )

            try:
                ocrmypdf.ocr(
                    str(input_pdf),
                    str(output_pdf),
                    language=language,
                    output_type=f"pdfa-{safe_pdfa_level}",
                    force_ocr=True,  # Still perform OCR
                    skip_text=False,
                    # Ghostscript-safe compression settings
                    image_dpi=safe_config.image_dpi,  # 100 DPI (low)
                    remove_vectors=safe_config.remove_vectors,  # False (preserve)
                    optimize=safe_config.optimize,  # 0 (no optimization)
                    jpg_quality=safe_config.jpg_quality,  # 95 (high quality)
                    jbig2_lossy=safe_config.jbig2_lossy,  # False
                    # 0 (disabled)
                    jbig2_page_group_size=safe_config.jbig2_page_group_size,
                    # Plugin manager for progress tracking
                    plugin_manager=plugin_manager,
                    progress_bar=True,
                )
                logger.info(
                    f"Successfully converted PDF/A-{safe_pdfa_level} with "
                    f"safe-mode parameters: {output_pdf}"
                )
            except ocrmypdf_exceptions.SubprocessOutputError as safe_mode_error:
                # TIER 3: Safe mode also failed, try without OCR as last resort
                logger.warning(
                    f"Safe-mode conversion also failed: {safe_mode_error}. "
                    "Tier 3 fallback: Attempting conversion without OCR..."
                )

                # Log fallback tier 3 event
                log_event(
                    "fallback_applied",
                    tier=3,
                    reason="tier2_failed",
                    tier2_error=str(safe_mode_error),
                    ocr_disabled=True,
                    safe_mode_config={
                        "image_dpi": safe_config.image_dpi,
                        "remove_vectors": safe_config.remove_vectors,
                        "optimize": safe_config.optimize,
                    },
                )

                try:
                    ocrmypdf.ocr(
                        str(input_pdf),
                        str(output_pdf),
                        language=language,
                        output_type=f"pdfa-{safe_pdfa_level}",
                        force_ocr=False,  # Disable OCR
                        skip_text=True,
                        # Keep safe compression settings
                        image_dpi=safe_config.image_dpi,
                        remove_vectors=safe_config.remove_vectors,
                        optimize=safe_config.optimize,
                        jpg_quality=safe_config.jpg_quality,
                        jbig2_lossy=safe_config.jbig2_lossy,
                        jbig2_page_group_size=safe_config.jbig2_page_group_size,
                        # Plugin manager for progress tracking
                        plugin_manager=plugin_manager,
                        progress_bar=True,
                    )
                    logger.info(
                        f"Successfully converted PDF/A-{safe_pdfa_level} without OCR "
                        f"(final fallback): {output_pdf}"
                    )
                except Exception as no_ocr_error:
                    logger.error(
                        f"All fallback attempts failed: {no_ocr_error}", exc_info=True
                    )
                    raise RuntimeError(
                        "PDF conversion failed: All fallback strategies exhausted. "
                        "Tried: (1) normal OCR, (2) safe-mode OCR with low DPI and "
                        "preserved vectors, (3) no OCR. Ghostscript could not render "
                        "this PDF. The file may be severely corrupted or contain "
                        "unsupported features."
                    ) from e
        else:
            # OCR was not enabled, so we can't try OCR-based fallbacks
            raise RuntimeError(
                "PDF conversion failed: Ghostscript could not render the PDF. "
                "The PDF may be corrupted or contain unsupported features."
            ) from e
    except ocrmypdf_exceptions.PriorOcrFoundError:
        # PDF already has OCR text layer - this is fine, just log it
        logger.info(f"PDF already has OCR layer: {input_pdf}")
        # Continue without raising error
    except ocrmypdf_exceptions.EncryptedPdfError as e:
        logger.error(f"PDF is encrypted: {input_pdf}")
        raise RuntimeError(
            "Cannot process encrypted PDF. Please remove encryption first."
        ) from e
    except ocrmypdf_exceptions.InputFileError as e:
        logger.error(f"Invalid input PDF: {input_pdf}")
        raise RuntimeError(f"Invalid or corrupted PDF file: {e}") from e
    except Exception as e:
        logger.error(f"OCRmyPDF conversion failed: {e}", exc_info=True)
        raise
