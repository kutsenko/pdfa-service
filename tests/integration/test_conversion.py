"""Integration tests that exercise PDF conversion via OCRmyPDF."""

from __future__ import annotations

import shutil

import pytest
from ocrmypdf.pdfa import file_claims_pdfa
from PIL import Image, ImageDraw

from pdfa import cli

REQUIRED_BINARIES = ("tesseract", "gs")

pytestmark = [
    pytest.mark.skipif(
        any(shutil.which(binary) is None for binary in REQUIRED_BINARIES),
        reason="Integration tests require Tesseract and Ghostscript binaries.",
    ),
    pytest.mark.timeout(120),
]


def create_sample_pdf(output_path: str, *, text: str) -> None:
    """Create a simple single-page PDF containing the provided text."""
    image = Image.new("RGB", (300, 200), color="white")
    drawer = ImageDraw.Draw(image)
    drawer.text((10, 90), text, fill="black")
    image.save(output_path, "PDF")


def test_cli_converts_multiple_pdfs(tmp_path) -> None:
    """End-to-end run of the CLI converting multiple PDFs to PDF/A."""
    output_paths = []
    for index in range(2):
        input_pdf = tmp_path / f"input_{index}.pdf"
        output_pdf = tmp_path / f"output_{index}.pdf"
        create_sample_pdf(str(input_pdf), text=f"Hello {index}")

        exit_code = cli.main(
            [
                str(input_pdf),
                str(output_pdf),
                "--language",
                "eng",
                "--pdfa-level",
                "2",
            ]
        )

        assert exit_code == 0
        assert output_pdf.exists()
        assert output_pdf.stat().st_size > 0

        output_paths.append(output_pdf)

    for output_pdf in output_paths:
        info = file_claims_pdfa(output_pdf)
        assert info["pass"] is True
        assert info["conformance"].startswith("PDF/A-2")
