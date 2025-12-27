Feature: Account Information and Settings Tab (Konto Tab)
  As a pdfa-service user
  I want to view my account information and settings on the Konto tab
  So that I can see my profile, configure default parameters, and manage my account

  Background:
    Given I am on the pdfa-service web interface
    And the tab interface is initialized with 5 tabs

  # ============================================================================
  # Account Information Display (Read-only)
  # ============================================================================

  Scenario: Display user profile information with authentication enabled
    Given authentication is enabled
    And I am logged in as "user@example.com"
    When I click on the "Konto" tab
    Then I should see the loading state
    And the profile API endpoint should be called
    And I should see my email address "user@example.com"
    And I should see my full name "Test User"
    And I should see my profile picture
    And I should see my user ID

  Scenario: Display default user profile with authentication disabled
    Given authentication is disabled
    When I click on the "Konto" tab
    Then I should see the profile for "Local User"
    And I should see the default email "local@localhost"
    And the account deletion button should be hidden
    And I should see a message "Account deletion is not available in local mode"

  Scenario: Display login statistics
    Given authentication is enabled
    And I am logged in as "user@example.com"
    And my account was created on "2025-01-15"
    And my last login was on "2025-12-27 10:30:00"
    And I have logged in 42 times
    When I click on the "Konto" tab
    Then I should see "Account Created: 15.01.2025"
    And I should see "Last Login: 27.12.2025, 10:30:00"
    And I should see "Total Logins: 42"

  Scenario: Display job statistics
    Given I am logged in as "user@example.com"
    And I have 10 total jobs
    And 8 jobs are completed
    And 2 jobs have failed
    And the average processing duration is 45.5 seconds
    And the total data processed is 5242880 bytes
    When I click on the "Konto" tab
    Then I should see "Total Jobs: 10"
    And I should see "Success Rate: 80.0%"
    And I should see "Avg Duration: 0.8 min"
    And I should see "Data Processed: 5.0 MB"

  Scenario: Display empty job statistics for new user
    Given I am logged in as "newuser@example.com"
    And I have 0 total jobs
    When I click on the "Konto" tab
    Then I should see "Total Jobs: 0"
    And I should see "Success Rate: -"
    And I should see "Avg Duration: -"
    And I should see "Data Processed: -"

  Scenario: Display activity log
    Given I am logged in as "user@example.com"
    And I have the following recent audit events:
      | event_type    | timestamp           | ip_address    |
      | user_login    | 2025-12-27 10:30:00 | 192.168.1.100 |
      | job_created   | 2025-12-27 10:31:00 | 192.168.1.100 |
      | job_completed | 2025-12-27 10:33:00 | 192.168.1.100 |
    When I click on the "Konto" tab
    Then I should see an activity log with 3 events
    And the first event should show "user_login"
    And the event should show timestamp "27.12.2025, 10:30:00"
    And the event should show IP address "192.168.1.100"

  Scenario: Display empty activity log
    Given I am logged in as "newuser@example.com"
    And I have no audit events
    When I click on the "Konto" tab
    Then I should see "No recent activity"

  # ============================================================================
  # User Preferences (Editable)
  # ============================================================================

  Scenario: Display default preferences for new user
    Given I am logged in as "user@example.com"
    And I have no saved preferences
    When I click on the "Konto" tab
    Then the PDF Type dropdown should show "PDF/A-2" selected
    And the OCR Language dropdown should show "Deutsch + English" selected
    And the Compression dropdown should show "Balanced" selected
    And the "Enable OCR" checkbox should be checked
    And the "Skip OCR for tagged PDFs" checkbox should be checked

  Scenario: Display saved preferences
    Given I am logged in as "user@example.com"
    And I have saved preferences:
      | field                       | value      |
      | default_pdfa_level          | standard   |
      | default_ocr_language        | eng        |
      | default_compression_profile | aggressive |
      | default_ocr_enabled         | false      |
      | default_skip_ocr_on_tagged  | false      |
    When I click on the "Konto" tab
    Then the PDF Type dropdown should show "Standard PDF" selected
    And the OCR Language dropdown should show "English" selected
    And the Compression dropdown should show "Aggressive" selected
    And the "Enable OCR" checkbox should be unchecked
    And the "Skip OCR for tagged PDFs" checkbox should be unchecked

  Scenario: Save preferences successfully
    Given I am logged in as "user@example.com"
    And I am on the "Konto" tab
    When I select "PDF/A-3" from the PDF Type dropdown
    And I select "Français" from the OCR Language dropdown
    And I select "High Quality" from the Compression dropdown
    And I click the "Save Preferences" button
    Then the preferences API should be called with:
      """
      {
        "default_pdfa_level": "3",
        "default_ocr_language": "fra",
        "default_compression_profile": "quality",
        "default_ocr_enabled": true,
        "default_skip_ocr_on_tagged": true
      }
      """
    And I should see a success message "Preferences saved successfully"
    And the success message should disappear after 5 seconds

  Scenario: Save preferences fails with error
    Given I am logged in as "user@example.com"
    And I am on the "Konto" tab
    And the API server is unavailable
    When I change a preference
    And I click the "Save Preferences" button
    Then I should see an error message "Failed to save preferences"
    And the error message should disappear after 5 seconds

  Scenario: Reset preferences to defaults
    Given I am logged in as "user@example.com"
    And I am on the "Konto" tab
    And I have modified the preferences form
    When I click the "Reset to Defaults" button
    Then the PDF Type dropdown should show "PDF/A-2" selected
    And the OCR Language dropdown should show "Deutsch + English" selected
    And the Compression dropdown should show "Balanced" selected
    And the "Enable OCR" checkbox should be checked
    And the "Skip OCR for tagged PDFs" checkbox should be checked

  Scenario: Preferences auto-apply to converter form
    Given I am logged in as "user@example.com"
    And I have saved preferences with PDF Type "Standard PDF"
    When I click on the "Konverter" tab
    Then the converter form should have PDF Type "Standard PDF" selected

  # ============================================================================
  # Account Deletion
  # ============================================================================

  Scenario: Show account deletion danger zone
    Given authentication is enabled
    And I am logged in as "user@example.com"
    When I click on the "Konto" tab
    Then I should see a red-bordered "Danger Zone" section
    And I should see a warning about irreversibility
    And I should see a red "Delete My Account" button

  Scenario: Account deletion disabled for local user
    Given authentication is disabled
    When I click on the "Konto" tab
    Then the "Delete My Account" button should be hidden
    And I should see "Account deletion is not available in local mode"

  Scenario: Open account deletion confirmation modal
    Given I am logged in as "user@example.com"
    And I am on the "Konto" tab
    When I click the "Delete My Account" button
    Then a confirmation modal should appear
    And the modal should have title "Confirm Account Deletion"
    And I should see an email input field
    And the "Delete Account" confirm button should be disabled

  Scenario: Cancel account deletion from modal
    Given I am logged in as "user@example.com"
    And I am on the "Konto" tab
    And the account deletion modal is open
    When I click the "Cancel" button
    Then the modal should close
    And my account should not be deleted

  Scenario: Email validation in deletion modal
    Given I am logged in as "user@example.com"
    And I am on the "Konto" tab
    And the account deletion modal is open
    When I type "wrong@email.com" in the email field
    Then I should see "Email does not match"
    And the "Delete Account" confirm button should be disabled
    When I type "user@example.com" in the email field
    Then the error message should disappear
    And the "Delete Account" confirm button should be enabled

  Scenario: Successfully delete account
    Given I am logged in as "user@example.com"
    And I am on the "Konto" tab
    And the account deletion modal is open
    When I type "user@example.com" in the email field
    And I click the "Delete Account" confirm button
    Then the delete account API should be called with:
      """
      {
        "email_confirmation": "user@example.com"
      }
      """
    And I should see an alert "Account deleted successfully"
    And I should be logged out automatically

  Scenario: Account deletion fails with wrong email
    Given I am logged in as "user@example.com"
    And I am on the "Konto" tab
    And the account deletion modal is open
    When I somehow bypass frontend validation
    And I submit with email "wrong@email.com"
    Then the API should return a 400 error
    And I should see "Failed to delete account: Email confirmation does not match"
    And I should still be logged in

  Scenario: Account deletion cascades data removal
    Given I am logged in as "user@example.com"
    And I have 5 conversion jobs in the database
    And I have 20 audit log entries
    And I have saved preferences
    When I successfully delete my account
    Then all my jobs should be removed from the database
    And all my audit logs should be removed from the database
    And my preferences should be removed from the database
    And my user profile should be removed from the database

  # ============================================================================
  # Caching and Performance
  # ============================================================================

  Scenario: Profile data cached for 30 seconds
    Given I am logged in as "user@example.com"
    When I click on the "Konto" tab
    Then the profile API should be called
    When I switch to another tab
    And I immediately switch back to the "Konto" tab within 30 seconds
    Then the profile API should not be called again
    And I should see the cached data

  Scenario: Cache expires after 30 seconds
    Given I am logged in as "user@example.com"
    And I am on the "Konto" tab
    And the profile data was fetched
    When I wait 31 seconds
    And I switch to another tab
    And I switch back to the "Konto" tab
    Then the profile API should be called again

  Scenario: Loading state during data fetch
    Given I am logged in as "user@example.com"
    When I click on the "Konto" tab
    Then I should see a loading spinner
    And I should see "Loading account information..."
    And the main content should be hidden
    When the API responds
    Then the loading spinner should disappear
    And the main content should be displayed

  Scenario: Error state with retry button
    Given I am logged in as "user@example.com"
    And the API server is unavailable
    When I click on the "Konto" tab
    Then I should see "Failed to load account information"
    And I should see a "Retry" button
    When I click the "Retry" button
    Then the profile API should be called again

  # ============================================================================
  # Localization (i18n)
  # ============================================================================

  Scenario Outline: All text translated for <language>
    Given the interface language is set to "<language>"
    And I am on the "Konto" tab
    Then all section headings should be in "<language>"
    And all field labels should be in "<language>"
    And all button text should be in "<language>"
    And the success/error messages should be in "<language>"

    Examples:
      | language |
      | English  |
      | Deutsch  |
      | Español  |
      | Français |

  Scenario: Language switcher updates Konto tab
    Given I am on the "Konto" tab
    And the interface language is "Deutsch"
    When I switch the language to "English"
    Then all text on the Konto tab should update to English
    And the PDF Type label should say "PDF Type"
    And the "Save Preferences" button should say "Save Preferences"

  # ============================================================================
  # Responsive Design
  # ============================================================================

  Scenario: Desktop layout (>800px)
    Given I am on the "Konto" tab
    And my viewport width is 1920 pixels
    Then the account cards should be displayed in a 2-column grid
    And all content should be visible without horizontal scrolling

  Scenario: Tablet layout (600-800px)
    Given I am on the "Konto" tab
    And my viewport width is 768 pixels
    Then the account cards should be displayed in a 2-column grid
    And the spacing should be adjusted for smaller screens

  Scenario: Mobile layout (<600px)
    Given I am on the "Konto" tab
    And my viewport width is 375 pixels
    Then the account cards should be stacked in a single column
    And all cards should be scrollable if content overflows

  # ============================================================================
  # Dark Mode Support
  # ============================================================================

  Scenario: Dark mode styling applied
    Given the system color scheme is set to "dark"
    When I click on the "Konto" tab
    Then all cards should have dark background colors
    And all text should have light colors for readability
    And the danger zone should have appropriate dark mode colors

  # ============================================================================
  # Security
  # ============================================================================

  Scenario: Cannot access other user's data
    Given I am logged in as "user1@example.com"
    And another user "user2@example.com" exists
    When I try to access user2's profile via API
    Then I should receive a 403 Forbidden error
    And I should only see my own data on the Konto tab

  Scenario: Bearer token required for authenticated endpoints
    Given authentication is enabled
    And I am not logged in
    When I try to access the profile API endpoint
    Then I should receive a 401 Unauthorized error

  Scenario: Job stats filtered by user_id
    Given I am logged in as "user1@example.com"
    And user2 has 10 jobs in the database
    And I have 3 jobs in the database
    When I click on the "Konto" tab
    Then I should only see statistics for my 3 jobs
    And user2's jobs should not be included in my statistics

  # ============================================================================
  # Edge Cases
  # ============================================================================

  Scenario: Handle missing profile picture gracefully
    Given I am logged in as "user@example.com"
    And my profile has no picture
    When I click on the "Konto" tab
    Then the profile picture element should be hidden
    And the profile section should still display correctly

  Scenario: Handle very long email addresses
    Given I am logged in as "verylongemailaddressfortesting@subdomain.example.com"
    When I click on the "Konto" tab
    Then the email should be displayed with word-break
    And the email should not overflow the container

  Scenario: Handle large activity log
    Given I am logged in as "user@example.com"
    And I have 100 recent audit events
    When I click on the "Konto" tab
    Then only the 20 most recent events should be displayed
    And the activity log should be scrollable

  Scenario: Concurrent tab switches
    Given I am logged in as "user@example.com"
    When I rapidly click between "Konverter" and "Konto" tabs
    Then only one API request should be in flight at a time
    And the cache should prevent duplicate API calls

  # ============================================================================
  # Integration with Converter
  # ============================================================================

  Scenario: Preferences applied when opening converter
    Given I am logged in as "user@example.com"
    And I have preferences with PDF Type "Standard PDF"
    And I am on the "Konto" tab
    When I save my preferences
    And I click on the "Konverter" tab
    Then the converter form should have PDF Type "Standard PDF" preselected

  Scenario: Preferences persist across sessions
    Given I am logged in as "user@example.com"
    And I am on the "Konto" tab
    When I set PDF Type to "PDF/A-1"
    And I save my preferences
    And I log out
    And I log in again
    And I click on the "Konto" tab
    Then the PDF Type should still be "PDF/A-1"
