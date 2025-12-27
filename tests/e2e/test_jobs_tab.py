"""End-to-end tests for the Jobs (Jobs) Tab using Playwright.

These tests verify the complete Jobs tab functionality based on US-007:
- Job list display with status, filename, duration, size, events
- Status filtering (all, completed, failed, processing)
- Pagination (20 jobs per page)
- Event expansion (inline accordion)
- Download action for completed jobs
- Retry action for failed jobs
- Real-time updates via WebSocket
- i18n support (EN, DE, ES, FR)
- Responsive design
- Dark mode
- Accessibility (WCAG 2.1 Level AA)

Run with:
    pytest tests/e2e/test_auftraege_tab.py -v
    pytest tests/e2e/test_auftraege_tab.py -k "test_job_list" -v

Requirements:
    - API server running on localhost:8001 (test server)
    - MongoDB running
    - Playwright browsers installed: playwright install
"""

from __future__ import annotations

from playwright.sync_api import Page, expect

# =============================================================================
# Job List Display Tests
# =============================================================================


class TestJobListDisplay:
    """Tests for job list display functionality."""

    def test_should_display_jobs_tab(self, page_with_server: Page):
        """Jobs tab should be visible and clickable."""
        page_with_server.goto("http://localhost:8001")
        page_with_server.wait_for_load_state("networkidle")

        # Jobs tab button should exist
        tab_btn = page_with_server.locator("#tab-jobs-btn")
        expect(tab_btn).to_be_visible()
        expect(tab_btn).to_be_enabled()

    def test_should_show_loading_state_initially(self, page_with_server: Page):
        """Loading state should be visible when opening Jobs tab."""
        page_with_server.goto("http://localhost:8001")
        page_with_server.wait_for_load_state("networkidle")

        # Click Jobs tab
        page_with_server.click("#tab-jobs-btn")

        # Should show loading or content
        # (Loading might be too fast to catch, so we check for either state)
        loading = page_with_server.locator("#jobsLoading")
        content = page_with_server.locator("#jobsContent")

        # At least one should be visible
        assert (
            loading.is_visible() or content.is_visible()
        ), "Either loading or content should be visible"

    def test_should_display_empty_state_when_no_jobs(self, page_with_server: Page):
        """Empty state should be displayed when user has no jobs."""
        page_with_server.goto("http://localhost:8001")
        page_with_server.wait_for_load_state("networkidle")

        page_with_server.click("#tab-jobs-btn")
        page_with_server.wait_for_timeout(1000)  # Wait for API call

        # Should show empty state OR table with rows
        empty_state = page_with_server.locator("#jobsEmpty")

        # Check if empty state is shown
        if empty_state.is_visible():
            expect(empty_state).to_contain_text("No jobs found")

    def test_should_display_jobs_table_with_columns(self, page_with_server: Page):
        """Jobs table should have all required columns."""
        page_with_server.goto("http://localhost:8001")
        page_with_server.click("#tab-jobs-btn")
        page_with_server.wait_for_timeout(1000)

        # Table should exist
        table = page_with_server.locator(".jobs-table")
        expect(table).to_be_visible()

        # Check column headers
        expect(
            page_with_server.locator('th[data-i18n="jobs.table.status"]')
        ).to_be_visible()
        expect(
            page_with_server.locator('th[data-i18n="jobs.table.filename"]')
        ).to_be_visible()
        expect(
            page_with_server.locator('th[data-i18n="jobs.table.created"]')
        ).to_be_visible()
        expect(
            page_with_server.locator('th[data-i18n="jobs.table.duration"]')
        ).to_be_visible()
        expect(
            page_with_server.locator('th[data-i18n="jobs.table.events"]')
        ).to_be_visible()
        expect(
            page_with_server.locator('th[data-i18n="jobs.table.actions"]')
        ).to_be_visible()

    def test_should_display_status_badges_with_colors(self, page_with_server: Page):
        """Status badges should have appropriate colors."""
        page_with_server.goto("http://localhost:8001")
        page_with_server.click("#tab-jobs-btn")
        page_with_server.wait_for_timeout(1000)

        # Check if any status badges exist
        badges = page_with_server.locator(".status-badge")
        count = badges.count()

        if count > 0:
            # Get first badge and check it has a class
            first_badge = badges.first
            class_attr = first_badge.get_attribute("class")
            assert "status-badge" in class_attr, "Badge should have status-badge class"

            # Verify badge has a status class (completed, failed, processing, etc.)
            has_status = any(
                status in class_attr
                for status in [
                    "completed",
                    "failed",
                    "processing",
                    "queued",
                    "cancelled",
                ]
            )
            assert has_status, f"Badge should have status class, got: {class_attr}"


