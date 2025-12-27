"""
End-to-end tests for the Konto (Account) Tab using Playwright.

These tests verify the complete Konto tab functionality based on US-006:
- Account information display
- User preferences management
- Account deletion workflow
- i18n support (EN, DE, ES, FR)
- Responsive design
- Dark mode

Run with:
    pytest tests/e2e/test_konto_tab.py -v
    pytest tests/e2e/test_konto_tab.py -k "test_account_info" -v

Requirements:
    - API server running on localhost:8000
    - MongoDB running
    - Playwright browsers installed: playwright install
"""

from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect


# =============================================================================
# Account Information Display Tests
# =============================================================================

class TestAccountInformationDisplay:
    """Tests for account information display functionality."""

    def test_should_display_loading_state(self, page: Page):
        """Loading state should be visible when opening Konto tab."""
        page.goto("http://localhost:8000")
        page.wait_for_load_state("networkidle")

        # Click Konto tab
        page.click('#tab-konto-btn')

        # Should show loading
        expect(page.locator("#kontoLoading")).to_be_visible()
        expect(page.locator("#kontoLoading p")).to_contain_text("Loading account information")

    def test_should_display_default_user_profile_auth_disabled(self, page: Page):
        """Should display Local User profile when auth is disabled."""
        page.goto("http://localhost:8000")
        page.click('#tab-konto-btn')

        # Wait for content
        expect(page.locator("#kontoContent")).to_be_visible()

        # Check default user data
        expect(page.locator("#kontoName")).to_contain_text("Local User")
        expect(page.locator("#kontoEmail")).to_contain_text("local@localhost")
        expect(page.locator("#kontoUserId")).to_contain_text("local-default")

        # Delete button should be hidden
        expect(page.locator("#deleteAccountBtn")).to_be_hidden()
        expect(page.locator("#deleteDisabledMessage")).to_be_visible()

    def test_should_display_all_sections(self, page: Page):
        """All major sections should be visible."""
        page.goto("http://localhost:8000/en")
        page.wait_for_load_state("networkidle")
        page.click('#tab-konto-btn')
        expect(page.locator("#kontoContent")).to_be_visible()

        # Check section headings
        expect(page.locator('h2:has-text("Account Information")')).to_be_visible()
        expect(page.locator('h3:has-text("Profile")')).to_be_visible()
        expect(page.locator('h3:has-text("Login Statistics")')).to_be_visible()
        expect(page.locator('h3:has-text("Conversion Statistics")')).to_be_visible()
        expect(page.locator('h3:has-text("Recent Activity")')).to_be_visible()
        expect(page.locator('h2:has-text("Settings")')).to_be_visible()
        expect(page.locator('h2:has-text("Danger Zone")')).to_be_visible()

    def test_should_display_job_statistics(self, page: Page):
        """Job statistics should be visible."""
        page.goto("http://localhost:8000")
        page.click('#tab-konto-btn')
        expect(page.locator("#kontoContent")).to_be_visible()

        # Job stats should be present
        expect(page.locator("#kontoTotalJobs")).to_be_visible()
        expect(page.locator("#kontoSuccessRate")).to_be_visible()
        expect(page.locator("#kontoAvgDuration")).to_be_visible()
        expect(page.locator("#kontoDataProcessed")).to_be_visible()

    def test_should_display_activity_log_or_empty_message(self, page: Page):
        """Activity log should show events or empty message."""
        page.goto("http://localhost:8000")
        page.click('#tab-konto-btn')
        expect(page.locator("#kontoContent")).to_be_visible()

        activity_log = page.locator("#kontoActivityLog")
        expect(activity_log).to_be_visible()

        # Should either have items or show empty message
        has_items = activity_log.locator(".activity-item").count() > 0
        has_empty_msg = activity_log.locator('p:has-text("No recent activity")').is_visible()

        assert has_items or has_empty_msg, "Activity log should show events or empty message"


# =============================================================================
# User Preferences Tests
# =============================================================================

