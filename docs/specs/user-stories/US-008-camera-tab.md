# User Story: Camera Tab for Multi-Page Document Capture

**ID**: US-008
**Title**: Browser-based camera interface for multi-page document scanning
**Status**: ✅ Implemented
**Date**: 2025-12-30

---

## Story

**As** a user of the PDF/A service
**I want** to capture multi-page documents using my device's camera directly in the browser
**so that** I can create searchable PDF/A documents without needing a physical scanner or separate app.

---

## Context

**Current State (before Camera Tab)**:
- Users must scan documents externally and upload files
- No built-in document capture capability
- Requires separate scanner app or device
- No multi-page workflow in browser
- No accessibility support for blind users

**Problem**:
- Physical scanners are not always available
- Mobile users prefer camera-based capture
- External apps create friction in workflow
- No integrated solution for document digitization
- Blind users cannot use camera features

**Solution**:
- Browser-based camera interface using getUserMedia API
- Multi-page document capture with page management
- Built-in photo editor for adjustments (rotation, brightness, contrast)
- Direct submission to PDF/A conversion pipeline
- Accessibility features for blind users (US-005)
- Progressive Web App capabilities (works offline)

---

## Acceptance Criteria

### 1. Camera Access and Preview
- **Given** a user opens the Camera tab
- **When** the page loads
- **Then** browser should request camera permission
- **And** live camera preview should be displayed
- **And** should use rear camera on mobile devices by default
- **And** should provide camera selection dropdown

### 2. Photo Capture
- **Given** camera preview is active
- **When** user clicks capture button or presses space bar
- **Then** current frame should be captured as high-resolution image
- **And** should use full camera resolution (not preview resolution)
- **And** should play camera shutter sound
- **And** captured photo should open in editor

### 3. Photo Editor
- **Given** a photo was captured
- **When** editor opens
- **Then** should display photo at full size
- **And** should provide rotation controls (90° left/right)
- **And** should provide brightness adjustment slider
- **And** should provide contrast adjustment slider
- **And** should show Accept and Retake buttons
- **And** adjustments should apply in real-time

### 4. Multi-Page Support
- **Given** user has captured and accepted a photo
- **When** returning to camera view
- **Then** captured page should be added to page list
- **And** page thumbnail should be visible
- **And** page counter should update (e.g., "Page 1/3")
- **And** user can capture additional pages
- **And** should support unlimited pages (memory permitting)

### 5. Page Management
- **Given** user has captured multiple pages
- **When** viewing page list
- **Then** user should be able to reorder pages (drag and drop)
- **And** user should be able to delete individual pages
- **And** user should be able to retake a page (re-edit)
- **And** thumbnails should update immediately

### 6. Document Submission
- **Given** user has captured at least one page
- **When** user clicks Convert button
- **Then** all pages should be submitted to conversion API
- **And** should upload as multi-page document
- **And** should apply selected PDF/A level and settings
- **And** should show progress indicator
- **And** should handle conversion errors gracefully

### 7. Accessibility Integration
- **Given** accessibility assistance is available (US-005)
- **When** user enables accessibility features
- **Then** should provide audio guidance for camera alignment
- **And** should detect document edges automatically
- **And** should auto-capture when document is stable and centered
- **And** should auto-crop and correct perspective
- **And** should work for blind users with screen readers

### 8. Camera Settings
- **Given** device has multiple cameras
- **When** user opens camera selection dropdown
- **Then** should list all available cameras
- **And** should remember user's camera preference
- **And** should switch cameras without page reload

### 9. Error Handling
- **Given** camera permission is denied
- **When** user tries to access camera
- **Then** should display clear error message
- **And** should provide instructions to enable permission
- **And** should not crash the application

### 10. Responsive Design
- **Given** user accesses Camera tab on any device
- **When** page is rendered
- **Then** should work on desktop, tablet, and mobile
- **And** should use appropriate camera resolution for device
- **And** should optimize UI for touch on mobile
- **And** should support portrait and landscape orientations