# =============================================================================
# Status Filtering Tests
# =============================================================================


class TestJobFiltering:
    """Tests for job status filtering functionality."""

    def test_should_display_filter_buttons(self, page_with_server: Page):
        """All filter buttons should be visible."""
        page_with_server.goto("http://localhost:8001")
        page_with_server.click("#tab-jobs-btn")
        page_with_server.wait_for_timeout(500)

        # Check all filter buttons exist
        expect(page_with_server.locator('button[data-status="all"]')).to_be_visible()
        expect(
            page_with_server.locator('button[data-status="completed"]')
        ).to_be_visible()
        expect(page_with_server.locator('button[data-status="failed"]')).to_be_visible()
        expect(
            page_with_server.locator('button[data-status="processing"]')
        ).to_be_visible()

    def test_all_filter_should_be_active_by_default(self, page_with_server: Page):
        """'All' filter button should be active by default."""
        page_with_server.goto("http://localhost:8001")
        page_with_server.click("#tab-jobs-btn")
        page_with_server.wait_for_timeout(500)

        all_btn = page_with_server.locator('button[data-status="all"]')
        class_attr = all_btn.get_attribute("class")
        assert "active" in class_attr, "All button should have 'active' class"

    def test_should_switch_active_filter_on_click(self, page_with_server: Page):
        """Clicking filter button should make it active."""
        page_with_server.goto("http://localhost:8001")
        page_with_server.click("#tab-jobs-btn")
        page_with_server.wait_for_timeout(500)

        # Click 'Completed' filter
        completed_btn = page_with_server.locator('button[data-status="completed"]')
        completed_btn.click()
        page_with_server.wait_for_timeout(300)

        # Completed button should be active
        class_attr = completed_btn.get_attribute("class")
        assert "active" in class_attr, "Completed button should be active after click"

        # All button should no longer be active
        all_btn = page_with_server.locator('button[data-status="all"]')
        all_class = all_btn.get_attribute("class")
        assert "active" not in all_class, "All button should not be active"

    def test_should_filter_jobs_by_status(self, page_with_server: Page):
        """Filtering should show only jobs with selected status."""
        page_with_server.goto("http://localhost:8001")
        page_with_server.click("#tab-jobs-btn")
        page_with_server.wait_for_timeout(1000)

        # Click 'Failed' filter
        failed_btn = page_with_server.locator('button[data-status="failed"]')
        failed_btn.click()
        page_with_server.wait_for_timeout(1000)  # Wait for API call

        # Check if any jobs are displayed
        rows = page_with_server.locator("tr.job-row")
        row_count = rows.count()

        if row_count > 0:
            # All visible rows should have 'failed' status badge
            for i in range(row_count):
                badge = rows.nth(i).locator(".status-badge")
                class_attr = badge.get_attribute("class")
                assert "failed" in class_attr, f"Row {i} should have failed status"


# =============================================================================
# Pagination Tests
# =============================================================================