class TestUserPreferences:
    """Tests for user preferences functionality."""

    def test_should_display_preferences_form(self, page: Page):
        """Preferences form should be visible with all fields."""
        page.goto("http://localhost:8000")
        page.click('#tab-konto-btn')
        expect(page.locator("#kontoContent")).to_be_visible()

        # Form should exist
        expect(page.locator("#preferencesForm")).to_be_visible()

        # All form fields should exist
        expect(page.locator("#prefPdfaLevel")).to_be_visible()
        expect(page.locator("#prefOcrLanguage")).to_be_visible()
        expect(page.locator("#prefCompression")).to_be_visible()
        expect(page.locator("#prefOcrEnabled")).to_be_visible()
        expect(page.locator("#prefSkipTagged")).to_be_visible()

    def test_should_have_standard_pdf_option(self, page: Page):
        """PDF Type dropdown should include Standard PDF option."""
        page.goto("http://localhost:8000")
        page.click('#tab-konto-btn')
        expect(page.locator("#kontoContent")).to_be_visible()

        pdf_type_select = page.locator("#prefPdfaLevel")

        # Should have Standard PDF option (check it exists in DOM)
        standard_option = pdf_type_select.locator('option[value="standard"]')
        expect(standard_option).to_have_count(1)
        expect(standard_option).to_contain_text("Standard PDF")

        # Should also have PDF/A-1, 2, 3
        expect(pdf_type_select.locator('option[value="1"]')).to_have_count(1)
        expect(pdf_type_select.locator('option[value="2"]')).to_have_count(1)
        expect(pdf_type_select.locator('option[value="3"]')).to_have_count(1)

    def test_should_display_default_preferences(self, page: Page):
        """Default preferences should be shown for new user."""
        page.goto("http://localhost:8000")
        page.click('#tab-konto-btn')
        expect(page.locator("#kontoContent")).to_be_visible()

        # Check default values
        expect(page.locator("#prefPdfaLevel")).to_have_value("2")  # PDF/A-2
        expect(page.locator("#prefOcrLanguage")).to_have_value("deu+eng")
        expect(page.locator("#prefCompression")).to_have_value("balanced")
        expect(page.locator("#prefOcrEnabled")).to_be_checked()
        expect(page.locator("#prefSkipTagged")).to_be_checked()

    def test_should_have_save_and_reset_buttons(self, page: Page):
        """Save and Reset buttons should be visible."""
        page.goto("http://localhost:8000")
        page.click('#tab-konto-btn')
        expect(page.locator("#kontoContent")).to_be_visible()

        expect(page.locator('button:has-text("Save Preferences")')).to_be_visible()
        expect(page.locator('#resetPreferencesBtn')).to_be_visible()

    def test_should_reset_preferences_to_defaults(self, page: Page):
        """Reset button should restore default values."""
        page.goto("http://localhost:8000")
        page.click('#tab-konto-btn')
        expect(page.locator("#kontoContent")).to_be_visible()

        # Change some values
        page.select_option("#prefPdfaLevel", "standard")
        page.select_option("#prefOcrLanguage", "eng")
        page.click("#prefOcrEnabled")  # Uncheck

        # Verify changes
        expect(page.locator("#prefPdfaLevel")).to_have_value("standard")
        expect(page.locator("#prefOcrEnabled")).not_to_be_checked()

        # Reset to defaults
        page.click("#resetPreferencesBtn")

        # Should be back to defaults
        expect(page.locator("#prefPdfaLevel")).to_have_value("2")
        expect(page.locator("#prefOcrLanguage")).to_have_value("deu+eng")
        expect(page.locator("#prefCompression")).to_have_value("balanced")
        expect(page.locator("#prefOcrEnabled")).to_be_checked()


# =============================================================================
# Account Deletion Tests
# =============================================================================

class TestAccountDeletion:
    """Tests for account deletion functionality."""

    def test_should_show_danger_zone(self, page: Page):
        """Danger Zone section should be visible."""
        page.goto("http://localhost:8000")
        page.click('#tab-konto-btn')
        expect(page.locator("#kontoContent")).to_be_visible()

        # Danger Zone should exist
        expect(page.locator('h2:has-text("Danger Zone")')).to_be_visible()
        expect(page.locator('.danger-warning')).to_be_visible()
        expect(page.locator('.danger-warning')).to_contain_text("cannot be undone")

    def test_should_disable_deletion_for_local_user(self, page: Page):
        """Account deletion should be disabled in local mode."""
        page.goto("http://localhost:8000")
        page.click('#tab-konto-btn')
        expect(page.locator("#kontoContent")).to_be_visible()

        # Delete button hidden, message shown
        expect(page.locator("#deleteAccountBtn")).to_be_hidden()
        expect(page.locator("#deleteDisabledMessage")).to_be_visible()
        expect(page.locator("#deleteDisabledMessage")).to_contain_text("not available in local mode")


# =============================================================================
# Internationalization Tests
# =============================================================================

