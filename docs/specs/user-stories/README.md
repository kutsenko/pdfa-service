# User Stories

This directory contains formal User Stories in **INVEST** format for major features of the PDF/A service.

---

## Overview

| ID | Title | Status | Date | File | Gherkin Feature |
|----|-------|--------|------|------|-----------------|
| US-001 | MongoDB Integration | ✅ Implemented | 2024-12-21 | [US-001-mongodb-integration.md](US-001-mongodb-integration.md) | [Feature](../features/gherkin-mongodb-integration.feature) |
| US-002 | Job Event Logging | ✅ Implemented | 2024-12-25 | [US-002-job-event-logging.md](US-002-job-event-logging.md) | [Feature](../features/gherkin-job-event-logging.feature) |
| US-003 | Local Default User | ✅ Implemented | 2024-12-25 | [US-003-local-default-user.md](US-003-local-default-user.md) | [Feature](../features/gherkin-local-default-user.feature) |
| US-004 | Live Job Events Display | ✅ Implemented | 2024-12-25 | [US-004-live-job-events.md](US-004-live-job-events.md) | [Feature](../features/gherkin-live-job-events.feature) |
| US-005 | Tab-Based Interface | 🚧 In Progress | 2024-12-26 | [US-005-tab-interface.md](US-005-tab-interface.md) | [Feature](../features/gherkin-tab-interface.feature) |
| US-006 | Account Tab | 🚧 In Progress | 2024-12-27 | [US-006-account-tab.md](US-006-account-tab.md) | [Feature](../features/gherkin-account-tab.feature) |
| US-007 | Jobs History Tab | 🚧 In Progress | 2024-12-27 | [US-007-jobs-tab.md](US-007-jobs-tab.md) | [Feature](../features/gherkin-jobs-tab.feature) |
| US-008 | Camera Tab | ✅ Implemented | 2025-12-30 | [US-008-camera-tab.md](US-008-camera-tab.md) | [Feature](../features/gherkin-camera-tab.feature) |
| US-009 | Accessibility Camera | ✅ Implemented | 2026-01-01 | [US-009-accessibility-camera-assistance.md](US-009-accessibility-camera-assistance.md) | [Feature](../features/gherkin-accessibility-camera-assistance.feature) |
| US-010 | Mobile-Desktop Pairing | ✅ Implemented | 2026-01-02 | [US-010-mobile-desktop-pairing.md](US-010-mobile-desktop-pairing.md) | [Feature](../features/gherkin-mobile-desktop-pairing.feature) |
| US-011 | Auth Page Visibility | ✅ Implemented | 2026-01-03 | [US-011-auth-page-visibility.md](US-011-auth-page-visibility.md) | [Feature](../features/gherkin-auth-page-visibility.feature) |

---

## INVEST Principles

All User Stories follow the **INVEST** principle:

- **I**ndependent - Can be implemented independently
- **N**egotiable - Flexible with clear priorities
- **V**aluable - Clear business value
- **E**stimable - Time estimates possible
- **S**mall - Achievable in 3-5 days
- **T**estable - Testable with acceptance criteria

---

## User Story Structure

Each User Story contains:

### 1. Metadata
- **ID**: Unique identifier (US-XXX)
- **Title**: Short description
- **Status**: In Progress / Implemented / Rejected
- **Date**: Creation date

### 2. Story
```
As [role]
I want [feature]
So that [benefit]
```

### 3. Context
- Current state
- Problem statement
- Solution

### 4. Acceptance Criteria
Given-When-Then format:
```
Given [precondition]
When [action]
Then [expected result]
And [further expectations]
```

### 5. Definition of Done
Checklist with clear acceptance criteria:
- [ ] Tests pass
- [ ] Code formatted
- [ ] Documentation updated
- etc.

### 6. Technical Details
- Data models
- Architecture
- Implemented components
- Deployment information

### 7. Risks & Mitigations
Table with:
- Risk
- Probability
- Impact
- Mitigation

### 8. Related Specifications
Links to:
- Related User Stories
- Gherkin Features
- Documentation

### 9. Change History
Version tracking with:
- Date
- Version
- Change

---

## User Stories Summary

### [US-001: MongoDB Integration](US-001-mongodb-integration.md)

**Story**: As a system administrator, I want persistent data storage with MongoDB so that jobs survive server restarts.

**Key Points**:
- 4 MongoDB Collections (users, jobs, oauth_states, audit_logs)
- TTL indexes for automatic cleanup
- Repository pattern for data access
- Multi-instance capable

### [US-002: Job Event Logging](US-002-job-event-logging.md)