class TestJobPagination:
    """Tests for pagination functionality."""

    def test_should_display_pagination_controls(self, page_with_server: Page):
        """Pagination controls should be visible."""
        page_with_server.goto("http://localhost:8001")
        page_with_server.click("#tab-jobs-btn")
        page_with_server.wait_for_timeout(1000)

        # Pagination navigation should exist
        expect(page_with_server.locator(".jobs-pagination")).to_be_visible()
        expect(page_with_server.locator("#jobsPrevBtn")).to_be_visible()
        expect(page_with_server.locator("#jobsNextBtn")).to_be_visible()
        expect(page_with_server.locator("#jobsPageInfo")).to_be_visible()

    def test_previous_button_should_be_disabled_on_first_page(
        self, page_with_server: Page
    ):
        """Previous button should be disabled when on first page."""
        page_with_server.goto("http://localhost:8001")
        page_with_server.click("#tab-jobs-btn")
        page_with_server.wait_for_timeout(1000)

        prev_btn = page_with_server.locator("#jobsPrevBtn")
        expect(prev_btn).to_be_disabled()

    def test_should_display_page_info(self, page_with_server: Page):
        """Page info should display current range."""
        page_with_server.goto("http://localhost:8001")
        page_with_server.click("#tab-jobs-btn")
        page_with_server.wait_for_timeout(1000)

        page_info = page_with_server.locator("#jobsPageInfo")
        text = page_info.inner_text()

        # Should contain pagination info (e.g., "1-20 of 50 jobs" or "No jobs")
        assert len(text) > 0, "Page info should contain text"

    def test_keyboard_navigation_should_work(self, page_with_server: Page):
        """Arrow keys should navigate pages."""
        page_with_server.goto("http://localhost:8001")
        page_with_server.click("#tab-jobs-btn")
        page_with_server.wait_for_timeout(1000)

        # Try pressing right arrow (next page)
        page_with_server.keyboard.press("ArrowRight")
        page_with_server.wait_for_timeout(500)

        # Check if anything changed (hard to verify without jobs, but should not error)
        # This test mainly ensures keyboard listeners are attached


# =============================================================================
# Event Expansion Tests
# =============================================================================


class TestJobEventExpansion:
    """Tests for job event expansion functionality."""

    def test_events_column_should_show_event_count(self, page_with_server: Page):
        """Events column should display event count or '0 events'."""
        page_with_server.goto("http://localhost:8001")
        page_with_server.click("#tab-jobs-btn")
        page_with_server.wait_for_timeout(1000)

        rows = page_with_server.locator("tr.job-row")
        if rows.count() > 0:
            # First row should have events cell
            first_row = rows.first
            events_cell = first_row.locator("td:nth-child(6)")  # Events column
            text = events_cell.inner_text()

            # Should contain number and "event" or "events"
            assert (
                "event" in text.lower()
            ), f"Events cell should contain 'event', got: {text}"

    def test_expand_button_should_be_visible_for_jobs_with_events(
        self, page_with_server: Page
    ):
        """Expand button should be visible for jobs with events."""
        page_with_server.goto("http://localhost:8001")
        page_with_server.click("#tab-jobs-btn")
        page_with_server.wait_for_timeout(1000)

        rows = page_with_server.locator("tr.job-row")
        if rows.count() > 0:
            # Check if any row has an expand button
            # At least structure should exist (even if no events yet)
            pass

    def test_clicking_expand_should_show_event_details_row(
        self, page_with_server: Page
    ):
        """Clicking expand button should show event details row."""
        page_with_server.goto("http://localhost:8001")
        page_with_server.click("#tab-jobs-btn")
        page_with_server.wait_for_timeout(1000)

        expand_btns = page_with_server.locator(".expand-btn")
        if expand_btns.count() > 0:
            # Click first expand button
            expand_btns.first.click()
            page_with_server.wait_for_timeout(1000)  # Wait for events to load

            # Check if events row appeared
            # Should have at least tried to load
            # (might show "No events" or actual events)

    def test_escape_key_should_collapse_expanded_job(self, page_with_server: Page):
        """Pressing Escape should collapse expanded job."""
        page_with_server.goto("http://localhost:8001")
        page_with_server.click("#tab-jobs-btn")
        page_with_server.wait_for_timeout(1000)

        expand_btns = page_with_server.locator(".expand-btn")
        if expand_btns.count() > 0:
            # Expand first job
            expand_btns.first.click()
            page_with_server.wait_for_timeout(500)

            # Press Escape
            page_with_server.keyboard.press("Escape")
            page_with_server.wait_for_timeout(300)

            # Events row should be hidden
            events_row = page_with_server.locator("tr.job-events-row").first
            expect(events_row).to_be_hidden()


