"""Command-line interface for converting PDFs to PDF/A using OCRmyPDF."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

import ocrmypdf
from ocrmypdf import exceptions as ocrmypdf_exceptions


def build_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser for the CLI."""
    parser = argparse.ArgumentParser(
        prog="pdfa",
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
    return parser


def convert_to_pdfa(
    input_pdf: Path,
    output_pdf: Path,
    *,
    language: str,
    pdfa_level: str,
) -> None:
    """Convert a PDF to PDF/A using OCRmyPDF."""
    if not input_pdf.exists():
        raise FileNotFoundError(f"Input file does not exist: {input_pdf}")

    output_pdf.parent.mkdir(parents=True, exist_ok=True)
    output_type = f"pdfa-{pdfa_level}"

    ocrmypdf.ocr(
        str(input_pdf),
        str(output_pdf),
        language=language,
        output_type=output_type,
        force_ocr=True,
    )


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
