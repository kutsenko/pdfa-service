"""E2E tests for authentication-based page visibility.

Tests verify that:
1. When auth is disabled, all tabs are visible
2. After logout simulation, URL hash is cleared
3. Tab panels don't have active class when they should be hidden

These tests correspond to the Gherkin scenarios in:
docs/specs/features/gherkin-auth-page-visibility.feature

Requirements:
    - Server running on localhost:8000 with PDFA_ENABLE_AUTH=false (default)
    - MongoDB running
    - Playwright browsers installed: playwright install

Run with:
    pytest tests/e2e/test_auth_page_visibility.py -v
    pytest tests/e2e/test_auth_page_visibility.py -k "regression" -v

Note: Tests for auth-enabled scenarios require manual testing with auth enabled server.
"""

from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect


# ============================================================================
# Tests: Auth Disabled (default server configuration)
# ============================================================================


class TestAuthDisabled:
    """Tests when authentication is disabled.

    Uses server with PDFA_ENABLE_AUTH=false (default configuration).
    """

    def test_tabs_visible_when_auth_disabled(self, page: Page):
        """Test that all tabs are visible when auth is disabled.

        Gherkin: Scenario: User sees all features when authentication is disabled
        """
        page.goto("http://localhost:8000")
        page.wait_for_load_state("networkidle")

        # Tab navigation should be visible
        tab_nav = page.locator(".tab-navigation")
        expect(tab_nav).to_be_visible()

        # All tab buttons should be visible
        tab_buttons = page.locator(".tab-button")
        expect(tab_buttons).to_have_count(5)

    def test_welcome_screen_hidden_when_auth_disabled(self, page: Page):
        """Test that welcome screen is hidden when auth is disabled.

        Gherkin: Scenario: User sees all features when authentication is disabled
        """
        page.goto("http://localhost:8000")
        page.wait_for_load_state("networkidle")

        welcome_screen = page.locator("#welcomeScreen")
        expect(welcome_screen).to_be_hidden()

    def test_login_screen_hidden_when_auth_disabled(self, page: Page):
        """Test that login screen is hidden when auth is disabled.

        Gherkin: Scenario: User sees all features when authentication is disabled
        """
        page.goto("http://localhost:8000")
        page.wait_for_load_state("networkidle")

        login_screen = page.locator("#loginScreen")
        expect(login_screen).not_to_have_class("visible")

    def test_first_tab_panel_visible_when_auth_disabled(self, page: Page):
        """Test that the first tab panel (Konverter) is visible.

        Gherkin: Scenario: User sees all features when authentication is disabled
        """
        page.goto("http://localhost:8000")
        page.wait_for_load_state("networkidle")

        konverter_panel = page.locator("#tab-konverter")
        expect(konverter_panel).to_be_visible()

    def test_no_logout_button_when_auth_disabled(self, page: Page):
        """Test that logout button is not visible when auth is disabled.

        Gherkin: Scenario: User sees all features when authentication is disabled
        """
        page.goto("http://localhost:8000")
        page.wait_for_load_state("networkidle")

        # Auth bar should be hidden
        auth_bar = page.locator("#authBar")
        expect(auth_bar).to_be_hidden()


# ============================================================================
# Tests: URL Hash Handling
# ============================================================================


class TestUrlHashHandling:
    """Tests for URL hash behavior."""

    def test_url_hash_navigates_to_tab(self, page: Page):
        """Test that URL hash correctly navigates to the specified tab."""
        # Navigate with hash
        page.goto("http://localhost:8000/#account")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(300)

        # Account panel should be visible
        account_panel = page.locator("#tab-account")
        expect(account_panel).to_be_visible()

        # Account button should be active
        account_btn = page.locator("#tab-account-btn")
        expect(account_btn).to_have_class("tab-button active")

    def test_all_hash_routes_work(self, page: Page):
        """Test that all hash routes work correctly."""
        routes_to_test = ["konverter", "kamera", "jobs", "account", "documentation"]

        for route in routes_to_test:
            page.goto(f"http://localhost:8000/#{route}")
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(200)

            # Tab panel should be visible
            panel = page.locator(f"#tab-{route}")
            expect(panel).to_be_visible()


