"""E2E tests for Camera Tab functionality."""

from __future__ import annotations

import time

import pytest
from playwright.sync_api import Page, expect

pytestmark = [pytest.mark.e2e, pytest.mark.playwright]


class TestCameraTabUI:
    """Test Camera Tab UI elements and basic interactions."""

    def test_camera_tab_exists(self, page_with_server: Page):
        """Test that camera tab is visible and accessible."""
        page = page_with_server
        page.goto("http://localhost:8001/")

        # Wait for page to load
        expect(page.locator("h1")).to_contain_text("PDF/A Converter")

        # Find and click camera tab
        camera_tab_btn = page.locator("#tab-kamera-btn")
        expect(camera_tab_btn).to_be_visible()
        camera_tab_btn.click()

        # Verify camera tab content is visible
        camera_tab = page.locator("#tab-kamera")
        expect(camera_tab).not_to_have_attribute("hidden")

    def test_camera_controls_present(self, page_with_server: Page):
        """Test that camera control buttons are present."""
        page = page_with_server
        page.goto("http://localhost:8001/#kamera")

        # Check for camera control buttons
        expect(page.locator("#startCameraBtn")).to_be_visible()
        expect(page.locator("#stopCameraBtn")).to_be_hidden()
        expect(page.locator("#captureBtn")).to_be_hidden()
        expect(page.locator("#switchCameraBtn")).to_be_hidden()

    def test_page_staging_area_present(self, page_with_server: Page):
        """Test that page staging area is present."""
        page = page_with_server
        page.goto("http://localhost:8001/#kamera")

        # Check for staging area elements
        expect(page.locator("#pageStaging")).to_be_visible()
        expect(page.locator("#pageList")).to_be_visible()
        expect(page.locator("#pageCount")).to_have_text("0")
        expect(page.locator("#submitPagesBtn")).to_be_disabled()

    def test_staging_action_buttons(self, page_with_server: Page):
        """Test that staging action buttons are present."""
        page = page_with_server
        page.goto("http://localhost:8001/#kamera")

        # Check for action buttons
        expect(page.locator("#addPageBtn")).to_be_visible()
        expect(page.locator("#clearAllBtn")).to_be_visible()
        expect(page.locator("#submitPagesBtn")).to_be_visible()
        expect(page.locator("#submitPagesBtn")).to_be_disabled()

    def test_image_editor_initially_hidden(self, page_with_server: Page):
        """Test that image editor is initially hidden."""
        page = page_with_server
        page.goto("http://localhost:8001/#kamera")

        # Image editor should be hidden initially
        expect(page.locator("#imageEditor")).to_be_hidden()


class TestCameraTabTranslations:
    """Test that camera tab translations are working."""

    def test_camera_tab_english(self, page_with_server: Page):
        """Test camera tab displays English translations."""
        page = page_with_server
        page.goto("http://localhost:8001/?lang=en#kamera")

        # Wait for page to load
        time.sleep(0.5)

        # Check English translations
        expect(page.locator("#startCameraBtn")).to_contain_text("Start Camera")
        expect(page.locator("#submitPagesBtn")).to_contain_text("Convert to PDF/A")

    def test_camera_tab_german(self, page_with_server: Page):
        """Test camera tab displays German translations."""
        page = page_with_server
        page.goto("http://localhost:8001/?lang=de#kamera")

        # Wait for page to load
        time.sleep(0.5)

        # Check German translations
        expect(page.locator("#startCameraBtn")).to_contain_text("Kamera starten")
        expect(page.locator("#submitPagesBtn")).to_contain_text("In PDF/A konvertieren")

    def test_camera_tab_spanish(self, page_with_server: Page):
        """Test camera tab displays Spanish translations."""
        page = page_with_server
        page.goto("http://localhost:8001/?lang=es#kamera")

        # Wait for page to load
        time.sleep(0.5)

        # Check Spanish translations
        expect(page.locator("#startCameraBtn")).to_contain_text("Iniciar Cámara")
        expect(page.locator("#submitPagesBtn")).to_contain_text("Convertir a PDF/A")

    def test_camera_tab_french(self, page_with_server: Page):
        """Test camera tab displays French translations."""
        page = page_with_server
        page.goto("http://localhost:8001/?lang=fr#kamera")

        # Wait for page to load
        time.sleep(0.5)

        # Check French translations
        expect(page.locator("#startCameraBtn")).to_contain_text("Démarrer la Caméra")
        expect(page.locator("#submitPagesBtn")).to_contain_text("Convertir en PDF/A")


