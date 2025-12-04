"""Command-line interface for converting PDFs, Office, and ODF documents to PDF/A."""

from __future__ import annotations

import argparse
import logging
import sys
import uuid
from collections.abc import Sequence
from pathlib import Path
from tempfile import TemporaryDirectory

from ocrmypdf import exceptions as ocrmypdf_exceptions

from pdfa.compression_config import CompressionConfig
from pdfa.converter import convert_to_pdfa
from pdfa.exceptions import OfficeConversionError, UnsupportedFormatError
from pdfa.format_converter import (
    convert_office_to_pdf,
    is_image_file,
    is_office_document,
)
from pdfa.image_converter import convert_image_to_pdf
from pdfa.logging_config import configure_logging, get_logger

logger = get_logger(__name__)


def build_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser for the CLI."""
    parser = argparse.ArgumentParser(
        prog="pdfa-cli",
        description=(
            "Convert PDF, Office, ODF documents, and images to PDF/A "
            "with OCR using OCRmyPDF."
        ),
    )
    parser.add_argument(
        "input_file",
        type=Path,
        help=(
            "Path to input file (PDF, DOCX, PPTX, XLSX, ODT, ODS, ODP, "
            "JPG, PNG, TIFF, BMP, GIF) to convert"
        ),
    )
    parser.add_argument(
        "output_pdf",
        type=Path,
        help="Destination path for the generated PDF/A file.",
    )
    parser.add_argument(
        "-l",
        "--language",
        default="deu+eng",
        help=(
            "Tesseract language codes to use for OCR (e.g., 'eng', 'deu+eng'). "
            "Defaults to 'deu+eng'."
        ),
    )
    parser.add_argument(
        "--pdfa-level",
        choices=["1", "2", "3"],
        default="2",
        help="PDF/A compliance level to target. Defaults to '2'.",
    )
    parser.add_argument(
        "--no-ocr",
        action="store_true",
        help="Disable OCR and convert PDF to PDF/A without text recognition.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose (debug) logging output.",
    )
    parser.add_argument(
        "--log-file",
        type=Path,
        default=None,
        help="Write logs to a file in addition to stderr.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Entrypoint for the CLI."""
    parser = build_parser()
    args = parser.parse_args(None if argv is None else list(argv))

    # Configure logging based on command-line arguments
    log_level = logging.DEBUG if args.verbose else logging.INFO
    configure_logging(level=log_level, log_file=args.log_file)

    # Load compression configuration from environment variables
    compression_config = CompressionConfig.from_env()

    logger.info("Starting file to PDF/A conversion")
    logger.debug(
        f"Arguments: input={args.input_file}, output={args.output_pdf}, "
        f"language={args.language}, pdfa_level={args.pdfa_level}, "
        f"ocr_enabled={not args.no_ocr}"
    )
    logger.debug(
        f"Compression: DPI={compression_config.image_dpi}, "
        f"JPG quality={compression_config.jpg_quality}, "
        f"Optimize={compression_config.optimize}"
    )

    try:
        # Check if input file needs conversion
        is_office = is_office_document(args.input_file.name)
        is_image = is_image_file(args.input_file.name)

        # Convert Office documents or images to PDF if needed
        pdf_file = args.input_file
        temp_dir = None
        temp_input_file = None

        if is_office or is_image:
            file_type = "Office document" if is_office else "Image file"
            logger.info(
                f"{file_type} detected, converting to PDF: {args.input_file.name}"
            )
            # Use temporary directory with random filenames for security
            temp_dir = TemporaryDirectory()
            temp_dir_path = Path(temp_dir.name)

            # Copy input file to temp dir with random name
            original_ext = args.input_file.suffix.lower()
            random_input_name = f"{uuid.uuid4().hex}{original_ext}"
            temp_input_file = temp_dir_path / random_input_name

            logger.debug(f"Using random temporary input filename: {random_input_name}")
            temp_input_file.write_bytes(args.input_file.read_bytes())

            # Convert to PDF with random name
            random_pdf_name = f"{uuid.uuid4().hex}.pdf"
            pdf_file = temp_dir_path / random_pdf_name
            logger.debug(f"Using random temporary PDF filename: {random_pdf_name}")

            if is_office:
                convert_office_to_pdf(temp_input_file, pdf_file)
            else:  # is_image
                convert_image_to_pdf(temp_input_file, pdf_file)

        try:
            # Convert to PDF/A
            convert_to_pdfa(
                pdf_file,
                args.output_pdf,
                language=args.language,
                pdfa_level=args.pdfa_level,
                ocr_enabled=not args.no_ocr,
                compression_config=compression_config,
            )
        finally:
            # Clean up temporary directory if we created one
            if temp_dir is not None:
                temp_dir.cleanup()

    except FileNotFoundError as error:
        logger.error(f"File not found: {error}")
        print(error, file=sys.stderr)
        return 1
    except UnsupportedFormatError as error:
        logger.error(f"Unsupported file format: {error}")
        print(error, file=sys.stderr)
        return 1
    except OfficeConversionError as error:
        logger.error(f"Office conversion failed: {error}")
        print(f"Office conversion failed: {error}", file=sys.stderr)
        return 1
    except ocrmypdf_exceptions.ExitCodeException as error:
        exit_code = getattr(error, "exit_code", 1)
        logger.error(f"OCRmyPDF failed with exit code {exit_code}: {error}")
        print(f"OCRmyPDF failed: {error}", file=sys.stderr)
        return exit_code
    except Exception as error:
        logger.exception(f"Unexpected error during conversion: {error}")
        print(f"Error: {error}", file=sys.stderr)
        return 1

    logger.info(f"Successfully created PDF/A file at {args.output_pdf}")
    print(f"Successfully created PDF/A file at {args.output_pdf}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
