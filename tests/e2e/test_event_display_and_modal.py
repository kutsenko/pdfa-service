"""E2E tests for event display and summary modal functionality.

Tests verify that:
1. Events are displayed in the event list during conversion
2. Event list container is visible when events are received
3. Event summary modal appears after successful conversion
4. Modal contains all received events
5. No JavaScript errors occur during event handling
"""

from __future__ import annotations

from pathlib import Path

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.e2e
@pytest.mark.playwright
class TestEventDisplayDuringConversion:
    """Test that events are displayed in real-time during conversion."""

    def test_event_list_container_appears_on_first_event(
        self, page: Page, test_data_dir: Path, base_url: str
    ) -> None:
        """Test event list container becomes visible on first event."""
        medium_pdf = test_data_dir / "medium.pdf"

        if not medium_pdf.exists():
            from tests.e2e.test_data.pdf_generator import create_medium_pdf

            create_medium_pdf(medium_pdf)

        page.goto(base_url if base_url else "http://localhost:8001")

        # Event list container should be hidden initially
        event_container = page.locator("#eventListContainer")
        expect(event_container).not_to_be_visible()

        # Upload and submit
        page.set_input_files('input[type="file"]', medium_pdf)
        page.wait_for_timeout(500)
        page.click("#convertBtn")

        # Wait for first event - container should become visible
        # Container becomes visible via style.display = 'block'
        page.wait_for_function(
            "document.getElementById('eventListContainer').style.display === 'block'",
            timeout=10000,
        )

        # Verify container is visible
        expect(event_container).to_be_visible()

    def test_events_are_added_to_event_list(
        self, page: Page, test_data_dir: Path, base_url: str
    ) -> None:
        """Test that events are actually added to the DOM event list."""
        medium_pdf = test_data_dir / "medium.pdf"

        if not medium_pdf.exists():
            from tests.e2e.test_data.pdf_generator import create_medium_pdf

            create_medium_pdf(medium_pdf)

        page.goto(base_url if base_url else "http://localhost:8001")

        # Upload and submit
        page.set_input_files('input[type="file"]', medium_pdf)
        page.wait_for_timeout(500)
        page.click("#convertBtn")

        # Wait for event list to have items
        page.wait_for_selector("#eventList .event-item", timeout=10000)

        # Get all event items
        event_items = page.locator("#eventList .event-item")

        # Should have at least 1 event
        count = event_items.count()
        assert count >= 1, f"Expected at least 1 event in list, got {count}"

        # Verify event items have correct structure
        first_event = event_items.first
        expect(first_event).to_have_attribute("role", "article")

        # Event should have icon, timestamp, and message
        expect(first_event.locator(".event-icon")).to_be_visible()
        expect(first_event.locator(".event-timestamp")).to_be_visible()
        expect(first_event.locator(".event-message")).to_be_visible()

    def test_event_count_badge_updates(
        self, page: Page, test_data_dir: Path, base_url: str
    ) -> None:
        """Test that event count badge shows correct number."""
        medium_pdf = test_data_dir / "medium.pdf"

        if not medium_pdf.exists():
            from tests.e2e.test_data.pdf_generator import create_medium_pdf

            create_medium_pdf(medium_pdf)

        page.goto(base_url if base_url else "http://localhost:8001")

        # Initial count should be 0
        event_count = page.locator("#eventCount")
        expect(event_count).to_have_text("0")

        # Upload and submit
        page.set_input_files('input[type="file"]', medium_pdf)
        page.wait_for_timeout(500)
        page.click("#convertBtn")

        # Wait for first event
        page.wait_for_selector("#eventList .event-item", timeout=10000)

        # Count should be updated (at least 1)
        # Use a more flexible assertion since count may vary
        page.wait_for_function(
            "document.getElementById('eventCount').textContent !== '0'",
            timeout=5000,
        )

        count_text = event_count.inner_text()
        count_value = int(count_text)
        assert count_value >= 1, f"Expected count >= 1, got {count_value}"

    def test_no_javascript_errors_during_event_handling(
        self, page: Page, test_data_dir: Path, base_url: str
    ) -> None:
        """Test that no JavaScript errors occur when events are received."""
        medium_pdf = test_data_dir / "medium.pdf"

        if not medium_pdf.exists():
            from tests.e2e.test_data.pdf_generator import create_medium_pdf

            create_medium_pdf(medium_pdf)

        # Collect console errors
        console_errors = []

        def on_console(msg):
            if msg.type == "error":
                console_errors.append(msg.text)

        page.on("console", on_console)

        page.goto(base_url if base_url else "http://localhost:8001")

        # Upload and submit
        page.set_input_files('input[type="file"]', medium_pdf)
        page.wait_for_timeout(500)
        page.click("#convertBtn")

        # Wait for events to be received
        page.wait_for_selector("#eventList .event-item", timeout=10000)

        # Wait a bit more to catch any delayed errors
        page.wait_for_timeout(2000)

        # Filter out known unrelated errors (Firefox internal, etc.)
        relevant_errors = [
            err
            for err in console_errors
            if "translations is not defined" in err
            or "ReferenceError" in err
            or "handleJobEvent" in err
            or "addEventToList" in err
            or "translateEventMessage" in err
        ]

        assert (
            len(relevant_errors) == 0
        ), f"JavaScript errors occurred during event handling: {relevant_errors}"

    def test_event_list_toggle_functionality(
        self, page: Page, test_data_dir: Path, base_url: str
    ) -> None:
        """Test that event list can be toggled open/closed."""
        medium_pdf = test_data_dir / "medium.pdf"

        if not medium_pdf.exists():
            from tests.e2e.test_data.pdf_generator import create_medium_pdf

            create_medium_pdf(medium_pdf)

        page.goto(base_url if base_url else "http://localhost:8001")

        # Upload and submit
        page.set_input_files('input[type="file"]', medium_pdf)
        page.wait_for_timeout(500)
        page.click("#convertBtn")

        # Wait for container to appear
        page.wait_for_selector("#eventListContainer.visible", timeout=10000)

        # Event list should be expanded by default (or after first event)
        event_list = page.locator("#eventList")
        toggle_btn = page.locator("#eventListToggle")

        # Click toggle to collapse
        toggle_btn.click()
        page.wait_for_timeout(300)

        # List should now be hidden
        expect(event_list).to_be_hidden()

        # Toggle should have aria-expanded="false"
        expect(toggle_btn).to_have_attribute("aria-expanded", "false")

        # Click toggle to expand
        toggle_btn.click()
        page.wait_for_timeout(300)

        # List should be visible again
        expect(event_list).to_be_visible()
        expect(toggle_btn).to_have_attribute("aria-expanded", "true")


