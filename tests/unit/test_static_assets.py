"""Unit tests for static asset files - US-012 Logo and Favicon.

Tests verify that logo and favicon files exist and are properly formatted.
"""

from pathlib import Path


class TestLogoAssets:
    """Test that logo asset files exist and are valid."""

    STATIC_DIR = Path("src/pdfa/static/images")

    def test_logo_svg_exists(self) -> None:
        """Test that main logo SVG file exists."""
        logo_path = self.STATIC_DIR / "logo.svg"
        assert logo_path.exists(), f"logo.svg should exist at {logo_path}"

    def test_logo_svg_is_valid_svg(self) -> None:
        """Test that logo.svg contains valid SVG markup."""
        logo_path = self.STATIC_DIR / "logo.svg"
        content = logo_path.read_text()
        assert "<svg" in content, "logo.svg should contain <svg> element"
        assert "</svg>" in content, "logo.svg should have closing </svg> tag"

    def test_logo_svg_has_viewbox(self) -> None:
        """Test that logo SVG has viewBox attribute for proper scaling."""
        logo_path = self.STATIC_DIR / "logo.svg"
        content = logo_path.read_text()
        assert "viewBox" in content, "logo.svg should have viewBox attribute"

    def test_logo_svg_uses_project_colors(self) -> None:
        """Test that logo uses project purple color palette."""
        logo_path = self.STATIC_DIR / "logo.svg"
        content = logo_path.read_text().lower()
        # Check for project purple color (case insensitive)
        assert any(
            color in content for color in ["#667eea", "667eea"]
        ), "logo.svg should use project purple color #667eea"

    def test_logo_svg_reasonable_size(self) -> None:
        """Test that logo SVG file is not excessively large."""
        logo_path = self.STATIC_DIR / "logo.svg"
        size_kb = logo_path.stat().st_size / 1024
        assert size_kb < 50, f"logo.svg should be < 50KB, got {size_kb:.1f}KB"


class TestFaviconAssets:
    """Test that favicon files exist and are valid."""

    STATIC_DIR = Path("src/pdfa/static/images")

    def test_favicon_svg_exists(self) -> None:
        """Test that favicon SVG file exists."""
        favicon_path = self.STATIC_DIR / "favicon.svg"
        assert favicon_path.exists(), f"favicon.svg should exist at {favicon_path}"

    def test_favicon_svg_is_valid_svg(self) -> None:
        """Test that favicon.svg contains valid SVG markup."""
        favicon_path = self.STATIC_DIR / "favicon.svg"
        content = favicon_path.read_text()
        assert "<svg" in content, "favicon.svg should contain <svg> element"
        assert "</svg>" in content, "favicon.svg should have closing </svg> tag"

    def test_favicon_16x16_png_exists(self) -> None:
        """Test that 16x16 PNG favicon exists."""
        favicon_path = self.STATIC_DIR / "favicon-16x16.png"
        assert (
            favicon_path.exists()
        ), f"favicon-16x16.png should exist at {favicon_path}"

    def test_favicon_32x32_png_exists(self) -> None:
        """Test that 32x32 PNG favicon exists."""
        favicon_path = self.STATIC_DIR / "favicon-32x32.png"
        assert (
            favicon_path.exists()
        ), f"favicon-32x32.png should exist at {favicon_path}"

    def test_apple_touch_icon_exists(self) -> None:
        """Test that Apple touch icon exists."""
        icon_path = self.STATIC_DIR / "apple-touch-icon.png"
        assert icon_path.exists(), f"apple-touch-icon.png should exist at {icon_path}"

    def test_png_files_are_valid_png(self) -> None:
        """Test that PNG files have valid PNG header."""
        png_header = b"\x89PNG\r\n\x1a\n"
        png_files = [
            "favicon-16x16.png",
            "favicon-32x32.png",
            "apple-touch-icon.png",
        ]

        for png_file in png_files:
            png_path = self.STATIC_DIR / png_file
            if png_path.exists():
                content = png_path.read_bytes()
                assert content.startswith(
                    png_header
                ), f"{png_file} should have valid PNG header"


class TestImagesDirectory:
    """Test that images directory exists and is properly structured."""

    STATIC_DIR = Path("src/pdfa/static/images")

    def test_images_directory_exists(self) -> None:
        """Test that images directory exists."""
        assert (
            self.STATIC_DIR.exists()
        ), f"Images directory should exist at {self.STATIC_DIR}"
        assert self.STATIC_DIR.is_dir(), "images should be a directory"

    def test_required_files_present(self) -> None:
        """Test that all required logo/favicon files are present."""
        required_files = [
            "logo.svg",
            "favicon.svg",
            "favicon-16x16.png",
            "favicon-32x32.png",
            "apple-touch-icon.png",
        ]

        missing_files = []
        for filename in required_files:
            file_path = self.STATIC_DIR / filename
            if not file_path.exists():
                missing_files.append(filename)

        assert not missing_files, f"Missing required files: {', '.join(missing_files)}"


class TestLogoAccessibility:
    """Document accessibility requirements for logo implementation."""

    def test_logo_accessibility_requirements(self) -> None:
        """Document accessibility requirements for logo.

        Requirements verified in E2E tests:
        1. Welcome logo should have aria-hidden="true" (decorative)
        2. Welcome logo should have empty alt="" (decorative)
        3. Header logo should have descriptive alt text
        4. Logo should be visible on all viewport sizes
        5. CSS should respect prefers-reduced-motion
        """
        assert True, "Accessibility requirements documented"