---

## Definition of Done

- [x] Camera tab implemented in web UI
- [x] getUserMedia API integration
- [x] Live camera preview with device selection
- [x] High-resolution photo capture
- [x] Photo editor with rotation, brightness, contrast controls
- [x] Multi-page capture and management
- [x] Page reordering (drag and drop)
- [x] Page deletion and retake
- [x] Submission to conversion API
- [x] Integration with accessibility features (US-005)
- [x] Keyboard shortcuts (Space for capture, Esc to cancel)
- [x] Responsive design for all devices
- [x] Error handling for camera permissions
- [x] Camera preference persistence
- [x] Gherkin feature with scenarios created
- [x] User story documented

---

## Technical Details

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Camera Tab UI                           │
│  ┌─────────────────┬──────────────────┬──────────────────┐ │
│  │  Camera View    │  Photo Editor    │  Page Manager    │ │
│  │  (Capture)      │  (Adjust)        │  (Organize)      │ │
│  └─────────────────┴──────────────────┴──────────────────┘ │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  CameraManager (src/pdfa/web_ui.html)                │  │
│  │  - startCamera()                                      │  │
│  │  - capturePhoto()                                     │  │
│  │  - openEditor()                                       │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  AccessibleCameraAssistant (US-005)                  │  │
│  │  - Audio guidance, edge detection, auto-crop         │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
         │                           │
         ▼                           ▼
┌──────────────────┐       ┌──────────────────┐
│ getUserMedia API │       │ Conversion API   │
│ (Browser Camera) │       │ POST /convert    │
└──────────────────┘       └──────────────────┘
```

### Components

#### CameraManager Class
**File**: `src/pdfa/web_ui.html` (lines ~8500-9300)

**Properties**:
```javascript
stream: MediaStream           // Camera video stream
videoElement: HTMLVideoElement // Video preview
canvasElement: HTMLCanvasElement // Capture canvas
capturedPages: Array<{
  dataUrl: string,            // Image data (base64 JPEG)
  rotation: number,           // 0, 90, 180, 270
  brightness: number,         // -100 to 100
  contrast: number            // -100 to 100
}>
currentDeviceId: string       // Selected camera ID
a11yAssistant: AccessibleCameraAssistant // Accessibility features
```

**Methods**:
```javascript
// Camera Control
async init()
async startCamera(deviceId)
stopCamera()
switchCamera(deviceId)
getCameraDevices()

// Capture Workflow
capturePhoto()                // Capture current frame
openEditor(imageData)         // Open photo editor
applyEdits(rotation, brightness, contrast)
acceptPhoto()                 // Add to pages
retakePhoto()                 // Return to camera

// Page Management
addPage(imageData, metadata)
deletePage(index)
reorderPages(fromIndex, toIndex)
updatePageThumbnail(index)

