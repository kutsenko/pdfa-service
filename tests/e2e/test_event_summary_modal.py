"""End-to-end tests for Event Summary Modal using Playwright.

These tests verify the Event Summary Modal feature (US-004) in real browsers:
- Modal appearance after successful conversion
- Modal content (events, buttons, translations)
- Modal interactions (close, download)
- Keyboard navigation and accessibility
- Multi-language support (DE, EN, ES, FR)
- Dark mode support
- Edge cases (no events, many events)

Related: US-004 (Live Display of Conversion Events)
"""

from __future__ import annotations

from pathlib import Path

import pytest
from playwright.sync_api import Page, expect

# Mark all tests in this module as e2e and playwright
pytestmark = [pytest.mark.e2e, pytest.mark.playwright]


@pytest.fixture(scope="module")
def test_pdfs() -> dict[str, Path]:
    """Generate and return paths to test PDF files."""
    from tests.e2e.test_data.pdf_generator import create_small_pdf

    test_dir = Path(__file__).parent / "test_data"
    test_dir.mkdir(parents=True, exist_ok=True)

    pdfs = {
        "small": test_dir / "modal_test_small.pdf",
    }

    # Create PDF if it doesn't exist
    if not pdfs["small"].exists():
        create_small_pdf(pdfs["small"], num_pages=3)

    return pdfs


class TestEventSummaryModalBasics:
    """Test basic modal functionality."""

    def test_modal_appears_after_conversion(
        self, page_with_server: Page, test_pdfs: dict[str, Path]
    ) -> None:
        """Test that modal appears 500ms after successful conversion."""
        page = page_with_server
        page.goto("http://localhost:8000/en")

        # Upload and convert file
        file_input = page.locator('input[type="file"]')
        file_input.set_input_files(test_pdfs["small"])

        convert_btn = page.locator("#convertBtn")
        convert_btn.click()

        # Wait for conversion to complete
        # Look for success status
        page.wait_for_selector(".status.success", timeout=30000)

        # Wait for modal to appear (500ms delay + buffer)
        modal = page.locator("#eventSummaryModal")
        expect(modal).to_be_visible(timeout=5000)

        # Verify modal is actually shown (has open attribute)
        expect(modal).to_have_attribute("open", "")

    def test_modal_contains_required_elements(
        self, page_with_server: Page, test_pdfs: dict[str, Path]
    ) -> None:
        """Test that modal contains all required UI elements."""
        page = page_with_server
        page.goto("http://localhost:8000/en")

        # Upload and convert
        file_input = page.locator('input[type="file"]')
        file_input.set_input_files(test_pdfs["small"])
        page.locator("#convertBtn").click()

        # Wait for modal
        modal = page.locator("#eventSummaryModal")
        modal.wait_for(state="visible", timeout=35000)

        # Check title
        title = modal.locator("#modalTitle")
        expect(title).to_be_visible()
        expect(title).to_contain_text("Conversion Summary")

        # Check description
        description = modal.locator(".modal-description")
        expect(description).to_be_visible()
        expect(description).to_contain_text("successfully converted")

        # Check event list
        event_list = modal.locator("#modalEventList")
        expect(event_list).to_be_visible()

        # Check buttons
        ok_btn = modal.locator("#modalOkBtn")
        expect(ok_btn).to_be_visible()
        expect(ok_btn).to_contain_text("OK")

        download_btn = modal.locator("#modalDownloadBtn")
        expect(download_btn).to_be_visible()
        expect(download_btn).to_contain_text("Download")

        # Check close button
        close_btn = modal.locator("#modalCloseBtn")
        expect(close_btn).to_be_visible()

    def test_modal_displays_events(
        self, page_with_server: Page, test_pdfs: dict[str, Path]
    ) -> None:
        """Test that modal displays conversion events."""
        page = page_with_server
        page.goto("http://localhost:8000/en")

        # Upload and convert
        file_input = page.locator('input[type="file"]')
        file_input.set_input_files(test_pdfs["small"])
        page.locator("#convertBtn").click()

        # Wait for modal
        modal = page.locator("#eventSummaryModal")
        modal.wait_for(state="visible", timeout=35000)

        # Check that events are displayed
        event_items = modal.locator(".event-item")
        expect(event_items).not_to_have_count(0)

        # Check first event has required structure
        first_event = event_items.first
        expect(first_event.locator(".event-icon")).to_be_visible()
        expect(first_event.locator(".event-message")).to_be_visible()
        expect(first_event.locator(".event-timestamp")).to_be_visible()

    def test_modal_focus_on_ok_button(
        self, page_with_server: Page, test_pdfs: dict[str, Path]
    ) -> None:
        """Test that OK button receives focus when modal opens."""
        page = page_with_server
        page.goto("http://localhost:8000/en")

        # Upload and convert
        file_input = page.locator('input[type="file"]')
        file_input.set_input_files(test_pdfs["small"])
        page.locator("#convertBtn").click()

        # Wait for modal
        modal = page.locator("#eventSummaryModal")
        modal.wait_for(state="visible", timeout=35000)

        # Check that OK button has focus
        ok_btn = modal.locator("#modalOkBtn")
        expect(ok_btn).to_be_focused()


