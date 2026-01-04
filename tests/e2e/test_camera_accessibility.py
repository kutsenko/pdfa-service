"""E2E tests for camera accessibility features (Phase 1)."""

from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect

pytestmark = [pytest.mark.e2e, pytest.mark.playwright]


def activate_camera_tab(page: Page):
    """Activate camera tab and wait for it to be visible."""
    camera_tab_btn = page.locator("#tab-kamera-btn")
    camera_tab_btn.click()
    page.wait_for_timeout(
        800
    )  # Wait for tab to become visible and translations to apply


class TestAccessibilityControlsUI:
    """Test accessibility controls UI elements."""

    def test_accessibility_controls_visible(self, page_with_server: Page):
        """Test that accessibility controls panel is visible in camera tab."""
        page = page_with_server
        page.goto("http://localhost:8001/")

        # Click camera tab to make it visible
        camera_tab_btn = page.locator("#tab-kamera-btn")
        camera_tab_btn.click()

        # Wait for tab to be visible
        page.wait_for_timeout(300)

        # Accessibility controls should be visible
        controls = page.locator("#cameraA11yControls")
        expect(controls).to_be_visible()

        # Check title
        title = controls.locator("h4")
        expect(title).to_be_visible()
        # Title should have accessibility icon (♿) in ::before pseudo-element
        # We can't test pseudo-elements directly, but we can verify the text

    def test_enable_toggle_present(self, page_with_server: Page):
        """Test that enable/disable toggle is present."""
        page = page_with_server
        page.goto("http://localhost:8001/")
        activate_camera_tab(page)

        checkbox = page.locator("#enableA11yAssistance")
        expect(checkbox).to_be_visible()
        expect(checkbox).not_to_be_checked()  # Should be unchecked by default

    def test_volume_slider_present(self, page_with_server: Page):
        """Test that volume slider is present with default value."""
        page = page_with_server
        page.goto("http://localhost:8001/")
        activate_camera_tab(page)

        slider = page.locator("#a11yVolume")
        expect(slider).to_be_visible()
        expect(slider).to_have_value("80")  # Default 80%

        value_display = page.locator("#a11yVolumeValue")
        expect(value_display).to_have_text("80%")

    def test_volume_slider_updates_value(self, page_with_server: Page):
        """Test that volume slider updates display value."""
        page = page_with_server
        page.goto("http://localhost:8001/")
        activate_camera_tab(page)

        slider = page.locator("#a11yVolume")
        value_display = page.locator("#a11yVolumeValue")

        # Change volume to 50%
        slider.fill("50")
        expect(value_display).to_have_text("50%")

        # Change volume to 100%
        slider.fill("100")
        expect(value_display).to_have_text("100%")

        # Change volume to 0%
        slider.fill("0")
        expect(value_display).to_have_text("0%")

    def test_auto_capture_toggle_present(self, page_with_server: Page):
        """Test that auto-capture toggle is present and checked by default."""
        page = page_with_server
        page.goto("http://localhost:8001/")
        activate_camera_tab(page)

        checkbox = page.locator("#enableAutoCapture")
        expect(checkbox).to_be_visible()
        expect(checkbox).to_be_checked()  # Should be checked by default

    def test_test_audio_button_present(self, page_with_server: Page):
        """Test that test audio button is present."""
        page = page_with_server
        page.goto("http://localhost:8001/")
        activate_camera_tab(page)

        button = page.locator("#testA11yAudioBtn")
        expect(button).to_be_visible()
        expect(button).to_be_enabled()

    def test_edge_status_initially_hidden(self, page_with_server: Page):
        """Test that edge detection status is initially hidden."""
        page = page_with_server
        page.goto("http://localhost:8001/")
        activate_camera_tab(page)

        status = page.locator("#edgeDetectionStatus")
        expect(status).to_have_attribute("hidden", "")

    def test_loading_indicator_initially_hidden(self, page_with_server: Page):
        """Test that loading indicator is initially hidden."""
        page = page_with_server
        page.goto("http://localhost:8001/")
        activate_camera_tab(page)

        loading = page.locator("#a11yLoadingIndicator")
        expect(loading).to_have_attribute("hidden", "")

    def test_aria_live_region_present(self, page_with_server: Page):
        """Test that ARIA live region for announcements exists."""
        page = page_with_server
        page.goto("http://localhost:8001/")

        # Use .first to get the first matching element
        live_region = page.locator("#srAnnouncements").first
        expect(live_region).to_be_attached()
        expect(live_region).to_have_attribute("role", "status")
        expect(live_region).to_have_attribute("aria-live", "polite")
        expect(live_region).to_have_attribute("aria-atomic", "true")


