"""E2E tests for Logo and Favicon - US-012.

Tests verify that logo and favicon are properly integrated and accessible.
"""

import pytest
from playwright.sync_api import Page, expect

pytestmark = [pytest.mark.e2e, pytest.mark.playwright]


class TestFavicon:
    """Test favicon presence and accessibility."""

    def test_favicon_svg_link_in_head(self, page: Page) -> None:
        """Test that SVG favicon link is present in HTML head."""
        page.goto("http://localhost:8001")

        # Check for SVG favicon
        svg_favicon = page.locator('link[rel="icon"][type="image/svg+xml"]')
        expect(svg_favicon).to_have_count(1)
        expect(svg_favicon).to_have_attribute("href", "/static/images/favicon.svg")

    def test_favicon_png_links_in_head(self, page: Page) -> None:
        """Test that PNG favicon fallback links are present."""
        page.goto("http://localhost:8001")

        # Check for 32x32 PNG favicon
        png_32 = page.locator('link[rel="icon"][sizes="32x32"]')
        expect(png_32).to_have_count(1)
        expect(png_32).to_have_attribute("href", "/static/images/favicon-32x32.png")

        # Check for 16x16 PNG favicon
        png_16 = page.locator('link[rel="icon"][sizes="16x16"]')
        expect(png_16).to_have_count(1)
        expect(png_16).to_have_attribute("href", "/static/images/favicon-16x16.png")

    def test_apple_touch_icon_in_head(self, page: Page) -> None:
        """Test that Apple touch icon link is present."""
        page.goto("http://localhost:8001")

        apple_icon = page.locator('link[rel="apple-touch-icon"]')
        expect(apple_icon).to_have_count(1)
        expect(apple_icon).to_have_attribute(
            "href", "/static/images/apple-touch-icon.png"
        )

    def test_favicon_svg_file_accessible(self, page: Page) -> None:
        """Test that favicon SVG file loads successfully."""
        response = page.goto("http://localhost:8001/static/images/favicon.svg")
        assert response is not None
        assert response.status == 200
        content_type = response.headers.get("content-type", "")
        assert "svg" in content_type or "xml" in content_type

    def test_favicon_png_files_accessible(self, page: Page) -> None:
        """Test that PNG favicon files load successfully."""
        base_url = "http://localhost:8001"
        png_files = [
            "/static/images/favicon-16x16.png",
            "/static/images/favicon-32x32.png",
            "/static/images/apple-touch-icon.png",
        ]

        for png_path in png_files:
            response = page.request.get(f"{base_url}{png_path}")
            assert response.status == 200, f"Failed to load {png_path}"
            content_type = response.headers.get("content-type", "")
            assert "png" in content_type, f"Wrong content type for {png_path}"


class TestWelcomeLogo:
    """Test logo on welcome screen."""

    def test_welcome_screen_has_logo_element(self, page: Page) -> None:
        """Test welcome screen has logo element (may be hidden if auth disabled)."""
        page.goto("http://localhost:8001")

        # Welcome logo element should exist in DOM
        welcome_logo = page.locator(".welcome-logo")
        expect(welcome_logo).to_have_count(1)
        expect(welcome_logo).to_have_attribute("src", "/static/images/logo.svg")

    def test_welcome_logo_has_aria_hidden(self, page: Page) -> None:
        """Test that welcome logo is hidden from screen readers (decorative)."""
        page.goto("http://localhost:8001")

        welcome_logo = page.locator(".welcome-logo")
        expect(welcome_logo).to_have_attribute("aria-hidden", "true")

    def test_welcome_logo_has_empty_alt(self, page: Page) -> None:
        """Test that welcome logo has empty alt text (decorative image)."""
        page.goto("http://localhost:8001")

        welcome_logo = page.locator(".welcome-logo")
        alt_text = welcome_logo.get_attribute("alt")
        assert alt_text == "", "Decorative logo should have empty alt text"

    def test_emoji_icon_not_present(self, page: Page) -> None:
        """Test that old emoji icon class is no longer used."""
        page.goto("http://localhost:8001")

        # Old welcome-icon class should not exist
        emoji_icon = page.locator(".welcome-icon")
        expect(emoji_icon).to_have_count(0)


