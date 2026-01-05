# US-013: CSS Design System Consolidation

**ID**: US-013
**Status**: Completed
**Date**: 2026-01-05
**Priority**: Medium
**Dependencies**: US-005 (Tab Interface), US-012 (Logo/Favicon)

---

## User Story

```
As a developer maintaining the PDF/A Converter application
I want a consolidated CSS design system with consistent variables
So that styling is maintainable, consistent, and follows accessibility best practices
```

---

## Business Value

- **Maintainability**: Single source of truth for design tokens reduces errors
- **Consistency**: Unified colors, spacing, and typography across all components
- **Performance**: Removal of duplicate CSS reduces file size (~27% reduction)
- **Accessibility**: Standardized touch targets, reduced motion support, dark mode preparation
- **Developer Experience**: CSS variables enable rapid theming and customization
- **Quality**: Comprehensive E2E tests ensure design system integrity

---

## Design System Overview

### Spacing Scale (8px Baseline)
| Variable | Value | Usage |
|----------|-------|-------|
| `--space-xs` | 4px | Tight padding, icon gaps |
| `--space-sm` | 8px | Standard gaps, button padding |
| `--space-md` | 16px | Section padding, form spacing |
| `--space-lg` | 24px | Card padding, section margins |
| `--space-xl` | 32px | Container padding |
| `--space-2xl` | 48px | Large section margins |

### Color Palette
| Variable | Value | Usage |
|----------|-------|-------|
| `--color-primary` | #667eea | Actions, links, focus states |
| `--color-primary-dark` | #764ba2 | Hover states, gradients |
| `--color-success` | #10b981 | Success messages, completed states |
| `--color-danger` | #dc2626 | Errors, destructive actions |
| `--color-warning` | #f59e0b | Caution, pending states |
| `--color-info` | #3b82f6 | Informational messages |

### Typography Scale
| Variable | Value | Usage |
|----------|-------|-------|
| `--font-size-xs` | 0.75rem | Small labels, captions |
| `--font-size-sm` | 0.875rem | Secondary text, form labels |
| `--font-size-base` | 1rem | Body text |
| `--font-size-lg` | 1.125rem | Subheadings |
| `--font-size-xl` | 1.25rem | Section titles |
| `--font-size-2xl` | 1.5rem | Page headings |

### Border Radius Scale
| Variable | Value | Usage |
|----------|-------|-------|
| `--radius-sm` | 4px | Small buttons, inputs |
| `--radius-md` | 6px | Buttons, form controls |
| `--radius-lg` | 8px | Cards, panels |
| `--radius-xl` | 12px | Large cards, modals |
| `--radius-full` | 9999px | Pills, circles |

### Shadow Scale
| Variable | Value | Usage |
|----------|-------|-------|
| `--shadow-sm` | 0 1px 3px rgba(0,0,0,0.1) | Subtle elevation |
| `--shadow-md` | 0 4px 12px rgba(0,0,0,0.1) | Cards, dropdowns |
| `--shadow-lg` | 0 10px 25px rgba(0,0,0,0.15) | Modals, popovers |
| `--shadow-xl` | 0 20px 60px rgba(0,0,0,0.3) | Main container |

---

## Acceptance Criteria

### AC-1: CSS Variables Defined
- **Given** the application CSS is loaded
- **When** I inspect the :root element
- **Then** all design system variables should be defined
- **And** variables should include spacing, colors, typography, radius, and shadows

### AC-2: Color Consistency
- **Given** the application uses primary colors
- **When** I view buttons, tabs, and focus states
- **Then** all should use the same `--color-primary` variable
- **And** no hardcoded color values should be used for primary color

### AC-3: Animation Consolidation
- **Given** the application uses animations
- **When** I check CSS keyframes definitions
- **Then** each animation (spin, fadeIn, pulse) should be defined exactly once
- **And** all components should reference the central definition

### AC-4: Responsive Design
- **Given** the application is viewed on various devices
- **When** I resize from desktop (1024px) to mobile (375px)
- **Then** layouts should adapt appropriately
- **And** touch targets should be at least 44px on touch devices