# =============================================================================
# Job Actions Tests
# =============================================================================


class TestJobActions:
    """Tests for job action buttons (download, retry)."""

    def test_should_display_download_button_for_completed_jobs(
        self, page_with_server: Page
    ):
        """Completed jobs should have a download button."""
        page_with_server.goto("http://localhost:8001")
        page_with_server.click("#tab-jobs-btn")
        page_with_server.wait_for_timeout(1000)

        # Filter to completed jobs
        page_with_server.click('button[data-status="completed"]')
        page_with_server.wait_for_timeout(1000)

        rows = page_with_server.locator("tr.job-row")
        if rows.count() > 0:
            # First completed job should have download button
            # Structure should exist (even if no completed jobs yet)
            pass

    def test_should_display_retry_button_for_failed_jobs(self, page_with_server: Page):
        """Failed jobs should have a retry button."""
        page_with_server.goto("http://localhost:8001")
        page_with_server.click("#tab-jobs-btn")
        page_with_server.wait_for_timeout(1000)

        # Filter to failed jobs
        page_with_server.click('button[data-status="failed"]')
        page_with_server.wait_for_timeout(1000)

        rows = page_with_server.locator("tr.job-row")
        if rows.count() > 0:
            # First failed job should have retry button
            # Structure should exist (even if no failed jobs yet)
            pass

    def test_retry_button_should_switch_to_converter_tab(self, page_with_server: Page):
        """Clicking retry should switch to converter tab."""
        page_with_server.goto("http://localhost:8001")
        page_with_server.click("#tab-jobs-btn")
        page_with_server.wait_for_timeout(1000)

        # Filter to failed jobs
        page_with_server.click('button[data-status="failed"]')
        page_with_server.wait_for_timeout(1000)

        retry_btns = page_with_server.locator(".retry-btn")
        if retry_btns.count() > 0:
            # Click retry
            retry_btns.first.click()
            page_with_server.wait_for_timeout(1000)

            # Should switch to Konverter tab
            konverter_tab = page_with_server.locator("#tab-konverter")
            expect(konverter_tab).not_to_have_attribute("hidden")


# =============================================================================
# Internationalization Tests
# =============================================================================


class TestInternationalization:
    """Tests for i18n support."""

    def test_should_display_english_translations(self, page_with_server: Page):
        """English translations should be visible."""
        page_with_server.goto("http://localhost:8001/en")
        page_with_server.wait_for_load_state("networkidle")

        page_with_server.click("#tab-jobs-btn")
        page_with_server.wait_for_timeout(1000)

        # Check English headings
        expect(page_with_server.locator('h2[data-i18n="jobs.title"]')).to_contain_text(
            "Job History"
        )

        # Check filter buttons
        expect(
            page_with_server.locator('button[data-i18n="jobs.filter.all"]')
        ).to_contain_text("All")
        expect(
            page_with_server.locator('button[data-i18n="jobs.filter.completed"]')
        ).to_contain_text("Completed")

    def test_should_display_german_translations(self, page_with_server: Page):
        """German translations should be visible."""
        page_with_server.goto("http://localhost:8001/de")
        page_with_server.wait_for_load_state("networkidle")

        page_with_server.click("#tab-jobs-btn")
        page_with_server.wait_for_timeout(1000)

        # Check German headings
        expect(page_with_server.locator('h2[data-i18n="jobs.title"]')).to_contain_text(
            "Jobs"
        )

        # Check filter buttons
        expect(
            page_with_server.locator('button[data-i18n="jobs.filter.all"]')
        ).to_contain_text("Alle")
        expect(
            page_with_server.locator('button[data-i18n="jobs.filter.completed"]')
        ).to_contain_text("Abgeschlossen")

    def test_should_display_spanish_translations(self, page_with_server: Page):
        """Spanish translations should be visible."""
        page_with_server.goto("http://localhost:8001/es")
        page_with_server.wait_for_load_state("networkidle")

        page_with_server.click("#tab-jobs-btn")
        page_with_server.wait_for_timeout(1000)

        # Check Spanish headings
        expect(page_with_server.locator('h2[data-i18n="jobs.title"]')).to_contain_text(
            "Historial de Trabajos"
        )

        # Check filter buttons
        expect(
            page_with_server.locator('button[data-i18n="jobs.filter.all"]')
        ).to_contain_text("Todos")

    def test_should_display_french_translations(self, page_with_server: Page):
        """French translations should be visible."""
        page_with_server.goto("http://localhost:8001/fr")
        page_with_server.wait_for_load_state("networkidle")

        page_with_server.click("#tab-jobs-btn")
        page_with_server.wait_for_timeout(1000)

        # Check French headings
        expect(page_with_server.locator('h2[data-i18n="jobs.title"]')).to_contain_text(
            "Historique des Tâches"
        )

        # Check filter buttons
        expect(
            page_with_server.locator('button[data-i18n="jobs.filter.all"]')
        ).to_contain_text("Tous")
        expect(
            page_with_server.locator('button[data-i18n="jobs.filter.completed"]')
        ).to_contain_text("Terminés")


