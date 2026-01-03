# Specifications

This directory contains formal User Stories and Gherkin Feature files for major features of the PDF/A service.

---

## Structure

```
docs/specs/
├── README.md                                    # This file
├── user-stories/                                # User Stories (INVEST)
│   ├── README.md                                # User Stories overview
│   ├── US-001-mongodb-integration.md            # MongoDB Integration
│   ├── US-002-job-event-logging.md              # Job Event Logging
│   ├── US-003-local-default-user.md             # Local Default User
│   ├── US-004-live-job-events.md                # Live Job Events Display
│   ├── US-005-tab-interface.md                  # Tab-Based Interface
│   ├── US-006-account-tab.md                    # Account Tab
│   ├── US-007-jobs-tab.md                       # Jobs History Tab
│   ├── US-008-camera-tab.md                     # Camera Tab
│   ├── US-009-accessibility-camera-assistance.md # Accessibility Camera
│   ├── US-010-mobile-desktop-pairing.md         # Mobile-Desktop Pairing
│   └── US-011-auth-page-visibility.md           # Auth-Based Page Visibility
└── features/                                    # Gherkin Features (BDD)
    ├── README.md                                # Gherkin Features overview
    ├── gherkin-mongodb-integration.feature      # MongoDB (36 scenarios)
    ├── gherkin-job-event-logging.feature        # Event Logging (21 scenarios)
    ├── gherkin-local-default-user.feature       # Local Default User (18 scenarios)
    ├── gherkin-live-job-events.feature          # Live Job Events
    ├── gherkin-tab-interface.feature            # Tab Interface
    ├── gherkin-account-tab.feature              # Account Tab
    ├── gherkin-jobs-tab.feature                 # Jobs Tab
    ├── gherkin-camera-tab.feature               # Camera Tab (57 scenarios)
    ├── gherkin-accessibility-camera-assistance.feature # Accessibility (65 scenarios)
    ├── gherkin-mobile-desktop-pairing.feature   # Mobile-Desktop Pairing
    └── gherkin-auth-page-visibility.feature     # Auth Page Visibility (18 scenarios)
```

---

## Overview

| ID | Title | Status | Date | User Story | Gherkin Feature |
|----|-------|--------|------|------------|-----------------|
| US-001 | MongoDB Integration | ✅ Implemented | 2024-12-21 | [User Story](user-stories/US-001-mongodb-integration.md) | [Feature](features/gherkin-mongodb-integration.feature) |
| US-002 | Job Event Logging | ✅ Implemented | 2024-12-25 | [User Story](user-stories/US-002-job-event-logging.md) | [Feature](features/gherkin-job-event-logging.feature) |
| US-003 | Local Default User | ✅ Implemented | 2024-12-25 | [User Story](user-stories/US-003-local-default-user.md) | [Feature](features/gherkin-local-default-user.feature) |
| US-004 | Live Job Events Display | ✅ Implemented | 2024-12-25 | [User Story](user-stories/US-004-live-job-events.md) | [Feature](features/gherkin-live-job-events.feature) |
| US-005 | Tab-Based Interface | 🚧 In Progress | 2024-12-26 | [User Story](user-stories/US-005-tab-interface.md) | [Feature](features/gherkin-tab-interface.feature) |
| US-006 | Account Tab | 🚧 In Progress | 2024-12-27 | [User Story](user-stories/US-006-account-tab.md) | [Feature](features/gherkin-account-tab.feature) |
| US-007 | Jobs History Tab | 🚧 In Progress | 2024-12-27 | [User Story](user-stories/US-007-jobs-tab.md) | [Feature](features/gherkin-jobs-tab.feature) |
| US-008 | Camera Tab | ✅ Implemented | 2025-12-30 | [User Story](user-stories/US-008-camera-tab.md) | [Feature](features/gherkin-camera-tab.feature) |
| US-009 | Accessibility Camera | ✅ Implemented | 2026-01-01 | [User Story](user-stories/US-009-accessibility-camera-assistance.md) | [Feature](features/gherkin-accessibility-camera-assistance.feature) |
| US-010 | Mobile-Desktop Pairing | ✅ Implemented | 2026-01-02 | [User Story](user-stories/US-010-mobile-desktop-pairing.md) | [Feature](features/gherkin-mobile-desktop-pairing.feature) |
| US-011 | Auth Page Visibility | ✅ Implemented | 2026-01-03 | [User Story](user-stories/US-011-auth-page-visibility.md) | [Feature](features/gherkin-auth-page-visibility.feature) |

