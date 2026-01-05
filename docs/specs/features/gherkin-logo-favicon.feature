# language: en
Feature: Logo and Favicon Integration
  As a user of the PDF/A Converter
  I want to see professional branding with a custom logo and favicon
  So that the application appears polished and trustworthy

  Background:
    Given the PDF/A Converter application is running

  # ============================================================================
  # Scenarios: Favicon
  # ============================================================================

  @favicon @visual
  Scenario: Browser tab displays custom favicon
    When I navigate to the application
    Then the browser tab should display the custom favicon
    And the favicon should not be the default browser icon

  @favicon @technical
  Scenario: Favicon files are available in multiple formats
    When I check the application head element
    Then I should find a link to "/static/images/favicon.svg" with type "image/svg+xml"
    And I should find a link to "/static/images/favicon-32x32.png" for high-DPI displays
    And I should find a link to "/static/images/favicon-16x16.png" for standard displays

  @favicon @mobile
  Scenario: Apple touch icon is available for iOS
    When I check the application head element
    Then I should find an apple-touch-icon link to "/static/images/apple-touch-icon.png"
    And the icon should be 180x180 pixels

  @favicon @accessibility
  Scenario: All favicon files are accessible via HTTP
    When I request the following favicon files:
      | File Path                          |
      | /static/images/favicon.svg         |
      | /static/images/favicon-16x16.png   |
      | /static/images/favicon-32x32.png   |
      | /static/images/apple-touch-icon.png|
    Then each request should return HTTP status 200
    And each file should have the appropriate content type

  # ============================================================================
  # Scenarios: Welcome Screen Logo
  # ============================================================================

  @logo @welcome
  Scenario: Welcome screen displays custom logo
    Given I am on the welcome screen
    When I view the welcome section
    Then I should see the Digital Fossil logo instead of the emoji icon
    And the logo should be centered above the title
    And the logo should have a drop shadow effect

  @logo @welcome @accessibility
  Scenario: Welcome logo is decorative and hidden from screen readers
    Given I am on the welcome screen
    When I inspect the welcome logo element
    Then the welcome logo should have aria-hidden="true"
    And the logo should have an empty alt text

  @logo @welcome @visual
  Scenario: Welcome logo uses correct source file
    Given I am on the welcome screen
    When I inspect the welcome logo element
    Then the logo src attribute should be "/static/images/logo.svg"

  # ============================================================================
  # Scenarios: Header Logo
  # ============================================================================

  @logo @header
  Scenario: Header displays logo alongside title
    Given I am viewing the main application
    When I look at the page header
    Then the header should display the logo to the left of the title
    And the logo should be approximately 40x40 pixels
    And the title text "PDF/A Converter" should be visible

  @logo @header @accessibility
  Scenario: Header logo has appropriate alt text
    Given I am viewing the main application
    When I inspect the header logo element
    Then the logo should have alt text "PDF/A Converter"

  @logo @header @visual
  Scenario: Header logo uses correct source file
    Given I am viewing the main application
    When I inspect the header logo element
    Then the logo src attribute should be "/static/images/logo.svg"

  # ============================================================================
  # Scenarios: Mobile Camera Page
  # ============================================================================

  @logo @mobile
  Scenario: Mobile camera page displays favicon
    When I navigate to the mobile camera page at "/mobile/camera"
    Then the page should have favicon link elements
    And the favicon should reference "/static/images/favicon.svg"

  @logo @mobile
  Scenario: Mobile camera page displays logo in header
    When I navigate to the mobile camera page at "/mobile/camera"
    Then the page header should display the logo
    And the logo should be smaller than the desktop version

  # ============================================================================
  # Scenarios: Responsive Design
  # ============================================================================

  @logo @responsive
  Scenario: Logo scales appropriately on mobile viewport
    Given I am using a mobile device with viewport width 375px
    When I view the welcome screen
    Then the welcome logo should be smaller than on desktop
    And the logo should remain visually clear and not pixelated

  @logo @responsive
  Scenario: Logo maintains aspect ratio on tablet viewport
    Given I am using a tablet device with viewport width 768px
    When I view the application
    Then the logo should maintain its square aspect ratio
    And the logo should not appear stretched or distorted

  @logo @responsive
  Scenario: Logo maintains aspect ratio on desktop viewport
    Given I am using a desktop device with viewport width 1920px
    When I view the application
    Then the logo should maintain its square aspect ratio
    And the logo should display at full size

  # ============================================================================
  # Scenarios: Visual Design
  # ============================================================================

  @logo @visual @design
  Scenario: Logo SVG uses project color palette
    When I inspect the logo SVG source at "/static/images/logo.svg"
    Then the logo should contain the purple color "#667eea"
    And the logo should contain amber/gold accent colors

  @logo @visual @animation
  Scenario: Welcome logo has hover animation
    Given I am on the welcome screen
    And reduced motion preference is not enabled
    When I hover over the welcome logo
    Then the logo should slightly scale up
    And the logo shadow should become more prominent

  @logo @visual @reduced-motion
  Scenario: Logo respects reduced motion preference
    Given I am on the welcome screen
    And my system has "prefers-reduced-motion: reduce" enabled
    When I hover over the welcome logo
    Then no animation should occur
    And the logo should remain static

  # ============================================================================
  # Scenarios: Error Handling
  # ============================================================================

  @logo @error
  Scenario: Application remains functional if logo fails to load
    Given the logo file is temporarily unavailable
    When I navigate to the application
    Then the application should not crash
    And the header title "PDF/A Converter" should still be visible
    And all application functionality should remain accessible
