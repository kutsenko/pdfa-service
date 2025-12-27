# US-005: Tab-Based User Interface

**Status**: 🚧 In Progress
**Date**: 2025-12-26
**Priority**: Medium
**Dependencies**: None

---

## User Story

```
Als pdfa-service Benutzer
möchte ich die Benutzeroberfläche als Tabs organisiert haben,
um zwischen verschiedenen Funktionen (Konverter, Kamera, Aufträge, Konto, Dokumentation) einfach wechseln zu können.
```

**English**:
```
As a pdfa-service user
I want the user interface organized as tabs
So that I can easily switch between different functions (Converter, Camera, Jobs, Account, Documentation)
```

---

## Business Value

- **Organization**: Clear separation of different application features improves user experience
- **Scalability**: Tab structure allows adding new features without cluttering the interface
- **Navigation**: Intuitive navigation between converter, job history, account settings, and documentation
- **Future-Ready**: Placeholder tabs prepared for upcoming features (Camera scanner, Job history, Account management)
- **Accessibility**: Tab navigation follows ARIA best practices for keyboard and screen reader users

---

## Acceptance Criteria

### Functional Requirements

1. **Tab Navigation**
   - [ ] 5 tabs displayed: "Konverter", "Kamera", "Aufträge", "Konto", "Dokumentation"
   - [ ] Tab bar positioned below header, above content area
   - [ ] Active tab visually highlighted (color, border, background)
   - [ ] Clicking tab switches to corresponding content panel
   - [ ] Only one tab active at a time
   - [ ] URL hash reflects active tab (e.g., `#konverter`, `#kamera`)
   - [ ] Browser back/forward buttons work with tab navigation

2. **Konverter Tab** (Existing Functionality)
   - [ ] Contains all existing converter functionality
   - [ ] File upload form with all options (language, PDF/A level, compression, OCR)
   - [ ] Progress bar and status messages
   - [ ] Live event list (from US-004)
   - [ ] Event summary modal (from US-004)
   - [ ] All WebSocket communication works
   - [ ] Authentication integration works (from US-003)

3. **Placeholder Tabs** (Kamera, Aufträge, Konto, Dokumentation)
   - [ ] Each tab displays centered "Coming soon" message
   - [ ] Placeholder includes appropriate icon (📷 camera, 📋 jobs, 👤 account, 📖 docs)
   - [ ] Placeholder title and description translated to all 4 languages
   - [ ] No functionality yet - pure placeholders for future implementation

4. **State Preservation**
   - [ ] Switching tabs preserves converter form state (selected file, options)
   - [ ] WebSocket connection persists across tab switches
   - [ ] File upload selection not lost when switching tabs
   - [ ] Progress bar state maintained during conversion

5. **Keyboard Navigation**
   - [ ] Tab key moves focus between tab buttons
   - [ ] Arrow Left/Right navigate between tabs
   - [ ] Arrow Up/Down navigate between tabs
   - [ ] Home key jumps to first tab (Konverter)
   - [ ] End key jumps to last tab (Dokumentation)
   - [ ] Enter/Space activates focused tab

6. **Accessibility** (WCAG 2.1 AA)
   - [ ] ARIA attributes: `role="tablist"`, `role="tab"`, `role="tabpanel"`
   - [ ] `aria-selected` indicates active tab
   - [ ] `aria-controls` links tab to panel
   - [ ] `aria-labelledby` links panel to tab
   - [ ] Screen reader announces tab switches
   - [ ] Focus management: active tab receives focus
   - [ ] Keyboard shortcuts documented

7. **Localization** (i18n)
   - [ ] Tab labels translated: EN, DE, ES, FR
   - [ ] Placeholder content translated: EN, DE, ES, FR
   - [ ] Language switcher updates all tab labels immediately
   - [ ] No hardcoded German/English text in HTML

8. **Responsive Design**
   - [ ] Desktop (>800px): All 5 tabs fit comfortably, no wrapping
   - [ ] Tablet (600-800px): Tabs display correctly
   - [ ] Mobile (<600px): Tabs scroll horizontally, touch-friendly
   - [ ] Touch scrolling smooth on mobile devices
   - [ ] Tab buttons sized appropriately for touch targets (min 44x44px)

9. **Visual Design**
   - [ ] Tab styling consistent with existing UI design
   - [ ] Active tab clearly distinguishable from inactive tabs
   - [ ] Hover states for inactive tabs
   - [ ] Focus indicators visible for keyboard navigation
   - [ ] Dark mode support (`prefers-color-scheme: dark`)
   - [ ] Smooth transitions when switching tabs (fade-in animation)

10. **Performance**
    - [ ] Tab switching instant (<100ms)
    - [ ] No layout shifts when switching tabs
    - [ ] All tabs rendered on initial load (no lazy loading needed for 5 tabs)
    - [ ] Reduced motion support (`prefers-reduced-motion: reduce`)

---

## Technical Implementation

### Architecture Decision

