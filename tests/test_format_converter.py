"""Tests for format detection and Office document conversion."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from pdfa.exceptions import OfficeConversionError, UnsupportedFormatError
from pdfa.format_converter import (
    convert_office_to_pdf,
    detect_format,
    is_image_file,
    is_office_document,
)


class TestDetectFormat:
    """Tests for format detection."""

    def test_detect_pdf_format(self) -> None:
        """detect_format should recognize PDF files."""
        assert detect_format("document.pdf") == ".pdf"
        assert detect_format("file.PDF") == ".pdf"

    def test_detect_docx_format(self) -> None:
        """detect_format should recognize DOCX files."""
        assert detect_format("document.docx") == ".docx"
        assert detect_format("file.DOCX") == ".docx"

    def test_detect_pptx_format(self) -> None:
        """detect_format should recognize PPTX files."""
        assert detect_format("presentation.pptx") == ".pptx"
        assert detect_format("slides.PPTX") == ".pptx"

    def test_detect_xlsx_format(self) -> None:
        """detect_format should recognize XLSX files."""
        assert detect_format("spreadsheet.xlsx") == ".xlsx"
        assert detect_format("data.XLSX") == ".xlsx"

    def test_detect_jpg_format(self) -> None:
        """detect_format should recognize JPG/JPEG files."""
        assert detect_format("photo.jpg") == ".jpg"
        assert detect_format("photo.JPG") == ".jpg"
        assert detect_format("photo.jpeg") == ".jpeg"
        assert detect_format("photo.JPEG") == ".jpeg"

    def test_detect_png_format(self) -> None:
        """detect_format should recognize PNG files."""
        assert detect_format("image.png") == ".png"
        assert detect_format("image.PNG") == ".png"

    def test_detect_tiff_format(self) -> None:
        """detect_format should recognize TIFF files."""
        assert detect_format("scan.tiff") == ".tiff"
        assert detect_format("scan.TIFF") == ".tiff"
        assert detect_format("scan.tif") == ".tif"

    def test_detect_bmp_format(self) -> None:
        """detect_format should recognize BMP files."""
        assert detect_format("bitmap.bmp") == ".bmp"
        assert detect_format("bitmap.BMP") == ".bmp"

    def test_detect_gif_format(self) -> None:
        """detect_format should recognize GIF files."""
        assert detect_format("animation.gif") == ".gif"
        assert detect_format("animation.GIF") == ".gif"

    def test_detect_unsupported_format(self) -> None:
        """detect_format should raise error for unsupported formats."""
        with pytest.raises(UnsupportedFormatError):
            detect_format("document.txt")

    def test_detect_unknown_format(self) -> None:
        """detect_format should raise error for unknown formats."""
        with pytest.raises(UnsupportedFormatError):
            detect_format("document.doc")

    def test_detect_format_no_extension(self) -> None:
        """detect_format should raise error for files without extension."""
        with pytest.raises(UnsupportedFormatError):
            detect_format("document")


class TestIsOfficeDocument:
    """Tests for office document detection."""

    def test_is_office_docx(self) -> None:
        """is_office_document should return True for DOCX files."""
        assert is_office_document("document.docx") is True
        assert is_office_document("document.DOCX") is True

    def test_is_office_pptx(self) -> None:
        """is_office_document should return True for PPTX files."""
        assert is_office_document("presentation.pptx") is True
        assert is_office_document("presentation.PPTX") is True

    def test_is_office_xlsx(self) -> None:
        """is_office_document should return True for XLSX files."""
        assert is_office_document("spreadsheet.xlsx") is True
        assert is_office_document("spreadsheet.XLSX") is True

    def test_is_office_pdf(self) -> None:
        """is_office_document should return False for PDF files."""
        assert is_office_document("document.pdf") is False

    def test_is_office_image(self) -> None:
        """is_office_document should return False for image files."""
        assert is_office_document("photo.jpg") is False
        assert is_office_document("image.png") is False

    def test_is_office_invalid_format(self) -> None:
        """is_office_document should return False for unsupported formats."""
        assert is_office_document("document.txt") is False

    def test_is_office_no_extension(self) -> None:
        """is_office_document should return False for files without extension."""
        assert is_office_document("document") is False


class TestIsImageFile:
    """Tests for image file detection."""

    def test_is_image_jpg(self) -> None:
        """is_image_file should return True for JPG/JPEG files."""
        assert is_image_file("photo.jpg") is True
        assert is_image_file("photo.JPG") is True
        assert is_image_file("photo.jpeg") is True
        assert is_image_file("photo.JPEG") is True

    def test_is_image_png(self) -> None:
        """is_image_file should return True for PNG files."""
        assert is_image_file("image.png") is True
        assert is_image_file("image.PNG") is True

    def test_is_image_tiff(self) -> None:
        """is_image_file should return True for TIFF files."""
        assert is_image_file("scan.tiff") is True
        assert is_image_file("scan.tif") is True

    def test_is_image_bmp(self) -> None:
        """is_image_file should return True for BMP files."""
        assert is_image_file("bitmap.bmp") is True

    def test_is_image_gif(self) -> None:
        """is_image_file should return True for GIF files."""
        assert is_image_file("animation.gif") is True

    def test_is_image_pdf(self) -> None:
        """is_image_file should return False for PDF files."""
        assert is_image_file("document.pdf") is False

    def test_is_image_office(self) -> None:
        """is_image_file should return False for Office files."""
        assert is_image_file("document.docx") is False
        assert is_image_file("presentation.pptx") is False

    def test_is_image_invalid_format(self) -> None:
        """is_image_file should return False for unsupported formats."""
        assert is_image_file("document.txt") is False

    def test_is_image_no_extension(self) -> None:
        """is_image_file should return False for files without extension."""
        assert is_image_file("document") is False


class TestConvertOfficeToPdf:
    """Tests for Office to PDF conversion."""

    def test_convert_missing_input_file(self, tmp_path: Path) -> None:
        """convert_office_to_pdf should raise FileNotFoundError for missing files."""
        input_file = tmp_path / "missing.docx"
        output_file = tmp_path / "output.pdf"

        with pytest.raises(FileNotFoundError):
            convert_office_to_pdf(input_file, output_file)

    @patch("pdfa.format_converter.subprocess.Popen")
    def test_convert_success(self, mock_popen: MagicMock, tmp_path: Path) -> None:
        """convert_office_to_pdf should convert Office file to PDF."""
        # Create input file
        input_file = tmp_path / "document.docx"
        input_file.write_text("dummy content")

        output_file = tmp_path / "output.pdf"

        # Create intermediate PDF (what LibreOffice would produce)
        intermediate_pdf = tmp_path / "document.pdf"
        intermediate_pdf.write_bytes(b"%PDF-1.4 test")

        # Mock subprocess.Popen
        mock_process = MagicMock()
        mock_process.poll.return_value = 0  # Process finished
        mock_process.returncode = 0
        mock_process.communicate.return_value = ("", "")
        mock_popen.return_value = mock_process

        convert_office_to_pdf(input_file, output_file)

        # Verify subprocess was called correctly
        mock_popen.assert_called_once()
        call_args = mock_popen.call_args
        assert call_args[0][0][0] == "libreoffice"
        assert "--headless" in call_args[0][0]
        assert "--convert-to" in call_args[0][0]
        assert "pdf" in call_args[0][0]
        assert str(input_file) in call_args[0][0]

        # Verify output file exists
        assert output_file.exists()
        assert output_file.read_bytes() == b"%PDF-1.4 test"

    @patch("pdfa.format_converter.subprocess.Popen")
    def test_convert_libreoffice_failure(
        self, mock_popen: MagicMock, tmp_path: Path
    ) -> None:
        """convert_office_to_pdf should raise error on LibreOffice failure."""
        input_file = tmp_path / "document.docx"
        input_file.write_text("dummy content")

        output_file = tmp_path / "output.pdf"

        # Mock subprocess failure
        mock_process = MagicMock()
        mock_process.poll.return_value = 1  # Process finished with error
        mock_process.returncode = 1
        mock_process.communicate.return_value = ("", "LibreOffice error message")
        mock_popen.return_value = mock_process

        with pytest.raises(OfficeConversionError):
            convert_office_to_pdf(input_file, output_file)

    @patch("pdfa.format_converter.time.time")
    @patch("pdfa.format_converter.subprocess.Popen")
    def test_convert_timeout(
        self, mock_popen: MagicMock, mock_time: MagicMock, tmp_path: Path
    ) -> None:
        """convert_office_to_pdf should raise error on timeout."""
        input_file = tmp_path / "document.docx"
        input_file.write_text("dummy content")

        output_file = tmp_path / "output.pdf"

        # Mock time to simulate timeout (start at 0, then jump to 301 seconds)
        mock_time.side_effect = [
            0,
            0,
            0,
            301,
        ]  # start_time, last_update, elapsed check, elapsed > timeout

        # Mock subprocess that never finishes
        mock_process = MagicMock()
        mock_process.poll.return_value = None  # Process still running
        mock_process.kill = MagicMock()
        mock_popen.return_value = mock_process

        with pytest.raises(OfficeConversionError, match="timeout"):
            convert_office_to_pdf(input_file, output_file)

        # Verify process was killed
        mock_process.kill.assert_called_once()

    @patch("pdfa.format_converter.subprocess.Popen")
    def test_convert_missing_output_pdf(
        self, mock_popen: MagicMock, tmp_path: Path
    ) -> None:
        """Raise error if LibreOffice doesn't produce output PDF."""
        input_file = tmp_path / "document.docx"
        input_file.write_text("dummy content")

        output_file = tmp_path / "output.pdf"

        # Mock subprocess success but no output file
        mock_process = MagicMock()
        mock_process.poll.return_value = 0  # Process finished
        mock_process.returncode = 0
        mock_process.communicate.return_value = ("", "")
        mock_popen.return_value = mock_process

        with pytest.raises(OfficeConversionError):
            convert_office_to_pdf(input_file, output_file)