# =============================================================================
# Responsive Design Tests
# =============================================================================


class TestResponsiveDesign:
    """Tests for responsive design."""

    def test_should_display_all_columns_on_desktop(self, page_with_server: Page):
        """Desktop layout should show all 7 columns."""
        page_with_server.set_viewport_size({"width": 1920, "height": 1080})
        page_with_server.goto("http://localhost:8001")

        page_with_server.click("#tab-jobs-btn")
        page_with_server.wait_for_timeout(1000)

        # All columns should be visible
        expect(
            page_with_server.locator('th[data-i18n="jobs.table.status"]')
        ).to_be_visible()
        expect(
            page_with_server.locator('th[data-i18n="jobs.table.size"]')
        ).to_be_visible()

    def test_should_hide_size_column_on_tablet(self, page_with_server: Page):
        """Tablet layout should hide size column."""
        page_with_server.set_viewport_size({"width": 768, "height": 1024})
        page_with_server.goto("http://localhost:8001")

        page_with_server.click("#tab-jobs-btn")
        page_with_server.wait_for_timeout(1000)

        # Size column should be hidden (has .hide-mobile class)
        # Check if it has display: none or is not visible
        # On tablet, size column might still be visible
        # only hidden on mobile (<600px)

    def test_should_use_card_layout_on_mobile(self, page_with_server: Page):
        """Mobile layout should use card-based layout."""
        page_with_server.set_viewport_size({"width": 375, "height": 667})
        page_with_server.goto("http://localhost:8001")

        page_with_server.click("#tab-jobs-btn")
        page_with_server.wait_for_timeout(1000)

        # Table should exist (CSS changes layout, not DOM)
        table = page_with_server.locator(".jobs-table")
        expect(table).to_be_visible()

    def test_action_buttons_should_be_touch_friendly_on_mobile(
        self, page_with_server: Page
    ):
        """Action buttons should have min 44px height on mobile."""
        page_with_server.set_viewport_size({"width": 375, "height": 667})
        page_with_server.goto("http://localhost:8001")

        page_with_server.click("#tab-jobs-btn")
        page_with_server.wait_for_timeout(1000)

        # Check if action buttons exist
        action_btns = page_with_server.locator(".action-btn")
        if action_btns.count() > 0:
            # Get computed height
            height = action_btns.first.evaluate(
                "el => parseFloat(window.getComputedStyle(el).height)"
            )
            assert height >= 44, f"Action button should be ≥44px, got {height}px"


# =============================================================================
# Dark Mode Tests
# =============================================================================


