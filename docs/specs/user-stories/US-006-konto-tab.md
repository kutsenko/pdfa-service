# US-006: Account Information and Settings Tab

**Status**: 🚧 In Progress
**Date**: 2025-12-27
**Priority**: Medium
**Dependencies**: US-005 (Tab Interface), US-003 (Authentication)

---

## User Story

```
As a pdfa-service user
I want to view my account information and settings on the Konto tab
So that I can see my profile, configure default parameters, and manage my account
```

---

## Business Value

- **Transparency**: Users can see their account details, login history, and conversion statistics
- **Personalization**: Default conversion parameters reduce repetitive form filling
- **Control**: Users can delete their account and all associated data (GDPR compliance)
- **Analytics**: Users understand their usage patterns via job statistics
- **Security**: Activity log shows login history for security awareness

---

## Acceptance Criteria

### 1. Account Information Display (Read-only)

**Profile Information:**
- [ ] Email address displayed
- [ ] Full name displayed
- [ ] Profile picture shown (if available)
- [ ] User ID displayed (for support reference)

**Login Statistics:**
- [ ] Account creation date displayed
- [ ] Last login timestamp displayed
- [ ] Total login count displayed

**Job Statistics:**
- [ ] Total jobs count
- [ ] Completed jobs count
- [ ] Failed jobs count
- [ ] Success rate percentage
- [ ] Average conversion duration
- [ ] Total data processed (input + output bytes)
- [ ] Average compression ratio

**Activity Log:**
- [ ] Last 20 audit events displayed
- [ ] Event type, timestamp, and details shown
- [ ] Scrollable list for many events
- [ ] Auto-refresh on tab activation (with 30s cache)

### 2. User Preferences (Editable)

**Default Conversion Parameters:**
- [ ] Default PDF Type (Standard PDF, PDF/A-1, PDF/A-2, or PDF/A-3)
- [ ] Default OCR Language (dropdown with all available languages)
- [ ] Default Compression Profile (balanced, quality, aggressive, minimal)
- [ ] Default "Enable OCR" checkbox state
- [ ] Default "Skip OCR for tagged PDFs" checkbox state

**Preferences Behavior:**
- [ ] Preferences auto-loaded when user visits Konverter tab
- [ ] Form pre-filled with saved preferences (or system defaults)
- [ ] "Save Preferences" button to update
- [ ] "Reset to Defaults" button to restore system defaults
- [ ] Success/error messages after save

### 3. Account Deletion

**Danger Zone:**
- [ ] Red-bordered "Danger Zone" section
- [ ] Clear warning about irreversibility
- [ ] "Delete Account" button (red, prominent)
- [ ] Confirmation modal requiring email verification
- [ ] User must type their exact email to confirm
- [ ] Deletes: user profile, all jobs, audit logs, preferences
- [ ] Automatic logout after successful deletion
- [ ] Disabled when auth is disabled (local user cannot be deleted)

### 4. Authentication Modes

**Auth Enabled (PDFA_ENABLE_AUTH=true):**
- [ ] Shows authenticated user's actual data
- [ ] All features functional (view, edit, delete)
- [ ] API calls include Bearer token

**Auth Disabled (PDFA_ENABLE_AUTH=false):**
- [ ] Shows default "Local User" data
- [ ] Profile info shows default values
- [ ] Job stats show all jobs (no user_id filter)
- [ ] Audit log shows all events
- [ ] Preferences editable (stored for "local-default" user_id)
- [ ] Account deletion disabled (shows message)

### 5. Localization

**All text translated (EN, DE, ES, FR):**
- [ ] Section headings (Profile, Login Stats, Job Stats, Activity, Settings, Danger Zone)
- [ ] Field labels
- [ ] Button text
- [ ] Confirmation dialog
- [ ] Success/error messages
- [ ] Placeholder text

### 6. Responsive Design

- [ ] Desktop (>800px): 2-column card layout
- [ ] Tablet (600-800px): 2-column with adjusted spacing
- [ ] Mobile (<600px): 1-column stacked layout
- [ ] All cards scrollable if content overflows

### 7. Performance

- [ ] Profile data fetched on tab activation
- [ ] 30-second cache to prevent excessive queries
- [ ] Manual refresh button available
- [ ] Loading states during API calls
- [ ] Error states with retry option

---

## Technical Implementation

### Backend Implementation

**New Model: UserPreferencesDocument**
```python
class UserPreferencesDocument(BaseModel):
    user_id: str  # Unique index
    default_pdfa_level: Literal["standard", "1", "2", "3"] = "2"
    default_ocr_language: str = "deu+eng"
    default_compression_profile: Literal["balanced", "quality", "aggressive", "minimal"] = "balanced"
    default_ocr_enabled: bool = True
    default_skip_ocr_on_tagged: bool = True
    updated_at: datetime
```

**New Repository: UserPreferencesRepository**
- `async get_preferences(user_id: str) -> UserPreferencesDocument | None`
- `async create_or_update_preferences(prefs: UserPreferencesDocument) -> UserPreferencesDocument`
- `async delete_preferences(user_id: str) -> bool`

**New API Endpoints:**

1. `GET /api/v1/user/profile`
   - Returns: `{ user: {}, login_stats: {}, job_stats: {}, recent_activity: [] }`
   - Auth: Optional (works with auth disabled)

2. `GET /api/v1/user/preferences`
   - Returns: UserPreferencesDocument or system defaults
   - Auth: Optional

