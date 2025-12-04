"""Tests for image conversion functionality."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from pdfa.exceptions import UnsupportedFormatError
from pdfa.image_converter import (
    SUPPORTED_IMAGE_FORMATS,
    convert_image_to_pdf,
    is_image_file,
)


class TestIsImageFile:
    """Tests for is_image_file function."""

    def test_is_image_jpg(self):
        """Test that .jpg files are recognized as images."""
        assert is_image_file("photo.jpg") is True
        assert is_image_file("photo.JPG") is True
        assert is_image_file("photo.jpeg") is True
        assert is_image_file("photo.JPEG") is True

    def test_is_image_png(self):
        """Test that .png files are recognized as images."""
        assert is_image_file("image.png") is True
        assert is_image_file("image.PNG") is True

    def test_is_image_tiff(self):
        """Test that .tiff files are recognized as images."""
        assert is_image_file("scan.tiff") is True
        assert is_image_file("scan.tif") is True
        assert is_image_file("scan.TIFF") is True

    def test_is_image_bmp(self):
        """Test that .bmp files are recognized as images."""
        assert is_image_file("bitmap.bmp") is True
        assert is_image_file("bitmap.BMP") is True

    def test_is_image_gif(self):
        """Test that .gif files are recognized as images."""
        assert is_image_file("animation.gif") is True
        assert is_image_file("animation.GIF") is True

    def test_is_not_image_pdf(self):
        """Test that PDF files are not recognized as images."""
        assert is_image_file("document.pdf") is False

    def test_is_not_image_office(self):
        """Test that Office files are not recognized as images."""
        assert is_image_file("document.docx") is False
        assert is_image_file("slides.pptx") is False
        assert is_image_file("spreadsheet.xlsx") is False

    def test_is_not_image_unknown(self):
        """Test that unknown formats are not recognized as images."""
        assert is_image_file("file.txt") is False
        assert is_image_file("archive.zip") is False


class TestConvertImageToPdf:
    """Tests for convert_image_to_pdf function."""

    def test_convert_missing_input_file(self, tmp_path):
        """Test that conversion fails with FileNotFoundError for missing file."""
        input_file = tmp_path / "nonexistent.jpg"
        output_file = tmp_path / "output.pdf"

        with pytest.raises(FileNotFoundError, match="Input image does not exist"):
            convert_image_to_pdf(input_file, output_file)

    def test_convert_unsupported_format(self, tmp_path):
        """Test conversion fails with UnsupportedFormatError for unsupported format."""
        input_file = tmp_path / "file.txt"
        input_file.write_text("not an image")
        output_file = tmp_path / "output.pdf"

        with pytest.raises(UnsupportedFormatError, match="Unsupported image format"):
            convert_image_to_pdf(input_file, output_file)

    @patch("pdfa.image_converter.img2pdf.convert")
    def test_convert_success(self, mock_convert, tmp_path):
        """Test successful image to PDF conversion."""
        # Create a dummy input image
        input_file = tmp_path / "image.jpg"
        input_file.write_bytes(b"fake image data")

        output_file = tmp_path / "output.pdf"

        # Mock img2pdf.convert to return fake PDF data
        mock_convert.return_value = b"%PDF-1.4 fake pdf"

        convert_image_to_pdf(input_file, output_file)

        # Check that output file was created
        assert output_file.exists()
        assert output_file.read_bytes() == b"%PDF-1.4 fake pdf"

        # Check that img2pdf.convert was called with correct path
        mock_convert.assert_called_once_with(str(input_file))

    @patch("pdfa.image_converter.img2pdf.convert")
    def test_convert_creates_output_directory(self, mock_convert, tmp_path):
        """Test that convert_image_to_pdf creates output directory if needed."""
        input_file = tmp_path / "image.png"
        input_file.write_bytes(b"fake image data")

        # Output in a non-existent subdirectory
        output_dir = tmp_path / "subdir"
        output_file = output_dir / "output.pdf"

        mock_convert.return_value = b"%PDF-1.4 fake pdf"

        convert_image_to_pdf(input_file, output_file)

        # Check that directory was created
        assert output_dir.exists()
        assert output_file.exists()

    @patch("pdfa.image_converter.img2pdf.convert")
    def test_convert_different_formats(self, mock_convert, tmp_path):
        """Test conversion works with different image formats."""
        mock_convert.return_value = b"%PDF-1.4 fake pdf"

        for ext in SUPPORTED_IMAGE_FORMATS:
            input_file = tmp_path / f"image{ext}"
            input_file.write_bytes(b"fake image data")
            output_file = tmp_path / f"output{ext}.pdf"

            convert_image_to_pdf(input_file, output_file)

            assert output_file.exists()
            mock_convert.reset_mock()

    @patch("pdfa.image_converter.img2pdf.convert")
    def test_convert_exception_handling(self, mock_convert, tmp_path):
        """Test that exceptions from img2pdf are properly raised."""
        input_file = tmp_path / "image.jpg"
        input_file.write_bytes(b"fake image data")
        output_file = tmp_path / "output.pdf"

        # Make img2pdf.convert raise an exception
        mock_convert.side_effect = Exception("img2pdf failed")

        with pytest.raises(Exception, match="img2pdf failed"):
            convert_image_to_pdf(input_file, output_file)


class TestSupportedImageFormats:
    """Test the SUPPORTED_IMAGE_FORMATS constant."""

    def test_supported_formats_contains_common_formats(self):
        """Test that SUPPORTED_IMAGE_FORMATS contains all common image formats."""
        expected_formats = {".jpg", ".jpeg", ".png", ".tiff", ".tif", ".bmp", ".gif"}
        assert SUPPORTED_IMAGE_FORMATS == expected_formats
