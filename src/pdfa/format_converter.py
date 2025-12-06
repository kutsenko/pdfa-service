"""Convert Office documents and images to PDF."""

from __future__ import annotations

import logging
import subprocess
import time
from collections.abc import Callable
from pathlib import Path

from pdfa.exceptions import OfficeConversionError, UnsupportedFormatError
from pdfa.progress_tracker import ProgressInfo

logger = logging.getLogger(__name__)

# Supported Office formats
OFFICE_EXTENSIONS = {".docx", ".pptx", ".xlsx"}

# Supported Open Document Format (ODF)
ODF_EXTENSIONS = {".odt", ".ods", ".odp"}

# Supported image formats
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tiff", ".tif", ".bmp", ".gif"}

# All document formats that require conversion to PDF
DOCUMENT_EXTENSIONS = OFFICE_EXTENSIONS | ODF_EXTENSIONS

# All formats that require conversion to PDF before PDF/A
CONVERTIBLE_EXTENSIONS = DOCUMENT_EXTENSIONS | IMAGE_EXTENSIONS

# All supported formats
SUPPORTED_EXTENSIONS = {".pdf"} | CONVERTIBLE_EXTENSIONS


def detect_format(filename: str) -> str:
    """Detect file format from filename extension.

    Args:
        filename: The filename to analyze.

    Returns:
        The file extension (e.g., '.pdf', '.docx').

    Raises:
        UnsupportedFormatError: If the file format is not supported.

    """
    ext = Path(filename).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise UnsupportedFormatError(
            f"Unsupported file format: {ext}. "
            f"Supported formats: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
        )
    return ext


def is_office_document(filename: str) -> bool:
    """Check if the file is an Office or ODF document.

    Args:
        filename: The filename to check.

    Returns:
        True if the file is an Office or ODF document, False otherwise.

    """
    try:
        ext = detect_format(filename)
        return ext in DOCUMENT_EXTENSIONS
    except UnsupportedFormatError:
        return False


def is_image_file(filename: str) -> bool:
    """Check if the file is a supported image format.

    Args:
        filename: The filename to check.

    Returns:
        True if the file is a supported image format, False otherwise.

    """
    try:
        ext = detect_format(filename)
        return ext in IMAGE_EXTENSIONS
    except UnsupportedFormatError:
        return False


def convert_office_to_pdf(
    input_file: Path,
    output_file: Path,
    progress_callback: Callable[[ProgressInfo], None] | None = None,
) -> None:
    """Convert Office or ODF document to PDF using LibreOffice.

    Args:
        input_file: Path to the document file (.docx, .pptx, .xlsx, .odt, .ods, .odp).
        output_file: Path where the PDF should be written.
        progress_callback: Optional callback for progress updates.

    Raises:
        FileNotFoundError: If the input file does not exist.
        OfficeConversionError: If the conversion fails.

    """
    if not input_file.exists():
        raise FileNotFoundError(f"Input file does not exist: {input_file}")

    logger.info(f"Converting Office document to PDF: {input_file}")
    logger.debug(f"Output directory: {output_file.parent}")

    # Send initial progress if callback provided
    if progress_callback:
        progress_callback(
            ProgressInfo(
                step="Office conversion",
                current=0,
                total=100,
                percentage=0.0,
                message="Converting Office document to PDF...",
            )
        )

    try:
        # Start LibreOffice conversion in background
        start_time = time.time()
        process = subprocess.Popen(
            [
                "libreoffice",
                "--headless",
                "--convert-to",
                "pdf",
                "--outdir",
                str(output_file.parent),
                str(input_file),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        # Poll process and send progress updates
        timeout = 300  # 5 minutes
        update_interval = 2  # Update every 2 seconds
        last_update = start_time

        while process.poll() is None:
            elapsed = time.time() - start_time
            if elapsed > timeout:
                process.kill()
                raise OfficeConversionError("Conversion timeout after 300 seconds")

            # Send progress update
            if progress_callback and (time.time() - last_update) >= update_interval:
                # Estimate progress (0-10% range, linear based on time)
                percentage = min(10.0, (elapsed / timeout) * 10)
                progress_callback(
                    ProgressInfo(
                        step="Office conversion",
                        current=int(percentage),
                        total=100,
                        percentage=percentage,
                        message=(
                            f"Converting Office document to PDF... "
                            f"({int(elapsed)}s)"
                        ),
                    )
                )
                last_update = time.time()

            time.sleep(0.5)

        # Get result
        stdout, stderr = process.communicate()
        result = process

        logger.debug(f"LibreOffice exit code: {result.returncode}")
        if stdout:
            logger.debug(f"LibreOffice stdout: {stdout}")
        if stderr:
            logger.debug(f"LibreOffice stderr: {stderr}")

        if result.returncode != 0:
            logger.error(
                f"LibreOffice conversion failed with exit code {result.returncode}: "
                f"{stderr}"
            )
            raise OfficeConversionError(f"LibreOffice conversion failed: {stderr}")

        # LibreOffice outputs the PDF with the same base name as input
        # e.g., input.docx -> input.pdf
        intermediate_pdf = input_file.parent / f"{input_file.stem}.pdf"

        if not intermediate_pdf.exists():
            raise OfficeConversionError(
                f"LibreOffice did not produce output PDF: {intermediate_pdf}"
            )

        # Move the PDF to the desired output location
        intermediate_pdf.rename(output_file)
        logger.info(f"Successfully converted to PDF: {output_file}")

        # Send final progress
        if progress_callback:
            progress_callback(
                ProgressInfo(
                    step="Office conversion",
                    current=10,
                    total=100,
                    percentage=10.0,
                    message="Office document converted to PDF",
                )
            )

    except OfficeConversionError:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during Office conversion: {e}")
        raise OfficeConversionError(f"Conversion failed: {e}") from e
