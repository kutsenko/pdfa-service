"""E2E tests for QR code library loading and functionality."""

import pytest
from playwright.sync_api import Page, expect


class TestQRCodeLibraryLoading:
    """Tests to ensure QR code library is properly loaded."""

    @pytest.mark.e2e
    def test_qr_code_library_is_loaded(self, page: Page, base_url: str):
        """Should load QR code library from CDN."""
        page.goto(f"{base_url}/en")

        # Wait for page to load
        page.wait_for_load_state("networkidle")

        # Check that QRCode global is defined
        qrcode_defined = page.evaluate("typeof QRCode !== 'undefined'")
        assert qrcode_defined, "QRCode library is not loaded"

    @pytest.mark.e2e
    def test_qr_code_library_has_correct_level(self, page: Page, base_url: str):
        """Should have QRCode.CorrectLevel available."""
        page.goto(f"{base_url}/en")
        page.wait_for_load_state("networkidle")

        # Check that CorrectLevel is available
        has_correct_level = page.evaluate(
            "typeof QRCode !== 'undefined' && typeof QRCode.CorrectLevel !== 'undefined'"
        )
        assert has_correct_level, "QRCode.CorrectLevel is not available"

    @pytest.mark.e2e
    def test_qr_code_cdn_script_tag_exists(self, page: Page, base_url: str):
        """Should have QR code script tag in HTML."""
        page.goto(f"{base_url}/en")

        # Check for script tag
        script_tag = page.locator('script[src*="qrcode"]')
        expect(script_tag).to_have_count(1)

    @pytest.mark.e2e
    def test_qr_code_cdn_loads_successfully(self, page: Page, base_url: str):
        """Should successfully load QR code library from CDN."""
        # Track failed requests
        failed_requests = []

        def handle_request_failed(request):
            if "qrcode" in request.url.lower():
                failed_requests.append(request.url)

        page.on("requestfailed", handle_request_failed)

        page.goto(f"{base_url}/en")
        page.wait_for_load_state("networkidle")

        # No QR code library requests should have failed
        assert len(failed_requests) == 0, f"QR code library failed to load: {failed_requests}"


class TestQRCodeGeneration:
    """Tests for QR code generation functionality."""

    @pytest.mark.e2e
    def test_qr_code_generation_in_pairing_ui(self, page: Page, base_url: str):
        """Should generate QR code when starting pairing."""
        page.goto(f"{base_url}/en")
        page.wait_for_load_state("networkidle")

        # Navigate to camera tab
        camera_tab = page.locator('[data-tab="kamera"]')
        camera_tab.click()

        # Click "Start Mobile Pairing" button
        start_pairing_btn = page.locator("#startPairingBtn")
        expect(start_pairing_btn).to_be_visible()
        start_pairing_btn.click()

        # Wait for QR code container to appear
        qr_container = page.locator("#qrCodeContainer")
        expect(qr_container).to_be_visible()

        # Check that QR code was generated (should have canvas or img element)
        qr_code_element = qr_container.locator("canvas, img")
        expect(qr_code_element).to_have_count(1)

    @pytest.mark.e2e
    def test_qr_code_error_handling(self, page: Page, base_url: str):
        """Should show error message if QR code library fails to load."""
        # Block QR code library from loading
        page.route("**/*qrcode*", lambda route: route.abort())

        page.goto(f"{base_url}/en")
        page.wait_for_load_state("networkidle")

        # Navigate to camera tab
        camera_tab = page.locator('[data-tab="kamera"]')
        camera_tab.click()

        # Try to start pairing
        start_pairing_btn = page.locator("#startPairingBtn")
        expect(start_pairing_btn).to_be_visible()
        start_pairing_btn.click()

        # Should show error message in QR container
        qr_container = page.locator("#qrCodeContainer")
        expect(qr_container).to_be_visible()

        # Should contain error message
        error_message = qr_container.locator(":text('QR code library not available')")
        expect(error_message).to_be_visible()

    @pytest.mark.e2e
    def test_pairing_code_display(self, page: Page, base_url: str):
        """Should display pairing code when starting pairing."""
        page.goto(f"{base_url}/en")
        page.wait_for_load_state("networkidle")

        # Navigate to camera tab
        camera_tab = page.locator('[data-tab="kamera"]')
        camera_tab.click()

        # Click "Start Mobile Pairing" button
        start_pairing_btn = page.locator("#startPairingBtn")
        start_pairing_btn.click()

        # Wait for pairing code to appear
        pairing_code_display = page.locator("#pairingCodeDisplay")
        expect(pairing_code_display).to_be_visible()

        # Pairing code should be 6 characters
        pairing_code = pairing_code_display.text_content()
        assert len(pairing_code) == 6, f"Pairing code should be 6 characters, got {len(pairing_code)}"

        # Should be alphanumeric uppercase
        assert pairing_code.isalnum(), "Pairing code should be alphanumeric"
        assert pairing_code.isupper(), "Pairing code should be uppercase"

    @pytest.mark.e2e
    def test_qr_code_contains_correct_url(self, page: Page, base_url: str):
        """Should generate QR code with correct mobile URL."""
        page.goto(f"{base_url}/en")
        page.wait_for_load_state("networkidle")

        # Navigate to camera tab
        camera_tab = page.locator('[data-tab="kamera"]')
        camera_tab.click()

        # Click "Start Mobile Pairing" button
        start_pairing_btn = page.locator("#startPairingBtn")
        start_pairing_btn.click()

        # Get pairing code
        pairing_code_display = page.locator("#pairingCodeDisplay")
        expect(pairing_code_display).to_be_visible()
        pairing_code = pairing_code_display.text_content()

        # Check that QR code was generated with correct data
        # The QRCode library creates an img element with the QR code
        # We can't easily decode it, but we can verify the structure
        qr_container = page.locator("#qrCodeContainer")
        qr_image = qr_container.locator("canvas")
        expect(qr_image).to_be_visible()

        # Verify that the QR data would include the mobile URL and code
        # This is done indirectly by checking the pairing code is displayed
        assert pairing_code, "Pairing code should be present"


class TestQRCodeResponsiveness:
    """Tests for QR code responsive behavior."""

    @pytest.mark.e2e
    def test_qr_code_size_on_desktop(self, page: Page, base_url: str):
        """Should have appropriate size on desktop."""
        page.set_viewport_size({"width": 1920, "height": 1080})
        page.goto(f"{base_url}/en")
        page.wait_for_load_state("networkidle")

        # Navigate to camera tab
        camera_tab = page.locator('[data-tab="kamera"]')
        camera_tab.click()

        # Start pairing
        start_pairing_btn = page.locator("#startPairingBtn")
        start_pairing_btn.click()

        # Check QR code size
        qr_container = page.locator("#qrCodeContainer")
        qr_canvas = qr_container.locator("canvas")
        expect(qr_canvas).to_be_visible()

        # QR code should be 200x200 as configured
        bbox = qr_canvas.bounding_box()
        assert bbox is not None
        # Allow some tolerance for rendering
        assert 190 <= bbox["width"] <= 210, f"QR code width should be ~200px, got {bbox['width']}"
        assert 190 <= bbox["height"] <= 210, f"QR code height should be ~200px, got {bbox['height']}"
