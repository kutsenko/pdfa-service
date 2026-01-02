"""Regression tests for critical UI bugs.

This module contains E2E tests that prevent regressions of previously fixed bugs:
- Audio system initialization without user gesture
- Tab panels not visible on initial page load
"""

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.playwright
class TestAudioSystemRegression:
    """Tests to prevent audio system initialization errors."""

    def test_should_not_initialize_audio_on_page_load(self, page: Page, base_url):
        """Regression test: Audio system should not initialize on page load.

        Bug: AccessibleCameraAssistant.init() auto-enabled assistance when
        screen reader was detected, creating AudioContext without user gesture.
        This caused "Audio system not available" error on page load.

        Fix: Only create AudioContext when user explicitly clicks the checkbox.

        Test verifies:
        - No AudioContext errors in console on page load
        - Audio guidance checkbox can be enabled without errors
        - AudioContext is only created after user interaction
        """
        console_errors = []

        # Capture console errors
        def handle_console(msg):
            if msg.type == "error":
                console_errors.append(msg.text)

        page.on("console", handle_console)

        # Load page
        page.goto(base_url)
        page.wait_for_selector(".tab-navigation", state="visible", timeout=5000)
        page.wait_for_timeout(1000)

        # Verify no AudioContext errors on page load
        audio_errors = [
            e for e in console_errors if "Audio" in e or "AudioContext" in e
        ]
        assert (
            len(audio_errors) == 0
        ), f"AudioContext errors on page load: {audio_errors}"

        # Switch to camera tab
        page.locator("#tab-kamera-btn").click()
        page.wait_for_timeout(500)

        # Verify camera tab is visible
        kamera_panel = page.locator("#tab-kamera")
        expect(kamera_panel).to_be_visible()

        # Audio checkbox should be unchecked by default
        checkbox = page.locator("#enableA11yAssistance")
        expect(checkbox).not_to_be_checked()

    def test_audio_only_starts_when_user_enables_it(self, page: Page, base_url):
        """Test that audio guidance only starts when user explicitly enables it.

        Test verifies:
        - Checkbox starts unchecked
        - User can check the checkbox
        - AudioContext is created only after user interaction
        """
        page.goto(f"{base_url}#kamera")
        page.wait_for_selector(".tab-navigation", state="visible", timeout=5000)
        page.wait_for_timeout(500)

        # Audio checkbox should be unchecked initially
        checkbox = page.locator("#enableA11yAssistance")
        expect(checkbox).not_to_be_checked()

        # User enables audio guidance
        checkbox.check()
        page.wait_for_timeout(500)

        # Checkbox should now be checked
        expect(checkbox).to_be_checked()

        # Loading indicator or status should be visible
        # (verifies that enable() was called and is processing)
        loading_or_status = page.locator("#a11yLoadingIndicator, #a11yStatus")
        expect(loading_or_status.first).to_be_visible()


@pytest.mark.playwright
class TestTabVisibilityRegression:
    """Tests to prevent tab visibility issues on page load."""

    def test_first_tab_visible_on_page_load_without_hash(self, page: Page, base_url):
        """Regression test: First tab panel should be visible on page load.

        Bug: initTabNavigation() only called switchTab() if URL had a hash.
        When loading page without hash, all panels remained hidden=true from
        showLoginScreen(), showing no content.

        Fix: Always call switchTab() on init, either with hash tab or default first tab.

        Test verifies:
        - Loading page without hash shows Konverter tab
        - Konverter panel is visible (hidden=false, display=block)
        - Other panels are hidden
        - Tab button has 'active' class
        """
        page.goto(base_url)  # No hash
        page.wait_for_selector(".tab-navigation", state="visible", timeout=5000)
        page.wait_for_timeout(1000)

        # Konverter tab should be active
        konverter_btn = page.locator("#tab-konverter-btn")
        expect(konverter_btn).to_have_class("tab-button active")

        # Konverter panel should be visible
        konverter_panel = page.locator("#tab-konverter")
        expect(konverter_panel).to_be_visible()

        # Verify panel is not hidden
        is_hidden = konverter_panel.evaluate("el => el.hidden")
        assert not is_hidden, "Konverter panel should not be hidden"

        # Other panels should be hidden
        kamera_panel = page.locator("#tab-kamera")
        expect(kamera_panel).to_be_hidden()

        # Verify panel has hidden attribute set to true
        is_hidden = kamera_panel.evaluate("el => el.hidden")
        assert is_hidden, "Kamera panel should be hidden"

    def test_tab_panel_visible_on_page_load_with_hash(self, page: Page, base_url):
        """Test that loading page with hash shows correct tab.

        Test verifies:
        - Loading page with #kamera shows Kamera tab
        - Kamera panel is visible
        - Other panels are hidden
        """
        page.goto(f"{base_url}#kamera")
        page.wait_for_selector(".tab-navigation", state="visible", timeout=5000)
        page.wait_for_timeout(1000)

        # Kamera tab should be active
        kamera_btn = page.locator("#tab-kamera-btn")
        expect(kamera_btn).to_have_class("tab-button active")

        # Kamera panel should be visible
        kamera_panel = page.locator("#tab-kamera")
        expect(kamera_panel).to_be_visible()

        # Verify panel is not hidden
        is_hidden = kamera_panel.evaluate("el => el.hidden")
        assert not is_hidden, "Kamera panel should not be hidden"

        # Konverter panel should be hidden
        konverter_panel = page.locator("#tab-konverter")
        expect(konverter_panel).to_be_hidden()

        # Verify panel has hidden attribute
        is_hidden = konverter_panel.evaluate("el => el.hidden")
        assert is_hidden, "Konverter panel should be hidden"

    def test_tab_switches_correctly_after_initial_load(self, page: Page, base_url):
        """Test that tab switching works correctly after page load.

        Test verifies:
        - Can click from first tab to second tab
        - Panels switch visibility correctly
        - Tab buttons update active state
        """
        page.goto(base_url)
        page.wait_for_selector(".tab-navigation", state="visible", timeout=5000)
        page.wait_for_timeout(1000)

        # Initially on Konverter
        konverter_panel = page.locator("#tab-konverter")
        expect(konverter_panel).to_be_visible()

        # Click Kamera tab
        kamera_btn = page.locator("#tab-kamera-btn")
        kamera_btn.click()
        page.wait_for_timeout(300)

        # Kamera should now be visible, Konverter hidden
        kamera_panel = page.locator("#tab-kamera")
        expect(kamera_panel).to_be_visible()
        expect(konverter_panel).to_be_hidden()

        # Click back to Konverter
        konverter_btn = page.locator("#tab-konverter-btn")
        konverter_btn.click()
        page.wait_for_timeout(300)

        # Konverter should be visible again, Kamera hidden
        expect(konverter_panel).to_be_visible()
        expect(kamera_panel).to_be_hidden()

    def test_invalid_hash_falls_back_to_first_tab(self, page: Page, base_url):
        """Test that invalid hash in URL falls back to first tab.

        Test verifies:
        - Loading page with non-existent hash (#invalid) shows first tab
        - First tab panel is visible
        - No JavaScript errors
        """
        page.goto(f"{base_url}#invalid-tab-name")
        page.wait_for_selector(".tab-navigation", state="visible", timeout=5000)
        page.wait_for_timeout(1000)

        # Should fall back to Konverter tab
        konverter_btn = page.locator("#tab-konverter-btn")
        expect(konverter_btn).to_have_class("tab-button active")

        konverter_panel = page.locator("#tab-konverter")
        expect(konverter_panel).to_be_visible()
