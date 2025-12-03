"""Convert Office documents to PDF using LibreOffice."""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path

from pdfa.exceptions import OfficeConversionError, UnsupportedFormatError

logger = logging.getLogger(__name__)

# Supported Office formats
OFFICE_EXTENSIONS = {".docx", ".pptx", ".xlsx"}

# Supported Open Document Format (ODF)
ODF_EXTENSIONS = {".odt", ".ods", ".odp"}

# All document formats that require conversion to PDF
DOCUMENT_EXTENSIONS = OFFICE_EXTENSIONS | ODF_EXTENSIONS

# All supported formats
SUPPORTED_EXTENSIONS = {".pdf"} | DOCUMENT_EXTENSIONS


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


def convert_office_to_pdf(input_file: Path, output_file: Path) -> None:
    """Convert Office or ODF document to PDF using LibreOffice.

    Args:
        input_file: Path to the document file (.docx, .pptx, .xlsx, .odt, .ods, .odp).
        output_file: Path where the PDF should be written.

    Raises:
        FileNotFoundError: If the input file does not exist.
        OfficeConversionError: If the conversion fails.

    """
    if not input_file.exists():
        raise FileNotFoundError(f"Input file does not exist: {input_file}")

    logger.info(f"Converting Office document to PDF: {input_file}")
    logger.debug(f"Output directory: {output_file.parent}")

    try:
        # LibreOffice --convert-to outputs to the input file's parent directory
        result = subprocess.run(
            [
                "libreoffice",
                "--headless",
                "--convert-to",
                "pdf",
                "--outdir",
                str(output_file.parent),
                str(input_file),
            ],
            capture_output=True,
            text=True,
            timeout=300,  # 5 minutes timeout
            check=False,
        )

        logger.debug(f"LibreOffice exit code: {result.returncode}")
        if result.stdout:
            logger.debug(f"LibreOffice stdout: {result.stdout}")
        if result.stderr:
            logger.debug(f"LibreOffice stderr: {result.stderr}")

        if result.returncode != 0:
            logger.error(
                f"LibreOffice conversion failed with exit code {result.returncode}: "
                f"{result.stderr}"
            )
            raise OfficeConversionError(
                f"LibreOffice conversion failed: {result.stderr}"
            )

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

    except subprocess.TimeoutExpired as e:
        logger.error(f"LibreOffice conversion timed out: {e}")
        raise OfficeConversionError("Conversion timeout after 300 seconds") from e
    except Exception as e:
        logger.error(f"Unexpected error during Office conversion: {e}")
        raise OfficeConversionError(f"Conversion failed: {e}") from e
