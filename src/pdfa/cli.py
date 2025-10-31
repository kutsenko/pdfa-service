"""Command-line interface for converting PDFs to PDF/A using OCRmyPDF."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from ocrmypdf import exceptions as ocrmypdf_exceptions

from pdfa.converter import convert_to_pdfa


def build_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser for the CLI."""
    parser = argparse.ArgumentParser(
        prog="pdfa-cli",
        description="Convert PDF files to PDF/A-2 with OCR using OCRmyPDF.",
    )
    parser.add_argument(
        "input_pdf",
        type=Path,
        help="Path to the input PDF file to convert.",
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
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Entrypoint for the CLI."""
    parser = build_parser()
    args = parser.parse_args(None if argv is None else list(argv))
    try:
        convert_to_pdfa(
            args.input_pdf,
            args.output_pdf,
            language=args.language,
            pdfa_level=args.pdfa_level,
            ocr_enabled=not args.no_ocr,
        )
    except FileNotFoundError as error:
        print(error, file=sys.stderr)
        return 1
    except ocrmypdf_exceptions.ExitCodeException as error:
        exit_code = getattr(error, "exit_code", 1)
        print(f"OCRmyPDF failed: {error}", file=sys.stderr)
        return exit_code

    print(f"Successfully created PDF/A file at {args.output_pdf}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
