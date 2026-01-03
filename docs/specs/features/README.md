# Gherkin Features

This directory contains **Gherkin Feature files** in BDD format (Behavior Driven Development) for major features of the PDF/A service.

---

## Overview

| Feature | Scenarios | File | User Story |
|---------|-----------|------|------------|
| MongoDB Integration | 36 | [gherkin-mongodb-integration.feature](gherkin-mongodb-integration.feature) | [US-001](../user-stories/US-001-mongodb-integration.md) |
| Job Event Logging | 21 | [gherkin-job-event-logging.feature](gherkin-job-event-logging.feature) | [US-002](../user-stories/US-002-job-event-logging.md) |
| Local Default User | 18 | [gherkin-local-default-user.feature](gherkin-local-default-user.feature) | [US-003](../user-stories/US-003-local-default-user.md) |
| Live Job Events | ~20 | [gherkin-live-job-events.feature](gherkin-live-job-events.feature) | [US-004](../user-stories/US-004-live-job-events.md) |
| Tab Interface | ~25 | [gherkin-tab-interface.feature](gherkin-tab-interface.feature) | [US-005](../user-stories/US-005-tab-interface.md) |
| Account Tab | ~20 | [gherkin-account-tab.feature](gherkin-account-tab.feature) | [US-006](../user-stories/US-006-account-tab.md) |
| Jobs Tab | ~30 | [gherkin-jobs-tab.feature](gherkin-jobs-tab.feature) | [US-007](../user-stories/US-007-jobs-tab.md) |
| Camera Tab | 57 | [gherkin-camera-tab.feature](gherkin-camera-tab.feature) | [US-008](../user-stories/US-008-camera-tab.md) |
| Accessibility Camera | 65 | [gherkin-accessibility-camera-assistance.feature](gherkin-accessibility-camera-assistance.feature) | [US-009](../user-stories/US-009-accessibility-camera-assistance.md) |
| Mobile-Desktop Pairing | ~15 | [gherkin-mobile-desktop-pairing.feature](gherkin-mobile-desktop-pairing.feature) | [US-010](../user-stories/US-010-mobile-desktop-pairing.md) |
| Auth Page Visibility | 18 | [gherkin-auth-page-visibility.feature](gherkin-auth-page-visibility.feature) | [US-011](../user-stories/US-011-auth-page-visibility.md) |

**Total**: ~325 scenarios in 11 features

---

## Gherkin Format

All features follow the **Gherkin** standard with English keywords.

### Structure

```gherkin
Feature: [Feature Name]
  As [role]
  I want [goal]
  So that [benefit]

  Background:
    Given [common context for all scenarios]

  Scenario: [Description]
    Given [precondition]
    When [action]
    Then [expected result]
    And [further expectation]
```

### Keywords

| Keyword | Usage |
|---------|-------|
| Feature | Feature description |
| Background | Common preconditions |
| Scenario | Single test case |
| Given | Precondition/Context |
| When | Action/Event |
| Then | Expected result |
| And | Additional steps |
| But | Negative expectation |

---

## Features

### [gherkin-mongodb-integration.feature](gherkin-mongodb-integration.feature)

**Feature**: Persistent data storage with MongoDB

**Scenario Groups** (36 scenarios):
1. Service start and MongoDB connection (3)
2. Job persistence (6)
3. OAuth State Token Management (4)
4. User profiles (3)
5. Audit logs (5)
6. Indexes and performance (3)
7. Repository pattern (4)
8. Error handling (3)
9. Backward compatibility (2)
10. Multi-instance deployment (3)

---

### [gherkin-job-event-logging.feature](gherkin-job-event-logging.feature)

**Feature**: Detailed event logging for conversion jobs

**Scenario Groups** (21 scenarios):
1. OCR decision (3)
2. Format conversion (3)
3. Fallback mechanisms (3)
4. Pass-through mode (2)
5. Compression profile selection (2)
6. Job lifecycle events (2)
7. Backward compatibility (2)
8. Complete job lifecycle examples (2)
9. Error handling (2)

---

### [gherkin-local-default-user.feature](gherkin-local-default-user.feature)

**Feature**: Local default user for non-auth mode

**Scenario Groups** (18 scenarios):
1. Service start and default user creation (3)
2. Configurable default user fields (2)
3. Job attribution with default user (3)
4. Job history queries (3)
5. Dependency injection (3)
6. Edge cases and error handling (4)

