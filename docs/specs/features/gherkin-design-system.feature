# language: en
Feature: CSS Design System
  As a developer maintaining the PDF/A Converter
  I want a consolidated CSS design system with consistent variables
  So that styling is maintainable, consistent, and accessible

  Background:
    Given the PDF/A Converter application is running

  # ============================================================================
  # Scenarios: CSS Custom Properties - Spacing
  # ============================================================================

  @design-system @css-variables @spacing
  Scenario: Spacing scale CSS variables are defined
    When I load the application stylesheet
    Then the following spacing variables should be defined in :root:
      | Variable      | Expected Value |
      | --space-xs    | 4px            |
      | --space-sm    | 8px            |
      | --space-md    | 16px           |
      | --space-lg    | 24px           |
      | --space-xl    | 32px           |
      | --space-2xl   | 48px           |

  # ============================================================================
  # Scenarios: CSS Custom Properties - Colors
  # ============================================================================

  @design-system @css-variables @colors
  Scenario: Primary color variables are defined
    When I load the application stylesheet
    Then the following color variables should be defined in :root:
      | Variable             | Expected Value |
      | --color-primary      | #667eea        |
      | --color-primary-dark | #764ba2        |
      | --color-text         | #333           |
      | --color-border       | #ddd           |
      | --color-bg           | #fff           |

  @design-system @css-variables @semantic-colors
  Scenario: Semantic status color variables are defined
    When I load the application stylesheet
    Then the following semantic color variables should be defined in :root:
      | Variable        | Expected Value |
      | --color-success | #10b981        |
      | --color-danger  | #dc2626        |
      | --color-warning | #f59e0b        |
      | --color-info    | #3b82f6        |

  @design-system @css-variables @legacy
  Scenario: Legacy color aliases are defined for backward compatibility
    When I load the application stylesheet
    Then the following legacy alias variables should be defined in :root:
      | Variable         |
      | --primary-color  |
      | --border-color   |
      | --card-bg        |
      | --text-color     |

  # ============================================================================
  # Scenarios: CSS Custom Properties - Typography
  # ============================================================================

  @design-system @css-variables @typography
  Scenario: Typography scale CSS variables are defined
    When I load the application stylesheet
    Then the following typography variables should be defined in :root:
      | Variable          | Expected Value |
      | --font-size-xs    | 0.75rem        |
      | --font-size-sm    | 0.875rem       |
      | --font-size-base  | 1rem           |
      | --font-size-lg    | 1.125rem       |
      | --font-size-xl    | 1.25rem        |
      | --font-size-2xl   | 1.5rem         |

  # ============================================================================
  # Scenarios: CSS Custom Properties - Border Radius
  # ============================================================================

  @design-system @css-variables @radius
  Scenario: Border radius scale CSS variables are defined
    When I load the application stylesheet
    Then the following radius variables should be defined in :root:
      | Variable       | Expected Value |
      | --radius-sm    | 4px            |
      | --radius-md    | 6px            |
      | --radius-lg    | 8px            |
      | --radius-xl    | 12px           |
      | --radius-full  | 9999px         |

  # ============================================================================
  # Scenarios: CSS Custom Properties - Shadows
  # ============================================================================

  @design-system @css-variables @shadows
  Scenario: Shadow scale CSS variables are defined
    When I load the application stylesheet
    Then the following shadow variables should be defined in :root:
      | Variable     |
      | --shadow-sm  |
      | --shadow-md  |
      | --shadow-lg  |
      | --shadow-xl  |

  # ============================================================================
  # Scenarios: Color Consistency
  # ============================================================================

  @design-system @color-consistency
  Scenario: Primary color is applied to convert button
    When I navigate to the converter tab
    Then the convert button should use the primary color gradient
    And the gradient should include colors from --color-primary

  @design-system @color-consistency
  Scenario: Primary color is applied to active tab
    When I navigate to the application
    Then the active tab button should use --color-primary for its border
    And the active tab text should use --color-primary

  @design-system @color-consistency
  Scenario: Focus outlines use primary color
    When I focus on a tab button using keyboard navigation
    Then the focus outline should use --color-primary
    And the outline should be clearly visible

  # ============================================================================
  # Scenarios: Animation Consolidation
  # ============================================================================

  @design-system @animations
  Scenario: Spin animation is defined once
    When I load the application stylesheet
    Then the @keyframes spin animation should be defined
    And it should only be defined once across all stylesheets

  @design-system @animations
  Scenario: FadeIn animation is defined once
    When I load the application stylesheet
    Then the @keyframes fadeIn animation should be defined
    And it should only be defined once across all stylesheets

  @design-system @animations
  Scenario: Pulse animation is defined once
    When I load the application stylesheet
    Then the @keyframes pulse animation should be defined
    And it should only be defined once across all stylesheets

  # ============================================================================
  # Scenarios: Responsive Design
  # ============================================================================

  @design-system @responsive @desktop
  Scenario: Desktop layout has correct container width
    Given my viewport is 1024x768 pixels
    When I navigate to the application
    Then the main container should have max-width of 800px
    And the container should be horizontally centered

  @design-system @responsive @tablet
  Scenario: Tablet layout adapts appropriately
    Given my viewport is 768x1024 pixels
    When I navigate to the application
    Then the layout should adapt for tablet viewing
    And all content should remain accessible

  @design-system @responsive @mobile
  Scenario: Mobile layout uses full width
    Given my viewport is 375x667 pixels
    When I navigate to the application
    Then the container should have reduced padding
    And form elements should stack vertically

  @design-system @responsive @landscape
  Scenario: Landscape orientation is supported
    Given my viewport is 667x375 pixels (landscape mobile)
    When I navigate to the application
    Then the layout should adapt for landscape viewing
    And the header should have reduced vertical spacing

  @design-system @responsive @mobile
  Scenario: Tab navigation is scrollable on narrow viewports
    Given my viewport is 320x568 pixels
    When I navigate to the application
    Then the tab navigation should be horizontally scrollable
    And all tab buttons should be accessible

  # ============================================================================
  # Scenarios: Touch Targets
  # ============================================================================

  @design-system @accessibility @touch
  Scenario: Buttons have minimum 44px touch target
    Given I am using a touch device
    When I view the application
    Then all interactive buttons should have at least 44px height
    And touch targets should not overlap

  @design-system @accessibility @touch
  Scenario: Tab buttons have adequate touch size
    Given I am using a touch device
    When I view the tab navigation
    Then tab buttons should have at least 40px height
    And there should be adequate spacing between tabs

  # ============================================================================
  # Scenarios: Logo Accessibility
  # ============================================================================

  @design-system @accessibility @logo
  Scenario: Header logo has concise alt text
    When I navigate to the application
    Then the header logo should have alt text "PDF/A"
    And the alt text should not duplicate the title text

  @design-system @accessibility @logo
  Scenario: Header logo has explicit dimensions
    When I navigate to the application
    Then the header logo should have width="40" attribute
    And the header logo should have height="40" attribute

  # ============================================================================
  # Scenarios: Progressive Disclosure
  # ============================================================================

  @design-system @progressive-disclosure
  Scenario: Advanced options are collapsed by default
    When I navigate to the converter tab
    Then the advanced options section should be collapsed
    And I should see a summary element with expand indicator

  @design-system @progressive-disclosure
  Scenario: Advanced options can be expanded
    Given I am on the converter tab
    When I click on the advanced options summary
    Then the advanced options section should expand
    And I should see the OCR language selector
    And I should see the PDF/A level selector

  @design-system @progressive-disclosure
  Scenario: Details summary has visual indicator
    When I navigate to the converter tab
    Then the advanced options summary should have cursor: pointer
    And there should be a visual expand/collapse indicator

  # ============================================================================
  # Scenarios: Dark Mode Support
  # ============================================================================

  @design-system @dark-mode @future
  Scenario: Dark mode media query is defined
    When I load the application stylesheet
    Then a prefers-color-scheme: dark media query should be defined
    And dark mode color variables should be prepared

  # ============================================================================
  # Scenarios: Reduced Motion
  # ============================================================================

  @design-system @accessibility @reduced-motion
  Scenario: Reduced motion preference is respected
    When I load the application stylesheet
    Then a prefers-reduced-motion media query should be defined
    And animations should be disabled when reduced motion is preferred

  # ============================================================================
  # Scenarios: No Duplicate CSS
  # ============================================================================

  @design-system @code-quality
  Scenario: No duplicate slider definitions exist
    When I load the application stylesheet
    Then the .slider class should be defined only once
    And all sliders should use --color-primary for the thumb

  @design-system @code-quality
  Scenario: No duplicate button-group definitions exist
    When I load the application stylesheet
    Then the .button-group class should be defined only once
    And it should use --space-sm for gap

  @design-system @code-quality
  Scenario: Empty CSS files are removed
    When I check the CSS directory
    Then converter.css should not exist
    And all CSS files should contain actual style rules
