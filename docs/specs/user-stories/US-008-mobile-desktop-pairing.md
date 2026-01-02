# User Story: Mobile-Desktop Camera Pairing

**ID**: US-008
**Title**: Jump to mobile device to utilize camera
**Status**: ✅ Implemented
**Date**: 2026-01-02

---

## Story

**As a** desktop user of pdfa-service
**I want to** use my mobile device to photograph documents
**so that** I can get the best of two worlds - desktop browser convenience and mobile device camera quality.

---

## Context

**Current State (before Mobile-Desktop Pairing)**:
- Desktop users must use webcam for camera capture
- Webcams typically have lower quality than mobile cameras
- No way to leverage high-quality mobile device cameras from desktop
- Users must choose between desktop workflow OR mobile camera quality

**Problem**:
- Desktop webcams produce lower quality document scans
- Mobile devices have superior cameras (higher resolution, better optics)
- Switching between devices interrupts workflow
- No seamless integration between desktop and mobile

**Solution**:
- Temporary pairing sessions linking desktop and mobile devices
- QR code for instant mobile connection
- Real-time image synchronization via WebSocket
- Basic mobile editing (rotation) before sync
- Desktop retains full editing and conversion capabilities
- 30-minute session TTL with automatic cleanup

---

## Acceptance Criteria

### 1. Desktop Pairing Initialization
- **Given** a user is on the desktop Camera tab
- **When** the user clicks "Start Mobile Pairing"
- **Then** a unique 6-character pairing code should be generated
- **And** a QR code containing the mobile URL should be displayed
- **And** a countdown timer showing 15:00 minutes should be visible
- **And** the status should show "Waiting for mobile..."

### 2. QR Code Scanning (Mobile)
- **Given** a desktop pairing session is active with code "ABC123"
- **When** a mobile user scans the QR code
- **Then** the mobile browser should navigate to `/mobile/camera?code=ABC123`
- **And** the pairing code input should be pre-filled with "ABC123"
- **And** the "Connect" button should be available

### 3. Manual Pairing Code Entry (Mobile)
- **Given** a desktop pairing session is active with code "ABC123"
- **When** a mobile user navigates to `/mobile/camera`
- **And** enters "ABC123" in the pairing code input
- **And** clicks "Connect"
- **Then** the session should be joined successfully
- **And** the mobile camera view should be displayed
- **And** the desktop should show "Mobile connected ✓"

### 4. Image Capture and Sync
- **Given** a mobile device is connected to a desktop session
- **And** camera permissions have been granted
- **When** the user clicks the capture button
- **Then** the image should be captured
- **And** the image editor screen should appear
- **And** rotation controls should be available

### 5. Image Transmission to Desktop
- **Given** a mobile user has captured and edited an image
- **When** the user clicks "Send to Desktop"
- **Then** the image should be transmitted via WebSocket
- **And** the image should appear in the desktop staging area
- **And** the mobile counter should increment "1 sent"
- **And** the desktop counter should show "1 images received"
- **And** the mobile should return to camera view

### 6. Multi-Page Workflow
- **Given** a mobile device is connected
- **When** the user captures and sends 3 images
- **Then** the desktop staging area should contain 3 pages
- **And** each page should be numbered (1, 2, 3)
- **And** pages can be reordered via drag-and-drop on desktop

### 7. Session Expiration
- **Given** a pairing session has been active for 30 minutes
- **When** the session expires
- **Then** the desktop should show "Pairing session expired"
- **And** the mobile should show "Pairing session expired"
- **And** the QR code should be hidden on desktop
- **And** the "Start Mobile Pairing" button should reappear

### 8. Manual Session Cancellation
- **Given** an active pairing session
- **When** the user clicks "Cancel Pairing" on desktop
- **Then** the session status should change to "cancelled"
- **And** the mobile should display "Pairing session expired"
- **And** both devices should disconnect

### 9. Mobile Disconnection
- **Given** a connected mobile-desktop session
- **When** the mobile user clicks "Disconnect"
- **Then** the desktop should show "Mobile disconnected"
- **And** the mobile should return to pairing code entry screen
- **And** captured images should remain in desktop staging area

### 10. Desktop Submission
- **Given** 5 images have been captured from mobile
- **And** all images are in the desktop staging area
- **When** the desktop user reorders the pages
- **And** clicks "Convert to PDF/A"
- **Then** a conversion job should be submitted with all 5 pages
- **And** pages should be in the reordered sequence
- **And** the user should be switched to the Jobs tab

### 11. Invalid Pairing Code Handling
- **Given** a user on the mobile pairing screen
- **When** the user enters "INVALID" as pairing code
- **And** clicks "Connect"
- **Then** an error message "Invalid pairing code" should be displayed
- **And** the user should remain on the pairing screen

### 12. Same-User Enforcement
- **Given** a desktop session for user "alice@example.com"
- **And** a mobile device logged in as "bob@example.com"
- **When** the mobile user attempts to join with the pairing code
- **Then** an error "Must use same account on both devices" should be shown
- **And** the session should not be joined

---

## Technical Requirements

### Security
- **Authentication**: JWT-based, same user required on both devices
- **Session TTL**: 30 minutes with automatic cleanup
- **Code Generation**: Exclude confusing characters (0, O, 1, I, L)
- **Rate Limiting**:
  - Create session: 10/minute
  - Join session: 20/minute
  - Status check: 60/minute
  - Cancel session: 30/minute
- **Transport**: WebSocket for real-time, HTTPS for API

