Feature: Job History Tab (Aufträge)
  As a pdfa-service user
  I want to view my conversion job history with detailed events
  So that I can track conversions, understand processing steps, and retry failed jobs

  Background:
    Given the pdfa-service web UI is running
    And I am on the homepage

  # =============================================================================
  # Job List Display
  # =============================================================================

  Scenario: Display empty job list
    Given there are no conversion jobs
    When I click on the "Aufträge" tab
    Then I should see the empty state message "No jobs found"
    And I should see the description "Start a conversion to see jobs here"

  Scenario: Display job list with completed jobs
    Given there are 5 completed conversion jobs
    When I click on the "Aufträge" tab
    Then I should see a table with 5 job rows
    And each row should display:
      | Column             | Example                  |
      | Status             | Completed (green badge)  |
      | Filename           | document.pdf             |
      | Created            | 2 minutes ago            |
      | Duration           | 3.5s                     |
      | Size               | 1.2 MB → 950 KB (1.3x)   |
      | Events             | 8 events                 |
      | Actions            | Download, Expand buttons |

  Scenario: Display job list with mixed statuses
    Given there are conversion jobs with different statuses:
      | Status     | Count |
      | completed  | 10    |
      | failed     | 3     |
      | processing | 2     |
    When I click on the "Aufträge" tab
    Then I should see 15 job rows total
    And completed jobs should have green status badges
    And failed jobs should have red status badges
    And processing jobs should have blue status badges

  Scenario: Display loading state
    Given the jobs API is responding slowly
    When I click on the "Aufträge" tab
    Then I should see a loading spinner
    And I should see the message "Loading jobs..."

  Scenario: Display error state
    Given the jobs API is unavailable
    When I click on the "Aufträge" tab
    Then I should see an error message
    And I should see a "Retry" button
    When I click the "Retry" button
    Then the job list should reload

  # =============================================================================
  # Status Filtering
  # =============================================================================

  Scenario: Filter jobs by status - All
    Given there are 20 conversion jobs with mixed statuses
    When I click on the "Aufträge" tab
    And I click the "All" filter button
    Then I should see all 20 jobs
    And the "All" button should be highlighted

  Scenario: Filter jobs by status - Completed
    Given there are conversion jobs:
      | Status     | Count |
      | completed  | 12    |
      | failed     | 5     |
      | processing | 3     |
    When I click on the "Aufträge" tab
    And I click the "Completed" filter button
    Then I should see only 12 jobs
    And all displayed jobs should have status "Completed"
    And the "Completed" button should be highlighted

  Scenario: Filter jobs by status - Failed
    Given there are conversion jobs:
      | Status     | Count |
      | completed  | 12    |
      | failed     | 5     |
      | processing | 3     |
    When I click on the "Aufträge" tab
    And I click the "Failed" filter button
    Then I should see only 5 jobs
    And all displayed jobs should have status "Failed"
    And the "Failed" button should be highlighted

  Scenario: Filter jobs by status - Processing
    Given there are conversion jobs:
      | Status     | Count |
      | completed  | 12    |
      | failed     | 5     |
      | processing | 3     |
    When I click on the "Aufträge" tab
    And I click the "Processing" filter button
    Then I should see only 3 jobs
    And all displayed jobs should have status "Processing"
    And the "Processing" button should be highlighted

  # =============================================================================
  # Pagination
  # =============================================================================

  Scenario: Display pagination controls
    Given there are 50 conversion jobs
    When I click on the "Aufträge" tab
    Then I should see pagination controls
    And I should see the page indicator "1-20 of 50 jobs"
    And the "Previous" button should be disabled
    And the "Next" button should be enabled

  Scenario: Navigate to next page
    Given there are 50 conversion jobs
    And I am on the "Aufträge" tab
    And I am viewing page 1
    When I click the "Next" button
    Then I should see page 2
    And the page indicator should show "21-40 of 50 jobs"
    And the "Previous" button should be enabled
    And the "Next" button should be enabled

  Scenario: Navigate to previous page
    Given there are 50 conversion jobs
    And I am on the "Aufträge" tab
    And I am viewing page 2
    When I click the "Previous" button
    Then I should see page 1
    And the page indicator should show "1-20 of 50 jobs"
    And the "Previous" button should be disabled

  Scenario: Last page pagination
    Given there are 50 conversion jobs
    And I am on the "Aufträge" tab
    And I am viewing page 3 (final page)
    Then the page indicator should show "41-50 of 50 jobs"
    And the "Next" button should be disabled
    And the "Previous" button should be enabled

  Scenario: Pagination with keyboard shortcuts
    Given there are 50 conversion jobs
    And I am on the "Aufträge" tab
    And I am viewing page 1
    When I press the right arrow key
    Then I should see page 2
    When I press the left arrow key
    Then I should see page 1

  # =============================================================================
  # Event Expansion (Inline Timeline)
  # =============================================================================

  Scenario: Expand job to view events
    Given there is a completed conversion job with 8 events
    When I click on the "Aufträge" tab
    And I click on the job row
    Then the job row should expand
    And I should see an event timeline with 8 events
    And each event should display:
      | Component  | Example                         |
      | Icon       | 📄, 👁️, 🗜️ (event type icon)   |
      | Message    | "OCR enabled for document"      |
      | Timestamp  | "14:32:45"                      |
      | Details    | "language: deu+eng \| confidence: 95%" |

  Scenario: Collapse expanded job
    Given there is a completed job
    And I am on the "Aufträge" tab
    And the job is expanded showing events
    When I click on the job row again
    Then the event timeline should collapse
    And I should see only the job summary row

  Scenario: Expand different job (accordion behavior)
    Given there are 3 completed jobs
    And I am on the "Aufträge" tab
    And job #1 is expanded
    When I click on job #2
    Then job #1 should collapse
    And job #2 should expand
    And only one job should be expanded at a time

  Scenario: Event icons display correctly
    Given there is a job with the following events:
      | Event Type           | Expected Icon |
      | format_conversion    | 📄            |
      | ocr_decision         | 👁️            |
      | compression_selected | 🗜️            |
      | passthrough_mode     | ⚡            |
      | fallback_applied     | 🔄            |
      | job_timeout          | ⏱️            |
      | job_cleanup          | 🧹            |
    When I expand the job
    Then each event should display its correct icon

  Scenario: Lazy load events on expansion
    Given there is a completed job
    And the job list was fetched without events (performance optimization)
    When I click on the "Aufträge" tab
    And I expand the job for the first time
    Then a request should be made to "/api/v1/jobs/{job_id}/status"
    And the events should be loaded and displayed
    And the events should be cached

  Scenario: Cached events on re-expansion
    Given there is a completed job
    And I am on the "Aufträge" tab
    And I have expanded the job once (events cached)
    When I collapse the job
    And I expand it again
    Then no new API request should be made
    And the cached events should be displayed

  Scenario: Display empty events message
    Given there is a job with no events recorded
    When I expand the job
    Then I should see the message "No events recorded"

  # =============================================================================
  # Download Action
  # =============================================================================

  Scenario: Download completed job PDF
    Given there is a completed conversion job "report.pdf"
    When I click on the "Aufträge" tab
    And I click the "Download" button for "report.pdf"
    Then the PDF should download with filename "report.pdf"
    And the browser should trigger a download

  Scenario: Download button only visible for completed jobs
    Given there are jobs with different statuses:
      | Status     | Filename      |
      | completed  | success.pdf   |
      | failed     | error.pdf     |
      | processing | running.pdf   |
    When I click on the "Aufträge" tab
    Then the "Download" button should be visible for "success.pdf"
    And the "Download" button should NOT be visible for "error.pdf"
    And the "Download" button should NOT be visible for "running.pdf"

  Scenario: Download with authentication enabled
    Given authentication is enabled (PDFA_ENABLE_AUTH=true)
    And I am logged in as "user@example.com"
    And there is a completed job owned by "user@example.com"
    When I click the "Download" button
    Then the request should include the Bearer token
    And the download should succeed

  Scenario: Download error handling
    Given there is a completed job
    And the download endpoint returns a 404 error
    When I click the "Download" button
    Then I should see an error message "Download failed. Please try again."

  # =============================================================================
  # Retry Action
  # =============================================================================

  Scenario: Retry failed job
    Given there is a failed conversion job "invoice.pdf" with config:
      | Parameter              | Value           |
      | pdfa_level             | 2               |
      | ocr_language           | deu+eng         |
      | compression_profile    | balanced        |
      | enable_ocr             | true            |
      | skip_ocr_on_tagged     | true            |
    When I click on the "Aufträge" tab
    And I click the "Retry" button for "invoice.pdf"
    Then I should be switched to the "Konverter" tab
    And the form should be pre-filled with:
      | Field                  | Value           |
      | PDF Type               | PDF/A-2         |
      | OCR Language           | deu+eng         |
      | Compression            | balanced        |
      | Enable OCR             | checked         |
      | Skip OCR on Tagged     | checked         |
    And I should see a notification "Please upload invoice.pdf to retry this conversion"

  Scenario: Retry button only visible for failed jobs
    Given there are jobs with different statuses:
      | Status     | Filename      |
      | completed  | success.pdf   |
      | failed     | error.pdf     |
      | processing | running.pdf   |
    When I click on the "Aufträge" tab
    Then the "Retry" button should be visible for "error.pdf"
    And the "Retry" button should NOT be visible for "success.pdf"
    And the "Retry" button should NOT be visible for "running.pdf"

  Scenario: Retry cancelled job
    Given there is a cancelled conversion job
    When I click on the "Aufträge" tab
    Then the "Retry" button should be visible
    When I click the "Retry" button
    Then I should be switched to the "Konverter" tab
    And the form should be pre-filled with the original config

  Scenario: Retry with Standard PDF type
    Given there is a failed job with config:
      | Parameter   | Value     |
      | pdfa_level  | standard  |
    When I retry the job
    Then the PDF Type dropdown should be set to "Standard PDF"

  Scenario: Retry error handling
    Given there is a failed job
    And the job status API returns a 500 error
    When I click the "Retry" button
    Then I should see an error message "Failed to load job details. Please try again."

  # =============================================================================
  # Real-time Updates (WebSocket)
  # =============================================================================

  Scenario: Real-time job completion via WebSocket
    Given I am on the "Aufträge" tab
    And there is a processing job "document.pdf"
    When the job completes (WebSocket message received)
    Then the job status should update to "Completed" without page refresh
    And the status badge should change to green
    And the "Download" button should appear

  Scenario: Real-time job failure via WebSocket
    Given I am on the "Aufträge" tab
    And there is a processing job "broken.pdf"
    When the job fails (WebSocket message received)
    Then the job status should update to "Failed" without page refresh
    And the status badge should change to red
    And the "Retry" button should appear

  Scenario: Real-time event count update
    Given I am on the "Aufträge" tab
    And there is a processing job with 5 events
    When a new event is added (WebSocket message received)
    Then the event count badge should update to "6 events"
    And the UI should transition smoothly

  Scenario: Fallback to polling when WebSocket unavailable
    Given the WebSocket connection is not available
    When I am on the "Aufträge" tab
    Then the system should poll "/api/v1/jobs/history" every 5 seconds
    And job updates should still appear (with slight delay)

  Scenario: Stop polling when tab inactive
    Given I am on the "Aufträge" tab
    And the system is polling for updates
    When I switch to the "Konverter" tab
    Then the polling should stop
    When I switch back to the "Aufträge" tab
    Then polling should resume

  # =============================================================================
  # Authentication Modes
  # =============================================================================

  Scenario: Jobs with authentication enabled
    Given authentication is enabled (PDFA_ENABLE_AUTH=true)
    And I am logged in as "user@example.com"
    And there are 10 jobs owned by "user@example.com"
    And there are 5 jobs owned by "other@example.com"
    When I click on the "Aufträge" tab
    Then I should see only 10 jobs (my jobs)
    And the job count should show "1-10 of 10 jobs"

  Scenario: Jobs with authentication disabled
    Given authentication is disabled (PDFA_ENABLE_AUTH=false)
    And there are 15 total jobs in the database
    When I click on the "Aufträge" tab
    Then I should see all 15 jobs
    And the job count should show "1-15 of 15 jobs"

  # =============================================================================
  # Localization (i18n)
  # =============================================================================

  Scenario: Display jobs tab in English
    Given the language is set to English
    When I click on the "Jobs" tab
    Then I should see:
      | Element              | Text                   |
      | Tab Title            | Job History            |
      | Filter - All         | All                    |
      | Filter - Completed   | Completed              |
      | Filter - Failed      | Failed                 |
      | Filter - Processing  | Processing             |
      | Table Header Status  | Status                 |
      | Table Header Actions | Actions                |
      | Download Button      | Download               |
      | Retry Button         | Retry                  |
      | Pagination Previous  | Previous               |
      | Pagination Next      | Next                   |

  Scenario: Display jobs tab in German
    Given the language is set to German
    When I click on the "Aufträge" tab
    Then I should see:
      | Element              | Text                   |
      | Tab Title            | Aufträge               |
      | Filter - All         | Alle                   |
      | Filter - Completed   | Abgeschlossen          |
      | Filter - Failed      | Fehlgeschlagen         |
      | Filter - Processing  | In Bearbeitung         |
      | Table Header Status  | Status                 |
      | Table Header Actions | Aktionen               |
      | Download Button      | Herunterladen          |
      | Retry Button         | Wiederholen            |
      | Pagination Previous  | Zurück                 |
      | Pagination Next      | Weiter                 |

  Scenario: Display jobs tab in Spanish
    Given the language is set to Spanish
    When I click on the "Trabajos" tab
    Then I should see:
      | Element              | Text                   |
      | Tab Title            | Historial de Trabajos  |
      | Filter - All         | Todos                  |
      | Filter - Completed   | Completados            |
      | Filter - Failed      | Fallidos               |
      | Download Button      | Descargar              |
      | Retry Button         | Reintentar             |

  Scenario: Display jobs tab in French
    Given the language is set to French
    When I click on the "Tâches" tab
    Then I should see:
      | Element              | Text                   |
      | Tab Title            | Historique des Tâches  |
      | Filter - All         | Tous                   |
      | Filter - Completed   | Terminés               |
      | Filter - Failed      | Échoués                |
      | Download Button      | Télécharger            |
      | Retry Button         | Réessayer              |

  # =============================================================================
  # Responsive Design
  # =============================================================================

  Scenario: Display jobs on desktop (>800px)
    Given I am viewing the page on a desktop (1920x1080)
    When I click on the "Aufträge" tab
    Then I should see a table with 7 columns:
      | Column             |
      | Status             |
      | Filename           |
      | Created            |
      | Duration           |
      | Size               |
      | Events             |
      | Actions            |
    And all columns should be fully visible

  Scenario: Display jobs on tablet (600-800px)
    Given I am viewing the page on a tablet (768x1024)
    When I click on the "Aufträge" tab
    Then I should see a condensed table
    And the compression ratio column should be hidden
    And 6 columns should be visible

  Scenario: Display jobs on mobile (<600px)
    Given I am viewing the page on a mobile device (375x667)
    When I click on the "Aufträge" tab
    Then I should see a card-based layout (not table)
    And each job should be displayed as a card
    And job details should be stacked vertically
    And action buttons should be full-width
    And touch targets should be at least 44px

  # =============================================================================
  # Performance
  # =============================================================================

  Scenario: Job list caching
    Given I am on the "Aufträge" tab
    And the job list was loaded 3 seconds ago
    When I switch to another tab and back
    Then no new API request should be made (cache used)
    And the cached job list should be displayed

  Scenario: Cache expiration
    Given I am on the "Aufträge" tab
    And the job list was loaded 6 seconds ago (cache expired)
    When I switch to another tab and back
    Then a new API request should be made
    And the fresh job list should be displayed

  Scenario: Lazy loading events on expansion
    Given there are 20 jobs in the list
    When I load the "Aufträge" tab
    Then the job list request should NOT include events (only events_count)
    And the response size should be minimal
    When I expand a job
    Then a separate request should fetch that job's events

  # =============================================================================
  # Accessibility (a11y)
  # =============================================================================

  Scenario: Keyboard navigation
    Given I am on the "Aufträge" tab
    When I press Tab repeatedly
    Then I should be able to focus:
      | Element                  |
      | Filter buttons           |
      | Job rows                 |
      | Download buttons         |
      | Retry buttons            |
      | Expand buttons           |
      | Pagination buttons       |
    And focus indicators should be clearly visible

  Scenario: Screen reader support
    Given I am using a screen reader
    When I navigate to the "Aufträge" tab
    Then all buttons should have ARIA labels
    And the table should have proper header associations
    And status changes should be announced (ARIA live region)
    And expanded/collapsed state should be announced

  Scenario: Keyboard shortcuts
    Given I am on the "Aufträge" tab viewing page 1
    When I press the right arrow key
    Then I should navigate to page 2
    When I press the left arrow key
    Then I should navigate back to page 1

  Scenario: Collapse with Escape key
    Given I am on the "Aufträge" tab
    And a job is expanded showing events
    When I press the Escape key
    Then the event timeline should collapse

  Scenario: Color contrast compliance
    Given I am on the "Aufträge" tab
    Then all text should have a contrast ratio of at least 4.5:1 (WCAG AA)
    And status should not be conveyed by color alone (icons + text used)

  Scenario: Dark mode support
    Given I have enabled dark mode in my system preferences
    When I view the "Aufträge" tab
    Then the page should use dark color scheme
    And status badges should have dark-appropriate colors
    And text contrast should still meet WCAG AA standards

  # =============================================================================
  # Edge Cases
  # =============================================================================

  Scenario: Very long filename truncation
    Given there is a job with filename "this_is_a_very_long_filename_that_exceeds_forty_characters_and_should_be_truncated.pdf"
    When I view the job in the list
    Then the filename should be truncated to "this_is_a_very_long_filename_that...pdf"
    And hovering should show the full filename in a tooltip

  Scenario: Job with zero events
    Given there is a job that failed immediately with 0 events
    When I expand the job
    Then I should see "No events recorded"

  Scenario: Job with very large file sizes
    Given there is a job with file size 2.5 GB input and 1.8 GB output
    When I view the job
    Then the size should display as "2.5 GB → 1.8 GB (1.4x)"

  Scenario: Very fast job completion (<1 second)
    Given there is a job that completed in 0.3 seconds
    When I view the job
    Then the duration should display as "0.3s"

  Scenario: Relative time display
    Given there are jobs created at different times:
      | Created      | Expected Display |
      | 30 sec ago   | Just now         |
      | 5 min ago    | 5 minutes ago    |
      | 2 hours ago  | 2 hours ago      |
      | 3 days ago   | 3 days ago       |
      | 2 weeks ago  | 2 weeks ago      |
      | 6 months ago | 6 months ago     |
    When I view the jobs
    Then each job should display the correct relative time

  Scenario: Network reconnection
    Given I am on the "Aufträge" tab
    And the WebSocket connection is lost
    When the network reconnects
    Then the WebSocket should reconnect automatically
    And job updates should resume without user action