**Single-Page Tab Implementation**:
- All tabs rendered in DOM on initial page load
- Tab switching via CSS `display: none/block` (not DOM manipulation)
- Preserves form state and WebSocket connections automatically
- Simple, performant, no complex state management needed

**Alternative Considered**: SPA framework (React/Vue) - Rejected due to:
- Overkill for 5 static tabs
- Would require major refactoring of existing codebase
- Current vanilla JS approach sufficient for requirements

### File Changes

**1. `src/pdfa/web_ui.html`** (Single file modification)

**CSS Changes** (~150 lines):
- Container max-width: `600px` → `800px` (more space for 5 tabs)
- Tab navigation styles: flex layout, active state, hover effects
- Tab panel styles: display toggle, fade-in animation
- Placeholder content styles: centered, icon, title, description
- Responsive: horizontal scroll on mobile (<600px)
- Dark mode: tab colors adjusted for dark theme

**HTML Structure Changes** (~200 lines):
- Wrap existing content in tab panels
- Add `<nav class="tab-navigation" role="tablist">` with 5 tab buttons
- Move existing converter content into `<div id="tab-konverter" role="tabpanel">`
- Add 4 placeholder panels: `tab-kamera`, `tab-auftraege`, `tab-konto`, `tab-dokumentation`
- Preserve all existing IDs (converterForm, progressContainer, eventListContainer, eventSummaryModal)

**JavaScript Changes** (~120 lines):
- `initTabNavigation()` function: sets up tab click and keyboard listeners
- `switchTab(tabId)` function: updates active tab, manages ARIA attributes
- `initFromHash()` function: loads tab from URL hash on page load
- `announceToScreenReader(message)` function: announces tab switches to screen readers
- Hash change listener: browser back/forward support
- Integration: call `initTabNavigation()` after auth initialization

**Translation Changes** (~24 lines, 4 languages):
```javascript
// English
'tabs.konverter': 'Converter',
'tabs.kamera': 'Camera',
'tabs.auftraege': 'Jobs',
'tabs.konto': 'Account',
'tabs.dokumentation': 'Documentation',
'placeholder.kamera.title': 'Camera Scanner',
'placeholder.kamera.description': 'Coming soon: Upload documents directly from your camera or scanner',
// ... (similar for Aufträge, Konto, Dokumentation)

// German (similar structure)
// Spanish (similar structure)
// French (similar structure)
```

### Component Integration

**Existing Components Preserved**:
- `AuthManager` class: remains global, works across all tabs
- `ConversionClient` class: WebSocket connection persists during tab switches
- Language switcher: remains global (fixed position, outside tabs)
- Authentication bar: remains global (fixed position, outside tabs)
- Event list: scoped to Konverter tab only
- Event summary modal: scoped to Konverter tab, but overlays entire page

**No Backend Changes Required**:
- Tab navigation is purely frontend feature
- No API changes needed
- No database schema changes
- WebSocket protocol unchanged

---

## Files Modified

| File | Lines Added | Lines Modified | Description |
|------|-------------|----------------|-------------|
| `src/pdfa/web_ui.html` | ~494 | ~20 | CSS (+150), HTML (+220 restructure), JS (+120), i18n (+24) |

**Total**: 1 file, ~514 line changes

---

## Testing Plan

### Manual Testing Checklist