class TestEventSummaryModalInteractions:
    """Test modal interaction patterns."""

    def test_ok_button_closes_modal(
        self, page_with_server: Page, test_pdfs: dict[str, Path]
    ) -> None:
        """Test that clicking OK button closes the modal."""
        page = page_with_server
        page.goto("http://localhost:8000/en")

        # Upload and convert
        file_input = page.locator('input[type="file"]')
        file_input.set_input_files(test_pdfs["small"])
        page.locator("#convertBtn").click()

        # Wait for modal
        modal = page.locator("#eventSummaryModal")
        modal.wait_for(state="visible", timeout=35000)

        # Click OK button
        ok_btn = modal.locator("#modalOkBtn")
        ok_btn.click()

        # Verify modal is closed
        expect(modal).not_to_be_visible()
        expect(modal).not_to_have_attribute("open")

    def test_close_button_closes_modal(
        self, page_with_server: Page, test_pdfs: dict[str, Path]
    ) -> None:
        """Test that clicking X button closes the modal."""
        page = page_with_server
        page.goto("http://localhost:8000/en")

        # Upload and convert
        file_input = page.locator('input[type="file"]')
        file_input.set_input_files(test_pdfs["small"])
        page.locator("#convertBtn").click()

        # Wait for modal
        modal = page.locator("#eventSummaryModal")
        modal.wait_for(state="visible", timeout=35000)

        # Click close button
        close_btn = modal.locator("#modalCloseBtn")
        close_btn.click()

        # Verify modal is closed
        expect(modal).not_to_be_visible()

    def test_escape_key_closes_modal(
        self, page_with_server: Page, test_pdfs: dict[str, Path]
    ) -> None:
        """Test that pressing Escape closes the modal."""
        page = page_with_server
        page.goto("http://localhost:8000/en")

        # Upload and convert
        file_input = page.locator('input[type="file"]')
        file_input.set_input_files(test_pdfs["small"])
        page.locator("#convertBtn").click()

        # Wait for modal
        modal = page.locator("#eventSummaryModal")
        modal.wait_for(state="visible", timeout=35000)

        # Press Escape
        page.keyboard.press("Escape")

        # Verify modal is closed
        expect(modal).not_to_be_visible()

    def test_backdrop_click_closes_modal(
        self, page_with_server: Page, test_pdfs: dict[str, Path]
    ) -> None:
        """Test that clicking backdrop closes the modal."""
        page = page_with_server
        page.goto("http://localhost:8000/en")

        # Upload and convert
        file_input = page.locator('input[type="file"]')
        file_input.set_input_files(test_pdfs["small"])
        page.locator("#convertBtn").click()

        # Wait for modal
        modal = page.locator("#eventSummaryModal")
        modal.wait_for(state="visible", timeout=35000)

        # Click on backdrop (outside modal content)
        # Get modal bounding box
        box = modal.bounding_box()
        assert box is not None

        # Click far outside the modal (top-left corner)
        page.mouse.click(10, 10)

        # Verify modal is closed
        expect(modal).not_to_be_visible()

    def test_inline_event_list_remains_visible(
        self, page_with_server: Page, test_pdfs: dict[str, Path]
    ) -> None:
        """Test that inline event list remains visible after modal closes."""
        page = page_with_server
        page.goto("http://localhost:8000/en")

        # Upload and convert
        file_input = page.locator('input[type="file"]')
        file_input.set_input_files(test_pdfs["small"])
        page.locator("#convertBtn").click()

        # Wait for modal
        modal = page.locator("#eventSummaryModal")
        modal.wait_for(state="visible", timeout=35000)

        # Check inline event list is visible
        inline_container = page.locator("#eventListContainer")
        expect(inline_container).to_be_visible()

        # Close modal
        ok_btn = modal.locator("#modalOkBtn")
        ok_btn.click()

        # Verify inline list is still visible
        expect(inline_container).to_be_visible()

    def test_download_button_triggers_download(
        self, page_with_server: Page, test_pdfs: dict[str, Path]
    ) -> None:
        """Test that download button in modal triggers file download."""
        page = page_with_server
        page.goto("http://localhost:8000/en")

        # Upload and convert
        file_input = page.locator('input[type="file"]')
        file_input.set_input_files(test_pdfs["small"])
        page.locator("#convertBtn").click()

        # Wait for modal
        modal = page.locator("#eventSummaryModal")
        modal.wait_for(state="visible", timeout=35000)

        # Set up download handler
        with page.expect_download() as download_info:
            download_btn = modal.locator("#modalDownloadBtn")
            download_btn.click()

        download = download_info.value

        # Verify download occurred
        assert download.suggested_filename.endswith(".pdf")

        # Modal should remain open after download
        expect(modal).to_be_visible()