// Submission
async submitDocument()        // Upload all pages to API
```

### Camera Capture Flow

```
1. User opens Camera tab
2. Browser requests camera permission
3. getUserMedia() → MediaStream
4. Stream connected to <video> element
5. User clicks Capture button
6. Draw video frame to <canvas> (full resolution)
7. canvas.toDataURL('image/jpeg', 0.85) → Base64 image
8. Open photo editor with image
9. User adjusts rotation, brightness, contrast
10. User clicks Accept
11. Image added to capturedPages array
12. Thumbnail generated and displayed
13. Return to camera for next page (or Convert)
```

### Photo Editor

**Adjustments**:
- **Rotation**: 0°, 90°, 180°, 270° (CSS transform)
- **Brightness**: -100 to +100 (canvas filter)
- **Contrast**: -100 to +100 (canvas filter)

**Implementation**:
```javascript
// Apply filters to canvas context
ctx.filter = `brightness(${brightness}%) contrast(${contrast}%)`;
ctx.translate(centerX, centerY);
ctx.rotate(rotation * Math.PI / 180);
ctx.drawImage(img, -centerX, -centerY);
```

### Multi-Page Document Submission

**Endpoint**: `POST /convert`

**Payload**:
```javascript
FormData {
  pages: [File, File, File],  // All captured pages as Blobs
  pdfa_level: "2",
  ocr_enabled: true,
  compression_profile: "quality",
  language: "deu+eng"
}
```

**Process**:
1. Convert base64 images to Blobs
2. Create File objects from Blobs
3. Append all files to FormData
4. POST to /convert endpoint
5. Backend concatenates pages into single PDF
6. OCRmyPDF processes multi-page document
7. Return PDF/A compliant file

### Accessibility Integration (US-005)

**Reference**: [US-005: Accessibility Camera Assistance](US-005-accessibility-camera-assistance.md)

**Integration Points**:
1. **Auto-Detection**: Accessible assistant detects screen readers and auto-enables
2. **Audio Guidance**: Tones and voice announcements guide camera positioning
3. **Edge Detection**: jscanify detects document edges in real-time
4. **Auto-Capture**: Captures automatically when document is stable and centered
5. **Auto-Crop**: Crops to detected edges and corrects perspective
6. **Keyboard Navigation**: Full keyboard support for blind users

**Workflow with Accessibility**:
```
1. User enables accessibility assistance
2. Audio guidance starts ("Camera assistance enabled")
3. User points camera at document
4. Edge detection activates
5. Audio feedback: "Document edges detected. Hold steady."
6. Auto-capture countdown: "2... 1..."
7. Auto-capture + auto-crop + perspective correction
8. Photo opens in editor (screen reader announces)
9. User accepts with keyboard (Enter key)
10. Page added to list (screen reader announces count)
```

### Browser Compatibility

**Required APIs**:
- `navigator.mediaDevices.getUserMedia()` - Camera access
- `HTMLVideoElement` - Video preview
- `HTMLCanvasElement` - Image capture and editing
- `FileReader` / `Blob` - Image conversion
- `FormData` - Multi-page upload
- `CSS Grid` / `Flexbox` - Responsive layout

**Supported Browsers**:
- ✅ Chrome 53+ (desktop & mobile)
- ✅ Firefox 36+ (desktop & mobile)
- ✅ Safari 11+ (desktop & iOS)
- ✅ Edge 79+ (Chromium)
- ❌ IE 11 (not supported)

### Performance Considerations

**Camera Resolution**:
- Preview: 1280x720 (720p) for performance
- Capture: Full camera resolution (e.g., 1920x1080 or higher)
- Thumbnails: 120x160 pixels

**Memory Management**:
- Base64 images stored in memory (each ~100-500 KB)
- 10 pages ≈ 1-5 MB memory usage
- Automatic cleanup on page navigation
- Optional: LocalStorage for crash recovery

**Network**:
- Upload compressed as JPEG (85% quality)
- Multi-part form data for multiple pages
- Progress indicator for large uploads
- Retry logic for network failures

---

## Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Camera permission denied | High | High | ✅ Clear instructions, fallback to file upload |
| Insufficient camera resolution | Medium | Medium | ✅ Detect resolution, warn user if too low |
| Memory issues with many pages | Low | Medium | ✅ Limit to 20 pages, compress images |
| Browser compatibility | Low | High | ✅ Feature detection, graceful degradation |
| Poor lighting conditions | High | Medium | ✅ Brightness/contrast controls, tips for users |
| Unsteady hand (blurry photos) | High | Medium | ✅ Auto-capture feature (US-005) helps stabilize |
| Large upload size | Medium | Low | ✅ JPEG compression, progress indicator |

---

## Related Specifications

**User Stories**:
- [US-005: Accessibility Camera Assistance](US-005-accessibility-camera-assistance.md) - Audio guidance and auto-capture

**Gherkin Features**:
- [Camera Tab](../features/gherkin-camera-tab.feature) (50+ scenarios)
- [Accessibility Camera Assistance](../features/gherkin-accessibility-camera-assistance.feature) (65 scenarios)

**Documentation**:
- [README.md](../../../README.md) - User guide with camera tab instructions
- [ACCESSIBILITY.md](../../ACCESSIBILITY.md) - Accessibility features overview
- [AGENTS.md](../../../AGENTS.md) - Development guidelines

**External Specs**:
- [MediaDevices.getUserMedia()](https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getUserMedia)
- [HTMLCanvasElement](https://developer.mozilla.org/en-US/docs/Web/API/HTMLCanvasElement)
- [FileReader API](https://developer.mozilla.org/en-US/docs/Web/API/FileReader)
- [Drag and Drop API](https://developer.mozilla.org/en-US/docs/Web/API/HTML_Drag_and_Drop_API)

---

## Change History

| Date | Version | Change | Commits |
|------|---------|--------|---------|
| 2025-12-30 | 1.0 | Initial camera tab implementation | Multiple commits |
| 2025-12-31 | 1.1 | Added accessibility features integration (US-005) | f523eee, ed0b81b |
| 2026-01-01 | 1.2 | iOS Safari fixes and auto-crop enhancement | 420d874, 1e07b3c, 2e10297 |
| 2026-01-01 | 2.0 | Retrospective user story documentation | 8dca73d |

---

**Feature Owner**: PDF/A Service Team
**Stakeholders**: All users (desktop, mobile, accessibility users)
**Priority**: High (Core Feature)
**Complexity**: Medium-High (Browser APIs, Multi-page workflow, Accessibility)
**Estimated Effort**: 8-12 days (already implemented)

---

## INVEST Check ✅

- ✅ **I**ndependent - Standalone camera interface, optional accessibility features
- ✅ **N**egotiable - Core capture works, editor features can be iterative
- ✅ **V**aluable - Enables document digitization without external tools
- ✅ **E**stimable - Clear scope, known browser APIs
- ✅ **S**mall - Implementable in 2 weeks
- ✅ **T**estable - Clear acceptance criteria, Gherkin scenarios available

---

## User Workflows

### Workflow 1: Quick Single-Page Scan
1. Open Camera tab
2. Point camera at document
3. Click Capture (or press Space)
4. Adjust rotation if needed
5. Click Accept
6. Click Convert
7. Download PDF/A

**Time**: ~30 seconds

### Workflow 2: Multi-Page Document
1. Open Camera tab
2. Capture page 1 → Accept
3. Capture page 2 → Accept
4. Capture page 3 → Accept
5. Review page thumbnails
6. Reorder if needed (drag & drop)
7. Click Convert
8. Download PDF/A

**Time**: ~2 minutes

### Workflow 3: Accessible Capture (Blind User)
1. Open Camera tab
2. Enable Accessibility Assistance (auto-detects screen reader)
3. Point camera at document (audio guidance: "Move closer...")
4. Audio feedback: "Document edges detected. Hold steady."
5. Auto-capture after 2 seconds
6. Auto-crop and perspective correction applied
7. Screen reader announces: "Photo captured. Page 1 added."
8. Repeat for additional pages
9. Screen reader navigates page list
10. Click Convert (keyboard: Enter)

**Time**: ~1 minute per page (hands-free)

---

## Future Enhancements (Out of Scope)

- **Batch Processing**: Upload and process multiple documents at once
- **Cloud Storage**: Save captured pages to cloud before conversion
- **Document Templates**: Pre-defined settings for invoices, receipts, etc.
- **Advanced Crop**: Manual crop selection (beyond auto-crop)
- **Filters**: Black & white, deskew, noise reduction
- **Offline Mode**: Cache captures for later upload
- **QR Code Detection**: Auto-extract metadata from QR codes
- **Multi-Camera Support**: Use front and rear camera simultaneously