**Functional Tests**:
1. [ ] All 5 tabs display correctly on page load
2. [ ] Konverter tab is active by default
3. [ ] Clicking each tab switches content correctly
4. [ ] File upload works in Konverter tab
5. [ ] Full conversion workflow works (upload → convert → progress → events → modal → download)
6. [ ] Switching to another tab during conversion preserves progress bar
7. [ ] Returning to Konverter tab shows updated progress
8. [ ] Placeholder tabs show "Coming soon" message with icon
9. [ ] URL hash updates when switching tabs (#konverter, #kamera, etc.)
10. [ ] Opening URL with hash (#auftraege) loads correct tab
11. [ ] Browser back/forward buttons work with tabs

**Keyboard Navigation Tests**:
1. [ ] Tab key cycles through tab buttons
2. [ ] Arrow Left/Right switch between tabs
3. [ ] Arrow Up/Down switch between tabs
4. [ ] Home key jumps to Konverter
5. [ ] End key jumps to Dokumentation
6. [ ] Enter/Space activates focused tab
7. [ ] Focus indicator visible on all tab buttons

**Accessibility Tests** (with screen reader):
1. [ ] Screen reader announces "Tablist" for navigation
2. [ ] Each tab announced as "Tab 1 of 5: Konverter"
3. [ ] Active tab announced as "selected"
4. [ ] Tab switch announced: "Switched to Camera tab"
5. [ ] All placeholder content readable

**Localization Tests**:
1. [ ] English: All tab labels correct, placeholder content correct
2. [ ] German: All tab labels correct, placeholder content correct
3. [ ] Spanish: All tab labels correct, placeholder content correct
4. [ ] French: All tab labels correct, placeholder content correct
5. [ ] Language switcher updates tabs immediately
6. [ ] No untranslated text in any language

**Responsive Tests**:
1. [ ] Desktop (1920x1080): All tabs fit, no scrolling
2. [ ] Laptop (1366x768): All tabs fit, no scrolling
3. [ ] Tablet (768x1024): Tabs display correctly
4. [ ] Mobile portrait (375x667): Tabs scroll horizontally
5. [ ] Mobile landscape (667x375): Tabs scroll horizontally
6. [ ] Touch scrolling smooth on mobile

**Visual Tests**:
1. [ ] Light mode: Tab styling matches design
2. [ ] Dark mode: Tab colors appropriate, good contrast
3. [ ] Hover states work on inactive tabs
4. [ ] Active tab clearly distinguishable
5. [ ] Focus indicators visible
6. [ ] Fade-in animation smooth (0.3s)
7. [ ] Reduced motion: Animation disabled when `prefers-reduced-motion: reduce`

**Browser Compatibility**:
1. [ ] Chrome/Edge (latest): All features work
2. [ ] Firefox (latest): All features work
3. [ ] Safari (latest): All features work
4. [ ] Mobile Chrome (Android): Touch and scrolling work
5. [ ] Mobile Safari (iOS): Touch and scrolling work

**Regression Tests** (existing features):
1. [ ] File upload validation still works
2. [ ] OCR language selection works
3. [ ] PDF/A level selection works
4. [ ] Compression profile selection works
5. [ ] Advanced options toggle works
6. [ ] Convert button triggers conversion
7. [ ] Progress bar animates correctly
8. [ ] WebSocket updates received
9. [ ] Event list populates and toggles correctly
10. [ ] Modal displays after successful conversion
11. [ ] Modal download button works
12. [ ] Authentication (login/logout) works

### Automated Testing

**Not Required for This Feature**:
- Tab navigation is pure UI interaction
- No business logic to unit test
- Existing E2E tests for converter workflow still apply
- Visual regression testing could be added later (optional)

---

## Risks and Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Tab structure breaks existing converter functionality | High | Low | Thorough manual testing, preserve all IDs and structure |
| WebSocket connection lost during tab switch | High | Low | Connection established globally, not scoped to tabs |
| Form state lost when switching tabs | Medium | Low | Tabs use `display: none`, form remains in DOM |
| Mobile horizontal scroll not smooth | Low | Medium | Use native CSS overflow-x scroll with touch support |
| URL hash conflicts with existing features | Medium | Low | Check for existing hash usage (none found) |
| Screen reader compatibility issues | Medium | Low | Follow ARIA authoring practices, test with NVDA/ORCA |

---

## Future Enhancements (Out of Scope)

1. **Kamera Tab Implementation** (US-006, future)
   - Camera/scanner document upload
   - QR code scanning for settings
   - Batch upload from mobile camera

2. **Aufträge Tab Implementation** (US-007, future)
   - Job history list from MongoDB
   - Re-download previous conversions
   - Delete old jobs
   - Filter/search job history

3. **Konto Tab Implementation** (US-008, future)
   - User profile settings
   - Default conversion preferences
   - API key management
   - Account deletion

4. **Dokumentation Tab Implementation** (US-009, future)
   - Inline help documentation
   - PDF/A format guide
   - OCR best practices
   - Troubleshooting FAQ

5. **Tab Badges** (future enhancement)
   - Show notification count (e.g., "3 pending jobs")
   - Red dot for important notifications

6. **Tab Icons** (future enhancement)
   - Add SVG icons to tab labels for better visual hierarchy

---

## Definition of Done

- [x] User Story created (US-005-tab-interface.md)
- [ ] Gherkin feature spec created (gherkin-tab-interface.feature)
- [ ] Feature branch created (`feature/tab-interface`)
- [ ] Implementation complete (all code changes in web_ui.html)
- [ ] Manual testing checklist completed (100% pass)
- [ ] No regressions in existing converter functionality
- [ ] All 4 languages tested and working
- [ ] Dark mode tested and working
- [ ] Mobile responsive tested and working
- [ ] Accessibility tested with screen reader
- [ ] Code committed with descriptive message
- [ ] Pull request created with testing summary
- [ ] Code review completed
- [ ] Merged to main branch
- [ ] Status updated to ✅ Implemented

---

## References

- **Related User Stories**: US-004 (Live Job Events), US-003 (Local Default User)
- **Design Pattern**: WAI-ARIA Authoring Practices - Tabs Pattern
  - https://www.w3.org/WAI/ARIA/apg/patterns/tabs/
- **Accessibility**: WCAG 2.1 Level AA
  - https://www.w3.org/WAI/WCAG21/quickref/
- **Browser Support**: Modern browsers (ES6+, CSS Grid, Flexbox)

---

**Created**: 2025-12-26
**Last Updated**: 2025-12-26
**Author**: AI Assistant (Claude Sonnet 4.5)
