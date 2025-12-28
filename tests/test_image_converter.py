"""Tests for image conversion functionality."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from pdfa.exceptions import UnsupportedFormatError
from pdfa.image_converter import (
    SUPPORTED_IMAGE_FORMATS,
    convert_image_to_pdf,
    convert_images_to_pdf,
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

        # Check that img2pdf.convert was called with list (delegates to multi-image)
        mock_convert.assert_called_once_with([str(input_file)])

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


class TestConvertImagesToPdf:
    """Tests for convert_images_to_pdf function (multi-image support)."""

    def test_convert_empty_list(self, tmp_path):
        """Test that conversion fails with ValueError for empty image list."""
        output_file = tmp_path / "output.pdf"

        with pytest.raises(ValueError, match="input_images cannot be empty"):
            convert_images_to_pdf([], output_file)

    def test_convert_single_image(self, tmp_path):
        """Test converting single image to PDF (backward compatibility)."""
        input_file = tmp_path / "image.jpg"
        input_file.write_bytes(b"fake image data")
        output_file = tmp_path / "output.pdf"

        with patch("pdfa.image_converter.img2pdf.convert") as mock_convert:
            mock_convert.return_value = b"%PDF-1.4 fake pdf"
            convert_images_to_pdf([input_file], output_file)

            assert output_file.exists()
            mock_convert.assert_called_once_with([str(input_file)])

    def test_convert_three_images(self, tmp_path):
        """Test converting 3 images to single multi-page PDF."""
        images = [tmp_path / f"image{i}.jpg" for i in range(3)]
        for img in images:
            img.write_bytes(b"fake image data")

        output_file = tmp_path / "output.pdf"

        with patch("pdfa.image_converter.img2pdf.convert") as mock_convert:
            mock_convert.return_value = b"%PDF-1.4 fake 3-page pdf"
            convert_images_to_pdf(images, output_file)

            assert output_file.exists()
            assert output_file.read_bytes() == b"%PDF-1.4 fake 3-page pdf"
            # Verify img2pdf was called with all 3 images
            mock_convert.assert_called_once_with(
                [str(images[0]), str(images[1]), str(images[2])]
            )

    def test_convert_ten_images(self, tmp_path):
        """Test converting 10 images to single PDF."""
        images = [tmp_path / f"page{i:02d}.jpg" for i in range(10)]
        for img in images:
            img.write_bytes(b"fake image data")

        output_file = tmp_path / "output.pdf"

        with patch("pdfa.image_converter.img2pdf.convert") as mock_convert:
            mock_convert.return_value = b"%PDF-1.4 fake 10-page pdf"
            convert_images_to_pdf(images, output_file)

            assert output_file.exists()
            # Verify all 10 images were passed
            mock_convert.assert_called_once()
            call_args = mock_convert.call_args[0][0]
            assert len(call_args) == 10

    def test_convert_twenty_images(self, tmp_path):
        """Test converting 20 images to single PDF (stress test)."""
        images = [tmp_path / f"scan{i:03d}.png" for i in range(20)]
        for img in images:
            img.write_bytes(b"fake image data")

        output_file = tmp_path / "output.pdf"

        with patch("pdfa.image_converter.img2pdf.convert") as mock_convert:
            mock_convert.return_value = b"%PDF-1.4 fake 20-page pdf"
            convert_images_to_pdf(images, output_file)

            assert output_file.exists()
            # Verify all 20 images were passed
            call_args = mock_convert.call_args[0][0]
            assert len(call_args) == 20

    def test_convert_missing_input_file(self, tmp_path):
        """Test that conversion fails if any input image is missing."""
        image1 = tmp_path / "image1.jpg"
        image1.write_bytes(b"fake image data")
        image2 = tmp_path / "nonexistent.jpg"  # Does not exist
        image3 = tmp_path / "image3.jpg"
        image3.write_bytes(b"fake image data")

        output_file = tmp_path / "output.pdf"

        with pytest.raises(FileNotFoundError, match="Input image does not exist"):
            convert_images_to_pdf([image1, image2, image3], output_file)

    def test_convert_unsupported_format(self, tmp_path):
        """Test conversion fails if any image has unsupported format."""
        image1 = tmp_path / "image1.jpg"
        image1.write_bytes(b"fake image data")
        image2 = tmp_path / "document.txt"
        image2.write_text("not an image")

        output_file = tmp_path / "output.pdf"

        with pytest.raises(UnsupportedFormatError, match="Unsupported image format"):
            convert_images_to_pdf([image1, image2], output_file)

    def test_convert_with_page_reordering(self, tmp_path):
        """Test page reordering: [0, 1, 2] → [2, 0, 1]."""
        images = [tmp_path / f"image{i}.jpg" for i in range(3)]
        for img in images:
            img.write_bytes(b"fake image data")

        output_file = tmp_path / "output.pdf"

        with patch("pdfa.image_converter.img2pdf.convert") as mock_convert:
            mock_convert.return_value = b"%PDF-1.4 reordered pdf"

            # Reorder: pages [0, 1, 2] → [2, 0, 1]
            convert_images_to_pdf(images, output_file, page_order=[2, 0, 1])

            # Verify images were passed in reordered sequence
            mock_convert.assert_called_once_with(
                [str(images[2]), str(images[0]), str(images[1])]
            )

    def test_convert_page_order_length_mismatch(self, tmp_path):
        """Test that page_order must have same length as input_images."""
        images = [tmp_path / f"image{i}.jpg" for i in range(3)]
        for img in images:
            img.write_bytes(b"fake image data")

        output_file = tmp_path / "output.pdf"

        # page_order has only 2 elements but images has 3
        with pytest.raises(
            ValueError, match="page_order must have same length as input_images"
        ):
            convert_images_to_pdf(images, output_file, page_order=[0, 1])

    def test_convert_creates_output_directory(self, tmp_path):
        """Test that output directory is created if needed."""
        images = [tmp_path / f"image{i}.png" for i in range(2)]
        for img in images:
            img.write_bytes(b"fake image data")

        # Output in non-existent subdirectory
        output_dir = tmp_path / "subdir" / "nested"
        output_file = output_dir / "output.pdf"

        with patch("pdfa.image_converter.img2pdf.convert") as mock_convert:
            mock_convert.return_value = b"%PDF-1.4 fake pdf"
            convert_images_to_pdf(images, output_file)

            assert output_dir.exists()
            assert output_file.exists()

    def test_convert_mixed_image_formats(self, tmp_path):
        """Test conversion with mixed image formats (jpg, png, tiff)."""
        images = [
            tmp_path / "image1.jpg",
            tmp_path / "image2.png",
            tmp_path / "image3.tiff",
        ]
        for img in images:
            img.write_bytes(b"fake image data")

        output_file = tmp_path / "output.pdf"

        with patch("pdfa.image_converter.img2pdf.convert") as mock_convert:
            mock_convert.return_value = b"%PDF-1.4 mixed format pdf"
            convert_images_to_pdf(images, output_file)

            assert output_file.exists()
            # Verify all 3 different formats were accepted
            call_args = mock_convert.call_args[0][0]
            assert len(call_args) == 3

    def test_convert_exception_handling(self, tmp_path):
        """Test that exceptions from img2pdf are properly raised."""
        images = [tmp_path / f"image{i}.jpg" for i in range(2)]
        for img in images:
            img.write_bytes(b"fake image data")

        output_file = tmp_path / "output.pdf"

        with patch("pdfa.image_converter.img2pdf.convert") as mock_convert:
            mock_convert.side_effect = Exception("img2pdf conversion failed")

            with pytest.raises(Exception, match="img2pdf conversion failed"):
                convert_images_to_pdf(images, output_file)


class TestSupportedImageFormats:
    """Test the SUPPORTED_IMAGE_FORMATS constant."""

    def test_supported_formats_contains_common_formats(self):
        """Test that SUPPORTED_IMAGE_FORMATS contains all common image formats."""
        expected_formats = {".jpg", ".jpeg", ".png", ".tiff", ".tif", ".bmp", ".gif"}
        assert SUPPORTED_IMAGE_FORMATS == expected_formats
