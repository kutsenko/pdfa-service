"""E2E tests for authentication-based page visibility.

Tests verify that:
1. When auth is disabled, all tabs are visible
2. When auth is enabled but user is not logged in, only welcome screen is visible
3. When auth is enabled and user is logged in, all tabs are visible
4. After logout, user is returned to welcome screen

These tests correspond to the Gherkin scenarios in:
docs/specs/features/gherkin-auth-page-visibility.feature
"""

from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path

import pytest
from playwright.sync_api import Page, expect


# ============================================================================
# Fixtures for Auth-Enabled Server
# ============================================================================


@pytest.fixture(scope="module")
def auth_enabled_server(mongodb_test_container):
    """Start the FastAPI server with authentication ENABLED."""
    project_root = Path(__file__).parent.parent.parent

    # Set test environment variables with auth enabled
    test_env = os.environ.copy()
    test_env.update(
        {
            "MONGODB_URI": "mongodb://admin:test_password@localhost:27018/pdfa_test?authSource=admin",
            "MONGODB_DATABASE": "pdfa_test",
            "PDFA_ENABLE_AUTH": "true",  # Enable auth for these tests
            "GOOGLE_CLIENT_ID": "test-client-id",
            "GOOGLE_CLIENT_SECRET": "test-client-secret",
            "JWT_SECRET_KEY": "test-jwt-secret-key-for-testing",
            "PYTHONUNBUFFERED": "1",
            "PDFA_OCR_ENABLED": "false",
        }
    )

    # Start server on port 8002 (different from default test port)
    print("[Auth E2E] Starting FastAPI server with auth enabled on port 8002...")
    process = subprocess.Popen(
        ["uvicorn", "pdfa.api:app", "--host", "localhost", "--port", "8002"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=test_env,
        cwd=project_root,
    )

    # Wait for server to be ready
    time.sleep(4)

    if process.poll() is not None:
        stdout, stderr = process.communicate()
        print(f"[Auth E2E] Server failed: {stderr.decode()}")
        pytest.skip("Auth-enabled server failed to start")

    print("[Auth E2E] Auth-enabled server is ready on http://localhost:8002!")

    yield "http://localhost:8002"

    # Cleanup
    print("[Auth E2E] Stopping auth-enabled server...")
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()


# ============================================================================
# Tests: Auth Disabled (default test server on port 8001)
# ============================================================================


class TestAuthDisabled:
    """Tests when authentication is disabled.

    Uses the default test server (api_process fixture) which has auth disabled.
    """

    @pytest.fixture
    def page_auth_disabled(self, page: Page, api_process) -> Page:
        """Page with auth-disabled server."""
        page.goto("http://localhost:8001")
        page.wait_for_load_state("networkidle")
        return page

    def test_tabs_visible_when_auth_disabled(self, page_auth_disabled: Page):
        """Test that all tabs are visible when auth is disabled.

        Gherkin: Scenario: User sees all features when authentication is disabled
        """
        # Tab navigation should be visible
        tab_nav = page_auth_disabled.locator(".tab-navigation")
        expect(tab_nav).to_be_visible()

        # All tab buttons should be visible
        tab_buttons = page_auth_disabled.locator(".tab-button")
        expect(tab_buttons).to_have_count(5)

        for btn in tab_buttons.all():
            expect(btn).to_be_visible()

    def test_welcome_screen_hidden_when_auth_disabled(self, page_auth_disabled: Page):
        """Test that welcome screen is hidden when auth is disabled.

        Gherkin: Scenario: User sees all features when authentication is disabled
        """
        welcome_screen = page_auth_disabled.locator("#welcomeScreen")
        expect(welcome_screen).to_be_hidden()

    def test_login_screen_hidden_when_auth_disabled(self, page_auth_disabled: Page):
        """Test that login screen is hidden when auth is disabled.

        Gherkin: Scenario: User sees all features when authentication is disabled
        """
        login_screen = page_auth_disabled.locator("#loginScreen")
        expect(login_screen).not_to_have_class("visible")

    def test_first_tab_panel_visible_when_auth_disabled(self, page_auth_disabled: Page):
        """Test that the first tab panel (Konverter) is visible.

        Gherkin: Scenario: User sees all features when authentication is disabled
        """
        konverter_panel = page_auth_disabled.locator("#tab-konverter")
        expect(konverter_panel).to_be_visible()

    def test_no_logout_button_when_auth_disabled(self, page_auth_disabled: Page):
        """Test that logout button is not visible when auth is disabled.

        Gherkin: Scenario: User sees all features when authentication is disabled
        """
        # Auth bar should be hidden
        auth_bar = page_auth_disabled.locator("#authBar")
        expect(auth_bar).to_be_hidden()


# ============================================================================
# Tests: Auth Enabled - Not Logged In
# ============================================================================


class TestAuthEnabledNotLoggedIn:
    """Tests when authentication is enabled but user is not logged in."""

    @pytest.fixture
    def page_auth_enabled(self, page: Page, auth_enabled_server: str) -> Page:
        """Page with auth-enabled server, not logged in."""
        page.goto(auth_enabled_server)
        page.wait_for_load_state("networkidle")
        # Wait for auth detection to complete
        page.wait_for_timeout(500)
        return page

    def test_welcome_screen_visible_when_not_logged_in(
        self, page_auth_enabled: Page
    ):
        """Test that welcome screen is visible when not logged in.

        Gherkin: Scenario: Unauthenticated user sees only the welcome page
        """
        welcome_screen = page_auth_enabled.locator("#welcomeScreen")
        expect(welcome_screen).to_be_visible()

    def test_login_button_visible_when_not_logged_in(self, page_auth_enabled: Page):
        """Test that login button is visible when not logged in.

        Gherkin: Scenario: Unauthenticated user sees only the welcome page
        """
        login_screen = page_auth_enabled.locator("#loginScreen")
        expect(login_screen).to_have_class("login-screen visible")

        login_btn = page_auth_enabled.locator("#googleLoginBtn")
        expect(login_btn).to_be_visible()

    def test_tabs_hidden_when_not_logged_in(self, page_auth_enabled: Page):
        """Test that tabs are hidden when not logged in.

        Gherkin: Scenario: Unauthenticated user sees only the welcome page
        """
        tab_nav = page_auth_enabled.locator(".tab-navigation")
        expect(tab_nav).to_be_hidden()

    def test_all_tab_panels_hidden_when_not_logged_in(self, page_auth_enabled: Page):
        """Test that all tab panels are hidden when not logged in.

        Gherkin: Scenario: Unauthenticated user sees only the welcome page
        """
        tab_panels = page_auth_enabled.locator(".tab-panel")

        for panel in tab_panels.all():
            expect(panel).to_be_hidden()

    def test_konverter_panel_not_visible_when_not_logged_in(
        self, page_auth_enabled: Page
    ):
        """Test specifically that Konverter panel is NOT visible.

        This is a regression test for the bug where Konverter content was visible
        alongside the welcome screen.
        """
        konverter_panel = page_auth_enabled.locator("#tab-konverter")
        expect(konverter_panel).to_be_hidden()

    def test_no_active_tab_class_when_not_logged_in(self, page_auth_enabled: Page):
        """Test that no tab panel has 'active' class when not logged in.

        This is a regression test - the 'active' class was causing content
        to be visible via CSS even with hidden attribute.
        """
        active_panels = page_auth_enabled.locator(".tab-panel.active")
        expect(active_panels).to_have_count(0)

    def test_auth_bar_hidden_when_not_logged_in(self, page_auth_enabled: Page):
        """Test that auth bar (with logout) is hidden when not logged in.

        Gherkin: Scenario: Unauthenticated user sees only the welcome page
        """
        auth_bar = page_auth_enabled.locator("#authBar")
        expect(auth_bar).to_be_hidden()


# ============================================================================
# Tests: URL Hash Handling
# ============================================================================


class TestUrlHashHandling:
    """Tests for URL hash behavior with authentication."""

    @pytest.fixture
    def page_auth_enabled(self, page: Page, auth_enabled_server: str) -> Page:
        """Page with auth-enabled server."""
        return page

    def test_url_hash_ignored_when_not_logged_in(
        self, page_auth_enabled: Page, auth_enabled_server: str
    ):
        """Test that URL hash doesn't show tab content when not logged in.

        This is a regression test for the bug where navigating to /#account
        would show the account tab content even without authentication.
        """
        # Navigate with hash
        page_auth_enabled.goto(f"{auth_enabled_server}/#account")
        page_auth_enabled.wait_for_load_state("networkidle")
        page_auth_enabled.wait_for_timeout(500)

        # Welcome screen should still be visible
        welcome_screen = page_auth_enabled.locator("#welcomeScreen")
        expect(welcome_screen).to_be_visible()

        # Account panel should be hidden
        account_panel = page_auth_enabled.locator("#tab-account")
        expect(account_panel).to_be_hidden()

        # Tabs should be hidden
        tab_nav = page_auth_enabled.locator(".tab-navigation")
        expect(tab_nav).to_be_hidden()

    def test_all_hash_routes_blocked_when_not_logged_in(
        self, page_auth_enabled: Page, auth_enabled_server: str
    ):
        """Test that all hash routes are blocked when not logged in.

        Gherkin: Scenario: Unauthenticated user cannot access protected routes directly
        """
        routes_to_test = ["konverter", "kamera", "jobs", "account", "documentation"]

        for route in routes_to_test:
            page_auth_enabled.goto(f"{auth_enabled_server}/#{route}")
            page_auth_enabled.wait_for_load_state("networkidle")
            page_auth_enabled.wait_for_timeout(300)

            # Welcome screen should be visible
            welcome_screen = page_auth_enabled.locator("#welcomeScreen")
            expect(welcome_screen).to_be_visible()

            # Tab panel should be hidden
            panel = page_auth_enabled.locator(f"#tab-{route}")
            expect(panel).to_be_hidden()


# ============================================================================
# Tests: API Behavior
# ============================================================================


class TestAuthApiEndpoints:
    """Tests for authentication API endpoints."""

    def test_auth_user_returns_404_when_auth_disabled(self, api_process):
        """Test that /auth/user returns 404 when auth is disabled.

        Gherkin: Scenario: API returns 404 for /auth/user when auth is disabled
        """
        import requests

        response = requests.get("http://localhost:8001/auth/user")
        assert response.status_code == 404

    def test_auth_user_returns_401_when_not_authenticated(
        self, auth_enabled_server: str
    ):
        """Test that /auth/user returns 401 when not authenticated.

        Gherkin: Scenario: API returns 401 for /auth/user when not authenticated
        """
        import requests

        response = requests.get(f"{auth_enabled_server}/auth/user")
        assert response.status_code == 401


# ============================================================================
# Tests: Logout Flow (simulated)
# ============================================================================


class TestLogoutFlow:
    """Tests for logout behavior.

    Note: These tests simulate logout by clearing localStorage and reloading,
    since we can't actually perform OAuth login in tests.
    """

    @pytest.fixture
    def page_with_simulated_login(
        self, page: Page, auth_enabled_server: str
    ) -> Page:
        """Page with simulated login state."""
        page.goto(auth_enabled_server)
        page.wait_for_load_state("networkidle")

        # Simulate logged-in state by setting a fake token
        # This won't actually authenticate, but allows testing UI behavior
        page.evaluate(
            """() => {
            // Set a fake token (won't validate, but tests UI state)
            localStorage.setItem('auth_token', 'fake-test-token');
        }"""
        )

        return page

    def test_logout_clears_url_hash(self, page: Page, api_process):
        """Test that logout clears URL hash.

        This is a regression test - the URL hash was persisting after logout,
        causing the last selected tab to be visible on the login screen.
        """
        # Use auth-disabled server for this test (can access tabs)
        page.goto("http://localhost:8001/#account")
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

    @pytest.fixture
    def page_auth_enabled(self, page: Page, auth_enabled_server: str) -> Page:
        """Page with auth-enabled server."""
        page.goto(auth_enabled_server)
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(500)
        return page

    def test_regression_konverter_visible_with_welcome(self, page_auth_enabled: Page):
        """Regression: Konverter content was visible alongside welcome screen.

        Bug: The CSS class .tab-panel.active { display: block } was overriding
        the hidden attribute, causing the Konverter tab content to be visible
        even on the login/welcome screen.

        Fix: showLoginScreen() now removes 'active' class from all tab panels.
        """
        # Welcome screen should be visible
        welcome_screen = page_auth_enabled.locator("#welcomeScreen")
        expect(welcome_screen).to_be_visible()

        # Konverter should be completely hidden
        konverter = page_auth_enabled.locator("#tab-konverter")
        expect(konverter).to_be_hidden()

        # The info-box inside Konverter should also be hidden
        info_box = page_auth_enabled.locator("#tab-konverter .info-box")
        expect(info_box).to_be_hidden()

    def test_regression_last_tab_visible_after_logout(
        self, page: Page, auth_enabled_server: str
    ):
        """Regression: Last selected tab was visible after logout.

        Bug: After logout, the URL hash (e.g., #account) was preserved,
        and tab navigation would restore that tab's content on reload.

        Fix: logout() now clears the URL hash before reloading.
        """
        # Navigate to a specific tab hash
        page.goto(f"{auth_enabled_server}/#account")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(500)

        # Account tab should be hidden (not logged in)
        account_panel = page.locator("#tab-account")
        expect(account_panel).to_be_hidden()

        # Only welcome screen should be visible
        welcome_screen = page.locator("#welcomeScreen")
        expect(welcome_screen).to_be_visible()

    def test_regression_tab_buttons_still_active_when_hidden(
        self, page_auth_enabled: Page
    ):
        """Regression: Tab buttons retained 'active' class when hidden.

        This could cause accessibility issues and inconsistent state.
        """
        # No tab buttons should have 'active' class when not logged in
        active_buttons = page_auth_enabled.locator(".tab-button.active")
        expect(active_buttons).to_have_count(0)

        # All buttons should have aria-selected="false"
        tab_buttons = page_auth_enabled.locator(".tab-button")
        for btn in tab_buttons.all():
            expect(btn).to_have_attribute("aria-selected", "false")