class TestEventSummaryModalKeyboard:
    """Test keyboard navigation and accessibility."""

    def test_tab_navigation_cycles_through_buttons(
        self, page_with_server: Page, test_pdfs: dict[str, Path]
    ) -> None:
        """Test that Tab key cycles through modal buttons."""
        page = page_with_server
        page.goto("http://localhost:8000/en")

        # Upload and convert
        file_input = page.locator('input[type="file"]')
        file_input.set_input_files(test_pdfs["small"])
        page.locator("#convertBtn").click()

        # Wait for modal
        modal = page.locator("#eventSummaryModal")
        modal.wait_for(state="visible", timeout=35000)

        # OK button should have initial focus
        ok_btn = modal.locator("#modalOkBtn")
        expect(ok_btn).to_be_focused()

        # Tab to Download button
        page.keyboard.press("Tab")
        download_btn = modal.locator("#modalDownloadBtn")
        expect(download_btn).to_be_focused()

        # Tab to Close button
        page.keyboard.press("Tab")
        close_btn = modal.locator("#modalCloseBtn")
        expect(close_btn).to_be_focused()

        # Tab should cycle back to OK button
        page.keyboard.press("Tab")
        expect(ok_btn).to_be_focused()

    def test_shift_tab_navigation_reverse(
        self, page_with_server: Page, test_pdfs: dict[str, Path]
    ) -> None:
        """Test that Shift+Tab navigates backwards through buttons."""
        page = page_with_server
        page.goto("http://localhost:8000/en")

        # Upload and convert
        file_input = page.locator('input[type="file"]')
        file_input.set_input_files(test_pdfs["small"])
        page.locator("#convertBtn").click()

        # Wait for modal
        modal = page.locator("#eventSummaryModal")
        modal.wait_for(state="visible", timeout=35000)

        # OK button has initial focus
        ok_btn = modal.locator("#modalOkBtn")
        expect(ok_btn).to_be_focused()

        # Shift+Tab to Close button (reverse)
        page.keyboard.press("Shift+Tab")
        close_btn = modal.locator("#modalCloseBtn")
        expect(close_btn).to_be_focused()

    def test_enter_on_ok_button_closes_modal(
        self, page_with_server: Page, test_pdfs: dict[str, Path]
    ) -> None:
        """Test that Enter key on OK button closes modal."""
        page = page_with_server
        page.goto("http://localhost:8000/en")

        # Upload and convert
        file_input = page.locator('input[type="file"]')
        file_input.set_input_files(test_pdfs["small"])
        page.locator("#convertBtn").click()

        # Wait for modal
        modal = page.locator("#eventSummaryModal")
        modal.wait_for(state="visible", timeout=35000)

        # OK button should have focus
        ok_btn = modal.locator("#modalOkBtn")
        expect(ok_btn).to_be_focused()

        # Press Enter
        page.keyboard.press("Enter")

        # Verify modal is closed
        expect(modal).not_to_be_visible()


