"""Playwright E2E tests for real-time progress updates via WebSocket.

This test suite verifies that progress percentage updates are actually
received and displayed by the browser during PDF conversion.
"""

from __future__ import annotations

import time
from pathlib import Path

import pytest
from playwright.sync_api import Page


@pytest.mark.e2e
@pytest.mark.playwright
class TestProgressUpdatesReal:
    """Test real-time progress updates in the browser."""

    def test_progress_percentage_updates_during_conversion(
        self, page: Page, test_data_dir: Path, base_url: str
    ) -> None:
        """Test that progress percentage actually updates during conversion.

        This is the CRITICAL test to verify that WebSocket progress events
        are received by the browser and update the UI.
        """
        # Use medium PDF from test_data
        medium_pdf = test_data_dir / "medium.pdf"

        # If medium.pdf doesn't exist, create it
        if not medium_pdf.exists():
            from tests.e2e.test_data.pdf_generator import create_medium_pdf
            create_medium_pdf(medium_pdf)

        # Navigate to the page using base_url
        page.goto(base_url if base_url else "http://localhost:8000")

        # Upload file
        page.set_input_files('input[type="file"]', medium_pdf)
        page.wait_for_timeout(500)

        # Get progress elements
        progress_percentage = page.locator("#progressPercentage")
        progress_fill = page.locator("#progressFill")
        progress_message = page.locator("#progressMessage")

        # Click convert button
        page.click("#convertBtn")

        # Wait for progress container to be visible
        page.wait_for_selector("#progressContainer.visible", timeout=5000)

        # Track progress updates
        progress_values = []
        start_time = time.time()
        max_wait = 30  # Maximum 30 seconds

        # Poll for progress updates
        while time.time() - start_time < max_wait:
            try:
                # Get current percentage text
                if progress_percentage.is_visible():
                    percentage_text = progress_percentage.inner_text()

                    # Extract numeric value
                    if "%" in percentage_text:
                        value = int(percentage_text.replace("%", ""))

                        # Record if it's a new value
                        if not progress_values or value != progress_values[-1]:
                            progress_values.append(value)
                            print(f"Progress update: {value}%")

                        # If we reached 100%, we might be done
                        if value >= 100:
                            break

                # Check if conversion completed (progress hidden)
                progress_container = page.locator("#progressContainer")
                if not progress_container.evaluate("el => el.classList.contains('visible')"):
                    print("Progress container hidden - conversion complete")
                    break

            except Exception as e:
                print(f"Error reading progress: {e}")

            # Wait a bit before next check
            page.wait_for_timeout(200)

        print(f"Collected {len(progress_values)} progress updates: {progress_values}")

        # Verify we got multiple progress updates
        assert len(progress_values) >= 2, (
            f"Expected at least 2 progress updates, got {len(progress_values)}: {progress_values}. "
            "This means progress events are not being received by the browser!"
        )

        # Verify progress increased over time
        assert progress_values[-1] > progress_values[0], (
            f"Progress should increase from {progress_values[0]}% to {progress_values[-1]}%"
        )

        # Verify we started at 0
        assert progress_values[0] == 0, f"Progress should start at 0%, got {progress_values[0]}%"

    def test_progress_message_updates(self, page: Page, test_data_dir: Path) -> None:
        """Test that progress message text updates during conversion."""
        medium_pdf = test_data_dir / "medium.pdf"

        if not medium_pdf.exists():
            from tests.e2e.test_data.pdf_generator import create_medium_pdf
            create_medium_pdf(medium_pdf)

        page.goto("http://localhost:8000")
        page.set_input_files('input[type="file"]', medium_pdf)
        page.wait_for_timeout(500)

        progress_message = page.locator("#progressMessage")
        progress_step = page.locator("#progressStep")

        page.click("#convertBtn")
        page.wait_for_selector("#progressContainer.visible", timeout=5000)

        # Collect message updates
        messages = []
        steps = []
        start_time = time.time()

        while time.time() - start_time < 30:
            try:
                if progress_message.is_visible():
                    msg = progress_message.inner_text()
                    if msg and (not messages or msg != messages[-1]):
                        messages.append(msg)
                        print(f"Progress message: {msg}")

                if progress_step.is_visible():
                    step = progress_step.inner_text()
                    if step and (not steps or step != steps[-1]):
                        steps.append(step)
                        print(f"Progress step: {step}")

                # Check if completed
                progress_container = page.locator("#progressContainer")
                if not progress_container.evaluate("el => el.classList.contains('visible')"):
                    break

            except Exception as e:
                print(f"Error reading messages: {e}")

            page.wait_for_timeout(200)

        print(f"Collected {len(messages)} message updates: {messages}")
        print(f"Collected {len(steps)} step updates: {steps}")

        # Should have at least some message updates
        assert len(messages) >= 1, (
            f"Expected at least 1 message update, got {len(messages)}: {messages}"
        )

    def test_websocket_connection_established(self, page: Page) -> None:
        """Test that WebSocket connection is established successfully."""
        page.goto("http://localhost:8000")

        # Wait for WebSocket to connect
        page.wait_for_timeout(2000)

        # Check WebSocket status indicator
        ws_status = page.locator("#wsStatus")

        # Should be connected
        assert ws_status.is_visible(), "WebSocket status indicator should be visible"

        # Check the status class
        ws_classes = ws_status.get_attribute("class")
        assert "connected" in ws_classes, (
            f"WebSocket should be connected, got classes: {ws_classes}"
        )

    def test_console_logs_progress_events(
        self, page: Page, test_data_dir: Path
    ) -> None:
        """Test that progress events are logged to console (for debugging)."""
        medium_pdf = test_data_dir / "medium.pdf"

        if not medium_pdf.exists():
            from tests.e2e.test_data.pdf_generator import create_medium_pdf
            create_medium_pdf(medium_pdf)

        # Collect console messages
        console_messages = []

        def on_console(msg):
            console_messages.append(msg.text)
            print(f"Console: {msg.text}")

        page.on("console", on_console)

        page.goto("http://localhost:8000")
        page.set_input_files('input[type="file"]', medium_pdf)
        page.wait_for_timeout(500)

        page.click("#convertBtn")
        page.wait_for_selector("#progressContainer.visible", timeout=5000)

        # Wait for some progress
        page.wait_for_timeout(5000)

        # Check console logs for WebSocket messages
        ws_logs = [msg for msg in console_messages if "WebSocket message" in msg]
        progress_logs = [
            msg for msg in console_messages if "progress" in msg.lower()
        ]

        print(f"WebSocket logs: {len(ws_logs)}")
        print(f"Progress logs: {len(progress_logs)}")

        # Should have at least some WebSocket activity
        assert len(ws_logs) > 0, (
            "Expected WebSocket messages in console logs, but got none. "
            "This suggests WebSocket events are not being received!"
        )

    def test_progress_bar_width_updates(
        self, page: Page, test_data_dir: Path
    ) -> None:
        """Test that the progress bar visual width actually updates."""
        medium_pdf = test_data_dir / "medium.pdf"

        if not medium_pdf.exists():
            from tests.e2e.test_data.pdf_generator import create_medium_pdf
            create_medium_pdf(medium_pdf)

        page.goto("http://localhost:8000")
        page.set_input_files('input[type="file"]', medium_pdf)
        page.wait_for_timeout(500)

        progress_fill = page.locator("#progressFill")

        page.click("#convertBtn")
        page.wait_for_selector("#progressContainer.visible", timeout=5000)

        # Track width changes
        widths = []
        start_time = time.time()

        while time.time() - start_time < 30:
            try:
                if progress_fill.is_visible():
                    width = progress_fill.evaluate("el => el.style.width")

                    if width and (not widths or width != widths[-1]):
                        widths.append(width)
                        print(f"Progress bar width: {width}")

                # Check if completed
                progress_container = page.locator("#progressContainer")
                if not progress_container.evaluate("el => el.classList.contains('visible')"):
                    break

            except Exception as e:
                print(f"Error reading width: {e}")

            page.wait_for_timeout(200)

        print(f"Collected {len(widths)} width changes: {widths}")

        # Should have multiple width changes
        assert len(widths) >= 2, (
            f"Expected at least 2 width changes, got {len(widths)}: {widths}. "
            "The progress bar is not visually updating!"
        )