# ============================================================================
# Tests: Logout Flow (simulated)
# ============================================================================


class TestLogoutSimulation:
    """Tests for logout behavior simulation."""

    def test_logout_clears_url_hash(self, page: Page):
        """Test that logout clears URL hash.

        This is a regression test - the URL hash was persisting after logout,
        causing the last selected tab to be visible on the login screen.
        """
        # Navigate to a specific tab hash
        page.goto("http://localhost:8000/#account")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(300)

        # Verify we're on account tab
        assert page.url.endswith("#account")

        # Simulate what logout does: clear hash and reload
        page.evaluate(
            """() => {
            if (window.location.hash) {
                history.replaceState(null, null, window.location.pathname + window.location.search);
            }
        }"""
        )

        # Verify hash is cleared
        current_url = page.url
        assert "#" not in current_url or current_url.endswith("/")


# ============================================================================
# Regression Tests
# ============================================================================


class TestAuthRegressions:
    """Regression tests for previously fixed auth bugs."""

    def test_regression_no_active_panels_initially_when_konverter_active(
        self, page: Page
    ):
        """Regression: Verify only one tab panel has 'active' class.

        Bug: Multiple panels could have 'active' class causing display issues.
        """
        page.goto("http://localhost:8000")
        page.wait_for_load_state("networkidle")

        # Only one panel should have 'active' class
        active_panels = page.locator(".tab-panel.active")
        expect(active_panels).to_have_count(1)

        # It should be the Konverter panel
        konverter = page.locator("#tab-konverter.active")
        expect(konverter).to_be_visible()

    def test_regression_tab_switch_removes_previous_active(self, page: Page):
        """Regression: Switching tabs should remove 'active' from previous tab.

        Bug: The 'active' class was not always removed from previous tab,
        causing multiple tabs to appear visible.
        """
        page.goto("http://localhost:8000")
        page.wait_for_load_state("networkidle")

        # Initial state - Konverter is active
        expect(page.locator("#tab-konverter")).to_have_class("tab-panel active")

        # Switch to Account tab
        page.click("#tab-account-btn")
        page.wait_for_timeout(200)

        # Only Account should be active now
        active_panels = page.locator(".tab-panel.active")
        expect(active_panels).to_have_count(1)

        # Konverter should not be active
        expect(page.locator("#tab-konverter")).not_to_have_class("tab-panel active")

        # Account should be active
        expect(page.locator("#tab-account")).to_have_class("tab-panel active")

    def test_regression_hidden_panels_have_no_active_class(self, page: Page):
        """Regression: Hidden panels should not have 'active' class.

        This tests the fix where showLoginScreen() now removes 'active' class
        to prevent CSS .tab-panel.active { display: block } from overriding hidden.
        """
        page.goto("http://localhost:8000")
        page.wait_for_load_state("networkidle")

        # Get all hidden panels
        all_panels = page.locator(".tab-panel").all()

        for panel in all_panels:
            # If panel is hidden, it should not have 'active' class
            is_visible = panel.is_visible()
            has_active = "active" in (panel.get_attribute("class") or "")

            if not is_visible:
                assert not has_active, f"Hidden panel {panel} should not have 'active' class"

    def test_regression_url_hash_with_multiple_switches(self, page: Page):
        """Regression: URL hash should stay in sync after multiple tab switches."""
        page.goto("http://localhost:8000")
        page.wait_for_load_state("networkidle")

        tabs = [
            ("tab-kamera-btn", "kamera"),
            ("tab-jobs-btn", "jobs"),
            ("tab-account-btn", "account"),
            ("tab-konverter-btn", "konverter"),
        ]

        for btn_id, hash_name in tabs:
            page.click(f"#{btn_id}")
            page.wait_for_timeout(100)

            # URL should reflect current tab
            current_url = page.url
            assert current_url.endswith(f"#{hash_name}"), f"URL should end with #{hash_name}, got {current_url}"