class TestEventSummaryModalAccessibility:
    """Test ARIA attributes and screen reader support."""

    def test_modal_has_required_aria_attributes(
        self, page_with_server: Page, test_pdfs: dict[str, Path]
    ) -> None:
        """Test that modal has correct ARIA attributes."""
        page = page_with_server
        page.goto("http://localhost:8000/en")

        # Upload and convert
        file_input = page.locator('input[type="file"]')
        file_input.set_input_files(test_pdfs["small"])
        page.locator("#convertBtn").click()

        # Wait for modal
        modal = page.locator("#eventSummaryModal")
        modal.wait_for(state="visible", timeout=35000)

        # Check aria-labelledby points to title
        expect(modal).to_have_attribute("aria-labelledby", "modalTitle")

        # Check modal title exists and has ID
        title = modal.locator("#modalTitle")
        expect(title).to_be_visible()

        # Check close button has aria-label
        close_btn = modal.locator("#modalCloseBtn")
        expect(close_btn).to_have_attribute("aria-label", "Close modal")

    def test_event_list_has_role_list(
        self, page_with_server: Page, test_pdfs: dict[str, Path]
    ) -> None:
        """Test that event list has correct role attribute."""
        page = page_with_server
        page.goto("http://localhost:8000/en")

        # Upload and convert
        file_input = page.locator('input[type="file"]')
        file_input.set_input_files(test_pdfs["small"])
        page.locator("#convertBtn").click()

        # Wait for modal
        modal = page.locator("#eventSummaryModal")
        modal.wait_for(state="visible", timeout=35000)

        # Check event list has role="list"
        event_list = modal.locator("#modalEventList")
        expect(event_list).to_have_attribute("role", "list")

        # Check event items have role="listitem"
        event_items = modal.locator(".event-item")
        first_item = event_items.first
        expect(first_item).to_have_attribute("role", "listitem")