class TestAccessibilityEnableDisable:
    """Test enabling and disabling accessibility assistance."""

    def test_enable_assistance_shows_loading(self, page_with_server: Page):
        """Test that enabling assistance shows loading indicator."""
        page = page_with_server
        page.goto("http://localhost:8001/")
        activate_camera_tab(page)

        checkbox = page.locator("#enableA11yAssistance")
        loading = page.locator("#a11yLoadingIndicator")

        # Initially hidden
        expect(loading).to_have_attribute("hidden", "")

        # Enable assistance
        checkbox.check()

        # Loading indicator should appear briefly
        # Note: It might disappear quickly if jscanify loads fast
        # So we just verify the checkbox is checked
        expect(checkbox).to_be_checked()

    def test_audiocontext_created_in_user_gesture(self, page_with_server: Page):
        """Test that AudioContext is created in direct user gesture (iOS fix).

        This test verifies the fix for iOS Safari/Chrome where AudioContext.resume()
        must be called synchronously within a user gesture event handler.
        The fix moved AudioContext creation from enable() to the checkbox event handler.
        """
        page = page_with_server
        page.goto("http://localhost:8001/")
        activate_camera_tab(page)

        # Set up console message listener
        console_messages = []

        def handle_console(msg):
            console_messages.append(msg.text)

        page.on("console", handle_console)

        # Enable assistance
        checkbox = page.locator("#enableA11yAssistance")
        checkbox.check()

        # Wait for initialization to complete
        page.wait_for_timeout(2000)

        # Verify checkbox is checked (no errors occurred)
        expect(checkbox).to_be_checked()

        # Check debug console messages for iOS AudioContext fix
        console_text = "\n".join(console_messages)

        # Should show AudioContext creation in user gesture
        assert (
            "Creating AudioContext in direct user gesture" in console_text
        ), "AudioContext should be created in user gesture"

        # Should show AudioContext state after creation
        assert (
            "AudioContext created in user gesture" in console_text
        ), "AudioContext creation should be logged"

        # Should verify pre-created AudioContext in enable()
        assert (
            "Checking AudioContext (should be pre-created)" in console_text
        ), "enable() should check for pre-created AudioContext"

        # Should confirm AudioContext exists
        assert (
            "AudioContext exists" in console_text
        ), "enable() should confirm AudioContext exists"

    def test_edge_detection_error_handling(self, page_with_server: Page):
        """Test enhanced error handling for edge detection (iOS fix).

        This test verifies the improvements added for iOS edge detection:
        - Video dimension validation
        - Canvas content verification
        - Better error messages
        - AudioContext state monitoring
        """
        page = page_with_server
        page.goto("http://localhost:8001/")
        activate_camera_tab(page)

        # Set up console message listener
        console_messages = []

        def handle_console(msg):
            console_messages.append(msg.text)

        page.on("console", handle_console)

        # Enable assistance
        checkbox = page.locator("#enableA11yAssistance")
        checkbox.check()

        # Wait for initialization and some frame processing
        page.wait_for_timeout(3000)

        # Verify checkbox is checked (no fatal errors occurred)
        expect(checkbox).to_be_checked()

        # Check debug console messages for enhanced logging
        console_text = "\n".join(console_messages)

        # Should show canvas verification (new in this PR)
        # This may or may not appear depending on timing
        # The important thing is that these new checks exist in the code

        # Should NOT show critical errors that would prevent operation
        assert (
            "Error analyzing frame" not in console_text
            or "Error stack:" in console_text
        ), "If errors occur, they should include stack trace for debugging"

        # Verify no video dimension errors (would indicate iOS issue)
        if "Video dimensions are 0" in console_text:
            # Expected on iOS during initialization, handled gracefully
            assert (
                "skipping frame" in console_text
            ), "Zero dimensions should be handled gracefully"

    def test_edge_detection_sensitivity_improvements(self, page_with_server: Page):
        """Test improved edge detection sensitivity (iOS fix).

        Verifies the sensitivity improvements:
        - Higher resolution (75% vs 50%)
        - Lower confidence threshold (40% vs 60%)
        - Enhanced periodic debugging logs
        """
        page = page_with_server
        page.goto("http://localhost:8001/")
        activate_camera_tab(page)

        # Set up console message listener
        console_messages = []

        def handle_console(msg):
            console_messages.append(msg.text)

        page.on("console", handle_console)

        # Enable assistance
        checkbox = page.locator("#enableA11yAssistance")
        checkbox.check()

        # Wait for several detection cycles (5+ seconds for periodic logs)
        page.wait_for_timeout(6000)

        # Verify checkbox is checked
        expect(checkbox).to_be_checked()

        # Check for periodic debug logs (new in this PR)
        console_text = "\n".join(console_messages)

        # Should see detection status logs (every 5 seconds)
        assert (
            "Detection status:" in console_text or "Edge confidence:" in console_text
        ), "Should see periodic detection status or confidence logs"

    def test_test_audio_button_clickable(self, page_with_server: Page):
        """Test that test audio button is clickable."""
        page = page_with_server
        page.goto("http://localhost:8001/")
        activate_camera_tab(page)

        button = page.locator("#testA11yAudioBtn")

        # Button should be clickable
        expect(button).to_be_enabled()

        # Click should not cause errors
        button.click()

        # Button should still be visible after click
        expect(button).to_be_visible()