class TestHeaderLogo:
    """Test logo in header."""

    def test_header_displays_logo(self, page: Page) -> None:
        """Test that header contains logo alongside title."""
        page.goto("http://localhost:8001")

        # Header logo should be present
        header_logo = page.locator(".header-logo")
        expect(header_logo).to_be_visible()
        expect(header_logo).to_have_attribute("src", "/static/images/logo.svg")

    def test_header_logo_has_alt_text(self, page: Page) -> None:
        """Test that header logo has appropriate alt text."""
        page.goto("http://localhost:8001")

        header_logo = page.locator(".header-logo")
        alt_text = header_logo.get_attribute("alt")
        assert alt_text is not None
        assert len(alt_text) > 0, "Header logo should have descriptive alt text"

    def test_header_title_visible(self, page: Page) -> None:
        """Test that header title is still visible alongside logo."""
        page.goto("http://localhost:8001")

        # Title in header should contain "PDF/A Converter"
        header_title = page.locator(".header h1.header-with-logo")
        expect(header_title).to_be_visible()
        title_text = header_title.inner_text()
        assert "PDF/A" in title_text


class TestLogoFile:
    """Test logo file properties."""

    def test_logo_svg_file_accessible(self, page: Page) -> None:
        """Test that main logo SVG file loads successfully."""
        response = page.goto("http://localhost:8001/static/images/logo.svg")
        assert response is not None
        assert response.status == 200
        content_type = response.headers.get("content-type", "")
        assert "svg" in content_type or "xml" in content_type

    def test_logo_svg_has_viewbox(self, page: Page) -> None:
        """Test that logo SVG has viewBox for proper scaling."""
        response = page.goto("http://localhost:8001/static/images/logo.svg")
        assert response is not None
        content = response.text()
        assert "viewBox" in content, "Logo SVG should have viewBox attribute"

    def test_logo_uses_project_colors(self, page: Page) -> None:
        """Test that logo uses project color palette."""
        response = page.goto("http://localhost:8001/static/images/logo.svg")
        assert response is not None
        content = response.text().lower()
        # Check for project purple color
        assert any(
            color in content for color in ["#667eea", "667eea"]
        ), "Logo should use project purple color"


class TestResponsiveDesign:
    """Test logo responsive behavior."""

    def test_header_logo_visible_on_mobile_viewport(self, page: Page) -> None:
        """Test that header logo is visible on mobile viewport."""
        page.set_viewport_size({"width": 375, "height": 667})
        page.goto("http://localhost:8001")

        # Header logo should be visible (header is always shown when auth disabled)
        header_logo = page.locator(".header-logo")
        expect(header_logo).to_be_visible()

    def test_header_logo_visible_on_tablet_viewport(self, page: Page) -> None:
        """Test that header logo is visible on tablet viewport."""
        page.set_viewport_size({"width": 768, "height": 1024})
        page.goto("http://localhost:8001")

        header_logo = page.locator(".header-logo")
        expect(header_logo).to_be_visible()

    def test_header_logo_visible_on_desktop_viewport(self, page: Page) -> None:
        """Test that header logo is visible on desktop viewport."""
        page.set_viewport_size({"width": 1920, "height": 1080})
        page.goto("http://localhost:8001")

        header_logo = page.locator(".header-logo")
        expect(header_logo).to_be_visible()


class TestMobileCameraLogo:
    """Test logo in mobile camera template."""

    def test_mobile_camera_has_favicon(self, page: Page) -> None:
        """Test that mobile camera page has favicon links."""
        page.goto("http://localhost:8001/mobile/camera")

        # Check for at least one favicon link
        favicon_count = page.locator('link[rel="icon"]').count()
        assert favicon_count > 0, "Mobile camera page should have favicon links"

    def test_mobile_camera_has_logo(self, page: Page) -> None:
        """Test that mobile camera page displays logo."""
        page.goto("http://localhost:8001/mobile/camera")

        # Logo should be present in mobile header
        mobile_logo = page.locator(".mobile-logo")
        expect(mobile_logo).to_be_visible()
