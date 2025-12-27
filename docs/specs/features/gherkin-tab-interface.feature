# Feature: US-005 - Tab-Based User Interface
# User Story: Als pdfa-service Benutzer möchte ich die Benutzeroberfläche als Tabs organisiert haben,
#             um zwischen verschiedenen Funktionen einfach wechseln zu können.
# Date: 2025-12-26
# Related: US-004 (Live Job Events - preserved in Konverter tab)

Feature: Tab-Based User Interface Navigation
  As a pdfa-service user
  I want the user interface organized as tabs
  So that I can easily switch between different functions (Converter, Camera, Jobs, Account, Documentation)

  Background:
    Given the pdfa-service web UI is loaded in a browser
    And the tab navigation is visible below the header
    And there are 5 tabs: "Konverter", "Kamera", "Aufträge", "Konto", "Dokumentation"

  # ==========================================
  # Scenario 1: Initial Tab State
  # ==========================================

  Scenario: Konverter tab is active by default on page load
    Given the user opens the web UI without a URL hash
    Then the "Konverter" tab is active
    And the "Konverter" tab has class "active"
    And the "Konverter" tab has aria-selected="true"
    And the "Konverter" tab panel is visible
    And all other tab panels are hidden
    And the converter form is displayed

  # ==========================================
  # Scenario 2: Tab Switching via Click
  # ==========================================

  Scenario: User switches tabs by clicking tab buttons
    Given the "Konverter" tab is active
    When the user clicks the "Kamera" tab button
    Then the "Kamera" tab becomes active
    And the "Kamera" tab has class "active"
    And the "Kamera" tab has aria-selected="true"
    And the "Kamera" tab panel is visible
    And the "Konverter" tab panel is hidden
    And the "Konverter" tab has aria-selected="false"
    And the URL hash changes to "#kamera"

  Scenario: User can switch to each of the 5 tabs
    Given the "Konverter" tab is active
    When the user clicks each tab in sequence
    Then each clicked tab becomes active
    And only one tab is active at any time
    And the corresponding tab panel is displayed
    And the URL hash reflects the active tab

  # ==========================================
  # Scenario 3: Keyboard Navigation
  # ==========================================

  Scenario: User navigates tabs with Arrow Right key
    Given the "Konverter" tab is active and has focus
    When the user presses Arrow Right
    Then focus moves to the "Kamera" tab
    And the "Kamera" tab becomes active
    When the user presses Arrow Right again
    Then focus moves to the "Aufträge" tab
    And the "Aufträge" tab becomes active

  Scenario: User navigates tabs with Arrow Left key
    Given the "Aufträge" tab is active and has focus
    When the user presses Arrow Left
    Then focus moves to the "Kamera" tab
    And the "Kamera" tab becomes active
    When the user presses Arrow Left again
    Then focus moves to the "Konverter" tab
    And the "Konverter" tab becomes active

  Scenario: Arrow Right wraps from last tab to first tab
    Given the "Dokumentation" tab (last tab) is active and has focus
    When the user presses Arrow Right
    Then focus moves to the "Konverter" tab (first tab)
    And the "Konverter" tab becomes active

  Scenario: Arrow Left wraps from first tab to last tab
    Given the "Konverter" tab (first tab) is active and has focus
    When the user presses Arrow Left
    Then focus moves to the "Dokumentation" tab (last tab)
    And the "Dokumentation" tab becomes active

  Scenario: Home key jumps to first tab
    Given the "Konto" tab is active and has focus
    When the user presses Home
    Then focus moves to the "Konverter" tab
    And the "Konverter" tab becomes active

  Scenario: End key jumps to last tab
    Given the "Konverter" tab is active and has focus
    When the user presses End
    Then focus moves to the "Dokumentation" tab
    And the "Dokumentation" tab becomes active

  Scenario: Tab key cycles through tab buttons
    Given the "Konverter" tab is active and has focus
    When the user presses Tab
    Then focus moves to the next focusable element in the tab panel
    And the tab navigation can be re-entered via Shift+Tab

  # ==========================================
  # Scenario 4: Accessibility (ARIA)
  # ==========================================

  Scenario: Tab navigation has correct ARIA attributes
    Given the tab navigation is rendered
    Then the tab navigation container has role="tablist"
    And the tab navigation has aria-label="Main navigation"
    And each tab button has role="tab"
    And each tab button has aria-controls pointing to its panel ID
    And the active tab has aria-selected="true"
    And inactive tabs have aria-selected="false"
    And each tab panel has role="tabpanel"
    And each tab panel has aria-labelledby pointing to its tab button ID

  Scenario: Screen reader announces tab switches
    Given the user has a screen reader active (NVDA/ORCA)
    And the "Konverter" tab is active
    When the user clicks the "Kamera" tab
    Then the screen reader announces "Switched to Kamera tab"
    Or the screen reader announces "Kamera tab selected"

  Scenario: Screen reader announces tab count
    Given the user has a screen reader active
    And focus is on a tab button
    Then the screen reader announces "Tab 1 of 5: Konverter"
    Or similar tab position information

  # ==========================================
  # Scenario 5: Localization (i18n)
  # ==========================================

  Scenario Outline: Tab labels are translated in all languages
    Given the user has selected language "<language>"
    Then the 5 tab labels are displayed as:
      | Tab            | Label                |
      | Konverter      | <konverter_label>    |
      | Kamera         | <kamera_label>       |
      | Aufträge       | <auftraege_label>    |
      | Konto          | <konto_label>        |
      | Dokumentation  | <dokumentation_label> |

    Examples:
      | language | konverter_label | kamera_label | auftraege_label | konto_label | dokumentation_label |
      | en       | Converter       | Camera       | Jobs            | Account     | Documentation       |
      | de       | Konverter       | Kamera       | Aufträge        | Konto       | Dokumentation       |
      | es       | Convertidor     | Cámara       | Trabajos        | Cuenta      | Documentación       |
      | fr       | Convertisseur   | Caméra       | Tâches          | Compte      | Documentation       |

  Scenario Outline: Placeholder content is translated in all languages
    Given the user has selected language "<language>"
    When the user opens the "<tab>" tab
    Then the placeholder title is displayed as "<title>"
    And the placeholder description is displayed as "<description>"

    Examples:
      | language | tab    | title            | description                                                |
      | en       | Kamera | Camera Scanner   | Coming soon: Upload documents directly from your camera or scanner |
      | de       | Kamera | Kamera-Scanner   | Demnächst: Dokumente direkt von Ihrer Kamera oder Ihrem Scanner hochladen |
      | es       | Kamera | Escáner de Cámara | Próximamente: Cargue documentos directamente desde su cámara o escáner |
      | fr       | Kamera | Scanner de Caméra | Bientôt disponible : Téléchargez des documents directement depuis votre caméra ou scanner |

  # ==========================================
  # Scenario 6: Placeholder Tab Content
  # ==========================================

  Scenario: Placeholder tabs display "Coming soon" message
    Given the user clicks the "Kamera" tab
    Then the "Kamera" tab panel is visible
    And the panel contains a centered placeholder
    And the placeholder shows an icon "📷"
    And the placeholder shows a title "Camera Scanner" (in current language)
    And the placeholder shows a description about future functionality
    And no interactive elements are present in the placeholder

  Scenario: Each placeholder tab has appropriate icon
    When the user views each placeholder tab
    Then the placeholders display the following icons:
      | Tab            | Icon |
      | Kamera         | 📷   |
      | Aufträge       | 📋   |
      | Konto          | 👤   |
      | Dokumentation  | 📖   |

  # ==========================================
  # Scenario 7: State Preservation
  # ==========================================

  Scenario: Form state preserved when switching tabs
    Given the "Konverter" tab is active
    And the user has selected a file "test.pdf"
    And the user has selected PDF/A level "2"
    And the user has selected compression "balanced"
    When the user switches to the "Kamera" tab
    And then switches back to the "Konverter" tab
    Then the selected file is still "test.pdf"
    And the PDF/A level is still "2"
    And the compression is still "balanced"
    And all form inputs retain their values

  Scenario: WebSocket connection persists during tab switches
    Given the "Konverter" tab is active
    And a conversion job is running
    And WebSocket is connected and receiving progress updates
    When the user switches to the "Aufträge" tab
    Then the WebSocket connection remains active
    And progress updates continue to be received
    When the user switches back to the "Konverter" tab
    Then the progress bar shows the current job progress
    And no connection re-establishment occurred

  Scenario: Event list state preserved during tab switches
    Given the "Konverter" tab is active
    And a conversion has completed
    And the event list shows 5 events
    And the event list is expanded (visible)
    When the user switches to the "Konto" tab
    And then switches back to the "Konverter" tab
    Then the event list still shows 5 events
    And the event list is still expanded
    And no events were lost or duplicated

  # ==========================================
  # Scenario 8: URL Hash Navigation
  # ==========================================

  Scenario: URL hash determines initial active tab
    Given the user opens the URL "https://example.com/#kamera"
    Then the "Kamera" tab is active on page load
    And the "Kamera" tab panel is visible
    And the "Konverter" tab is inactive

  Scenario: URL hash updates when switching tabs
    Given the URL is "https://example.com/#konverter"
    When the user clicks the "Aufträge" tab
    Then the URL changes to "https://example.com/#auftraege"
    And the browser history contains this change

  Scenario: Browser back button returns to previous tab
    Given the user is on the "Konverter" tab
    When the user clicks the "Kamera" tab (URL: #kamera)
    And then clicks the "Aufträge" tab (URL: #auftraege)
    And then presses the browser back button
    Then the URL changes to "https://example.com/#kamera"
    And the "Kamera" tab becomes active

  Scenario: Browser forward button moves to next tab in history
    Given the user navigated Konverter → Kamera → Aufträge → (back) → Kamera
    When the user presses the browser forward button
    Then the URL changes to "https://example.com/#auftraege"
    And the "Aufträge" tab becomes active

  Scenario: Invalid hash defaults to Konverter tab
    Given the user opens the URL "https://example.com/#invalid-tab"
    Then the "Konverter" tab is active
    And the URL remains "https://example.com/#invalid-tab" (no forced redirect)

  # ==========================================
  # Scenario 9: Visual States
  # ==========================================

  Scenario: Active tab has distinct visual styling
    Given the "Konverter" tab is active
    Then the "Konverter" tab button has:
      | Property        | Value                      |
      | class           | contains "active"          |
      | color           | #667eea (purple)           |
      | border-bottom   | 3px solid #667eea          |
      | background      | rgba(102, 126, 234, 0.08)  |

  Scenario: Inactive tabs have default styling
    Given the "Kamera" tab is inactive
    Then the "Kamera" tab button has:
      | Property        | Value                      |
      | class           | does not contain "active"  |
      | color           | #666 (gray)                |
      | border-bottom   | transparent                |
      | background      | transparent                |

  Scenario: Hover state on inactive tabs
    Given the "Aufträge" tab is inactive
    When the user hovers over the "Aufträge" tab button
    Then the button background changes to "rgba(102, 126, 234, 0.05)"
    And the text color changes to "#667eea"
    And the cursor changes to "pointer"

  Scenario: Focus indicator visible on keyboard navigation
    Given the user is navigating with keyboard
    When focus is on the "Konto" tab button
    Then the button has a visible 2px outline in color #667eea
    And the outline is offset by -2px (inside button)
    And the focus indicator meets WCAG 2.1 contrast requirements

  # ==========================================
  # Scenario 10: Responsive Design
  # ==========================================

  Scenario: Desktop view shows all tabs without scrolling
    Given the viewport width is 1920px (desktop)
    Then all 5 tab buttons are visible without scrolling
    And no horizontal scrollbar appears on the tab navigation
    And each tab button has adequate width (not cramped)

  Scenario: Mobile view enables horizontal scrolling for tabs
    Given the viewport width is 375px (mobile)
    Then the tab navigation container has horizontal scroll enabled
    And overflow-x is set to "auto"
    And -webkit-overflow-scrolling is set to "touch" (smooth scrolling on iOS)
    And the tab buttons have minimum width 90px each
    And the user can swipe left/right to scroll tabs

  Scenario: Touch targets meet minimum size on mobile
    Given the viewport width is 375px (mobile)
    Then each tab button has minimum dimensions:
      | Property        | Minimum Value |
      | height          | 44px          |
      | width           | 90px          |
      | padding         | 10px 12px     |
    And the touch targets are easily tappable with a finger

  Scenario: Tablet view shows all tabs comfortably
    Given the viewport width is 768px (tablet)
    Then all 5 tab buttons are visible without scrolling
    And the container max-width is 800px
    And tabs are not cramped or overlapping

  # ==========================================
  # Scenario 11: Dark Mode
  # ==========================================

  Scenario: Dark mode adjusts tab colors appropriately
    Given the system is in dark mode (prefers-color-scheme: dark)
    When the user views the tab navigation
    Then the tab navigation border-bottom is "#374151" (dark gray)
    And inactive tab buttons have color "#9ca3af" (light gray)
    And the active tab has color "#818cf8" (light purple)
    And the active tab border is "#818cf8"
    And the placeholder content title is "#e5e7eb" (light)
    And the placeholder content description is "#6b7280" (medium gray)

  Scenario: Dark mode hover states
    Given the system is in dark mode
    And the "Kamera" tab is inactive
    When the user hovers over the "Kamera" tab button
    Then the background changes to "rgba(102, 126, 234, 0.1)"
    And the text color changes to "#818cf8"

  # ==========================================
  # Scenario 12: Animation and Motion
  # ==========================================

  Scenario: Tab panel fade-in animation on switch
    Given the user is on the "Konverter" tab
    When the user clicks the "Kamera" tab
    Then the "Kamera" panel animates with a 0.3s fade-in
    And the animation includes translateY(8px) to translateY(0)
    And opacity transitions from 0 to 1

  Scenario: Reduced motion disables animations
    Given the user has prefers-reduced-motion: reduce enabled
    When the user switches from "Konverter" to "Kamera" tab
    Then no fade-in animation occurs
    And the tab panel appears instantly (no transition)

  # ==========================================
  # Scenario 13: Regression Tests (Existing Features)
  # ==========================================

  Scenario: Converter functionality works in Konverter tab
    Given the "Konverter" tab is active
    When the user uploads a PDF file "test.pdf"
    And clicks the "Convert" button
    Then the conversion starts
    And the progress bar is displayed
    And WebSocket updates are received
    And the event list populates with events
    And the modal appears after successful conversion
    And the download link works

  Scenario: Authentication bar remains visible across tabs
    Given the authentication is enabled
    And the user is logged in
    Then the authentication bar is fixed at the top of the page
    When the user switches to any tab
    Then the authentication bar remains visible and functional
    And the logout button is always accessible

  Scenario: Language switcher remains visible across tabs
    Given the language switcher is in the top-right corner
    When the user switches to any tab
    Then the language switcher remains visible
    And clicking it switches the language for all tabs
    And all tab labels update to the new language

  Scenario: Modal overlay works from Konverter tab
    Given the "Konverter" tab is active
    And a conversion has completed successfully
    When the event summary modal appears
    Then the modal overlays the entire page (not just the tab panel)
    And the backdrop covers all tabs
    And clicking "Download" in the modal works
    And clicking "OK" closes the modal and returns focus to the Konverter tab

  # ==========================================
  # Non-Functional Requirements
  # ==========================================

  Scenario: Tab switching is performant
    Given the user is on any tab
    When the user clicks a different tab
    Then the tab switch completes in less than 100ms
    And no layout shift occurs
    And no flickering is visible

  Scenario: All tabs render on initial page load
    Given the user opens the web UI
    When the page finishes loading
    Then all 5 tab panels are present in the DOM
    And only the active tab panel has display: block
    And inactive tab panels have display: none
    And no lazy loading occurs for tabs

  Scenario: No memory leaks when switching tabs repeatedly
    Given the user is on the "Konverter" tab
    When the user switches between all 5 tabs 100 times
    Then browser memory usage remains stable
    And no event listeners accumulate
    And no DOM nodes leak

  # ==========================================
  # Edge Cases
  # ==========================================

  Scenario: Clicking active tab does nothing
    Given the "Kamera" tab is already active
    When the user clicks the "Kamera" tab button again
    Then the tab remains active
    And no state change occurs
    And no unnecessary re-rendering happens

  Scenario: Rapid tab switching does not cause errors
    Given the user is on the "Konverter" tab
    When the user rapidly clicks all 5 tabs in quick succession
    Then all tab switches complete successfully
    And no JavaScript errors occur
    And the final active tab is the last clicked tab

  Scenario: Tab navigation works without JavaScript enabled
    Given the user has JavaScript disabled in the browser
    Then the tab navigation is still visible
    But tab switching does not work (graceful degradation)
    And the page displays a message: "JavaScript required for full functionality"

  # ==========================================
  # Browser Compatibility
  # ==========================================

  Scenario: Tab interface works in all supported browsers
    When the user opens the web UI in "<browser>"
    Then all tab functionality works correctly
    And visual styling is consistent
    And ARIA attributes are respected
    And keyboard navigation works

    Examples:
      | browser              |
      | Chrome (latest)      |
      | Firefox (latest)     |
      | Safari (latest)      |
      | Edge (latest)        |
      | Mobile Chrome        |
      | Mobile Safari (iOS)  |
