"""E2E tests for Tab Icons - Amber-Fossil Style.

Tests verify that tab icons are properly integrated, accessible,
and responsive (icon-only on mobile).
"""

import pytest
from playwright.sync_api import Page, expect

pytestmark = [pytest.mark.e2e, pytest.mark.playwright]


class TestTabIconPresence:
    """Test that all tab icons are present and accessible."""

    def test_converter_tab_has_icon(self, page: Page) -> None:
        """Test that converter tab has an icon."""
        page.goto("http://localhost:8001")

        icon = page.locator("#tab-konverter-btn .tab-icon")
        expect(icon).to_have_count(1)
        expect(icon).to_have_attribute("src", "/static/images/icons/icon-converter.svg")

    def test_camera_tab_has_icon(self, page: Page) -> None:
        """Test that camera tab has an icon."""
        page.goto("http://localhost:8001")

        icon = page.locator("#tab-kamera-btn .tab-icon")
        expect(icon).to_have_count(1)
        expect(icon).to_have_attribute("src", "/static/images/icons/icon-camera.svg")

    def test_jobs_tab_has_icon(self, page: Page) -> None:
        """Test that jobs tab has an icon."""
        page.goto("http://localhost:8001")

        icon = page.locator("#tab-jobs-btn .tab-icon")
        expect(icon).to_have_count(1)
        expect(icon).to_have_attribute("src", "/static/images/icons/icon-jobs.svg")

    def test_account_tab_has_icon(self, page: Page) -> None:
        """Test that account tab has an icon."""
        page.goto("http://localhost:8001")

        icon = page.locator("#tab-account-btn .tab-icon")
        expect(icon).to_have_count(1)
        expect(icon).to_have_attribute("src", "/static/images/icons/icon-account.svg")

    def test_docs_tab_has_icon(self, page: Page) -> None:
        """Test that documentation tab has an icon."""
        page.goto("http://localhost:8001")

        icon = page.locator("#tab-documentation-btn .tab-icon")
        expect(icon).to_have_count(1)
        expect(icon).to_have_attribute("src", "/static/images/icons/icon-docs.svg")

    def test_all_five_tab_icons_present(self, page: Page) -> None:
        """Test that all 5 tab icons are present."""
        page.goto("http://localhost:8001")

        icons = page.locator(".tab-icon")
        expect(icons).to_have_count(5)


class TestTabIconAccessibility:
    """Test tab icon accessibility attributes."""

    def test_tab_icons_are_decorative(self, page: Page) -> None:
        """Test that tab icons have aria-hidden (decorative)."""
        page.goto("http://localhost:8001")

        icons = page.locator(".tab-icon")
        for i in range(5):
            icon = icons.nth(i)
            expect(icon).to_have_attribute("aria-hidden", "true")

    def test_tab_icons_have_empty_alt(self, page: Page) -> None:
        """Test that tab icons have empty alt text."""
        page.goto("http://localhost:8001")

        icons = page.locator(".tab-icon")
        for i in range(5):
            icon = icons.nth(i)
            alt = icon.get_attribute("alt")
            assert alt == "", f"Tab icon {i} should have empty alt"

    def test_tab_buttons_have_title_for_tooltip(self, page: Page) -> None:
        """Test that tab buttons have title attribute for mobile tooltips."""
        page.goto("http://localhost:8001")

        expected_titles = ["Konverter", "Kamera", "Aufträge", "Konto", "Dokumentation"]
        buttons = page.locator(".tab-button")

        for i, expected in enumerate(expected_titles):
            button = buttons.nth(i)
            title = button.get_attribute("title")
            assert title == expected, f"Tab {i} should have title '{expected}'"

    def test_tab_icons_have_explicit_dimensions(self, page: Page) -> None:
        """Test that tab icons have width and height attributes."""
        page.goto("http://localhost:8001")

        icons = page.locator(".tab-icon")
        for i in range(5):
            icon = icons.nth(i)
            expect(icon).to_have_attribute("width", "20")
            expect(icon).to_have_attribute("height", "20")


