"""Simple debug test to check what happens during conversion."""

from pathlib import Path
import pytest
from playwright.sync_api import Page

pytestmark = [pytest.mark.e2e, pytest.mark.playwright]


@pytest.fixture(scope="module")
def test_pdf(tmp_path_factory) -> Path:
    """Generate a test PDF."""
    from tests.e2e.test_data.pdf_generator import create_small_pdf

    test_dir = tmp_path_factory.mktemp("test_pdfs")
    pdf_path = test_dir / "debug_test.pdf"
    create_small_pdf(pdf_path, num_pages=2)
    return pdf_path


def test_simple_upload_and_debug(page_with_server: Page, test_pdf: Path) -> None:
    """Simple test to debug what happens when uploading a file."""
    page = page_with_server

    # Capture all console messages
    console_messages = []
    def capture_console(msg):
        text = f"[{msg.type}] {msg.text}"
        console_messages.append(text)
        # Print WebSocket messages immediately for debugging
        if "WebSocket message" in msg.text or "handleCompleted" in msg.text or "handleJobError" in msg.text:
            print(f"  >>> {text}")

    page.on("console", capture_console)

    # Capture all errors
    errors = []
    page.on("pageerror", lambda err: errors.append(str(err)))

    print("\n=== Loading page ===")
    page.goto("http://localhost:8001/en")
    page.screenshot(path="/tmp/01_page_loaded.png")
    print("Screenshot saved: /tmp/01_page_loaded.png")

    # Check if page loaded
    title = page.title()
    print(f"Page title: {title}")

    # Upload file
    print("\n=== Uploading file ===")
    file_input = page.locator('input[type="file"]')
    file_input.set_input_files(str(test_pdf))
    page.screenshot(path="/tmp/02_file_selected.png")
    print("Screenshot saved: /tmp/02_file_selected.png")

    # Check if filename appears
    file_name_display = page.locator("#fileName")
    filename_text = file_name_display.text_content()
    print(f"Filename displayed: {filename_text}")

    # Click convert button
    print("\n=== Clicking convert button ===")
    convert_btn = page.locator("#convertBtn")
    convert_btn.click()
    page.screenshot(path="/tmp/03_convert_clicked.png")
    print("Screenshot saved: /tmp/03_convert_clicked.png")

    # Wait a bit for something to happen
    print("\n=== Waiting 5 seconds ===")
    page.wait_for_timeout(5000)
    page.screenshot(path="/tmp/04_after_5_seconds.png")
    print("Screenshot saved: /tmp/04_after_5_seconds.png")

    # Check status element
    status_elem = page.locator("#status")
    status_class = status_elem.get_attribute("class")
    status_text = status_elem.text_content()
    status_visible = status_elem.is_visible()

    print(f"\nStatus element:")
    print(f"  class: {status_class}")
    print(f"  text: {status_text}")
    print(f"  visible: {status_visible}")

    # Check progress bar
    progress_bar = page.locator("#progressBarContainer")
    progress_visible = progress_bar.is_visible()
    print(f"\nProgress bar visible: {progress_visible}")

    # Print console messages
    print(f"\n=== Console Messages ({len(console_messages)}) ===")
    for msg in console_messages[:20]:  # First 20
        print(msg)

    # Print errors
    if errors:
        print(f"\n=== Page Errors ({len(errors)}) ===")
        for err in errors:
            print(err)

    # Check if WebSocket connected
    ws_status = page.evaluate("() => window.conversionClient ? 'Client exists' : 'No client'")
    print(f"\nWebSocket client: {ws_status}")

    # Wait longer to see if anything happens
    print("\n=== Waiting another 10 seconds ===")
    page.wait_for_timeout(10000)
    page.screenshot(path="/tmp/05_after_15_seconds.png")
    print("Screenshot saved: /tmp/05_after_15_seconds.png")

    # Final status check
    status_class_final = status_elem.get_attribute("class")
    status_text_final = status_elem.text_content()
    print(f"\nFinal status:")
    print(f"  class: {status_class_final}")
    print(f"  text: {status_text_final}")

    print("\n=== Checking for modal ===")
    # Wait a bit after completion for modal to appear (should be 500ms)
    page.wait_for_timeout(1000)

    # Check modal
    modal = page.locator("#eventSummaryModal")
    modal_visible = modal.is_visible()
    has_open = modal.evaluate("el => el.hasAttribute('open')")

    print(f"Modal visible: {modal_visible}")
    print(f"Modal has 'open' attribute: {has_open}")

    if modal_visible:
        # Check modal content
        modal_title = page.locator("#modalTitle").text_content()
        modal_events = page.locator("#modalEventList .event-item").count()
        print(f"Modal title: {modal_title}")
        print(f"Modal events: {modal_events}")
        page.screenshot(path="/tmp/06_modal_visible.png")
        print("Screenshot saved: /tmp/06_modal_visible.png")
    else:
        print("⚠️  MODAL NOT VISIBLE - This is the bug!")

        # Check events array
        events_in_array = page.evaluate(
            "() => window.conversionClient ? window.conversionClient.events.length : -1"
        )
        print(f"Events in JavaScript array: {events_in_array}")

    print("\n=== Test completed - check screenshots in /tmp/ ===")

    # This test always passes - it's just for debugging
    assert True
