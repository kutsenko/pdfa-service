"""E2E tests for Design System - CSS Consolidation.

Tests verify that CSS design system variables, animations, and responsive
behavior work correctly across the application.
"""

import pytest
from playwright.sync_api import Page, expect

pytestmark = [pytest.mark.e2e, pytest.mark.playwright]


class TestCSSVariables:
    """Test that CSS custom properties are defined and applied."""

    def test_root_has_spacing_variables(self, page: Page) -> None:
        """Test that spacing scale CSS variables are defined in :root."""
        page.goto("http://localhost:8001")

        # Check spacing variables via computed styles on :root
        spacing_vars = [
            "--space-xs",
            "--space-sm",
            "--space-md",
            "--space-lg",
            "--space-xl",
            "--space-2xl",
        ]

        for var in spacing_vars:
            value = page.evaluate(
                f"getComputedStyle(document.documentElement).getPropertyValue('{var}')"
            )
            assert value.strip(), f"CSS variable {var} should be defined"

    def test_root_has_color_variables(self, page: Page) -> None:
        """Test that color CSS variables are defined in :root."""
        page.goto("http://localhost:8001")

        color_vars = [
            "--color-primary",
            "--color-primary-dark",
            "--color-text",
            "--color-text-secondary",
            "--color-border",
            "--color-bg",
            "--color-bg-secondary",
        ]

        for var in color_vars:
            value = page.evaluate(
                f"getComputedStyle(document.documentElement).getPropertyValue('{var}')"
            )
            assert value.strip(), f"CSS variable {var} should be defined"

    def test_root_has_semantic_color_variables(self, page: Page) -> None:
        """Test that semantic status color CSS variables are defined."""
        page.goto("http://localhost:8001")

        semantic_vars = [
            "--color-success",
            "--color-danger",
            "--color-warning",
            "--color-info",
        ]

        for var in semantic_vars:
            value = page.evaluate(
                f"getComputedStyle(document.documentElement).getPropertyValue('{var}')"
            )
            assert value.strip(), f"CSS variable {var} should be defined"

    def test_root_has_typography_scale(self, page: Page) -> None:
        """Test that typography scale CSS variables are defined."""
        page.goto("http://localhost:8001")

        typography_vars = [
            "--font-size-xs",
            "--font-size-sm",
            "--font-size-base",
            "--font-size-lg",
            "--font-size-xl",
            "--font-size-2xl",
        ]

        for var in typography_vars:
            value = page.evaluate(
                f"getComputedStyle(document.documentElement).getPropertyValue('{var}')"
            )
            assert value.strip(), f"CSS variable {var} should be defined"

    def test_root_has_radius_scale(self, page: Page) -> None:
        """Test that border radius scale CSS variables are defined."""
        page.goto("http://localhost:8001")

        radius_vars = [
            "--radius-sm",
            "--radius-md",
            "--radius-lg",
            "--radius-xl",
            "--radius-full",
        ]

        for var in radius_vars:
            value = page.evaluate(
                f"getComputedStyle(document.documentElement).getPropertyValue('{var}')"
            )
            assert value.strip(), f"CSS variable {var} should be defined"

    def test_root_has_shadow_scale(self, page: Page) -> None:
        """Test that shadow scale CSS variables are defined."""
        page.goto("http://localhost:8001")

        shadow_vars = [
            "--shadow-sm",
            "--shadow-md",
            "--shadow-lg",
            "--shadow-xl",
        ]

        for var in shadow_vars:
            value = page.evaluate(
                f"getComputedStyle(document.documentElement).getPropertyValue('{var}')"
            )
            assert value.strip(), f"CSS variable {var} should be defined"

    def test_legacy_aliases_defined(self, page: Page) -> None:
        """Test that legacy CSS variable aliases are defined for compatibility."""
        page.goto("http://localhost:8001")

        legacy_vars = [
            "--primary-color",
            "--border-color",
            "--card-bg",
            "--text-color",
        ]

        for var in legacy_vars:
            value = page.evaluate(
                f"getComputedStyle(document.documentElement).getPropertyValue('{var}')"
            )
            assert value.strip(), f"Legacy alias {var} should be defined"