3. `PUT /api/v1/user/preferences`
   - Body: `{ default_pdfa_level, default_ocr_language, ... }`
   - Returns: Updated UserPreferencesDocument
   - Auth: Optional

4. `DELETE /api/v1/user/account`
   - Body: `{ email_confirmation: "user@example.com" }`
   - Returns: `{ message: "Account deleted successfully" }`
   - Auth: Required (disabled when auth=false)

### Frontend Implementation

**HTML Structure:** (in `tab-konto` panel)
- Profile Card (picture, name, email, user_id)
- Login Stats Card (created, last_login, total_logins)
- Job Stats Card (total, success_rate, avg_duration, data_processed)
- Activity Log Card (scrollable event list)
- Settings Form (default parameters)
- Danger Zone (delete account)

**JavaScript: AccountManager Class**
- `async fetchProfile()` - Loads all account data
- `async fetchPreferences()` - Loads preferences
- `async savePreferences(prefs)` - Saves preferences
- `async deleteAccount(email)` - Deletes account after confirmation
- `populateTab()` - Main render function
- `applyPreferencesToForm()` - Pre-fills converter form

**i18n Translations:** (~64 keys × 4 languages = 256 lines)

---

## Files Modified

| File | Lines | Description |
|------|-------|-------------|
| `docs/specs/user-stories/US-006-konto-tab.md` | New | User story document |
| `docs/specs/features/gherkin-konto-tab.feature` | New | Gherkin scenarios |
| `src/pdfa/models.py` | +40 | UserPreferencesDocument model |
| `src/pdfa/repositories.py` | +85 | UserPreferencesRepository |
| `src/pdfa/api.py` | +180 | 4 new API endpoints |
| `src/pdfa/db.py` | +8 | MongoDB index for user_preferences |
| `src/pdfa/web_ui.html` | +1,580 | HTML, CSS, JS, i18n |

**Total:** ~1,893 new lines

---

## Testing Plan

### Manual Testing Checklist

**Functional Tests:**
- [ ] Profile info displays correctly (auth enabled)
- [ ] Profile shows default user (auth disabled)
- [ ] Login stats accurate (created_at, last_login, login_count)
- [ ] Job stats calculated correctly
- [ ] Activity log shows recent events
- [ ] Preferences save successfully
- [ ] Preferences auto-apply to converter form
- [ ] Reset to defaults works
- [ ] Account deletion requires email confirmation
- [ ] Account deletion succeeds and logs out user
- [ ] Account deletion disabled when auth=false
- [ ] 30s cache prevents excessive queries
- [ ] Manual refresh button works

**API Tests:**
- [ ] GET /api/v1/user/profile returns all data
- [ ] GET /api/v1/user/preferences returns saved or defaults
- [ ] PUT /api/v1/user/preferences validates input
- [ ] DELETE /api/v1/user/account requires correct email
- [ ] DELETE /api/v1/user/account cascades deletions
- [ ] All endpoints work with auth disabled

**i18n Tests:**
- [ ] All text translated (EN, DE, ES, FR)
- [ ] Language switcher updates Konto tab
- [ ] No hardcoded German/English text

**Responsive Tests:**
- [ ] Desktop: 2-column layout
- [ ] Tablet: adjusted spacing
- [ ] Mobile: 1-column stacked
- [ ] Cards scrollable on overflow

**Security Tests:**
- [ ] Account deletion requires correct email
- [ ] Cannot delete other user's account
- [ ] Preferences only affect current user
- [ ] Job stats filtered by user_id

---

## Risks and Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Account deletion deletes active jobs | High | Medium | Cascade delete is correct, jobs cleanly removed |
| Preferences incompatible with old values | Medium | Low | Defaults for missing fields, Pydantic validation |
| Performance with many jobs | Medium | Low | MongoDB aggregation pipeline efficient, indexes in place |
| UI overloaded with information | Low | Medium | Card-based layout, good visual hierarchy |
| Email confirmation insecure | High | Low | Email match required, no simple confirm() |

---

## Future Enhancements (Out of Scope)

1. **UI Preferences** (future)
   - Theme selection (light/dark)
   - Language persistence per user
   - Custom date/time format

2. **Job History Export** (future)
   - Export job history as CSV
   - Filter and search capabilities

3. **Email Notifications** (future)
   - Notify when conversion completes
   - Weekly usage summaries

4. **Two-Factor Authentication** (future)
   - Enhanced account security
   - TOTP or SMS-based 2FA

5. **Team Accounts** (future)
   - Share accounts across team members
   - Role-based access control

---

## Definition of Done

- [x] User Story US-006 created
- [ ] Gherkin feature spec created
- [ ] Feature branch created
- [ ] Backend models, repositories, API implemented
- [ ] Frontend HTML, CSS, JavaScript implemented
- [ ] i18n translations complete (4 languages)
- [ ] Manual testing completed (100% pass)
- [ ] No regressions in existing features
- [ ] Code committed with descriptive message
- [ ] Pull request created
- [ ] Code review completed
- [ ] Merged to main
- [ ] Status updated to ✅ Implemented

---

## References

- **Related User Stories**: US-004 (Live Job Events), US-003 (Local Default User), US-005 (Tab Interface)
- **Design Pattern**: Repository Pattern for data access
  - Existing patterns in `src/pdfa/repositories.py`
- **Security**: GDPR compliance for account deletion
  - Complete data removal on user request
- **Accessibility**: ARIA attributes for screen readers
  - Following patterns from US-005 tab interface

---

**Created**: 2025-12-27
**Last Updated**: 2025-12-27
**Author**: AI Assistant (Claude Sonnet 4.5)