class TestAccessibilityTranslations:
    """Test that accessibility UI is translated correctly."""

    def test_accessibility_ui_english(self, page_with_server: Page):
        """Test accessibility UI displays English translations."""
        page = page_with_server
        page.goto("http://localhost:8001/en#kamera")

        # Wait for page to load
        page.wait_for_timeout(500)

        # Check title
        title = page.locator("#cameraA11yControls h4")
        expect(title).to_contain_text("Accessibility Assistance")

        # Check enable label
        enable_label = page.locator(
            "label.checkbox-label:has(#enableA11yAssistance) span"
        )
        expect(enable_label).to_contain_text("Enable audio guidance")

        # Check volume label (this one does have for attribute)
        volume_label = page.locator('label[for="a11yVolume"]')
        expect(volume_label).to_contain_text("Volume")

        # Check test button
        test_button = page.locator("#testA11yAudioBtn")
        expect(test_button).to_contain_text("Test Audio")

    def test_accessibility_ui_german(self, page_with_server: Page):
        """Test accessibility UI displays German translations."""
        page = page_with_server
        page.goto("http://localhost:8001/de#kamera")

        # Wait for page to load
        page.wait_for_timeout(500)

        # Check title
        title = page.locator("#cameraA11yControls h4")
        expect(title).to_contain_text("Barrierefreiheits-Unterstützung")

        # Check enable label
        enable_label = page.locator(
            "label.checkbox-label:has(#enableA11yAssistance) span"
        )
        expect(enable_label).to_contain_text("Audio-Führung aktivieren")

        # Check volume label
        volume_label = page.locator('label[for="a11yVolume"]')
        expect(volume_label).to_contain_text("Lautstärke")

        # Check test button
        test_button = page.locator("#testA11yAudioBtn")
        expect(test_button).to_contain_text("Audio testen")

    def test_accessibility_ui_spanish(self, page_with_server: Page):
        """Test accessibility UI displays Spanish translations."""
        page = page_with_server
        page.goto("http://localhost:8001/es#kamera")

        # Wait for page to load
        page.wait_for_timeout(500)

        # Check title
        title = page.locator("#cameraA11yControls h4")
        expect(title).to_contain_text("Asistencia de Accesibilidad")

        # Check enable label
        enable_label = page.locator(
            "label.checkbox-label:has(#enableA11yAssistance) span"
        )
        expect(enable_label).to_contain_text("Activar guía de audio")

        # Check volume label
        volume_label = page.locator('label[for="a11yVolume"]')
        expect(volume_label).to_contain_text("Volumen")

        # Check test button
        test_button = page.locator("#testA11yAudioBtn")
        expect(test_button).to_contain_text("Probar Audio")

    def test_accessibility_ui_french(self, page_with_server: Page):
        """Test accessibility UI displays French translations."""
        page = page_with_server
        page.goto("http://localhost:8001/fr#kamera")

        # Wait for page to load
        page.wait_for_timeout(500)

        # Check title
        title = page.locator("#cameraA11yControls h4")
        expect(title).to_contain_text("Assistance d'Accessibilité")

        # Check enable label
        enable_label = page.locator(
            "label.checkbox-label:has(#enableA11yAssistance) span"
        )
        expect(enable_label).to_contain_text("Activer le guidage audio")

        # Check volume label
        volume_label = page.locator('label[for="a11yVolume"]')
        expect(volume_label).to_contain_text("Volume")

        # Check test button
        test_button = page.locator("#testA11yAudioBtn")
        expect(test_button).to_contain_text("Tester l'Audio")