class TestTabIconFiles:
    """Test that icon SVG files are accessible."""

    def test_converter_icon_file_accessible(self, page: Page) -> None:
        """Test that converter icon SVG loads successfully."""
        response = page.goto(
            "http://localhost:8001/static/images/icons/icon-converter.svg"
        )
        assert response is not None
        assert response.status == 200

    def test_camera_icon_file_accessible(self, page: Page) -> None:
        """Test that camera icon SVG loads successfully."""
        response = page.goto(
            "http://localhost:8001/static/images/icons/icon-camera.svg"
        )
        assert response is not None
        assert response.status == 200

    def test_jobs_icon_file_accessible(self, page: Page) -> None:
        """Test that jobs icon SVG loads successfully."""
        response = page.goto("http://localhost:8001/static/images/icons/icon-jobs.svg")
        assert response is not None
        assert response.status == 200

    def test_account_icon_file_accessible(self, page: Page) -> None:
        """Test that account icon SVG loads successfully."""
        response = page.goto(
            "http://localhost:8001/static/images/icons/icon-account.svg"
        )
        assert response is not None
        assert response.status == 200

    def test_docs_icon_file_accessible(self, page: Page) -> None:
        """Test that docs icon SVG loads successfully."""
        response = page.goto("http://localhost:8001/static/images/icons/icon-docs.svg")
        assert response is not None
        assert response.status == 200


class TestTabIconResponsive:
    """Test responsive behavior - icon-only on mobile."""

    def test_desktop_shows_icon_and_text(self, page: Page) -> None:
        """Test that desktop viewport shows both icon and text."""
        page.set_viewport_size({"width": 1024, "height": 768})
        page.goto("http://localhost:8001")

        # Icon should be visible
        icon = page.locator("#tab-konverter-btn .tab-icon")
        expect(icon).to_be_visible()

        # Text should be visible
        text = page.locator("#tab-konverter-btn .tab-text")
        expect(text).to_be_visible()

    def test_mobile_shows_icon_only(self, page: Page) -> None:
        """Test that mobile viewport shows only icon (text hidden)."""
        page.set_viewport_size({"width": 375, "height": 667})
        page.goto("http://localhost:8001")

        # Icon should be visible
        icon = page.locator("#tab-konverter-btn .tab-icon")
        expect(icon).to_be_visible()

        # Text should be hidden
        text = page.locator("#tab-konverter-btn .tab-text")
        expect(text).to_be_hidden()

    def test_mobile_all_icons_visible(self, page: Page) -> None:
        """Test that all icons are visible on mobile."""
        page.set_viewport_size({"width": 375, "height": 667})
        page.goto("http://localhost:8001")

        icons = page.locator(".tab-icon")
        for i in range(5):
            expect(icons.nth(i)).to_be_visible()

    def test_mobile_all_text_hidden(self, page: Page) -> None:
        """Test that all text is hidden on mobile."""
        page.set_viewport_size({"width": 375, "height": 667})
        page.goto("http://localhost:8001")

        texts = page.locator(".tab-text")
        for i in range(5):
            expect(texts.nth(i)).to_be_hidden()

    def test_mobile_tab_buttons_have_adequate_size(self, page: Page) -> None:
        """Test that tab buttons have adequate touch target on mobile."""
        page.set_viewport_size({"width": 375, "height": 667})
        page.goto("http://localhost:8001")

        button = page.locator(".tab-button").first
        box = button.bounding_box()
        assert box is not None
        assert box["width"] >= 48, "Tab button should be at least 48px wide on mobile"
        assert box["height"] >= 40, "Tab button should be at least 40px tall"


class TestTabIconStyling:
    """Test tab icon styling consistency."""

    def test_tab_icon_has_correct_class(self, page: Page) -> None:
        """Test that all icons have the tab-icon class."""
        page.goto("http://localhost:8001")

        icons = page.locator(".tab-button img")
        for i in range(5):
            icon = icons.nth(i)
            classes = icon.get_attribute("class")
            assert "tab-icon" in classes, f"Icon {i} should have tab-icon class"

    def test_tab_text_has_correct_class(self, page: Page) -> None:
        """Test that all text spans have the tab-text class."""
        page.goto("http://localhost:8001")

        texts = page.locator(".tab-button span")
        for i in range(5):
            text = texts.nth(i)
            classes = text.get_attribute("class")
            assert "tab-text" in classes, f"Text {i} should have tab-text class"
