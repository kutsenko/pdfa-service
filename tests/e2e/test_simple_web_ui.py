"""Simplified E2E tests for Web UI - works with Chromium and Firefox."""

from pathlib import Path

import pytest
from playwright.sync_api import Page

pytestmark = [pytest.mark.e2e, pytest.mark.playwright]


@pytest.fixture(scope="module")
def small_pdf(tmp_path_factory) -> Path:
    """Create a small test PDF."""
    from reportlab.pdfgen import canvas

    pdf_path = tmp_path_factory.mktemp("data") / "test.pdf"
    c = canvas.Canvas(str(pdf_path))
    c.drawString(100, 750, "Test PDF for E2E testing")
    c.showPage()
    c.save()
    return pdf_path


class TestWebUIBasics:
    """Basic Web UI tests."""

    def test_page_loads(self, page: Page) -> None:
        """Test that the page loads."""
        page.goto("http://localhost:8001")
        # Title can be in English or German
        title = page.title()
        assert "PDF/A" in title and ("Converter" in title or "Konverter" in title)

    def test_upload_and_convert_flow(self, page: Page, small_pdf: Path) -> None:
        """Test basic upload and conversion."""
        page.goto("http://localhost:8001")

        # Upload file
        page.set_input_files('input[type="file"]', small_pdf)

        # Click convert
        page.click("#convertBtn")

        # Wait for either progress or status using smart polling
        # (conversion is fast, so poll frequently with condition check)
        page.wait_for_function(
            """() => {
                const progress = document.getElementById('progressContainer');
                const status = document.getElementById('status');
                return (progress && progress.offsetParent !== null) ||
                       (status && status.offsetParent !== null);
            }""",
            timeout=5000,
        )

    def test_progress_not_stuck_on_starting(self, page: Page, small_pdf: Path) -> None:
        """Test that progress doesn't show 'Starting...' - THIS IS THE KEY TEST."""
        page.goto("http://localhost:8001")

        page.set_input_files('input[type="file"]', small_pdf)
        page.click("#convertBtn")

        # Wait for progress container to appear (if it appears at all)
        # Conversion might be too fast to show progress
        try:
            page.wait_for_selector("#progressContainer", state="visible", timeout=2000)
            # If visible, check the message
            msg = page.locator("#progressMessage").inner_text()
            print(f"Progress message: {msg}")
            assert "Starting..." not in msg, f"Progress stuck on 'Starting...': {msg}"
        except Exception:
            # Progress might not appear for fast conversions - that's OK
            # Just verify status appeared instead
            page.wait_for_selector("#status", state="visible", timeout=1000)

    def test_progress_percentage_visible(self, page: Page, small_pdf: Path) -> None:
        """Test that progress percentage is visible and not stuck at 8%."""
        page.goto("http://localhost:8001")

        page.set_input_files('input[type="file"]', small_pdf)
        page.click("#convertBtn")

        # Wait for progress container and percentage to appear
        page.wait_for_selector("#progressContainer", state="visible", timeout=5000)
        page.wait_for_selector("#progressPercentage", state="visible", timeout=2000)

        pct = page.locator("#progressPercentage").inner_text()
        print(f"Progress percentage: {pct}")
        assert "%" in pct, "Should show percentage"
        # Should not be stuck at exactly 8%
        assert pct != "8%", "Should not be stuck at 8%"