---

## User Stories

📁 **Directory**: [`user-stories/`](user-stories/)

User Stories follow the **INVEST** principle and contain:
- Story in "As... I want... So that..." format
- Context and problem statement
- Acceptance criteria
- Definition of Done
- Technical details
- Risks & Mitigations

---

## Gherkin Features

📁 **Directory**: [`features/`](features/)

Gherkin features follow the **Given-When-Then** pattern and are written in English.

---

## Usage

### For Developers

1. **Read the User Story** to understand the "why"
   - 📄 Start in [`user-stories/`](user-stories/)
2. **Check acceptance criteria** for requirements
3. **Follow Gherkin scenarios** for concrete examples
   - 🧪 See [`features/`](features/)
4. **Implement with TDD** (RED-GREEN-REFACTOR)

### For Testers

1. **Use Gherkin scenarios** as test cases
   - 🧪 All features in [`features/`](features/)
2. **Verify all scenarios** against implementation
3. **Extend with new edge cases** as needed

### For Product Owners

1. **Validate acceptance criteria** in User Stories
   - 📄 See [`user-stories/`](user-stories/)
2. **Check Definition of Done**
3. **Accept or reject** based on fulfillment

---

## Standards

### User Story Format

```markdown
# User Story: [Title]

**ID**: US-XXX
**Title**: [Short description]
**Status**: [In Progress / Implemented / Rejected]
**Date**: YYYY-MM-DD

## Story
As [role]
I want [feature]
So that [benefit]

## Context
[Background and problem statement]

## Acceptance Criteria
[Given-When-Then criteria]

## Definition of Done
- [ ] Checklist

## Technical Details
[Implementation details]

## Related Specifications
**User Stories**: Links to related stories
**Gherkin Features**: Links to Gherkin features
```

### Gherkin Format

```gherkin
Feature: [Title]
  As [role]
  I want [goal]
  So that [benefit]

  Background:
    Given [context]

  Scenario: [Description]
    Given [precondition]
    When [action]
    Then [expected result]
```

---

## Statistics

**User Stories**: 11
**Gherkin Features**: 11
**Total Scenarios**: ~290

**Coverage**:
- ✅ All major features documented
- ✅ Backward compatibility considered
- ✅ Error handling specified
- ✅ Multi-instance scenarios (MongoDB)
- ✅ Accessibility features documented
- ✅ Mobile-desktop pairing documented
- ✅ Authentication flows documented

---

## Related Documentation

- [AGENTS.md](../../AGENTS.md) - Development guidelines
- [README.md](../../README.md) - User documentation (English)
- [README.de.md](../../README.de.md) - User documentation (German)

---

## Change History

| Date | Version | Change |
|------|---------|--------|
| 2024-12-25 | 1.0 | Initial creation with US-001 and US-002 |
| 2024-12-25 | 2.0 | Restructured: User Stories and Gherkin Features in separate directories |
| 2024-12-25 | 3.0 | US-003: Local Default User added |
| 2025-12-30 | 4.0 | US-004-US-007: UI features added |
| 2026-01-01 | 5.0 | US-008-US-009: Camera and Accessibility added |
| 2026-01-03 | 6.0 | Unified structure, renamed German files to English, added US-010-US-011 |