class TestInternationalization:
    """Tests for i18n support."""

    def test_should_display_english_translations(self, page: Page):
        """English translations should be visible."""
        page.goto("http://localhost:8000/en")
        page.wait_for_load_state("networkidle")

        page.click('#tab-konto-btn')
        expect(page.locator("#kontoContent")).to_be_visible()

        # Check English headings
        expect(page.locator('h2:has-text("Account Information")')).to_be_visible()
        expect(page.locator('h2:has-text("Settings")')).to_be_visible()
        expect(page.locator('h2:has-text("Danger Zone")')).to_be_visible()

    def test_should_display_german_translations(self, page: Page):
        """German translations should be visible."""
        page.goto("http://localhost:8000/de")
        page.wait_for_load_state("networkidle")

        page.click('#tab-konto-btn')
        expect(page.locator("#kontoContent")).to_be_visible()

        # Check German headings
        expect(page.locator('h2:has-text("Konto-Informationen")')).to_be_visible()
        expect(page.locator('h2:has-text("Einstellungen")')).to_be_visible()
        expect(page.locator('h2:has-text("Gefahrenbereich")')).to_be_visible()

    def test_should_display_spanish_translations(self, page: Page):
        """Spanish translations should be visible."""
        page.goto("http://localhost:8000/es")
        page.wait_for_load_state("networkidle")

        page.click('button[id="tab-konto-btn"]')
        expect(page.locator("#kontoContent")).to_be_visible()

        # Check Spanish headings (use data-i18n attributes for specificity)
        expect(page.locator('h2[data-i18n="konto.accountInfo"]')).to_contain_text("Información de Cuenta")
        expect(page.locator('h2[data-i18n="konto.settings"]')).to_contain_text("Configuración")

    def test_should_display_french_translations(self, page: Page):
        """French translations should be visible."""
        page.goto("http://localhost:8000/fr")
        page.wait_for_load_state("networkidle")

        page.click('button[id="tab-konto-btn"]')
        expect(page.locator("#kontoContent")).to_be_visible()

        # Check French headings (use data-i18n attributes for specificity)
        expect(page.locator('h2[data-i18n="konto.accountInfo"]')).to_contain_text("Informations de Compte")
        expect(page.locator('h2[data-i18n="konto.settings"]')).to_contain_text("Paramètres")


# =============================================================================
# Responsive Design Tests
# =============================================================================

class TestResponsiveDesign:
    """Tests for responsive design."""

    def test_should_use_two_column_grid_on_desktop(self, page: Page):
        """Desktop layout should use 2-column grid."""
        page.set_viewport_size({"width": 1920, "height": 1080})
        page.goto("http://localhost:8000")

        page.click('#tab-konto-btn')
        expect(page.locator("#kontoContent")).to_be_visible()

        # Grid should be 2 columns
        grid = page.locator(".konto-grid")
        grid_columns = grid.evaluate("el => window.getComputedStyle(el).gridTemplateColumns")

        # Should have 2 columns
        columns = [c for c in grid_columns.split() if 'px' in c or 'fr' in c]
        assert len(columns) == 2, f"Expected 2 columns, got {len(columns)}"

    def test_should_use_single_column_on_mobile(self, page: Page):
        """Mobile layout should use single column."""
        page.set_viewport_size({"width": 375, "height": 667})
        page.goto("http://localhost:8000")

        page.click('#tab-konto-btn')
        expect(page.locator("#kontoContent")).to_be_visible()

        # Grid should be 1 column
        grid = page.locator(".konto-grid")
        grid_columns = grid.evaluate("el => window.getComputedStyle(el).gridTemplateColumns")

        # Should have 1 column
        columns = [c for c in grid_columns.split() if 'px' in c or 'fr' in c]
        assert len(columns) == 1, f"Expected 1 column, got {len(columns)}"

    def test_should_not_overflow_horizontally_on_mobile(self, page: Page):
        """Content should not overflow horizontally on mobile."""
        page.set_viewport_size({"width": 375, "height": 667})
        page.goto("http://localhost:8000")

        page.click('#tab-konto-btn')
        expect(page.locator("#kontoContent")).to_be_visible()

        # Check no horizontal scroll
        has_h_scroll = page.evaluate("""
            () => document.documentElement.scrollWidth > document.documentElement.clientWidth
        """)

        assert not has_h_scroll, "Page should not have horizontal scrollbar on mobile"


# =============================================================================
# Dark Mode Tests
# =============================================================================

class TestDarkMode:
    """Tests for dark mode support."""

    def test_should_apply_dark_mode_styles(self, page: Page):
        """Dark mode should apply dark background colors."""
        page.emulate_media(color_scheme="dark")
        page.goto("http://localhost:8000")

        page.click('#tab-konto-btn')
        expect(page.locator("#kontoContent")).to_be_visible()

        # Check card has dark background
        card = page.locator(".konto-card").first
        bg_color = card.evaluate("el => window.getComputedStyle(el).backgroundColor")

        # Extract RGB values
        import re
        rgb_match = re.findall(r'\d+', bg_color)
        if rgb_match:
            rgb = [int(x) for x in rgb_match[:3]]
            max_value = max(rgb)

            # Dark background should have low RGB values
            assert max_value < 150, f"Expected dark background, got RGB {rgb}"


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def page(playwright):
    """Create a new browser page for each test."""
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()

    yield page

    page.close()
    context.close()
    browser.close()