class TestEventSummaryModalInternationalization:
    """Test multi-language support (i18n)."""

    def test_modal_german_translations(
        self, page_with_server: Page, test_pdfs: dict[str, Path]
    ) -> None:
        """Test that modal displays German translations correctly."""
        page = page_with_server
        page.goto("http://localhost:8000/de")

        # Upload and convert
        file_input = page.locator('input[type="file"]')
        file_input.set_input_files(test_pdfs["small"])
        page.locator("#convertBtn").click()

        # Wait for modal
        modal = page.locator("#eventSummaryModal")
        modal.wait_for(state="visible", timeout=35000)

        # Check German title
        title = modal.locator("#modalTitle")
        expect(title).to_contain_text("Konvertierungs-Zusammenfassung")

        # Check German description
        description = modal.locator(".modal-description")
        expect(description).to_contain_text("erfolgreich konvertiert")

        # Check German buttons
        ok_btn = modal.locator("#modalOkBtn")
        expect(ok_btn).to_contain_text("OK")

        download_btn = modal.locator("#modalDownloadBtn")
        expect(download_btn).to_contain_text("Herunterladen")

    def test_modal_spanish_translations(
        self, page_with_server: Page, test_pdfs: dict[str, Path]
    ) -> None:
        """Test that modal displays Spanish translations correctly."""
        page = page_with_server
        page.goto("http://localhost:8000/es")

        # Upload and convert
        file_input = page.locator('input[type="file"]')
        file_input.set_input_files(test_pdfs["small"])
        page.locator("#convertBtn").click()

        # Wait for modal
        modal = page.locator("#eventSummaryModal")
        modal.wait_for(state="visible", timeout=35000)

        # Check Spanish title
        title = modal.locator("#modalTitle")
        expect(title).to_contain_text("Resumen de Conversión")

        # Check Spanish description
        description = modal.locator(".modal-description")
        expect(description).to_contain_text("exitosamente")

        # Check Spanish buttons
        download_btn = modal.locator("#modalDownloadBtn")
        expect(download_btn).to_contain_text("Descargar")

    def test_modal_french_translations(
        self, page_with_server: Page, test_pdfs: dict[str, Path]
    ) -> None:
        """Test that modal displays French translations correctly."""
        page = page_with_server
        page.goto("http://localhost:8000/fr")

        # Upload and convert
        file_input = page.locator('input[type="file"]')
        file_input.set_input_files(test_pdfs["small"])
        page.locator("#convertBtn").click()

        # Wait for modal
        modal = page.locator("#eventSummaryModal")
        modal.wait_for(state="visible", timeout=35000)

        # Check French title
        title = modal.locator("#modalTitle")
        expect(title).to_contain_text("Résumé de Conversion")

        # Check French description
        description = modal.locator(".modal-description")
        expect(description).to_contain_text("avec succès")

        # Check French buttons
        download_btn = modal.locator("#modalDownloadBtn")
        expect(download_btn).to_contain_text("Télécharger")

    def test_modal_english_translations(
        self, page_with_server: Page, test_pdfs: dict[str, Path]
    ) -> None:
        """Test that modal displays English translations correctly."""
        page = page_with_server
        page.goto("http://localhost:8000/en")

        # Upload and convert
        file_input = page.locator('input[type="file"]')
        file_input.set_input_files(test_pdfs["small"])
        page.locator("#convertBtn").click()

        # Wait for modal
        modal = page.locator("#eventSummaryModal")
        modal.wait_for(state="visible", timeout=35000)

        # Check English title
        title = modal.locator("#modalTitle")
        expect(title).to_contain_text("Conversion Summary")

        # Check English description
        description = modal.locator(".modal-description")
        expect(description).to_contain_text("successfully converted")

        # Check English buttons
        download_btn = modal.locator("#modalDownloadBtn")
        expect(download_btn).to_contain_text("Download")