@pytest.mark.e2e
@pytest.mark.playwright
class TestEventSummaryModal:
    """Test event summary modal functionality after conversion completion."""

    def test_modal_appears_after_successful_conversion(
        self, page: Page, test_data_dir: Path, base_url: str
    ) -> None:
        """Test that event summary modal appears after download completes."""
        medium_pdf = test_data_dir / "medium.pdf"

        if not medium_pdf.exists():
            from tests.e2e.test_data.pdf_generator import create_medium_pdf

            create_medium_pdf(medium_pdf)

        page.goto(base_url if base_url else "http://localhost:8001")

        # Upload and submit
        page.set_input_files('input[type="file"]', medium_pdf)
        page.wait_for_timeout(500)
        page.click("#convertBtn")

        # Wait for conversion to complete and modal to appear
        # Modal should appear shortly after download (500ms delay in code)
        modal = page.locator("#eventSummaryModal")
        page.wait_for_selector("#eventSummaryModal[open]", timeout=60000)

        # Modal should be visible (open attribute set)
        expect(modal).to_have_attribute("open", "")

    def test_modal_contains_events(
        self, page: Page, test_data_dir: Path, base_url: str
    ) -> None:
        """Test that modal contains the events from conversion."""
        medium_pdf = test_data_dir / "medium.pdf"

        if not medium_pdf.exists():
            from tests.e2e.test_data.pdf_generator import create_medium_pdf

            create_medium_pdf(medium_pdf)

        page.goto(base_url if base_url else "http://localhost:8001")

        # Upload and submit
        page.set_input_files('input[type="file"]', medium_pdf)
        page.wait_for_timeout(500)
        page.click("#convertBtn")

        # Wait for modal to appear
        page.wait_for_selector("#eventSummaryModal[open]", timeout=60000)

        # Check modal event list has items
        modal_event_items = page.locator("#modalEventList .modal-event-item")
        count = modal_event_items.count()

        # Should have at least 1 event (format_conversion is always logged)
        assert count >= 1, f"Expected at least 1 event in modal, got {count}"

        # Verify modal events have correct structure
        first_event = modal_event_items.first
        expect(first_event).to_have_attribute("role", "listitem")

        # Event should have icon, timestamp, type, and message
        expect(first_event.locator(".modal-event-icon")).to_be_visible()
        expect(first_event.locator(".modal-event-timestamp")).to_be_visible()
        expect(first_event.locator(".modal-event-type")).to_be_visible()
        expect(first_event.locator(".modal-event-message")).to_be_visible()

    def test_modal_close_button_works(
        self, page: Page, test_data_dir: Path, base_url: str
    ) -> None:
        """Test that modal can be closed with close button."""
        medium_pdf = test_data_dir / "medium.pdf"

        if not medium_pdf.exists():
            from tests.e2e.test_data.pdf_generator import create_medium_pdf

            create_medium_pdf(medium_pdf)

        page.goto(base_url if base_url else "http://localhost:8001")

        # Upload and submit
        page.set_input_files('input[type="file"]', medium_pdf)
        page.wait_for_timeout(500)
        page.click("#convertBtn")

        # Wait for modal to appear
        modal = page.locator("#eventSummaryModal")
        page.wait_for_selector("#eventSummaryModal[open]", timeout=60000)

        # Click close button
        page.click("#modalCloseBtn")
        page.wait_for_timeout(300)

        # Modal should no longer have open attribute
        expect(modal).not_to_have_attribute("open")

    def test_modal_ok_button_works(
        self, page: Page, test_data_dir: Path, base_url: str
    ) -> None:
        """Test that modal can be closed with OK button."""
        medium_pdf = test_data_dir / "medium.pdf"

        if not medium_pdf.exists():
            from tests.e2e.test_data.pdf_generator import create_medium_pdf

            create_medium_pdf(medium_pdf)

        page.goto(base_url if base_url else "http://localhost:8001")

        # Upload and submit
        page.set_input_files('input[type="file"]', medium_pdf)
        page.wait_for_timeout(500)
        page.click("#convertBtn")

        # Wait for modal to appear
        modal = page.locator("#eventSummaryModal")
        page.wait_for_selector("#eventSummaryModal[open]", timeout=60000)

        # Click OK button
        page.click("#modalOkBtn")
        page.wait_for_timeout(300)

        # Modal should be closed
        expect(modal).not_to_have_attribute("open")

    def test_modal_download_button_works(
        self, page: Page, test_data_dir: Path, base_url: str
    ) -> None:
        """Test that download button in modal triggers download."""
        medium_pdf = test_data_dir / "medium.pdf"

        if not medium_pdf.exists():
            from tests.e2e.test_data.pdf_generator import create_medium_pdf

            create_medium_pdf(medium_pdf)

        page.goto(base_url if base_url else "http://localhost:8001")

        # Setup download listener
        download_promise = None

        def setup_download_listener():
            nonlocal download_promise
            download_promise = page.expect_download()

        # Upload and submit
        page.set_input_files('input[type="file"]', medium_pdf)
        page.wait_for_timeout(500)
        page.click("#convertBtn")

        # Wait for modal to appear
        page.wait_for_selector("#eventSummaryModal[open]", timeout=60000)

        # Setup download expectation before clicking
        with page.expect_download() as download_info:
            page.click("#modalDownloadBtn")

        # Download should occur
        download = download_info.value
        assert download.suggested_filename.endswith("_pdfa.pdf")

        # Modal should remain open (download doesn't close it)
        modal = page.locator("#eventSummaryModal")
        expect(modal).to_have_attribute("open", "")

    def test_modal_backdrop_click_closes_modal(
        self, page: Page, test_data_dir: Path, base_url: str
    ) -> None:
        """Test that clicking modal backdrop closes the modal."""
        medium_pdf = test_data_dir / "medium.pdf"

        if not medium_pdf.exists():
            from tests.e2e.test_data.pdf_generator import create_medium_pdf

            create_medium_pdf(medium_pdf)

        page.goto(base_url if base_url else "http://localhost:8001")

        # Upload and submit
        page.set_input_files('input[type="file"]', medium_pdf)
        page.wait_for_timeout(500)
        page.click("#convertBtn")

        # Wait for modal to appear
        modal = page.locator("#eventSummaryModal")
        page.wait_for_selector("#eventSummaryModal[open]", timeout=60000)

        # Click on the modal element itself (backdrop)
        # Get modal position
        modal_box = modal.bounding_box()

        # Click outside the modal content (on backdrop)
        # Modal content is centered, so click at the edge
        if modal_box:
            page.mouse.click(modal_box["x"] + 10, modal_box["y"] + 10)
            page.wait_for_timeout(300)

            # Modal should be closed
            expect(modal).not_to_have_attribute("open")

    def test_no_errors_when_showing_modal(
        self, page: Page, test_data_dir: Path, base_url: str
    ) -> None:
        """Test that no JavaScript errors occur when showing modal."""
        medium_pdf = test_data_dir / "medium.pdf"

        if not medium_pdf.exists():
            from tests.e2e.test_data.pdf_generator import create_medium_pdf

            create_medium_pdf(medium_pdf)

        # Collect console errors
        console_errors = []

        def on_console(msg):
            if msg.type == "error":
                console_errors.append(msg.text)

        page.on("console", on_console)

        page.goto(base_url if base_url else "http://localhost:8001")

        # Upload and submit
        page.set_input_files('input[type="file"]', medium_pdf)
        page.wait_for_timeout(500)
        page.click("#convertBtn")

        # Wait for modal to appear
        page.wait_for_selector("#eventSummaryModal[open]", timeout=60000)

        # Wait a bit more to catch any delayed errors
        page.wait_for_timeout(2000)

        # Filter for relevant errors
        relevant_errors = [
            err
            for err in console_errors
            if "translations is not defined" in err
            or "showEventSummaryModal" in err
            or "createModalEventItem" in err
            or "translateEventMessage" in err
        ]

        assert (
            len(relevant_errors) == 0
        ), f"JavaScript errors occurred when showing modal: {relevant_errors}"