---

### [gherkin-camera-tab.feature](gherkin-camera-tab.feature)

**Feature**: Camera Tab for Multi-Page Document Capture

**Scenario Groups** (57 scenarios):
1. Camera access and preview (7)
2. Photo capture (6)
3. Photo editor (10)
4. Multi-page support (8)
5. Page management (6)
6. Document submission (8)
7. Accessibility integration (6)
8. Camera settings (3)
9. Error handling (4)
10. Responsive design (6)

---

### [gherkin-accessibility-camera-assistance.feature](gherkin-accessibility-camera-assistance.feature)

**Feature**: Accessibility Camera Assistance for Blind Users

**Scenario Groups** (65 scenarios):
1. Screen reader auto-detection (3)
2. iOS Safari audio/TTS unlock (4)
3. Page reload AudioContext handling (2)
4. Edge detection with jscanify (4)
5. Confidence calculation (5)
6. Hysteresis (3)
7. Audio feedback (5)
8. Edge-based guidance (4)
9. Auto-capture (5)
10. Auto-crop and perspective correction (7)
11. Multilingualism (4)
12. Visual indicators (2)
13. ARIA live regions (1)
14. Volume control (1)
15. Test audio button (1)
16. Disable feature (2)
17. Error handling (3)
18. Performance & memory (4)

---

### [gherkin-auth-page-visibility.feature](gherkin-auth-page-visibility.feature)

**Feature**: Authentication-Based Page Visibility

**Scenario Groups** (18 scenarios):
1. Authentication disabled (2)
2. Authentication enabled - not logged in (3)
3. Authentication enabled - logged in (3)
4. Logout flow (3)
5. API behavior (3)
6. Session persistence (2)
7. Mobile camera pairing anonymous access (2)

---

## Usage

### For Testers

1. **Use scenarios as test cases**
   - Each scenario = 1 test case
   - Given-When-Then as test structure

2. **Run manual tests**
   - Follow the steps
   - Verify expected results

3. **Automate with BDD tools**
   ```bash
   # Example with behave (Python)
   behave features/gherkin-mongodb-integration.feature
   ```

### For Developers

1. **Understand requirements**
   - Scenarios show concrete examples
   - Tables define data structures

2. **Implement with TDD**
   - Write tests based on scenarios
   - RED-GREEN-REFACTOR

3. **Extend as needed**
   - Add new scenarios for edge cases
   - Document in Gherkin

### For Product Owners

1. **Validate scenarios**
   - Are all important cases covered?
   - Do expectations match?

2. **Accept based on scenarios**
   - All scenarios must be fulfilled
   - Definition of Done

---

## Best Practices

### Scenario Names

✅ **Good**: "OCR is skipped for tagged PDF"
❌ **Bad**: "Test 1"

### Given-When-Then

✅ **Good**:
```gherkin
Given a PDF file "document.pdf" is uploaded
When the conversion job is executed
Then an event with type "format_conversion" should exist
```

❌ **Bad**:
```gherkin
Given PDF
When job
Then event
```

### Tables for Data

✅ **Good**:
```gherkin
And the configuration is:
  | Parameter   | Value |
  | pdfa_level  | 2     |
  | ocr_enabled | true  |
```

❌ **Bad**:
```gherkin
And pdfa_level is 2 and ocr_enabled is true
```

---

## Automation

### With Behave (Python)

```bash
# Installation
pip install behave

# Run feature
behave features/gherkin-mongodb-integration.feature

# Run specific scenario
behave features/gherkin-mongodb-integration.feature:10
```

### With Cucumber (JavaScript)

```bash
# Installation
npm install @cucumber/cucumber

# Run features
npx cucumber-js features/
```

### With pytest-bdd (Python)

```bash
# Installation
pip install pytest-bdd

# Run features
pytest --bdd
```

---

## Related Documentation

- [Back to Overview](../README.md)
- [User Stories](../user-stories/)
- [AGENTS.md](../../../AGENTS.md)
- [Behave Documentation](https://behave.readthedocs.io/)
- [Cucumber Documentation](https://cucumber.io/docs/gherkin/)

---

## Change History

| Date | Version | Change |
|------|---------|--------|
| 2024-12-25 | 1.0 | Initial creation |
| 2026-01-03 | 2.0 | Unified structure, renamed German files, added auth-page-visibility |