class TestEventSummaryModalEdgeCases:
    """Test edge cases and special scenarios."""

    def test_modal_handles_many_events_with_scroll(
        self, page_with_server: Page, test_pdfs: dict[str, Path]
    ) -> None:
        """Test that modal handles many events with scrollbar."""
        page = page_with_server
        page.goto("http://localhost:8000/en")

        # Upload and convert (small PDF might generate several events)
        file_input = page.locator('input[type="file"]')
        file_input.set_input_files(test_pdfs["small"])

        # Enable OCR to generate more events
        ocr_checkbox = page.locator('input[type="checkbox"][value="enable_ocr"]')
        if not ocr_checkbox.is_checked():
            ocr_checkbox.check()

        page.locator("#convertBtn").click()

        # Wait for modal
        modal = page.locator("#eventSummaryModal")
        modal.wait_for(state="visible", timeout=60000)

        # Check event list exists
        event_list = modal.locator("#modalEventList")
        expect(event_list).to_be_visible()

        # Check that events are present
        event_items = modal.locator(".event-item")
        expect(event_items).not_to_have_count(0)

        # Modal body should have overflow-y: auto for scrolling
        modal_body = modal.locator(".modal-body")
        overflow_y = modal_body.evaluate("el => getComputedStyle(el).overflowY")
        assert overflow_y in ["auto", "scroll"]

    def test_modal_responsive_on_narrow_viewport(
        self, page_with_server: Page, test_pdfs: dict[str, Path]
    ) -> None:
        """Test that modal is responsive on narrow viewports (mobile)."""
        page = page_with_server

        # Set narrow viewport (mobile)
        page.set_viewport_size({"width": 375, "height": 667})

        page.goto("http://localhost:8000/en")

        # Upload and convert
        file_input = page.locator('input[type="file"]')
        file_input.set_input_files(test_pdfs["small"])
        page.locator("#convertBtn").click()

        # Wait for modal
        modal = page.locator("#eventSummaryModal")
        modal.wait_for(state="visible", timeout=35000)

        # Verify modal is visible and fits viewport
        expect(modal).to_be_visible()

        # Check modal width is constrained (90vw)
        box = modal.bounding_box()
        assert box is not None
        # Modal should be narrower than viewport (90vw)
        assert box["width"] < 375

        # All buttons should be visible
        expect(modal.locator("#modalOkBtn")).to_be_visible()
        expect(modal.locator("#modalDownloadBtn")).to_be_visible()
        expect(modal.locator("#modalCloseBtn")).to_be_visible()


class TestEventSummaryModalDarkMode:
    """Test dark mode support."""

    def test_modal_dark_mode_styles(
        self, page_with_server: Page, test_pdfs: dict[str, Path]
    ) -> None:
        """Test that modal applies dark mode styles."""
        page = page_with_server

        # Emulate dark mode preference
        page.emulate_media(color_scheme="dark")

        page.goto("http://localhost:8000/en")

        # Upload and convert
        file_input = page.locator('input[type="file"]')
        file_input.set_input_files(test_pdfs["small"])
        page.locator("#convertBtn").click()

        # Wait for modal
        modal = page.locator("#eventSummaryModal")
        modal.wait_for(state="visible", timeout=35000)

        # Check modal background is dark
        bg_color = modal.evaluate("el => getComputedStyle(el).backgroundColor")
        # Should be dark gray (not white)
        # Dark mode uses #1f2937 which is rgb(31, 41, 55)
        assert "rgb(31, 41, 55)" in bg_color or "rgba(31, 41, 55" in bg_color

        # Check text color is light
        color = modal.evaluate("el => getComputedStyle(el).color")
        # Dark mode uses #e5e7eb which is rgb(229, 231, 235)
        assert "229" in color  # Light gray text in dark mode

    def test_modal_light_mode_styles(
        self, page_with_server: Page, test_pdfs: dict[str, Path]
    ) -> None:
        """Test that modal applies light mode styles."""
        page = page_with_server

        # Emulate light mode preference
        page.emulate_media(color_scheme="light")

        page.goto("http://localhost:8000/en")

        # Upload and convert
        file_input = page.locator('input[type="file"]')
        file_input.set_input_files(test_pdfs["small"])
        page.locator("#convertBtn").click()

        # Wait for modal
        modal = page.locator("#eventSummaryModal")
        modal.wait_for(state="visible", timeout=35000)

        # Check modal background is light (white)
        bg_color = modal.evaluate("el => getComputedStyle(el).backgroundColor")
        # Should be white or very light
        # Light mode uses white which is rgb(255, 255, 255)
        assert "255, 255, 255" in bg_color

        # Check text color is dark
        color = modal.evaluate("el => getComputedStyle(el).color")
        # Light mode uses #1f2937 which is rgb(31, 41, 55)
        assert "31, 41, 55" in color


