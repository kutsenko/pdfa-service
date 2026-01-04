"""Integration tests for tab navigation functionality."""

from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect

pytestmark = [pytest.mark.e2e, pytest.mark.playwright]


@pytest.fixture
def page_with_tabs(page: Page, base_url: str) -> Page:
    """Load page and wait for tabs to be visible."""
    page.goto(base_url)
    page.wait_for_selector(".tab-navigation", state="visible", timeout=5000)
    return page


class TestTabNavigation:
    """Test tab navigation and switching."""

    def test_tabs_are_visible_on_load(self, page_with_tabs: Page):
        """Test that tab navigation is visible when page loads."""
        tab_nav = page_with_tabs.locator(".tab-navigation")
        expect(tab_nav).to_be_visible()

    def test_all_tab_buttons_present(self, page_with_tabs: Page):
        """Test that all tab buttons are present."""
        tab_buttons = page_with_tabs.locator(".tab-button")
        expect(tab_buttons).to_have_count(
            5
        )  # Konverter, Kamera, Jobs, Account, Documentation

    def test_first_tab_active_by_default(self, page_with_tabs: Page):
        """Test that the first tab (Konverter) is active by default."""
        konverter_btn = page_with_tabs.locator("#tab-konverter-btn")
        expect(konverter_btn).to_have_class("tab-button active")
        expect(konverter_btn).to_have_attribute("aria-selected", "true")

        konverter_panel = page_with_tabs.locator("#tab-konverter")
        expect(konverter_panel).to_have_class("tab-panel active")
        expect(konverter_panel).to_be_visible()

    def test_only_active_tab_panel_visible(self, page_with_tabs: Page):
        """Test that only the active tab panel is visible."""
        konverter_panel = page_with_tabs.locator("#tab-konverter")
        kamera_panel = page_with_tabs.locator("#tab-kamera")
        jobs_panel = page_with_tabs.locator("#tab-jobs")
        account_panel = page_with_tabs.locator("#tab-account")
        docs_panel = page_with_tabs.locator("#tab-documentation")

        # Only Konverter should be visible initially
        expect(konverter_panel).to_be_visible()
        expect(kamera_panel).to_be_hidden()
        expect(jobs_panel).to_be_hidden()
        expect(account_panel).to_be_hidden()
        expect(docs_panel).to_be_hidden()

    def test_click_tab_switches_content(self, page_with_tabs: Page):
        """Test that clicking a tab switches to that tab's content."""
        # Click on Kamera tab
        kamera_btn = page_with_tabs.locator("#tab-kamera-btn")
        kamera_btn.click()

        # Wait for tab to switch
        page_with_tabs.wait_for_timeout(100)

        # Check that Kamera tab is now active
        expect(kamera_btn).to_have_class("tab-button active")
        expect(kamera_btn).to_have_attribute("aria-selected", "true")

        # Check panels
        konverter_panel = page_with_tabs.locator("#tab-konverter")
        kamera_panel = page_with_tabs.locator("#tab-kamera")

        expect(konverter_panel).to_be_hidden()
        expect(kamera_panel).to_be_visible()

    def test_switch_multiple_tabs(self, page_with_tabs: Page):
        """Test switching between multiple tabs."""
        tabs_to_test = [
            ("tab-kamera-btn", "tab-kamera"),
            ("tab-jobs-btn", "tab-jobs"),
            ("tab-account-btn", "tab-account"),
            ("tab-documentation-btn", "tab-documentation"),
            ("tab-konverter-btn", "tab-konverter"),  # Back to first
        ]

        for btn_id, panel_id in tabs_to_test:
            # Click tab button
            page_with_tabs.locator(f"#{btn_id}").click()
            page_with_tabs.wait_for_timeout(100)

            # Verify only this panel is visible
            for _, check_panel_id in tabs_to_test:
                panel = page_with_tabs.locator(f"#{check_panel_id}")
                if check_panel_id == panel_id:
                    expect(panel).to_be_visible()
                else:
                    expect(panel).to_be_hidden()

    def test_keyboard_navigation_arrow_right(self, page_with_tabs: Page):
        """Test keyboard navigation with arrow right."""
        # Focus first tab
        konverter_btn = page_with_tabs.locator("#tab-konverter-btn")
        konverter_btn.focus()

        # Press arrow right
        konverter_btn.press("ArrowRight")
        page_with_tabs.wait_for_timeout(100)

        # Should switch to Kamera tab
        kamera_btn = page_with_tabs.locator("#tab-kamera-btn")
        expect(kamera_btn).to_have_class("tab-button active")

        kamera_panel = page_with_tabs.locator("#tab-kamera")
        expect(kamera_panel).to_be_visible()

    def test_keyboard_navigation_arrow_left(self, page_with_tabs: Page):
        """Test keyboard navigation with arrow left."""
        # Click Kamera tab first
        kamera_btn = page_with_tabs.locator("#tab-kamera-btn")
        kamera_btn.click()
        page_with_tabs.wait_for_timeout(100)

        # Press arrow left
        kamera_btn.press("ArrowLeft")
        page_with_tabs.wait_for_timeout(100)

        # Should switch back to Konverter tab
        konverter_btn = page_with_tabs.locator("#tab-konverter-btn")
        expect(konverter_btn).to_have_class("tab-button active")

        konverter_panel = page_with_tabs.locator("#tab-konverter")
        expect(konverter_panel).to_be_visible()

    def test_keyboard_navigation_home(self, page_with_tabs: Page):
        """Test keyboard navigation with Home key."""
        # Click last tab
        docs_btn = page_with_tabs.locator("#tab-documentation-btn")
        docs_btn.click()
        page_with_tabs.wait_for_timeout(100)

        # Press Home
        docs_btn.press("Home")
        page_with_tabs.wait_for_timeout(100)

        # Should switch to first tab
        konverter_btn = page_with_tabs.locator("#tab-konverter-btn")
        expect(konverter_btn).to_have_class("tab-button active")

    def test_keyboard_navigation_end(self, page_with_tabs: Page):
        """Test keyboard navigation with End key."""
        # Focus first tab
        konverter_btn = page_with_tabs.locator("#tab-konverter-btn")
        konverter_btn.focus()

        # Press End
        konverter_btn.press("End")
        page_with_tabs.wait_for_timeout(100)

        # Should switch to last tab
        docs_btn = page_with_tabs.locator("#tab-documentation-btn")
        expect(docs_btn).to_have_class("tab-button active")

    def test_url_hash_updates_on_tab_switch(self, page_with_tabs: Page):
        """Test that URL hash is updated when switching tabs."""
        # Click Kamera tab
        kamera_btn = page_with_tabs.locator("#tab-kamera-btn")
        kamera_btn.click()
        page_with_tabs.wait_for_timeout(100)

        # Check URL hash
        assert "#kamera" in page_with_tabs.url

    def test_load_page_with_hash(self, page: Page, base_url: str):
        """Test loading page with hash in URL."""
        # Load page with #jobs hash
        page.goto(f"{base_url}#jobs")
        page.wait_for_selector(".tab-navigation", state="visible", timeout=5000)

        # Jobs tab should be active
        jobs_btn = page.locator("#tab-jobs-btn")
        expect(jobs_btn).to_have_class("tab-button active")

        jobs_panel = page.locator("#tab-jobs")
        expect(jobs_panel).to_be_visible()

    def test_browser_back_forward_navigation(self, page_with_tabs: Page):
        """Test browser back/forward navigation between tabs."""
        # Click through tabs to create history
        page_with_tabs.locator("#tab-kamera-btn").click()
        page_with_tabs.wait_for_timeout(100)

        page_with_tabs.locator("#tab-jobs-btn").click()
        page_with_tabs.wait_for_timeout(100)

        # Go back
        page_with_tabs.go_back()
        page_with_tabs.wait_for_timeout(100)

        # Should be on Kamera tab
        kamera_btn = page_with_tabs.locator("#tab-kamera-btn")
        expect(kamera_btn).to_have_class("tab-button active")

        # Go back again
        page_with_tabs.go_back()
        page_with_tabs.wait_for_timeout(100)

        # Should be on Konverter tab
        konverter_btn = page_with_tabs.locator("#tab-konverter-btn")
        expect(konverter_btn).to_have_class("tab-button active")

        # Go forward
        page_with_tabs.go_forward()
        page_with_tabs.wait_for_timeout(100)

        # Should be on Kamera tab again
        expect(kamera_btn).to_have_class("tab-button active")

    def test_aria_attributes_updated(self, page_with_tabs: Page):
        """Test that ARIA attributes are correctly updated."""
        # Click Kamera tab
        kamera_btn = page_with_tabs.locator("#tab-kamera-btn")
        kamera_btn.click()
        page_with_tabs.wait_for_timeout(100)

        # Check ARIA attributes
        expect(kamera_btn).to_have_attribute("aria-selected", "true")
        expect(kamera_btn).to_have_attribute("tabindex", "0")

        # Other tabs should have aria-selected="false"
        konverter_btn = page_with_tabs.locator("#tab-konverter-btn")
        expect(konverter_btn).to_have_attribute("aria-selected", "false")
        expect(konverter_btn).to_have_attribute("tabindex", "-1")

    def test_rapid_tab_switching(self, page_with_tabs: Page):
        """Test that rapid tab switching doesn't break the UI."""
        # Rapidly click through all tabs
        for i in range(3):  # Do it multiple times
            for btn_id in [
                "tab-kamera-btn",
                "tab-jobs-btn",
                "tab-account-btn",
                "tab-konverter-btn",
            ]:
                page_with_tabs.locator(f"#{btn_id}").click()

        # Should end on Konverter tab
        konverter_btn = page_with_tabs.locator("#tab-konverter-btn")
        expect(konverter_btn).to_have_class("tab-button active")

        konverter_panel = page_with_tabs.locator("#tab-konverter")
        expect(konverter_panel).to_be_visible()

        # Only one panel should be visible
        visible_panels = page_with_tabs.locator(".tab-panel:visible")
        expect(visible_panels).to_have_count(1)