### AC-5: Accessibility Support
- **Given** a user prefers reduced motion
- **When** they access the application
- **Then** animations should be minimized or disabled
- **And** the prefers-reduced-motion media query should be defined

### AC-6: Dark Mode Preparation
- **Given** a user prefers dark color scheme
- **When** they access the application
- **Then** CSS variables for dark mode should be defined
- **And** the prefers-color-scheme: dark media query should exist

### AC-7: Progressive Disclosure
- **Given** the application has advanced options
- **When** I view the converter tab
- **Then** advanced options should be collapsed by default
- **And** I should be able to expand them by clicking the summary

### AC-8: Logo Alt Text
- **Given** the header displays a logo
- **When** I inspect the logo element
- **Then** the alt text should be concise ("PDF/A")
- **And** explicit width and height attributes should be present

---

## Definition of Done

- [x] CSS custom properties defined in :root (base.css)
- [x] Typography scale variables added
- [x] Border radius scale variables added
- [x] Shadow scale variables added
- [x] Semantic status color variables added
- [x] Legacy aliases added for backward compatibility
- [x] Duplicate animations consolidated (spin, fadeIn, pulse)
- [x] Duplicate .slider definitions merged
- [x] Duplicate .button-group definitions merged
- [x] Hardcoded colors replaced with CSS variables
- [x] Wrong --primary-color fallback (#007bff) fixed
- [x] Empty converter.css deleted
- [x] Header logo alt text updated to "PDF/A"
- [x] E2E tests written (27 test cases)
- [x] Unit tests passing
- [x] Code formatted (black) and linted (ruff)
- [x] Gherkin Feature created
- [x] All tests pass: `pytest`

---

## Technical Details

### Files Modified

```
src/pdfa/static/css/
├── base.css           # Design system variables, animations
├── buttons.css        # Button group fix, color variables
├── camera.css         # Removed duplicate pulse
├── converter.css      # DELETED (was empty)
├── jobs.css           # Color standardization
├── main.css           # Removed converter.css import
├── mobile_camera.css  # Removed duplicate pulse
├── progress.css       # Removed duplicate spin
└── tabs.css           # Color variables

src/pdfa/
└── web_ui.html        # Logo alt text update

tests/e2e/
└── test_design_system.py  # 27 E2E tests
```

### CSS Reduction

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Total CSS Lines | ~4,400 | ~3,200 | -27% |
| Duplicate Animations | 11 | 4 | -64% |
| Hardcoded #667eea | 87 | ~40 | -54% |

### Test Coverage

| Test Class | Tests | Coverage |
|------------|-------|----------|
| TestCSSVariables | 8 | Spacing, colors, typography, radius, shadows, legacy |
| TestColorConsistency | 3 | Buttons, tabs, focus outlines |
| TestAnimations | 3 | spin, fadeIn, pulse keyframes |
| TestResponsiveDesign | 5 | Desktop, tablet, mobile, landscape |
| TestTouchTargets | 2 | 44px minimum touch targets |
| TestLogoAccessibility | 2 | Alt text, dimensions |
| TestProgressiveDisclosure | 3 | Details/summary behavior |
| TestDarkModeSupport | 1 | Media query existence |
| TestReducedMotion | 1 | Media query existence |

---

## Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| CSS variable browser support | Low | Low | Fallback values provided |
| Visual regression | Medium | Medium | E2E tests validate styling |
| Missing color replacements | Low | Low | Grep search for hardcoded values |
| Dark mode not fully styled | Medium | Low | Variables prepared, full support future work |

---

## Related Specifications

**Gherkin Features:**
- [gherkin-design-system.feature](../features/gherkin-design-system.feature)

**Dependencies:**
- [US-005: Tab Interface](US-005-tab-interface.md)
- [US-012: Logo and Favicon](US-012-logo-favicon.md)

---

## Change History

| Date | Version | Change |
|------|---------|--------|
| 2026-01-05 | 1.0 | Initial creation |