### Performance
- **Image Compression**: JPEG with 85% quality
- **Image Size**: 1920x1080 maximum from mobile
- **Sync Latency**: < 1 second for image transfer
- **Session Cleanup**: MongoDB TTL index (automatic)

### Data Model
```
PairingSessionDocument:
  - session_id: UUID
  - pairing_code: 6-char alphanumeric
  - desktop_user_id: string
  - mobile_user_id: string | null
  - status: pending | active | expired | cancelled
  - created_at: datetime
  - expires_at: datetime (created_at + 30 min)
  - joined_at: datetime | null
  - last_activity_at: datetime
  - images_synced: integer
```

### WebSocket Protocol
**Client → Server**:
- `register_pairing`: Register WebSocket for session (desktop/mobile)
- `sync_image`: Transfer image from mobile to desktop

**Server → Client**:
- `image_synced`: Notify desktop of new image
- `pairing_peer_status`: Notify of peer connection/disconnection
- `pairing_expired`: Notify of session expiration

---

## UI/UX Requirements

### Desktop UI
- **Pairing Section**: Visible in Camera tab
- **QR Code**: 200x200px, high correction level
- **Pairing Code**: Large, monospace font with letter spacing
- **Status Badge**: Color-coded (yellow=waiting, green=connected)
- **Countdown Timer**: MM:SS format
- **Images Counter**: "X images received"

### Mobile UI
- **Optimized Layout**: Full-screen, touch-friendly
- **Pairing Screen**: Large input, auto-focus on QR scan
- **Camera View**: Full viewport with overlay controls
- **Editor**: Simple rotation controls
- **Feedback**: Visual confirmation on image send

### Responsive Design
- Desktop: QR code prominent, horizontal layout
- Mobile: Vertical layout, large touch targets
- Tablet: Adaptive between desktop/mobile styles

---

## Dependencies

### Backend
- FastAPI (WebSocket support)
- MongoDB (with TTL indexes)
- Motor (async MongoDB driver)
- Jinja2 (template rendering)

### Frontend
- qrcodejs (QR code generation)
- WebSocket API (browser native)
- MediaDevices API (camera access)
- Canvas API (image manipulation)

---

## Testing Strategy

### Unit Tests
- Pairing code generation (character exclusion)
- Session creation and lifecycle
- Same-user validation
- WebSocket message handling

### Integration Tests
- REST API endpoints
- WebSocket message flow
- MongoDB TTL cleanup
- Rate limiting

### E2E Tests
- Full pairing workflow
- Multi-page capture and sync
- Session expiration
- Error scenarios

### Manual Testing
- Cross-device testing (iOS, Android, desktop)
- Network interruption handling
- Camera permission scenarios
- QR code scanning accuracy

---

## Non-Functional Requirements

### Accessibility
- Mobile UI: Large touch targets (44x44px minimum)
- Keyboard navigation: Full support on desktop
- Screen readers: Proper ARIA labels
- Color contrast: WCAG AA compliance

### Internationalization
- All UI strings use i18n keys
- Support for: English, German, Spanish, French
- Date/time formatting: Locale-aware

### Browser Support
- Desktop: Chrome 90+, Firefox 88+, Safari 14+, Edge 90+
- Mobile: iOS Safari 14+, Chrome Mobile 90+
- WebSocket: Required (no fallback)
- Camera API: Required (no fallback)

---

## Rollout Plan

### Phase 1: Feature Flag (Optional)
- Environment variable: `ENABLE_MOBILE_PAIRING=true`
- Default: Enabled for all users
- Allows quick disable if issues arise

### Phase 2: Monitoring
- Track session creation rate
- Monitor WebSocket connection stability
- Alert on high failure rates
- Log pairing code collisions (should be rare)

### Phase 3: Optimization
- Monitor image sync latency
- Optimize image compression if needed
- Tune WebSocket message size
- Adjust TTL based on usage patterns

---

## Future Enhancements

### Potential Improvements
- [ ] **Crop Tool**: Mobile-side image cropping
- [ ] **Auto-Capture**: Detect document edges and auto-capture
- [ ] **Multi-Session**: Multiple mobile devices to one desktop
- [ ] **Persistent Storage**: Save session state for reconnection
- [ ] **Feedback Sounds**: Audio confirmation on image sync
- [ ] **Haptic Feedback**: Vibration on successful capture/sync
- [ ] **Advanced Editing**: Brightness, contrast adjustments on mobile

### Out of Scope
- Video streaming (too bandwidth intensive)
- File transfer (not document capture)
- Chat/messaging (not related to core feature)

---

## Related Stories

- **US-004**: Camera Tab for Multi-Page Document Capture
- **US-005**: Accessibility Camera Assistance

---

## Implementation

**Branch**: `feature/mobile-desktop-pairing`
**Pull Request**: #41
**Commit**: `feat: Add mobile-desktop camera pairing for real-time image sync`

**Files Changed**: 15 files, 2446 insertions

**Key Components**:
- `src/pdfa/pairing_manager.py` - Core pairing logic
- `src/pdfa/templates/mobile_camera.html` - Mobile UI
- `src/pdfa/static/js/camera/MobilePairingManager.js` - Desktop pairing UI
- `src/pdfa/static/js/mobile/MobileCameraClient.js` - Mobile client

---

## Notes

- Pairing codes are designed to be human-readable while avoiding confusion
- Session cleanup is automatic via MongoDB TTL indexes
- Same-user enforcement prevents unauthorized access
- WebSocket connection is bidirectional for peer status updates
- Mobile UI is PWA-compatible for future offline support