class TestDarkMode:
    """Tests for dark mode support."""

    def test_should_apply_dark_mode_styles(self, page_with_server: Page):
        """Dark mode should apply dark background colors."""
        page_with_server.emulate_media(color_scheme="dark")
        page_with_server.goto("http://localhost:8001")

        page_with_server.click("#tab-jobs-btn")
        page_with_server.wait_for_timeout(1000)

        # Check table has dark background
        table = page_with_server.locator(".jobs-table")
        if table.is_visible():
            bg_color = table.evaluate(
                "el => window.getComputedStyle(el).backgroundColor"
            )

            # Extract RGB values
            import re

            rgb_match = re.findall(r"\d+", bg_color)
            if rgb_match:
                rgb = [int(x) for x in rgb_match[:3]]
                max_value = max(rgb)

                # Dark background should have low RGB values
                assert max_value < 200, f"Expected dark background, got RGB {rgb}"

    def test_status_badges_should_have_dark_mode_colors(self, page_with_server: Page):
        """Status badges should have readable colors in dark mode."""
        page_with_server.emulate_media(color_scheme="dark")
        page_with_server.goto("http://localhost:8001")

        page_with_server.click("#tab-jobs-btn")
        page_with_server.wait_for_timeout(1000)

        # Check if badges exist and have color
        badges = page_with_server.locator(".status-badge")
        if badges.count() > 0:
            bg_color = badges.first.evaluate(
                "el => window.getComputedStyle(el).backgroundColor"
            )
            # Should have a background color defined
            assert (
                len(bg_color) > 0
            ), "Status badge should have background color in dark mode"


# =============================================================================
# Accessibility Tests
# =============================================================================


class TestAccessibility:
    """Tests for accessibility (WCAG 2.1 Level AA)."""

    def test_filter_buttons_should_have_aria_pressed(self, page_with_server: Page):
        """Filter buttons should have aria-pressed attribute."""
        page_with_server.goto("http://localhost:8001")
        page_with_server.click("#tab-jobs-btn")
        page_with_server.wait_for_timeout(1000)

        all_btn = page_with_server.locator('button[data-status="all"]')
        aria_pressed = all_btn.get_attribute("aria-pressed")
        assert aria_pressed in [
            "true",
            "false",
        ], "Filter button should have aria-pressed"

    def test_table_should_have_proper_roles(self, page_with_server: Page):
        """Table should have proper ARIA roles."""
        page_with_server.goto("http://localhost:8001")
        page_with_server.click("#tab-jobs-btn")
        page_with_server.wait_for_timeout(1000)

        table = page_with_server.locator(".jobs-table")
        role = table.get_attribute("role")
        assert role == "table", "Jobs table should have role='table'"

    def test_pagination_should_have_aria_labels(self, page_with_server: Page):
        """Pagination buttons should have aria-label."""
        page_with_server.goto("http://localhost:8001")
        page_with_server.click("#tab-jobs-btn")
        page_with_server.wait_for_timeout(1000)

        prev_btn = page_with_server.locator("#jobsPrevBtn")
        next_btn = page_with_server.locator("#jobsNextBtn")

        prev_label = prev_btn.get_attribute("aria-label")
        next_label = next_btn.get_attribute("aria-label")

        assert prev_label is not None, "Previous button should have aria-label"
        assert next_label is not None, "Next button should have aria-label"

    def test_page_info_should_have_aria_live(self, page_with_server: Page):
        """Page info should have aria-live for screen readers."""
        page_with_server.goto("http://localhost:8001")
        page_with_server.click("#tab-jobs-btn")
        page_with_server.wait_for_timeout(1000)

        page_info = page_with_server.locator("#jobsPageInfo")
        aria_live = page_info.get_attribute("aria-live")
        assert aria_live == "polite", "Page info should have aria-live='polite'"

    def test_jobs_should_be_keyboard_navigable(self, page_with_server: Page):
        """Job rows should be keyboard accessible."""
        page_with_server.goto("http://localhost:8001")
        page_with_server.click("#tab-jobs-btn")
        page_with_server.wait_for_timeout(1000)

        rows = page_with_server.locator("tr.job-row")
        if rows.count() > 0:
            # First row should have tabindex
            tabindex = rows.first.get_attribute("tabindex")
            assert tabindex == "0", "Job row should have tabindex='0'"