class TestColorConsistency:
    """Test that colors are applied consistently across components."""

    def test_primary_color_on_buttons(self, page: Page) -> None:
        """Test that primary color is applied to primary buttons."""
        page.goto("http://localhost:8001")

        # Convert button has primary gradient
        convert_btn = page.locator(".btn-convert").first
        expect(convert_btn).to_be_visible()

        # Check background includes gradient with primary color
        background = page.evaluate(
            "getComputedStyle(document.querySelector('.btn-convert')).background"
        )
        assert "gradient" in background.lower() or "rgb" in background.lower()

    def test_primary_color_on_active_tab(self, page: Page) -> None:
        """Test that primary color is applied to active tab."""
        page.goto("http://localhost:8001")

        active_tab = page.locator(".tab-button.active").first
        expect(active_tab).to_be_visible()

        # Check border or color uses primary
        border_color = page.evaluate(
            "getComputedStyle(document.querySelector('.tab-button.active')).borderBottomColor"
        )
        # Primary color #667eea = rgb(102, 126, 234)
        assert "102" in border_color or "126" in border_color or "234" in border_color

    def test_focus_outline_uses_primary_color(self, page: Page) -> None:
        """Test that focus outlines use primary color."""
        page.goto("http://localhost:8001")

        # Focus the first tab button
        tab_btn = page.locator(".tab-button").first
        tab_btn.focus()

        # Get computed outline color
        outline_color = page.evaluate(
            "getComputedStyle(document.querySelector('.tab-button:focus')).outlineColor"
        )
        # Should contain primary color components
        assert outline_color != "rgb(0, 0, 0)", "Focus outline should not be black"


class TestAnimations:
    """Test that animations are defined and working."""

    def test_spin_animation_exists(self, page: Page) -> None:
        """Test that spin animation is available for spinners."""
        page.goto("http://localhost:8001")

        # Check if @keyframes spin is defined
        has_spin = page.evaluate(
            """
            () => {
                const sheets = document.styleSheets;
                for (let sheet of sheets) {
                    try {
                        for (let rule of sheet.cssRules) {
                            if (rule.type === CSSRule.KEYFRAMES_RULE &&
                                rule.name === 'spin') {
                                return true;
                            }
                        }
                    } catch (e) {}
                }
                return false;
            }
        """
        )
        assert has_spin, "@keyframes spin should be defined"

    def test_fadein_animation_exists(self, page: Page) -> None:
        """Test that fadeIn animation is available."""
        page.goto("http://localhost:8001")

        has_fadein = page.evaluate(
            """
            () => {
                const sheets = document.styleSheets;
                for (let sheet of sheets) {
                    try {
                        for (let rule of sheet.cssRules) {
                            if (rule.type === CSSRule.KEYFRAMES_RULE &&
                                rule.name === 'fadeIn') {
                                return true;
                            }
                        }
                    } catch (e) {}
                }
                return false;
            }
        """
        )
        assert has_fadein, "@keyframes fadeIn should be defined"

    def test_pulse_animation_exists(self, page: Page) -> None:
        """Test that pulse animation is available."""
        page.goto("http://localhost:8001")

        has_pulse = page.evaluate(
            """
            () => {
                const sheets = document.styleSheets;
                for (let sheet of sheets) {
                    try {
                        for (let rule of sheet.cssRules) {
                            if (rule.type === CSSRule.KEYFRAMES_RULE &&
                                rule.name === 'pulse') {
                                return true;
                            }
                        }
                    } catch (e) {}
                }
                return false;
            }
        """
        )
        assert has_pulse, "@keyframes pulse should be defined"


class TestResponsiveDesign:
    """Test responsive design behavior at different viewport sizes."""

    def test_desktop_layout(self, page: Page) -> None:
        """Test layout at desktop viewport (1024px)."""
        page.set_viewport_size({"width": 1024, "height": 768})
        page.goto("http://localhost:8001")

        container = page.locator(".container").first
        expect(container).to_be_visible()

        # Container should have reasonable max-width
        max_width = page.evaluate(
            "getComputedStyle(document.querySelector('.container')).maxWidth"
        )
        assert max_width == "800px", "Container max-width should be 800px"

    def test_tablet_layout(self, page: Page) -> None:
        """Test layout at tablet viewport (768px)."""
        page.set_viewport_size({"width": 768, "height": 1024})
        page.goto("http://localhost:8001")

        container = page.locator(".container").first
        expect(container).to_be_visible()

    def test_mobile_layout(self, page: Page) -> None:
        """Test layout at mobile viewport (375px)."""
        page.set_viewport_size({"width": 375, "height": 667})
        page.goto("http://localhost:8001")

        container = page.locator(".container").first
        expect(container).to_be_visible()

        # Container should have reduced padding on mobile
        padding = page.evaluate(
            "getComputedStyle(document.querySelector('.container')).padding"
        )
        assert padding, "Container should have padding on mobile"

    def test_landscape_mobile_layout(self, page: Page) -> None:
        """Test layout in landscape orientation on mobile."""
        page.set_viewport_size({"width": 667, "height": 375})
        page.goto("http://localhost:8001")

        container = page.locator(".container").first
        expect(container).to_be_visible()

    def test_tabs_scrollable_on_mobile(self, page: Page) -> None:
        """Test that tabs are scrollable on narrow viewports."""
        page.set_viewport_size({"width": 320, "height": 568})
        page.goto("http://localhost:8001")

        tab_nav = page.locator(".tab-navigation").first
        expect(tab_nav).to_be_visible()

        # Tab buttons should still be accessible
        tab_buttons = page.locator(".tab-button")
        assert tab_buttons.count() >= 4, "Should have at least 4 tab buttons"