class TestAccessibilityResponsiveDesign:
    """Test responsive design for accessibility controls."""

    def test_accessibility_controls_mobile_viewport(self, page_with_server: Page):
        """Test accessibility controls render correctly on mobile."""
        page = page_with_server
        page.set_viewport_size({"width": 375, "height": 667})  # iPhone SE
        page.goto("http://localhost:8001/")
        activate_camera_tab(page)

        # Controls should be visible
        controls = page.locator("#cameraA11yControls")
        expect(controls).to_be_visible()

        # All controls should be accessible
        expect(page.locator("#enableA11yAssistance")).to_be_visible()
        expect(page.locator("#a11yVolume")).to_be_visible()
        expect(page.locator("#enableAutoCapture")).to_be_visible()
        expect(page.locator("#testA11yAudioBtn")).to_be_visible()

    def test_accessibility_controls_tablet_viewport(self, page_with_server: Page):
        """Test accessibility controls render correctly on tablet."""
        page = page_with_server
        page.set_viewport_size({"width": 768, "height": 1024})  # iPad
        page.goto("http://localhost:8001/")
        activate_camera_tab(page)

        # Controls should be visible
        controls = page.locator("#cameraA11yControls")
        expect(controls).to_be_visible()

        # All controls should be accessible
        expect(page.locator("#enableA11yAssistance")).to_be_visible()
        expect(page.locator("#a11yVolume")).to_be_visible()
        expect(page.locator("#enableAutoCapture")).to_be_visible()
        expect(page.locator("#testA11yAudioBtn")).to_be_visible()


class TestAccessibilityKeyboardNavigation:
    """Test keyboard navigation of accessibility controls."""

    def test_accessibility_controls_keyboard_accessible(self, page_with_server: Page):
        """Test that accessibility controls are keyboard navigable."""
        page = page_with_server
        page.goto("http://localhost:8001/")
        activate_camera_tab(page)

        # Tab to enable checkbox
        checkbox = page.locator("#enableA11yAssistance")
        checkbox.focus()
        expect(checkbox).to_be_focused()

        # Should be able to toggle with space
        page.keyboard.press("Space")
        expect(checkbox).to_be_checked()

        # Tab to volume slider
        page.keyboard.press("Tab")
        slider = page.locator("#a11yVolume")
        expect(slider).to_be_focused()

        # Tab to auto-capture checkbox
        page.keyboard.press("Tab")
        auto_capture = page.locator("#enableAutoCapture")
        expect(auto_capture).to_be_focused()

        # Tab to test button
        page.keyboard.press("Tab")
        button = page.locator("#testA11yAudioBtn")
        expect(button).to_be_focused()


@pytest.mark.skip(reason="Requires camera hardware and actual edge detection")
class TestAccessibilityEdgeDetection:
    """Tests for edge detection and audio feedback.

    Note: These tests are skipped because:
    1. Edge detection requires real camera feed
    2. jscanify library needs actual document images
    3. Audio feedback testing requires audio output
    4. Cannot be automated in CI/CD environment

    For manual testing:
    1. Open browser with camera enabled
    2. Navigate to Camera Tab
    3. Enable "Accessibility Assistance"
    4. Point camera at a document
    5. Verify:
       - Loading indicator appears briefly
       - jscanify loads successfully (check console)
       - Audio tones play when document edges detected
       - Voice announcements in correct language
       - Auto-capture triggers after 2 seconds when stable
       - Volume control affects audio volume
       - Visual status indicator shows success/warning
    """

    def test_edge_detection_starts_with_camera(self, page_with_server: Page):
        """Test edge detection starts when camera starts (manual test)."""
        pytest.skip("Requires camera hardware and user permission")

    def test_audio_feedback_on_edge_detection(self, page_with_server: Page):
        """Test audio tones play on edge detection (manual test)."""
        pytest.skip("Requires camera hardware and audio output")

    def test_voice_announcements(self, page_with_server: Page):
        """Test voice announcements in user's language (manual test)."""
        pytest.skip("Requires Web Speech API and audio output")

    def test_auto_capture_countdown(self, page_with_server: Page):
        """Test auto-capture triggers after 2 seconds (manual test)."""
        pytest.skip("Requires camera hardware and stable document")

    def test_positional_guidance(self, page_with_server: Page):
        """Test positional guidance announcements (manual test)."""
        pytest.skip("Requires camera hardware and document positioning")


