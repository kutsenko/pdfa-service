# Feature: US-004 - Live Display of Conversion Events
# User Story: Als pdfa-service Benutzer möchte ich die Konvertierungsevents sehen, sobald sie erzeugt werden,
#             um den Fortschritt der Konvertierung besser nachvollziehen zu können.
# Date: 2025-12-25
# Related: US-002 (Job Event Logging - provides the events to display)

Feature: Live Display of Conversion Events via WebSocket
  As a pdfa-service user
  I want to see conversion events as they occur in real-time
  So that I can better understand the progress and decisions made during conversion

  Background:
    Given the pdfa-service is running with MongoDB enabled
    And the web UI is loaded in a browser
    And WebSocket support is available
    And the user has an active WebSocket connection

  # ==========================================
  # Scenario 1: Event List Appears on First Event
  # ==========================================

  Scenario: Event list container appears when first event is received
    Given the user is on the PDF/A converter page
    And no conversion job is running
    And the event list container is hidden
    When the user uploads a DOCX file "sample.docx"
    And the user starts the conversion
    And the system emits the first job event "format_conversion"
    Then the event list container becomes visible
    And the event count badge shows "1"
    And the event list toggle button is displayed with aria-expanded="false"

  # ==========================================
  # Scenario 2: Event Display with Localization
  # ==========================================

  Scenario Outline: Events are displayed in the selected language
    Given the user has selected language "<language>"
    And the user is converting a PDF file
    When the system emits an OCR decision event with:
      | event_type | ocr_decision      |
      | decision   | skip              |
      | reason     | tagged_pdf        |
      | _i18n_key  | ocr_decision.skip.tagged_pdf |
    Then the event appears in the event list
    And the event message is displayed as "<expected_message>"
    And the event has the purple left border (ocr_decision color)
    And the event timestamp is formatted for "<language>" locale

    Examples:
      | language | expected_message                       |
      | en       | OCR skipped: PDF already tagged        |
      | de       | OCR übersprungen: PDF bereits getaggt  |
      | es       | OCR omitido: PDF ya etiquetado         |
      | fr       | OCR ignoré: PDF déjà balisé            |

  # ==========================================
  # Scenario 3: All Event Types Displayed
  # ==========================================

  Scenario: All 7 event types are displayed with correct styling
    Given the user is converting a DOCX file with OCR enabled
    When the conversion emits the following events in sequence:
      | event_type            | icon | color   |
      | format_conversion     | 🔄   | Blue    |
      | ocr_decision          | 🔍   | Purple  |
      | compression_selected  | 📦   | Green   |
      | passthrough_mode      | ⚡   | Amber   |
      | fallback_applied      | ⚠️   | Red     |
      | job_timeout           | ⏱️   | Red     |
      | job_cleanup           | 🧹   | Gray    |
    Then all 7 events appear in the event list
    And each event displays the correct emoji icon
    And each event has the correct color-coded left border
    And the event count badge shows "7"
    And events are ordered with newest first (reverse chronological)

  # ==========================================
  # Scenario 4: Event Details Expansion
  # ==========================================

  Scenario: User can expand event details
    Given the user is viewing a completed conversion
    And an "ocr_decision" event is displayed with details:
      """
      {
        "decision": "skip",
        "reason": "tagged_pdf",
        "confidence": 0.95
      }
      """
    When the user clicks on the "Details" summary
    Then the details section expands
    And the JSON details are displayed in a formatted code block
    And internal i18n keys (_i18n_key, _i18n_params) are not shown
    And only user-relevant data (decision, reason, confidence) is displayed

  # ==========================================
  # Scenario 5: Event List Toggle
  # ==========================================

  Scenario: User can collapse and expand the event list
    Given the event list container is visible
    And the event list contains 5 events
    And the event list is collapsed (hidden)
    And the toggle button shows aria-expanded="false"
    When the user clicks the event list toggle button
    Then the event list expands and becomes visible
    And the toggle arrow rotates 90 degrees
    And the toggle button aria-expanded changes to "true"
    When the user clicks the toggle button again
    Then the event list collapses and becomes hidden
    And the toggle arrow rotates back to original position
    And the toggle button aria-expanded changes to "false"
    And the event count badge still shows "5" when collapsed

  # ==========================================
  # Scenario 6: Events Reset on New Job
  # ==========================================

  Scenario: Previous events are cleared when starting a new conversion
    Given the user has completed a conversion
    And the event list shows 8 events from the previous job
    And the event count badge shows "8"
    When the user uploads a new file "another.pdf"
    And the user starts a new conversion
    And the system sends the "job_accepted" message
    Then the event list is cleared
    And the event count badge shows "0"
    And the event list container becomes hidden
    And the toggle state is reset to collapsed

  # ==========================================
  # Scenario 7: Parameter Substitution in Messages
  # ==========================================

  Scenario: Event messages support parameter substitution
    Given the user is converting a DOCX file
    When the system emits a format_conversion event with:
      | event_type   | format_conversion           |
      | input_format | docx                        |
      | pages        | 15                          |
      | _i18n_key    | format_conversion.docx.success |
      | _i18n_params | {"pages": 15}               |
    Then the event message displays "DOCX converted to PDF (15 pages)" in English
    And the parameter "15" is correctly substituted in the template

  # ==========================================
  # Scenario 8: WebSocket Broadcasting
  # ==========================================

  Scenario: Events are broadcast via WebSocket immediately after MongoDB persistence
    Given the system is processing a conversion job
    And the EventLogger logs an OCR decision event to MongoDB
    When the MongoDB write completes successfully
    Then the system broadcasts a "job_event" WebSocket message
    And the message type is "job_event"
    And the message contains job_id, event_type, timestamp, message, and details
    And the message includes _i18n_key and _i18n_params in details
    And the broadcast completes within 5 seconds (timeout protection)

  # ==========================================
  # Scenario 9: Broadcast Error Handling
  # ==========================================

  Scenario: MongoDB persistence succeeds even if WebSocket broadcast fails
    Given the system is processing a conversion job
    And the EventLogger logs a compression event to MongoDB
    When the MongoDB write succeeds
    And the WebSocket broadcast fails with a timeout error
    Then the event is still persisted in MongoDB
    And the error is logged with level WARNING
    And the conversion job continues without interruption
    And the user sees the event when reconnecting to WebSocket

  # ==========================================
  # Scenario 10: Accessibility - Screen Reader Announcements
  # ==========================================

  Scenario: High-priority events are announced to screen readers
    Given the user is using a screen reader (NVDA or ORCA)
    And the user has language set to German
    When the following events occur during conversion:
      | event_type            | announced | message_de                                       |
      | format_conversion     | no        | -                                                |
      | ocr_decision          | yes       | OCR übersprungen: PDF bereits getaggt            |
      | compression_selected  | no        | -                                                |
      | fallback_applied      | yes       | Fallback: OCR fehlgeschlagen, fortfahren ohne OCR|
      | job_timeout           | yes       | Timeout: maximale Dauer überschritten (300s)     |
      | job_cleanup           | no        | -                                                |
    Then the screen reader announces 3 events (ocr_decision, fallback_applied, job_timeout)
    And the announcements are in German
    And the announcements appear in the aria-live region
    And low-priority events (format_conversion, compression_selected, job_cleanup) are NOT announced

  # ==========================================
  # Scenario 11: Accessibility - Keyboard Navigation
  # ==========================================

  Scenario: Event list is fully keyboard accessible
    Given the event list container is visible with 5 events
    And the user is navigating with keyboard only
    When the user presses Tab to focus the toggle button
    Then the toggle button receives keyboard focus with visible outline
    When the user presses Enter key
    Then the event list expands
    When the user presses Tab to move to the first event details
    And the user presses Enter on a details summary
    Then the details expand
    And all interactive elements are reachable via Tab
    And focus indicators are clearly visible (2px outline)

  # ==========================================
  # Scenario 12: Dark Mode Support
  # ==========================================

  Scenario: Event list adapts to dark mode
    Given the user's system is set to dark mode (prefers-color-scheme: dark)
    And the event list contains 3 events
    Then the event list container background is dark (#1e1e1e)
    And event item backgrounds are dark (#2a2a2a)
    And event text is light-colored (#e0e0e0)
    And event timestamps are lighter gray (#999)
    And color-coded borders remain visible and distinct
    And the event details code background is very dark (#1a1a1a)

  # ==========================================
  # Scenario 13: Reduced Motion Support
  # ==========================================

  Scenario: Animations are disabled for users who prefer reduced motion
    Given the user has enabled "prefers-reduced-motion" in system settings
    When new events are added to the event list
    Then the fade-in animation is disabled
    And events appear instantly without transition
    When the user clicks the toggle button
    Then the toggle icon does not rotate with animation
    And the event list expands/collapses instantly

  # ==========================================
  # Scenario 14: Multiple Concurrent Clients
  # ==========================================

  Scenario: Multiple WebSocket clients receive the same events
    Given User A has an active WebSocket connection to job "job-123"
    And User B has an active WebSocket connection to job "job-123"
    When the system emits an OCR decision event for job "job-123"
    Then User A receives the "job_event" WebSocket message
    And User B receives the "job_event" WebSocket message
    And both users see the event appear in their event list simultaneously
    And the event data is identical for both clients

  # ==========================================
  # Scenario 15: Backward Compatibility
  # ==========================================

  Scenario: Old WebSocket clients ignore unknown message types
    Given a legacy WebSocket client that only knows "progress", "completed", "error"
    And the client is connected to a conversion job
    When the system broadcasts a "job_event" message (unknown to legacy client)
    Then the legacy client logs "Unknown message type: job_event"
    And the legacy client continues to function normally
    And the legacy client still receives "progress" and "completed" messages
    And the conversion process completes successfully for the legacy client

  # ==========================================
  # Edge Cases
  # ==========================================

  Scenario: Event list handles very long event messages gracefully
    Given an event with a very long message (500 characters)
    When the event is added to the event list
    Then the message is displayed without overflow
    And the event item expands vertically to fit the content
    And the timestamp remains aligned to the top-right
    And horizontal scrolling is not required

  Scenario: Event list handles rapid successive events (stress test)
    Given the system emits 50 events in rapid succession (< 1 second)
    When all events are broadcast via WebSocket
    Then all 50 events appear in the event list
    And the event count badge shows "50"
    And the event list remains scrollable with max-height 400px
    And the newest event is at the top
    And no events are lost or duplicated
    And the UI remains responsive

  Scenario: Fallback to English when translation is missing
    Given the user has language set to French
    And an event is emitted with _i18n_key "ocr_decision.apply.new_reason"
    And this key does not exist in French translations
    When the event is displayed
    Then the event message falls back to the English message from the backend
    And the event timestamp is still formatted for French locale
    And no JavaScript error occurs

  Scenario: Event details with nested objects are formatted correctly
    Given an event with complex nested details:
      """
      {
        "input_format": "docx",
        "pages": 25,
        "metadata": {
          "author": "John Doe",
          "created": "2025-12-25T10:00:00Z"
        }
      }
      """
    When the user expands the event details
    Then the JSON is displayed with proper indentation (2 spaces)
    And nested objects are correctly formatted
    And the details are readable and valid JSON

# ==========================================
# Non-Functional Requirements
# ==========================================

  @performance
  Scenario: Event broadcasting does not impact conversion performance
    Given the system is converting a 100-page PDF with OCR
    When 20 events are emitted and broadcast during the conversion
    Then the total overhead from WebSocket broadcasting is < 1 second
    And each broadcast completes within 50ms or times out at 5 seconds
    And MongoDB persistence is not delayed by broadcasts
    And conversion time is within 2% of baseline (without events)

  @security
  Scenario: Event details do not expose sensitive information
    Given the system is converting a PDF with metadata
    When events are broadcast to the WebSocket client
    Then no system file paths are exposed in event details
    And no environment variables are exposed
    And no internal error stack traces are exposed
    And only user-relevant information is included in details

  @reliability
  Scenario: Event logging continues after WebSocket reconnection
    Given the user's WebSocket connection drops during conversion
    And 5 events were missed during the disconnection
    When the WebSocket reconnects
    Then the conversion continues normally
    And future events are broadcast correctly
    And the user can retrieve missed events from job history API (US-003)
    And the event count badge may show fewer events than total (expected behavior)