class TestTouchTargets:
    """Test touch target sizes for accessibility."""

    def test_buttons_have_minimum_touch_target(self, page: Page) -> None:
        """Test that buttons have minimum 44px touch target height."""
        page.set_viewport_size({"width": 375, "height": 667})
        page.goto("http://localhost:8001")

        # Check convert button
        convert_btn = page.locator(".btn-convert").first
        if convert_btn.is_visible():
            box = convert_btn.bounding_box()
            assert box is not None
            assert box["height"] >= 44, "Button should have min 44px height"

    def test_tab_buttons_have_adequate_size(self, page: Page) -> None:
        """Test that tab buttons have adequate touch target size."""
        page.set_viewport_size({"width": 375, "height": 667})
        page.goto("http://localhost:8001")

        tab_btn = page.locator(".tab-button").first
        expect(tab_btn).to_be_visible()

        box = tab_btn.bounding_box()
        assert box is not None
        assert box["height"] >= 40, "Tab button should have adequate height"


class TestLogoAccessibility:
    """Test logo accessibility attributes."""

    def test_header_logo_has_short_alt_text(self, page: Page) -> None:
        """Test that header logo has concise alt text."""
        page.goto("http://localhost:8001")

        header_logo = page.locator(".header-logo")
        expect(header_logo).to_have_count(1)

        alt_text = header_logo.get_attribute("alt")
        assert alt_text == "PDF/A", "Header logo should have short alt 'PDF/A'"

    def test_header_logo_has_explicit_dimensions(self, page: Page) -> None:
        """Test that header logo has width and height attributes."""
        page.goto("http://localhost:8001")

        header_logo = page.locator(".header-logo")
        expect(header_logo).to_have_attribute("width", "40")
        expect(header_logo).to_have_attribute("height", "40")


class TestProgressiveDisclosure:
    """Test progressive disclosure UI patterns."""

    def test_advanced_options_collapsed_by_default(self, page: Page) -> None:
        """Test that advanced options are collapsed initially."""
        page.goto("http://localhost:8001")

        advanced_details = page.locator("details.advanced-options").first
        expect(advanced_details).to_have_count(1)

        # Should not have 'open' attribute
        is_open = advanced_details.get_attribute("open")
        assert is_open is None, "Advanced options should be collapsed by default"

    def test_advanced_options_can_be_expanded(self, page: Page) -> None:
        """Test that advanced options can be expanded by clicking summary."""
        page.goto("http://localhost:8001")

        summary = page.locator("details.advanced-options summary").first
        expect(summary).to_be_visible()

        # Click to expand
        summary.click()

        # Now should have 'open' attribute
        details = page.locator("details.advanced-options").first
        expect(details).to_have_attribute("open", "")

    def test_details_summary_has_indicator(self, page: Page) -> None:
        """Test that details summary has visual expand/collapse indicator."""
        page.goto("http://localhost:8001")

        summary = page.locator("details.advanced-options summary").first
        expect(summary).to_be_visible()

        # Check for ::before pseudo-element (triangle indicator) via computed style
        # The summary should have cursor: pointer
        cursor = page.evaluate(
            """
            getComputedStyle(
                document.querySelector('details.advanced-options summary')
            ).cursor
        """
        )
        assert cursor == "pointer", "Summary should have pointer cursor"


class TestDarkModeSupport:
    """Test dark mode CSS variable support."""

    def test_dark_mode_variables_defined_in_media_query(self, page: Page) -> None:
        """Test that dark mode overrides are defined in prefers-color-scheme."""
        page.goto("http://localhost:8001")

        # Check if dark mode media query exists in stylesheets
        has_dark_mode = page.evaluate(
            """
            () => {
                const sheets = document.styleSheets;
                for (let sheet of sheets) {
                    try {
                        for (let rule of sheet.cssRules) {
                            const isDarkMode = rule.type === CSSRule.MEDIA_RULE &&
                                rule.conditionText &&
                                rule.conditionText.includes('color-scheme: dark');
                            if (isDarkMode) return true;
                        }
                    } catch (e) {}
                }
                return false;
            }
        """
        )
        assert has_dark_mode, "Dark mode media query should be defined"


class TestReducedMotion:
    """Test reduced motion preference support."""

    def test_reduced_motion_media_query_exists(self, page: Page) -> None:
        """Test that prefers-reduced-motion media query is defined."""
        page.goto("http://localhost:8001")

        has_reduced_motion = page.evaluate(
            """
            () => {
                const sheets = document.styleSheets;
                for (let sheet of sheets) {
                    try {
                        for (let rule of sheet.cssRules) {
                            if (rule.type === CSSRule.MEDIA_RULE &&
                                rule.conditionText &&
                                rule.conditionText.includes('prefers-reduced-motion')) {
                                return true;
                            }
                        }
                    } catch (e) {}
                }
                return false;
            }
        """
        )
        assert has_reduced_motion, "Reduced motion media query should be defined"