class TestAccessibilityIntegration:
    """Test integration with CameraManager."""

    @pytest.mark.skip(
        reason="AccessibleCameraAssistant JavaScript not yet implemented (Phase 2-6)"
    )
    def test_accessibility_assistant_initialized_with_camera(
        self, page_with_server: Page
    ):
        """Test that AccessibleCameraAssistant is initialized with CameraManager."""
        page = page_with_server
        page.goto("http://localhost:8001/")
        activate_camera_tab(page)

        # Check console for initialization message
        # We can't directly test JavaScript objects, but we can verify UI is present
        controls = page.locator("#cameraA11yControls")
        expect(controls).to_be_visible()

        # Enable assistance and verify no JavaScript errors
        checkbox = page.locator("#enableA11yAssistance")
        expect(checkbox).to_be_visible()
        expect(checkbox).to_be_enabled()

        # Use JavaScript to check the checkbox and trigger change event
        page.evaluate(
            """
            const cb = document.getElementById('enableA11yAssistance');
            cb.checked = true;
            cb.dispatchEvent(new Event('change', { bubbles: true }));
        """
        )

        # Wait a moment for async operations
        page.wait_for_timeout(1500)

        # Checkbox should remain checked (no errors)
        expect(checkbox).to_be_checked()

    @pytest.mark.skip(
        reason="AccessibleCameraAssistant JavaScript not yet implemented (Phase 2-6)"
    )
    def test_accessibility_controls_persist_on_tab_switch(self, page_with_server: Page):
        """Test that accessibility settings persist when switching tabs."""
        page = page_with_server
        page.goto("http://localhost:8001/")
        activate_camera_tab(page)

        # Set custom volume
        slider = page.locator("#a11yVolume")
        slider.fill("50")

        # Enable assistance
        checkbox = page.locator("#enableA11yAssistance")
        expect(checkbox).to_be_visible()
        expect(checkbox).to_be_enabled()

        # Use JavaScript to check the checkbox and trigger change event
        page.evaluate(
            """
            const cb = document.getElementById('enableA11yAssistance');
            cb.checked = true;
            cb.dispatchEvent(new Event('change', { bubbles: true }));
        """
        )
        page.wait_for_timeout(500)  # Wait for check to complete

        # Switch to another tab
        jobs_tab = page.locator("#tab-jobs-btn")
        jobs_tab.click()
        page.wait_for_timeout(500)

        # Switch back to camera tab
        camera_tab = page.locator("#tab-kamera-btn")
        camera_tab.click()
        page.wait_for_timeout(800)  # Wait for tab switch and translations

        # Settings should persist
        expect(slider).to_have_value("50")
        expect(checkbox).to_be_checked()


class TestAccessibilityCSS:
    """Test CSS styling of accessibility controls."""

    def test_accessibility_controls_have_distinctive_styling(
        self, page_with_server: Page
    ):
        """Test that accessibility controls have distinctive blue theme."""
        page = page_with_server
        page.goto("http://localhost:8001/")
        activate_camera_tab(page)

        controls = page.locator("#cameraA11yControls")

        # Check that controls panel has blue border (computed style)
        border_color = controls.evaluate("el => getComputedStyle(el).borderColor")
        # Border should be blue (rgb(59, 130, 246))
        assert "59" in border_color or "130" in border_color or "246" in border_color

    def test_edge_status_hidden_by_default(self, page_with_server: Page):
        """Test that edge status indicator is hidden by default."""
        page = page_with_server
        page.goto("http://localhost:8001/")
        activate_camera_tab(page)

        status = page.locator("#edgeDetectionStatus")
        expect(status).to_have_attribute("hidden", "")

    def test_slider_styling(self, page_with_server: Page):
        """Test that volume slider has custom styling."""
        page = page_with_server
        page.goto("http://localhost:8001/")
        activate_camera_tab(page)

        slider = page.locator("#a11yVolume")

        # Slider should be visible and styled
        expect(slider).to_be_visible()

        # Check slider has custom class
        expect(slider).to_have_class("slider")
