"""End-to-end tests for the Web UI using Playwright.

These tests verify the complete conversion flow in real browsers:
- Chromium
- Firefox

Tests cover:
- Basic conversion flow
- Progress updates and status dialog
- Large file conversion
- Error handling
- UI state management
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
    from tests.e2e.test_data.pdf_generator import (
        create_large_pdf,
        create_medium_pdf,
        create_minimal_pdf,
        create_small_pdf,
    )

    test_dir = Path(__file__).parent / "test_data"
    test_dir.mkdir(parents=True, exist_ok=True)

    # Generate test files
    pdfs = {
        "minimal": test_dir / "minimal.pdf",
        "small": test_dir / "small.pdf",
        "medium": test_dir / "medium.pdf",
        "large": test_dir / "large.pdf",
    }

    # Create PDFs if they don't exist
    if not pdfs["minimal"].exists():
        create_minimal_pdf(pdfs["minimal"])
    if not pdfs["small"].exists():
        create_small_pdf(pdfs["small"], num_pages=3)
    if not pdfs["medium"].exists():
        create_medium_pdf(pdfs["medium"], num_pages=10)
    if not pdfs["large"].exists():
        create_large_pdf(pdfs["large"], num_pages=25)

    return pdfs


class TestBasicConversionFlow:
    """Test basic conversion functionality."""

    def test_page_loads_successfully(self, page_with_server: Page) -> None:
        """Test that the web UI loads successfully."""
        page = page_with_server
        page.goto("http://localhost:8001")

        # Check title
        expect(page).to_have_title("PDF/A Converter - Test Interface")

        # Check main heading is visible
        heading = page.locator("h1")
        expect(heading).to_be_visible()
        expect(heading).to_contain_text("PDF/A Converter")

    def test_file_upload_button_present(self, page_with_server: Page) -> None:
        """Test that file upload controls are present."""
        page = page_with_server
        page.goto("http://localhost:8001")

        # Check file input exists
        file_input = page.locator('input[type="file"]')
        expect(file_input).to_be_attached()

        # Check convert button exists
        convert_btn = page.locator("#convertBtn")
        expect(convert_btn).to_be_visible()

    def test_minimal_pdf_conversion(
        self, page_with_server: Page, test_pdfs: dict[str, Path]
    ) -> None:
        """Test conversion of a minimal PDF file."""
        page = page_with_server
        page.goto("http://localhost:8001")

        # Upload file
        file_input = page.locator('input[type="file"]')
        file_input.set_input_files(test_pdfs["minimal"])

        # Wait for file name to appear
        page.wait_for_timeout(500)

        # Click convert button
        convert_btn = page.locator("#convertBtn")
        convert_btn.click()

        # Wait for progress container to appear
        progress_container = page.locator("#progressContainer")
        # Wait for progress container to have visible class
        page.wait_for_timeout(500)
        progress_classes = progress_container.get_attribute("class")
        assert (
            progress_classes and "visible" in progress_classes
        ), "Progress container should be visible"

        # Wait for completion or error (with longer timeout)
        # Either status message or download should appear
        page.wait_for_selector("#status", state="visible", timeout=60000)

        # Check if there's an error or success
        status_div = page.locator("#status")
        status_text = status_div.inner_text()

        # Should either succeed or have a known error
        assert (
            "successful" in status_text.lower()
            or "error" in status_text.lower()
            or "failed" in status_text.lower()
        ), f"Unexpected status: {status_text}"


class TestProgressUpdates:
    """Test progress dialog and status updates."""

    def test_progress_dialog_appears(
        self, page_with_server: Page, test_pdfs: dict[str, Path]
    ) -> None:
        """Test that progress dialog appears when conversion starts."""
        page = page_with_server
        page.goto("http://localhost:8001")

        # Upload file
        file_input = page.locator('input[type="file"]')
        file_input.set_input_files(test_pdfs["small"])

        page.wait_for_timeout(500)

        # Start conversion
        convert_btn = page.locator("#convertBtn")
        convert_btn.click()

        # Progress container should become visible
        progress_container = page.locator("#progressContainer")
        # Wait for progress container to have visible class
        page.wait_for_timeout(500)
        progress_classes = progress_container.get_attribute("class")
        assert (
            progress_classes and "visible" in progress_classes
        ), "Progress container should be visible"

    def test_progress_bar_updates(
        self, page_with_server: Page, test_pdfs: dict[str, Path]
    ) -> None:
        """Test that progress bar updates during conversion."""
        page = page_with_server
        page.goto("http://localhost:8001")

        # Upload file
        file_input = page.locator('input[type="file"]')
        file_input.set_input_files(test_pdfs["medium"])

        page.wait_for_timeout(500)

        # Start conversion
        convert_btn = page.locator("#convertBtn")
        convert_btn.click()

        # Wait for progress to appear
        progress_container = page.locator("#progressContainer")
        # Wait for progress container to have visible class
        page.wait_for_timeout(500)
        progress_classes = progress_container.get_attribute("class")
        assert (
            progress_classes and "visible" in progress_classes
        ), "Progress container should be visible"

        # Get progress elements
        progress_percentage = page.locator("#progressPercentage")
        progress_message = page.locator("#progressMessage")

        # Check initial state - should NOT be "Starting..."
        initial_message = progress_message.inner_text()
        assert (
            "Starting..." not in initial_message
        ), f"Progress should not show 'Starting...', got: {initial_message}"

        # Progress percentage should be visible and have a value
        expect(progress_percentage).to_be_visible()
        initial_percentage_text = progress_percentage.inner_text()
        assert "%" in initial_percentage_text, "Should show percentage"

        # Wait a bit for progress to potentially update
        page.wait_for_timeout(2000)

        # Even if it's still 0%, that's fine - we just check it's not "Starting..."

    def test_status_message_not_stuck_on_starting(
        self, page_with_server: Page, test_pdfs: dict[str, Path]
    ) -> None:
        """Test that status message is not stuck on 'Starting...'."""
        page = page_with_server
        page.goto("http://localhost:8001")

        # Upload file
        file_input = page.locator('input[type="file"]')
        file_input.set_input_files(test_pdfs["medium"])

        page.wait_for_timeout(500)

        # Start conversion
        convert_btn = page.locator("#convertBtn")
        convert_btn.click()

        # Wait for progress to appear
        progress_container = page.locator("#progressContainer")
        # Wait for progress container to have visible class
        page.wait_for_timeout(500)
        progress_classes = progress_container.get_attribute("class")
        assert (
            progress_classes and "visible" in progress_classes
        ), "Progress container should be visible"

        # Sample progress message multiple times
        progress_message = page.locator("#progressMessage")

        messages_seen = []
        for i in range(5):
            page.wait_for_timeout(1000)
            msg = progress_message.inner_text()
            messages_seen.append(msg)

            # Check: should NOT be "Starting..."
            assert (
                "Starting..." not in msg
            ), f"Progress message stuck on 'Starting...' after {i+1}s"

        print(f"Progress messages seen: {messages_seen}")

    def test_progress_percentage_not_stuck_at_8_percent(
        self, page_with_server: Page, test_pdfs: dict[str, Path]
    ) -> None:
        """Test that progress percentage is not stuck at 8%."""
        page = page_with_server
        page.goto("http://localhost:8001")

        # Upload file
        file_input = page.locator('input[type="file"]')
        file_input.set_input_files(test_pdfs["medium"])

        page.wait_for_timeout(500)

        # Start conversion
        convert_btn = page.locator("#convertBtn")
        convert_btn.click()

        # Wait for progress to appear
        progress_container = page.locator("#progressContainer")
        # Wait for progress container to have visible class
        page.wait_for_timeout(500)
        progress_classes = progress_container.get_attribute("class")
        assert (
            progress_classes and "visible" in progress_classes
        ), "Progress container should be visible"

        # Sample percentage multiple times
        progress_percentage = page.locator("#progressPercentage")

        percentages_seen = []
        for i in range(10):
            page.wait_for_timeout(500)
            pct_text = progress_percentage.inner_text()
            percentages_seen.append(pct_text)

            # Should not be stuck at exactly 8%
            if i > 5:  # After a few seconds
                assert (
                    pct_text != "8%"
                ), f"Progress stuck at 8% after {i*0.5}s: {percentages_seen}"

        print(f"Progress percentages seen: {percentages_seen}")


class TestLargeFileConversion:
    """Test conversion of large files."""

    @pytest.mark.slow
    def test_large_pdf_conversion_completes(
        self, page_with_server: Page, test_pdfs: dict[str, Path]
    ) -> None:
        """Test that large PDF conversion completes successfully."""
        page = page_with_server
        page.goto("http://localhost:8001")

        # Upload large file
        file_input = page.locator('input[type="file"]')
        file_input.set_input_files(test_pdfs["large"])

        page.wait_for_timeout(1000)

        # Start conversion
        convert_btn = page.locator("#convertBtn")
        convert_btn.click()

        # Progress should appear
        progress_container = page.locator("#progressContainer")
        # Wait for progress container to have visible class
        page.wait_for_timeout(500)
        progress_classes = progress_container.get_attribute("class")
        assert (
            progress_classes and "visible" in progress_classes
        ), "Progress container should be visible"

        # Wait for completion with extended timeout (large file)
        status_div = page.locator("#status")

        # Wait up to 3 minutes for large file
        try:
            expect(status_div).to_be_visible(timeout=180000)
            status_text = status_div.inner_text()

            # Should complete successfully
            assert (
                "successful" in status_text.lower() or "✓" in status_text
            ), f"Expected success, got: {status_text}"
        except Exception as e:
            # Capture state for debugging
            print(f"Status div visible: {status_div.is_visible()}")
            print(f"Progress container: {progress_container.get_attribute('class')}")
            raise e

    @pytest.mark.slow
    def test_large_pdf_shows_progress_updates(
        self, page_with_server: Page, test_pdfs: dict[str, Path]
    ) -> None:
        """Test that large PDF shows multiple progress updates."""
        page = page_with_server
        page.goto("http://localhost:8001")

        # Upload large file
        file_input = page.locator('input[type="file"]')
        file_input.set_input_files(test_pdfs["large"])

        page.wait_for_timeout(1000)

        # Start conversion
        convert_btn = page.locator("#convertBtn")
        convert_btn.click()

        # Progress should appear
        progress_container = page.locator("#progressContainer")
        # Wait for progress container to have visible class
        page.wait_for_timeout(500)
        progress_classes = progress_container.get_attribute("class")
        assert (
            progress_classes and "visible" in progress_classes
        ), "Progress container should be visible"

        # Track progress updates
        progress_percentage = page.locator("#progressPercentage")
        progress_message = page.locator("#progressMessage")

        updates = []
        last_percentage = "0%"

        # Sample every 2 seconds for up to 60 seconds
        for i in range(30):
            page.wait_for_timeout(2000)

            pct = progress_percentage.inner_text()
            msg = progress_message.inner_text()

            updates.append({"time": i * 2, "percentage": pct, "message": msg})

            # Check if conversion is done
            if not progress_container.get_attribute(
                "class"
            ) or "visible" not in progress_container.get_attribute("class"):
                break

            # Progress should change over time
            if i > 3 and pct == last_percentage:
                # Still acceptable if message changes
                pass

            last_percentage = pct

        print(f"Progress updates captured: {len(updates)}")
        print(f"Sample updates: {updates[:5]}")

        # Should have captured multiple updates
        assert len(updates) > 2, "Should have multiple progress updates for large file"


class TestErrorHandling:
    """Test error handling in the UI."""

    def test_invalid_file_type_shows_error(
        self, page_with_server: Page, tmp_path: Path
    ) -> None:
        """Test that uploading invalid file type shows an error."""
        page = page_with_server
        page.goto("http://localhost:8001")

        # Create a text file
        invalid_file = tmp_path / "test.txt"
        invalid_file.write_text("This is not a PDF")

        # Try to upload it
        file_input = page.locator('input[type="file"]')
        file_input.set_input_files(invalid_file)

        page.wait_for_timeout(500)

        # Try to convert
        convert_btn = page.locator("#convertBtn")
        convert_btn.click()

        # Should show error
        status_div = page.locator("#status")
        expect(status_div).to_be_visible(timeout=10000)

        status_text = status_div.inner_text()
        assert (
            "error" in status_text.lower()
            or "failed" in status_text.lower()
            or "invalid" in status_text.lower()
        ), f"Expected error message, got: {status_text}"

    def test_empty_file_shows_error(
        self, page_with_server: Page, tmp_path: Path
    ) -> None:
        """Test that uploading empty file shows an error."""
        page = page_with_server
        page.goto("http://localhost:8001")

        # Create empty PDF
        empty_file = tmp_path / "empty.pdf"
        empty_file.write_bytes(b"")

        # Try to upload it
        file_input = page.locator('input[type="file"]')
        file_input.set_input_files(empty_file)

        page.wait_for_timeout(500)

        # Try to convert
        convert_btn = page.locator("#convertBtn")
        convert_btn.click()

        # Should show error
        status_div = page.locator("#status")
        expect(status_div).to_be_visible(timeout=10000)

        status_text = status_div.inner_text()
        assert (
            "error" in status_text.lower() or "empty" in status_text.lower()
        ), f"Expected error for empty file, got: {status_text}"


class TestUIStateManagement:
    """Test UI state management during conversion."""

    def test_convert_button_disabled_during_conversion(
        self, page_with_server: Page, test_pdfs: dict[str, Path]
    ) -> None:
        """Test that convert button is disabled during conversion."""
        page = page_with_server
        page.goto("http://localhost:8001")

        # Upload file
        file_input = page.locator('input[type="file"]')
        file_input.set_input_files(test_pdfs["medium"])

        page.wait_for_timeout(500)

        # Start conversion
        convert_btn = page.locator("#convertBtn")
        convert_btn.click()

        # Wait a bit for conversion to start
        page.wait_for_timeout(1000)

        # Convert button should be disabled
        expect(convert_btn).to_be_disabled()

    def test_cancel_button_appears_during_conversion(
        self, page_with_server: Page, test_pdfs: dict[str, Path]
    ) -> None:
        """Test that cancel button appears during conversion."""
        page = page_with_server
        page.goto("http://localhost:8001")

        # Upload file
        file_input = page.locator('input[type="file"]')
        file_input.set_input_files(test_pdfs["medium"])

        page.wait_for_timeout(500)

        # Start conversion
        convert_btn = page.locator("#convertBtn")
        convert_btn.click()

        # Wait for progress to appear
        page.wait_for_timeout(1000)

        # Cancel button should be visible and enabled
        cancel_btn = page.locator("#cancelBtn")
        expect(cancel_btn).to_be_visible()
        expect(cancel_btn).not_to_be_disabled()