@pytest.mark.e2e
@pytest.mark.playwright
class TestEventAndModalIntegration:
    """Test integration between event list and summary modal."""

    def test_modal_shows_same_events_as_list(
        self, page: Page, test_data_dir: Path, base_url: str
    ) -> None:
        """Test that modal contains the same events that were in the event list."""
        medium_pdf = test_data_dir / "medium.pdf"

        if not medium_pdf.exists():
            from tests.e2e.test_data.pdf_generator import create_medium_pdf

            create_medium_pdf(medium_pdf)

        page.goto(base_url if base_url else "http://localhost:8001")

        # Upload and submit
        page.set_input_files('input[type="file"]', medium_pdf)
        page.wait_for_timeout(500)
        page.click("#convertBtn")

        # Wait for events to appear in list
        page.wait_for_selector("#eventList .event-item", timeout=10000)

        # Get event count from list
        list_event_count = page.locator("#eventList .event-item").count()

        # Wait for modal to appear
        page.wait_for_selector("#eventSummaryModal[open]", timeout=60000)

        # Get event count from modal
        modal_event_count = page.locator("#modalEventList .modal-event-item").count()

        # Counts should match
        assert list_event_count == modal_event_count, (
            f"Event list had {list_event_count} events, "
            f"but modal has {modal_event_count}"
        )

    def test_console_logging_shows_event_flow(
        self, page: Page, test_data_dir: Path, base_url: str
    ) -> None:
        """Test that console logs show correct event flow (for debugging)."""
        medium_pdf = test_data_dir / "medium.pdf"

        if not medium_pdf.exists():
            from tests.e2e.test_data.pdf_generator import create_medium_pdf

            create_medium_pdf(medium_pdf)

        # Collect console logs
        console_logs = []

        def on_console(msg):
            console_logs.append(msg.text)

        page.on("console", on_console)

        page.goto(base_url if base_url else "http://localhost:8001")

        # Upload and submit
        page.set_input_files('input[type="file"]', medium_pdf)
        page.wait_for_timeout(500)
        page.click("#convertBtn")

        # Wait for modal to appear
        page.wait_for_selector("#eventSummaryModal[open]", timeout=60000)

        # Check for expected log messages
        log_text = "\n".join(console_logs)

        # Should have handleJobEvent logs
        assert (
            "[handleJobEvent] Job event received:" in log_text
        ), "Expected handleJobEvent log not found"

        # Should have addEventToList logs
        assert (
            "[addEventToList] Adding event:" in log_text
        ), "Expected addEventToList log not found"

        # Should have showEventSummaryModal logs
        assert (
            "[showEventSummaryModal] Total events in array:" in log_text
        ), "Expected showEventSummaryModal log not found"

        # Should NOT have error about translations
        assert (
            "translations is not defined" not in log_text
        ), "Unexpected 'translations is not defined' error found in logs"
