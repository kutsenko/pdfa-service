# Authentication-Based Page Visibility

## User Story

**As a** user of the PDF/A Converter application
**I want** to see only the pages and features appropriate to my authentication status
**So that** I can access the application securely while maintaining a seamless experience when authentication is not required

### Acceptance Criteria

1. When authentication is **disabled**, I am automatically logged in as the default local user and can access all features
2. When authentication is **enabled** and I am **not logged in**, I only see the welcome page with login option
3. When authentication is **enabled** and I am **logged in**, I can access all application features
4. When I **log out**, I am returned to the welcome page and cannot access protected features

---

## Gherkin Specification

```gherkin
Feature: Authentication-Based Page Visibility
  As a user of the PDF/A Converter
  I want to see appropriate pages based on my authentication status
  So that the application is secure yet accessible

  Background:
    Given the PDF/A Converter application is running

  # ============================================================================
  # Scenario: Authentication Disabled
  # ============================================================================

  @auth-disabled
  Scenario: User sees all features when authentication is disabled
    Given authentication is disabled in the application configuration
    When I navigate to the application
    Then I should be automatically logged in as the default local user
    And I should see the main navigation with all tabs
    And the following tabs should be visible:
      | Tab Name    |
      | Convert     |
      | Camera      |
      | History     |
      | Account     |
    And I should not see a login button
    And I should not see a logout button

  @auth-disabled
  Scenario: Default user information is displayed when auth is disabled
    Given authentication is disabled in the application configuration
    When I navigate to the application
    Then the user display name should be "Local User"
    And the user email should be "local@localhost"

  # ============================================================================
  # Scenario: Authentication Enabled - Not Logged In
  # ============================================================================

  @auth-enabled @not-logged-in
  Scenario: Unauthenticated user sees only the welcome page
    Given authentication is enabled in the application configuration
    And I am not logged in
    When I navigate to the application
    Then I should see the welcome page
    And I should see a login button
    And I should not see the main navigation tabs
    And the following tabs should not be visible:
      | Tab Name    |
      | Convert     |
      | Camera      |
      | History     |
      | Account     |

  @auth-enabled @not-logged-in
  Scenario: Unauthenticated user cannot access protected routes directly
    Given authentication is enabled in the application configuration
    And I am not logged in
    When I try to access the "/convert" route directly
    Then I should be redirected to the welcome page
    And I should see a login button

  @auth-enabled @not-logged-in
  Scenario: Login button initiates OAuth flow
    Given authentication is enabled in the application configuration
    And I am not logged in
    And I am on the welcome page
    When I click the login button
    Then I should be redirected to the Google OAuth login page

  # ============================================================================
  # Scenario: Authentication Enabled - Logged In
  # ============================================================================

  @auth-enabled @logged-in
  Scenario: Authenticated user sees all features
    Given authentication is enabled in the application configuration
    And I am logged in as "test@example.com"
    When I navigate to the application
    Then I should see the main navigation with all tabs
    And the following tabs should be visible:
      | Tab Name    |
      | Convert     |
      | Camera      |
      | History     |
      | Account     |
    And I should see a logout button
    And I should not see a login button

  @auth-enabled @logged-in
  Scenario: User information is displayed when logged in
    Given authentication is enabled in the application configuration
    And I am logged in with the following details:
      | Field   | Value              |
      | email   | test@example.com   |
      | name    | Test User          |
      | picture | https://example.com/photo.jpg |
    When I navigate to the Account tab
    Then I should see my email "test@example.com"
    And I should see my name "Test User"
    And I should see my profile picture

  @auth-enabled @logged-in
  Scenario: Authenticated user can access all protected routes
    Given authentication is enabled in the application configuration
    And I am logged in as "test@example.com"
    When I navigate to each of the following routes:
      | Route     |
      | /         |
      | /convert  |
      | /camera   |
      | /history  |
      | /account  |
    Then each route should load successfully
    And I should not be redirected to the welcome page

  # ============================================================================
  # Scenario: Logout Flow
  # ============================================================================

  @auth-enabled @logout
  Scenario: User is redirected to welcome page after logout
    Given authentication is enabled in the application configuration
    And I am logged in as "test@example.com"
    And I am on the Convert tab
    When I click the logout button
    Then I should be redirected to the welcome page
    And I should see a login button
    And I should not see the main navigation tabs

  @auth-enabled @logout
  Scenario: Session is cleared after logout
    Given authentication is enabled in the application configuration
    And I am logged in as "test@example.com"
    When I click the logout button
    Then my authentication token should be removed from storage
    And subsequent API requests should return 401 Unauthorized

  @auth-enabled @logout
  Scenario: User cannot access protected routes after logout
    Given authentication is enabled in the application configuration
    And I am logged in as "test@example.com"
    When I click the logout button
    And I try to access the "/convert" route directly
    Then I should be redirected to the welcome page

  # ============================================================================
  # Scenario: API Behavior
  # ============================================================================

  @api @auth-disabled
  Scenario: API returns 404 for /auth/user when auth is disabled
    Given authentication is disabled in the application configuration
    When I make a GET request to "/auth/user"
    Then the response status should be 404
    And the response should contain "Authentication is disabled"

  @api @auth-enabled @not-logged-in
  Scenario: API returns 401 for /auth/user when not authenticated
    Given authentication is enabled in the application configuration
    And I do not include an authorization token
    When I make a GET request to "/auth/user"
    Then the response status should be 401
    And the response should contain "Not authenticated"

  @api @auth-enabled @logged-in
  Scenario: API returns user info for /auth/user when authenticated
    Given authentication is enabled in the application configuration
    And I include a valid authorization token for "test@example.com"
    When I make a GET request to "/auth/user"
    Then the response status should be 200
    And the response should contain the user's email
    And the response should contain the user's name

  # ============================================================================
  # Scenario: Session Persistence
  # ============================================================================

  @auth-enabled @session
  Scenario: User remains logged in after page refresh
    Given authentication is enabled in the application configuration
    And I am logged in as "test@example.com"
    When I refresh the page
    Then I should still be logged in
    And I should see the main navigation with all tabs

  @auth-enabled @session
  Scenario: User remains logged in when opening new tab
    Given authentication is enabled in the application configuration
    And I am logged in as "test@example.com"
    When I open the application in a new browser tab
    Then I should be logged in in the new tab
    And I should see the main navigation with all tabs

  # ============================================================================
  # Scenario: Mobile Camera Pairing (Anonymous Access)
  # ============================================================================

  @auth-enabled @mobile-pairing
  Scenario: Mobile camera page allows anonymous access via pairing code
    Given authentication is enabled in the application configuration
    And a valid pairing session exists with code "ABC123"
    When I navigate to "/mobile/camera?code=ABC123" without authentication
    Then I should see the mobile camera pairing page
    And I should be able to connect to the pairing session

  @auth-enabled @mobile-pairing
  Scenario: Mobile camera WebSocket allows anonymous pairing messages
    Given authentication is enabled in the application configuration
    And I have joined a pairing session
    When I send a "register_pairing" message via WebSocket without authentication
    Then the message should be accepted
    And I should receive a success response
```

---

## Technical Notes

### Frontend Detection Logic

The frontend (`AuthManager.js`) detects authentication status by calling `/auth/user`:

| Response Status | Meaning | Frontend Action |
|-----------------|---------|-----------------|
| 404 | Auth disabled | Show all UI, no login/logout buttons |
| 401 | Auth enabled, not logged in | Show welcome page with login button |
| 200 | Auth enabled, logged in | Show all UI with logout button |

### Backend Endpoints

| Endpoint | Auth Disabled | Auth Enabled (No Token) | Auth Enabled (Valid Token) |
|----------|---------------|-------------------------|----------------------------|
| `GET /auth/user` | 404 | 401 | 200 + user info |
| `GET /auth/status` | `{enabled: false}` | `{enabled: true}` | `{enabled: true}` |
| `POST /auth/logout` | 404 | 200 | 200 |

### Environment Variables

```bash
# Enable/disable authentication
PDFA_ENABLE_AUTH=true|false

# Default user when auth is disabled
DEFAULT_USER_ID=local-default
DEFAULT_USER_EMAIL=local@localhost
DEFAULT_USER_NAME=Local User
```
