"""Simplified E2E tests for Web UI - works with Chromium and Firefox."""

from pathlib import Path
import pytest
from playwright.sync_api import Page, expect

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
        page.goto("http://localhost:8000")
        # Title can be in English or German
        title = page.title()
        assert "PDF/A" in title and ("Converter" in title or "Konverter" in title)

    def test_upload_and_convert_flow(self, page: Page, small_pdf: Path) -> None:
        """Test basic upload and conversion."""
        page.goto("http://localhost:8000")
        
        # Upload file
        page.set_input_files('input[type="file"]', small_pdf)
        page.wait_for_timeout(500)
        
        # Click convert
        page.click("#convertBtn")
        
        # Wait longer for WebSocket connection and processing
        page.wait_for_timeout(5000)
        
        # Check that something happened (progress or status)
        progress_visible = page.locator("#progressContainer").is_visible()
        status_visible = page.locator("#status").is_visible()
        
        assert progress_visible or status_visible, "Either progress or status should be visible"

    def test_progress_not_stuck_on_starting(self, page: Page, small_pdf: Path) -> None:
        """Test that progress doesn't show 'Starting...' - THIS IS THE KEY TEST."""
        page.goto("http://localhost:8000")
        
        page.set_input_files('input[type="file"]', small_pdf)
        page.wait_for_timeout(500)
        page.click("#convertBtn")
        
        # Wait a moment for UI to update
        page.wait_for_timeout(1500)
        
        # Check progress message
        if page.locator("#progressContainer").is_visible():
            msg = page.locator("#progressMessage").inner_text()
            print(f"Progress message: {msg}")
            assert "Starting..." not in msg, f"Progress stuck on 'Starting...': {msg}"
        
    def test_progress_percentage_visible(self, page: Page, small_pdf: Path) -> None:
        """Test that progress percentage is visible and not stuck at 8%."""
        page.goto("http://localhost:8000")
        
        page.set_input_files('input[type="file"]', small_pdf)
        page.wait_for_timeout(500)
        page.click("#convertBtn")
        
        # Wait for progress to appear
        page.wait_for_timeout(1000)
        
        if page.locator("#progressContainer").is_visible():
            pct = page.locator("#progressPercentage").inner_text()
            print(f"Progress percentage: {pct}")
            assert "%" in pct, "Should show percentage"
            # Should not be stuck at exactly 8%
            assert pct != "8%", "Should not be stuck at 8%"