class TestImageEditorUI:
    """Test Image Editor UI elements."""

    def test_editor_controls_present(self, page_with_server: Page):
        """Test that editor control elements exist."""
        page = page_with_server
        page.goto("http://localhost:8001/#kamera")

        # Editor should be hidden initially
        editor = page.locator("#imageEditor")
        expect(editor).to_be_hidden()

        # But controls should exist in DOM
        expect(page.locator("#editCanvas")).to_be_attached()
        expect(page.locator("#rotateLeftBtn")).to_be_attached()
        expect(page.locator("#rotateRightBtn")).to_be_attached()
        expect(page.locator("#brightnessSlider")).to_be_attached()
        expect(page.locator("#contrastSlider")).to_be_attached()
        expect(page.locator("#acceptEditBtn")).to_be_attached()
        expect(page.locator("#cancelEditBtn")).to_be_attached()


class TestResponsiveDesign:
    """Test responsive design for mobile devices."""

    def test_camera_tab_mobile_viewport(self, page_with_server: Page):
        """Test camera tab renders correctly on mobile viewport."""
        page = page_with_server
        page.set_viewport_size({"width": 375, "height": 667})  # iPhone SE
        page.goto("http://localhost:8001/#kamera")

        # Camera controls should be visible
        expect(page.locator("#cameraControls")).to_be_visible()

        # Staging area should be visible
        expect(page.locator("#pageStaging")).to_be_visible()

    def test_camera_tab_tablet_viewport(self, page_with_server: Page):
        """Test camera tab renders correctly on tablet viewport."""
        page = page_with_server
        page.set_viewport_size({"width": 768, "height": 1024})  # iPad
        page.goto("http://localhost:8001/#kamera")

        # Camera controls should be visible
        expect(page.locator("#cameraControls")).to_be_visible()

        # Staging area should be visible
        expect(page.locator("#pageStaging")).to_be_visible()


class TestAccessibility:
    """Test accessibility features of camera tab."""

    def test_aria_labels_present(self, page_with_server: Page):
        """Test that ARIA labels are present for accessibility."""
        page = page_with_server
        page.goto("http://localhost:8001/#kamera")

        # Check for ARIA labels
        preview = page.locator("#cameraPreview")
        expect(preview).to_have_attribute("aria-label", "Camera preview")

        # Tab should have role
        camera_tab = page.locator("#tab-kamera")
        expect(camera_tab).to_have_attribute("role", "tabpanel")

    def test_keyboard_navigation(self, page_with_server: Page):
        """Test that camera tab is keyboard navigable."""
        page = page_with_server
        page.goto("http://localhost:8001/")

        # Navigate to camera tab via keyboard
        page.keyboard.press("Tab")  # Focus on first interactive element

        # Find camera tab button and activate it
        camera_tab_btn = page.locator("#tab-kamera-btn")
        camera_tab_btn.focus()
        page.keyboard.press("Enter")

        # Camera tab should now be visible
        expect(page.locator("#tab-kamera")).not_to_have_attribute("hidden")


@pytest.mark.skip(reason="Camera access requires user permission and hardware")
class TestCameraFunctionality:
    """Tests for actual camera functionality.

    Note: These tests are skipped because:
    1. Camera access requires user permission (getUserMedia)
    2. Requires actual camera hardware
    3. Cannot be automated in CI/CD environment

    For manual testing:
    1. Open browser with camera enabled
    2. Click "Start Camera" button
    3. Grant camera permission
    4. Click "Capture" button
    5. Verify photo appears in staging area
    6. Click "Convert to PDF/A"
    7. Verify job is submitted to Jobs tab
    """

    def test_camera_start(self, page_with_server: Page):
        """Test starting camera (requires manual testing)."""
        pytest.skip("Requires user permission and camera hardware")

    def test_photo_capture(self, page_with_server: Page):
        """Test photo capture (requires manual testing)."""
        pytest.skip("Requires user permission and camera hardware")

    def test_multi_page_capture(self, page_with_server: Page):
        """Test capturing multiple pages (requires manual testing)."""
        pytest.skip("Requires user permission and camera hardware")

    def test_image_editing(self, page_with_server: Page):
        """Test image editing workflow (requires manual testing)."""
        pytest.skip("Requires user permission and camera hardware")

    def test_drag_and_drop_reordering(self, page_with_server: Page):
        """Test drag-and-drop page reordering (requires manual testing)."""
        pytest.skip("Requires user permission and camera hardware")

    def test_multi_file_submission(self, page_with_server: Page):
        """Test multi-file PDF job submission (requires manual testing)."""
        pytest.skip("Requires user permission and camera hardware")
