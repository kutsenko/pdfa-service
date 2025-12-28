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


def convert_images_to_pdf(
    input_images: list[Path],
    output_pdf: Path,
    page_order: list[int] | None = None,
) -> None:
    """Convert multiple image files to a single multi-page PDF.

    Args:
        input_images: List of paths to input image files (in order).
        output_pdf: Path for the output PDF file.
        page_order: Optional reordering of pages
            (e.g., [0, 2, 1] to swap pages 2 and 3).

    Raises:
        ValueError: If input_images is empty.
        FileNotFoundError: If any input image does not exist.
        UnsupportedFormatError: If any image format is not supported.
        Exception: If conversion fails.

    """
    if not input_images:
        logger.error("No input images provided")
        raise ValueError("input_images cannot be empty")

    # Validate all images exist and are supported formats
    for i, img_path in enumerate(input_images):
        if not img_path.exists():
            logger.error(f"Input image {i} does not exist: {img_path}")
            raise FileNotFoundError(f"Input image does not exist: {img_path}")

        extension = img_path.suffix.lower()
        if extension not in SUPPORTED_IMAGE_FORMATS:
            logger.error(f"Unsupported image format for image {i}: {extension}")
            raise UnsupportedFormatError(
                f"Unsupported image format: {extension}. "
                f"Supported formats: {', '.join(sorted(SUPPORTED_IMAGE_FORMATS))}"
            )

    # Apply page ordering if specified
    ordered_images = input_images
    if page_order is not None:
        if len(page_order) != len(input_images):
            raise ValueError("page_order must have same length as input_images")
        ordered_images = [input_images[i] for i in page_order]
        logger.info(f"Applying page order: {page_order}")

    logger.info(
        f"Converting {len(ordered_images)} images to multi-page PDF: {output_pdf}"
    )

    try:
        # Create output directory if needed
        output_pdf.parent.mkdir(parents=True, exist_ok=True)

        # Convert images to single multi-page PDF
        # img2pdf supports multiple images natively
        with open(output_pdf, "wb") as pdf_file:
            pdf_file.write(img2pdf.convert([str(img) for img in ordered_images]))

        logger.info(
            f"Successfully converted {len(ordered_images)} images to PDF: {output_pdf}"
        )

    except Exception as e:
        logger.error(f"Multi-image to PDF conversion failed: {e}", exc_info=True)
        raise


def convert_image_to_pdf(input_image: Path, output_pdf: Path) -> None:
    """Convert a single image file to PDF.

    Args:
        input_image: Path to the input image file.
        output_pdf: Path for the output PDF file.

    Raises:
        FileNotFoundError: If the input image does not exist.
        UnsupportedFormatError: If the image format is not supported.
        Exception: If conversion fails.

    """
    # Delegate to multi-image converter for consistency
    convert_images_to_pdf([input_image], output_pdf)