**Story**: As a user, I want detailed event lists for each job so that I can understand conversion decisions.

**Key Points**:
- 7 event types (format_conversion, ocr_decision, etc.)
- Event callback pattern in converter.py
- Async event logger helper
- Backward compatible

### [US-003: Local Default User](US-003-local-default-user.md)

**Story**: As a user without OAuth, I want an automatic local default user so that I can use features like job history.

**Key Points**:
- Automatic creation when AUTH_ENABLED=false
- Configurable via environment variables
- Idempotent implementation (multi-instance safe)

### [US-004: Live Job Events Display](US-004-live-job-events.md)

**Story**: As a user, I want to see conversion events as they occur in real-time.

### [US-005: Tab-Based Interface](US-005-tab-interface.md)

**Story**: As a user, I want the interface organized as tabs for easy navigation.

### [US-006: Account Tab](US-006-account-tab.md)

**Story**: As a user, I want to view my account information and settings.

### [US-007: Jobs History Tab](US-007-jobs-tab.md)

**Story**: As a user, I want to view my conversion job history with detailed events.

### [US-008: Camera Tab](US-008-camera-tab.md)

**Story**: As a user, I want to capture multi-page documents using my device's camera.

**Key Points**:
- Browser-based camera interface using getUserMedia API
- Multi-page document capture with page management
- Built-in photo editor (rotation, brightness, contrast)
- Direct submission to PDF/A conversion pipeline

### [US-009: Accessibility Camera Assistance](US-009-accessibility-camera-assistance.md)

**Story**: As a blind or visually impaired user, I want audio-guided document capture.

**Key Points**:
- Real-time edge detection with jscanify and OpenCV.js
- Audio feedback via Web Audio API and Speech Synthesis
- Automatic capture on stable document recognition
- Auto-crop and perspective correction

### [US-010: Mobile-Desktop Pairing](US-010-mobile-desktop-pairing.md)

**Story**: As a user, I want to pair my mobile device with the desktop application for remote capture.

**Key Points**:
- QR code-based pairing
- WebSocket real-time synchronization
- Session-based security via pairing codes

### [US-011: Auth Page Visibility](US-011-auth-page-visibility.md)

**Story**: As a user, I want to see only pages appropriate to my authentication status.

**Key Points**:
- Protected features only accessible to authenticated users
- Seamless experience when auth is disabled
- Clear login/logout flows

---

## Usage

### For Developers

1. **Read the complete User Story** before implementation
2. **Understand the business value** (Why?)
3. **Check acceptance criteria** (What must be fulfilled?)
4. **Follow Definition of Done** (When is it done?)
5. **Consult Gherkin Features** for concrete examples
6. **Implement with TDD** (RED-GREEN-REFACTOR)

### For Product Owners

1. **Validate business value**
2. **Check acceptance criteria** for completeness
3. **Evaluate risks** and accept mitigations
4. **Accept based on DoD**

### For Testers

1. **Use acceptance criteria** as test cases
2. **Reference Gherkin Features** for detailed scenarios
3. **Document deviations**

---

## Template

New User Stories should follow this template:

```markdown
# US-XXX: [Title]

**ID**: US-XXX
**Status**: 🚧 In Progress
**Date**: YYYY-MM-DD
**Priority**: [High/Medium/Low]
**Dependencies**: [Related User Stories]

---

## User Story

\`\`\`
As [role]
I want [feature]
So that [benefit]
\`\`\`

---

## Business Value

- [Value 1]
- [Value 2]

---

## Acceptance Criteria

### 1. [Criterion]
- **Given** [precondition]
- **When** [action]
- **Then** [expectation]

---

## Definition of Done

- [ ] Tests written and passing
- [ ] Code formatted (black) and linted (ruff)
- [ ] Documentation updated
- [ ] Gherkin Feature created
- [ ] Code review completed

---

## Technical Details

[Implementation details]

---

## Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| [Risk] | [Low/Medium/High] | [Low/Medium/High] | [Mitigation] |

---

## Related Specifications

**User Stories**:
- [Related Story](US-XXX.md)

**Gherkin Features**:
- [Feature](../features/feature-name.feature)

---

## Change History

| Date | Version | Change |
|------|---------|--------|
| YYYY-MM-DD | 1.0 | Initial creation |
```

---

## Related Documentation

- [Back to Overview](../README.md)
- [Gherkin Features](../features/)
- [AGENTS.md](../../../AGENTS.md)

---

## Change History

| Date | Version | Change |
|------|---------|--------|
| 2024-12-25 | 1.0 | Initial creation |
| 2026-01-03 | 2.0 | Unified structure, renamed German files, renumbered IDs |
