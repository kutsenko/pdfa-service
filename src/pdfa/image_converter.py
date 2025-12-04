"""Convert image files to PDF format."""

from __future__ import annotations

import logging
from pathlib import Path

import img2pdf

from pdfa.exceptions import UnsupportedFormatError

logger = logging.getLogger(__name__)

# Supported image formats
SUPPORTED_IMAGE_FORMATS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".tiff",
    ".tif",
    ".bmp",
    ".gif",
}


def is_image_file(filename: str) -> bool:
    """Check if a file is a supported image format.

    Args:
        filename: Name of the file to check.

    Returns:
        True if the file is a supported image format, False otherwise.

    """
    extension = Path(filename).suffix.lower()
    return extension in SUPPORTED_IMAGE_FORMATS


def convert_image_to_pdf(input_image: Path, output_pdf: Path) -> None:
    """Convert an image file to PDF.

    Args:
        input_image: Path to the input image file.
        output_pdf: Path for the output PDF file.

    Raises:
        FileNotFoundError: If the input image does not exist.
        UnsupportedFormatError: If the image format is not supported.
        Exception: If conversion fails.

    """
    if not input_image.exists():
        logger.error(f"Input image does not exist: {input_image}")
        raise FileNotFoundError(f"Input image does not exist: {input_image}")

    # Check if format is supported
    extension = input_image.suffix.lower()
    if extension not in SUPPORTED_IMAGE_FORMATS:
        logger.error(f"Unsupported image format: {extension}")
        raise UnsupportedFormatError(
            f"Unsupported image format: {extension}. "
            f"Supported formats: {', '.join(sorted(SUPPORTED_IMAGE_FORMATS))}"
        )

    logger.info(f"Converting image to PDF: {input_image} -> {output_pdf}")

    try:
        # Create output directory if needed
        output_pdf.parent.mkdir(parents=True, exist_ok=True)

        # Convert image to PDF
        with open(output_pdf, "wb") as pdf_file:
            pdf_file.write(img2pdf.convert(str(input_image)))

        logger.info(f"Successfully converted image to PDF: {output_pdf}")

    except Exception as e:
        logger.error(f"Image to PDF conversion failed: {e}", exc_info=True)
        raise