class TestEventSummaryModalDebugging:
    """Debug tests to diagnose modal display issues."""

    def test_debug_modal_trigger_timing(
        self, page_with_server: Page, test_pdfs: dict[str, Path]
    ) -> None:
        """Debug test to check modal trigger timing and conditions.

        This test captures comprehensive debug information to diagnose
        why the modal might not appear after conversion.
        """
        page = page_with_server
        page.goto("http://localhost:8001/en")

        # Capture all console logs
        logs = []
        page.on("console", lambda msg: logs.append(f"{msg.type}: {msg.text}"))

        # Upload file
        file_input = page.locator('input[type="file"]')
        file_input.set_input_files(test_pdfs["small"])

        # Start conversion
        convert_btn = page.locator("#convertBtn")
        convert_btn.click()

        # Wait for conversion to complete
        page.wait_for_selector(".status.success", timeout=60000)

        # Wait extra time for modal trigger (500ms + buffer)
        page.wait_for_timeout(2000)

        # Check logs for modal-related messages
        modal_logs = [log for log in logs if "modal" in log.lower()]
        event_logs = [
            log for log in logs if "handleJobEvent" in log or "addEventToList" in log
        ]
        completed_logs = [log for log in logs if "handleCompleted" in log]
        show_modal_logs = [log for log in logs if "showEventSummaryModal" in log]

        print("\n=== MODAL RELATED LOGS ===")
        for log in modal_logs:
            print(log)

        print("\n=== EVENT LOGS ===")
        for log in event_logs[:10]:  # First 10 events
            print(log)

        print(f"\n=== TOTAL EVENTS LOGGED: {len(event_logs)} ===")

        print("\n=== COMPLETED LOGS ===")
        for log in completed_logs:
            print(log)

        # Check if showEventSummaryModal was called
        if not show_modal_logs:
            print("\n[FAIL] showEventSummaryModal() was NEVER called!")
            print("Possible reasons:")
            print("1. handleCompleted() not called")
            print("2. this.events.length === 0")
            print("3. setTimeout not executing")
        else:
            print(
                f"\n[INFO] showEventSummaryModal() called {len(show_modal_logs)} times"
            )
            for log in show_modal_logs:
                print(f"  {log}")

        # Check modal element state
        modal = page.locator("#eventSummaryModal")
        is_visible = modal.is_visible()
        has_open_attr = modal.evaluate("el => el.hasAttribute('open')")

        print("\n=== MODAL STATE ===")
        print(f"Is visible: {is_visible}")
        print(f"Has 'open' attribute: {has_open_attr}")

        # Check events array in JavaScript
        events_length = page.evaluate(
            "() => window.conversionClient ? window.conversionClient.events.length : -1"
        )
        print(f"Events in client array: {events_length}")

        # Check inline event list
        event_list = page.locator("#eventList")
        inline_events = event_list.locator(".event-item").count()
        print(f"Inline events in DOM: {inline_events}")

        # This test always passes but provides debug output
        print("\n[INFO] Debug test completed - check output above")

    def test_events_display_in_inline_list(
        self, page_with_server: Page, test_pdfs: dict[str, Path]
    ) -> None:
        """Verify events displayed in inline event list during conversion."""
        page = page_with_server
        page.goto("http://localhost:8001/en")

        # Enable console logging
        received_events = []

        def log_console(msg):
            text = msg.text
            if "[handleJobEvent]" in text or "[addEventToList]" in text:
                received_events.append(text)
                print(f"[Console] {text}")

        page.on("console", log_console)

        # Upload and convert
        file_input = page.locator('input[type="file"]')
        file_input.set_input_files(test_pdfs["small"])

        convert_btn = page.locator("#convertBtn")
        convert_btn.click()

        # Wait for first event to appear
        event_list_container = page.locator("#eventListContainer")
        event_list_container.wait_for(state="visible", timeout=10000)

        # Wait for conversion to complete
        page.wait_for_selector(".status.success", timeout=60000)

        # Check inline event list
        event_list = page.locator("#eventList")
        inline_events = event_list.locator(".event-item").count()

        print(f"\n[INFO] Inline events displayed: {inline_events}")
        print(f"[INFO] WebSocket events received: {len(received_events)}")

        assert inline_events > 0, (
            f"No events displayed in inline list. "
            f"WebSocket events received: {len(received_events)}"
        )
