# User Story: Accessibility Camera Assistance for Blind Users

**ID**: US-008
**Title**: Audio-Guided Document Capture with Automatic Edge Detection
**Status**: ✅ Implemented
**Date**: 2026-01-01

---

## Story

**As** a blind or visually impaired user
**I want** to photograph documents using audio guidance
**so that** I can create high-quality document scans without visual control, with automatic cropping and perspective correction.

---

## Context

**Current State (before Accessibility Feature)**:
- Camera interface only visually operable
- No audio feedback for document positioning
- Manual centering and alignment required
- No support for screen readers
- Blind users cannot use the service

**Problem**:
- Accessibility is legally required (WCAG 2.1 Level AA)
- Blind users cannot digitize documents
- No audio feedback for camera alignment
- Manual perspective correction impossible for visually impaired

**Solution**:
- Real-time edge detection with jscanify v1.4.0 and OpenCV.js 4.7.0
- Audio feedback via Web Audio API (tones) and Speech Synthesis API (voice announcements)
- Automatic triggering when stable document recognition achieved
- Automatic cropping and perspective correction
- iOS Safari compatibility (special handling)
- Multilingual (de, en, es, fr)

---

## Acceptance Criteria

### 1. Screen Reader Auto-Detection
- **Given** a user opens the camera page
- **When** a screen reader is active (e.g., VoiceOver, NVDA, JAWS)
- **Then** the Accessibility Assistance should be automatically enabled
- **And** a voice announcement "Camera assistance enabled" should occur

### 2. Audio Unlock for iOS Safari
- **Given** a user enables audio guidance on iOS Safari
- **When** the checkbox is clicked
- **Then** AudioContext should be created and resumed in user gesture
- **And** speechSynthesis should be "unlocked" with empty utterance
- **And** a brief unlock tone should be played
- **And** "Camera assistance enabled" should be announced immediately

### 3. Real-time Edge Detection with Audio Feedback
- **Given** the camera is running and audio guidance is active
- **When** a document comes into view
- **Then** jscanify should detect edges in real-time
- **And** a success tone should be played
- **And** "Document edges detected. Hold steady." should be announced
- **And** a continuous tone should indicate confidence level (higher pitch = better recognition)

### 4. Edge-Based Guidance (not directional)
- **Given** document edges are detected but not optimally positioned
- **When** document corners are too close to frame edge
- **Then** which edges are not visible should be announced
- **And** should say e.g., "Top edge not visible" instead of "Move camera down"
- **And** should list all missing edges (e.g., "Top edge, Left edge not visible")

### 5. Automatic Capture on Stable Recognition
- **Given** document edges are detected and centered
- **When** recognition remains stable for 10 frames (~1 second)
- **Then** a countdown should start ("2", "1")
- **And** should automatically capture after 2 seconds
- **And** "Photo captured" should be announced
- **And** a camera shutter sound should be played

### 6. Auto-Crop and Perspective Correction
- **Given** a photo was captured and edges were detected
- **When** the photo is processed
- **Then** the image should be cropped to detected edges
- **And** perspective should be corrected (jscanify.extractPaper)
- **And** should be high resolution (full videoWidth/videoHeight)
- **And** should be saved at 90% JPEG quality

### 7. Partial Document Recognition (1/3 of area)
- **Given** a document fills only 33% of the image
- **When** edge detection runs
- **Then** the document should still be recognized (Threshold: 10-90%)
- **And** auto-capture should be possible
- **And** auto-crop should work

### 8. Hysteresis to Prevent Flickering
- **Given** confidence fluctuates around threshold
- **When** edges are detected/lost
- **Then** hysteresis should be used (Upper: 45%, Lower: 35%)
- **And** should not switch between "detected" and "lost" every frame
- **And** should only make announcements on significant changes

### 9. Page Reload Compatibility
- **Given** a user reloads the page
- **When** AudioContext from previous session exists but is closed
- **Then** a new AudioContext should be created
- **And** no "Audio system not available" error message should appear
- **And** audio guidance should work normally

### 10. Multilingualism (i18n)
- **Given** a user selects a language (de, en, es, fr)
- **When** audio announcements are made
- **Then** all announcements should be in the selected language
- **And** edge names should be translated ("Top edge" / "Oberer Rand" / "Borde superior" / "Bord supérieur")

---

## Definition of Done

- [x] jscanify v1.4.0 and OpenCV.js 4.7.0 loaded via CDN
- [x] AccessibleCameraAssistant class implemented
- [x] Screen Reader Auto-Detection (ARIA landmarks)
- [x] iOS Safari AudioContext + SpeechSynthesis Unlock
- [x] On-Demand Oscillator Pattern for iOS
- [x] Edge Detection with Hysteresis (45%/35% thresholds)
- [x] Auto-Capture after 10 stable frames
- [x] Auto-Crop with perspective correction
- [x] Edge-Based Guidance (not directional)
- [x] Confidence-based continuous tone
- [x] Partial document recognition (10-90% area)
- [x] Page Reload AudioContext handling
- [x] i18n for 4 languages (de, en, es, fr)
- [x] All translation keys documented
- [x] Volume control and test audio button
- [x] Visual indicators for visually impaired (color overlay)
- [x] ARIA Live Regions for screen readers
- [x] Gherkin Feature with scenarios created
- [x] User Story documented

---

## Technical Details

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    CameraManager                             │
│  ┌────────────────────────────────────────────────────┐    │
│  │  AccessibleCameraAssistant                          │    │
│  │  ┌────────────┬──────────────┬──────────────────┐ │    │
│  │  │ Audio      │ Edge         │ Auto-Capture     │ │    │
│  │  │ System     │ Detection    │ & Auto-Crop      │ │    │
│  │  └────────────┴──────────────┴──────────────────┘ │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
         │                  │                    │
         ▼                  ▼                    ▼
┌──────────────┐  ┌──────────────┐   ┌──────────────┐
│ Web Audio    │  │ jscanify     │   │ OpenCV.js    │
│ API +        │  │ v1.4.0       │   │ 4.7.0        │
│ Speech       │  │              │   │              │
│ Synthesis    │  │ getEdges()   │   │ cv.imread()  │
│              │  │ extractPaper │   │ cv.imshow()  │
└──────────────┘  └──────────────┘   └──────────────┘
```

### Components

#### AccessibleCameraAssistant Class
**File**: `src/pdfa/web_ui.html` (lines 9300-10700)

**Properties**:
- `audioContext: AudioContext` - Web Audio API context
- `synth: SpeechSynthesis` - Browser TTS engine
- `scanner: jscanify.Scanner` - Edge detection library
- `analysisCanvas: HTMLCanvasElement` - 640x480 analysis canvas
- `lastDetectedCorners` - Stored corners for auto-crop
- `edgeState: 'detected' | 'lost'` - Hysteresis state
- `stableFrameCount: number` - Counter for auto-capture
- `degradedMode: boolean` - Fallback if jscanify fails

**Methods**:
```javascript
// Initialization
async init()
async enable()
disable()
setupControls()

// Audio System
async playTone(frequency, duration)
playSuccessTone()
playWarningTone()
playContinuousFeedbackTone(confidence)
announce(text, priority)

// Edge Detection
async analyzeFrame()
calculateConfidence(result)
provideFeedback(confidence, result)
getMissingEdges(result)
isDocumentCentered(result)

// Auto-Capture
initiateAutoCapture()
performAutoCapture()
cancelAutoCapture()

// Auto-Crop
autoCropAndCorrect(canvas, corners) // in CameraManager
```

### Audio System

#### Tones (Web Audio API)
```javascript
Success: 880 Hz, 200ms (A5 - edges detected)
Warning: 440 Hz, 150ms (A4 - edges lost)
Continuous: 300-800 Hz (confidence-dependent)
Countdown: 523 Hz, 100ms (C5 - "2", "1")
Shutter: 880 Hz + 440 Hz (camera shutter)
```

#### iOS Safari Special Handling
1. **AudioContext**: Must be created and resumed in direct user gesture
2. **SpeechSynthesis**: Must be "unlocked" with empty utterance
3. **On-Demand Oscillators**: Each tone creates own oscillator (not persistent)
4. **State Handling**: Check for `state === 'closed'` on page reload

### Edge Detection

#### jscanify Integration
```javascript
// Load from CDN with fallbacks
https://cdn.jsdelivr.net/npm/jscanify@1.4.0/dist/jscanify.min.js
https://unpkg.com/jscanify@1.4.0/dist/jscanify.min.js

// Initialize scanner
const scanner = new jscanify();

// Detect edges
const result = scanner.findPaperContour(imageData);
// result.success: boolean
// result.corners: Array<{x, y}> (4 corners)

// Perspective correction
const corrected = scanner.extractPaper(mat, corners);
```

#### OpenCV.js Integration
```javascript
// Canvas to Mat conversion
const mat = cv.imread(canvas);

// Mat to Canvas conversion
cv.imshow(outputCanvas, mat);

// Cleanup (Memory Management)
mat.delete();
correctedImage.delete();
```

### Confidence Calculation

```javascript
function calculateConfidence(corners) {
  const area = calculatePolygonArea(corners);
  const areaRatio = area / canvasArea;

  // Accept 10-90% coverage (tolerant for partial capture)
  if (areaRatio < 0.10 || areaRatio > 0.90) return 0;

  // Peak at 40% (realistic for well-centered)
  if (areaRatio <= 0.40) {
    // Linear from 0.25 (at 10%) to 1.0 (at 40%)
    return 0.25 + (areaRatio - 0.10) * (0.75 / 0.30);
  } else {
    // Linear from 1.0 (at 40%) to 0.5 (at 90%)
    return 1.0 - (areaRatio - 0.40) * (0.5 / 0.50);
  }
}
```

### Hysteresis Pattern

```javascript
const upperThreshold = 0.45; // Threshold for lost → detected
const lowerThreshold = 0.35; // Threshold for detected → lost

const isDetected = wasDetected
  ? confidence >= lowerThreshold  // Stay detected until < 35%
  : confidence >= upperThreshold;  // Become detected at >= 45%
```

### Auto-Crop Workflow

```
1. Video Frame → Full Resolution Canvas (videoWidth × videoHeight)
2. Check: Are corners stored? (lastDetectedCorners)
3. Scale corners: Analysis Canvas (640×480) → Full Resolution
4. cv.imread(canvas) → Mat
5. scanner.extractPaper(mat, scaledCorners) → Corrected Mat
6. cv.imshow(outputCanvas, correctedMat) → Canvas
7. canvas.toDataURL('image/jpeg', 0.90) → High-Quality JPEG
8. mat.delete(), correctedMat.delete() → Cleanup
```

### i18n Translations

**New Keys (US-008)**:
```javascript
'camera.a11y.topEdge': 'Top edge' / 'Oberer Rand' / ...
'camera.a11y.bottomEdge': 'Bottom edge' / 'Unterer Rand' / ...
'camera.a11y.leftEdge': 'Left edge' / 'Linker Rand' / ...
'camera.a11y.rightEdge': 'Right edge' / 'Rechter Rand' / ...
'camera.a11y.notVisible': 'not visible' / 'nicht sichtbar' / ...
```

**Existing Keys**:
```javascript
'camera.a11y.enabled': 'Camera assistance enabled'
'camera.a11y.edgesDetected': 'Document edges detected. Hold steady.'
'camera.a11y.edgesLost': 'Edges lost. Adjust camera position.'
'camera.a11y.moveCloser': 'Move closer to document'
'camera.a11y.moveFarther': 'Move farther from document'
'camera.a11y.centerDocument': 'Center the document'
'camera.a11y.holdSteady': 'Hold camera steady'
'camera.a11y.photoCaptured': 'Photo captured'
```

### Deployment

**Client-Side Only** (no backend required):
- Feature activates on screen reader detection
- All libraries loaded via CDN (jscanify, OpenCV.js)
- Browser Requirements:
  - Web Audio API Support
  - Speech Synthesis API Support (optional, degrades gracefully)
  - getUserMedia() for camera
  - Canvas 2D Context
  - ES6+ JavaScript

**Performance**:
- Frame Analysis: ~10 FPS (100ms interval)
- Analysis Canvas: 640×480 (performance-optimized)
- Capture Canvas: Full videoWidth/videoHeight (quality-optimized)
- Memory Management: All cv.Mat explicitly freed with .delete()

---

## Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| iOS Safari blocks audio | Medium | High | ✅ AudioContext + SpeechSynthesis unlock in user gesture |
| jscanify CDN unreachable | Low | High | ✅ Degraded mode: Audio without edge detection |
| False edge detection | Medium | Medium | ✅ Confidence threshold + hysteresis + manual correction possible |
| OpenCV.js too large (8MB) | Low | Low | ✅ Lazy loading only when feature enabled |
| Screen reader interference | Medium | Medium | ✅ ARIA Live Regions + throttled announcements |
| Battery drain (continuous analysis) | Low | Low | ✅ 10 FPS instead of 30 FPS, analysis canvas 640×480 |
| Memory leaks (cv.Mat) | Medium | High | ✅ Explicit .delete() in try-finally blocks |

---

## Related Specifications

**User Stories**:
- None (standalone feature)

**Gherkin Features**:
- [Accessibility Camera Assistance](../features/gherkin-accessibility-camera-assistance.feature) (65 scenarios)

**Documentation**:
- [ACCESSIBILITY.md](../../ACCESSIBILITY.md)
- [AGENTS.md](../../../AGENTS.md)
- [TRANSLATIONS.md](../../../TRANSLATIONS.md)

**External Specs**:
- [WCAG 2.1 Level AA](https://www.w3.org/WAI/WCAG21/quickref/)
- [ARIA 1.2](https://www.w3.org/TR/wai-aria-1.2/)
- [Web Audio API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Audio_API)
- [Speech Synthesis API](https://developer.mozilla.org/en-US/docs/Web/API/SpeechSynthesis)
- [jscanify Documentation](https://www.npmjs.com/package/jscanify)
- [OpenCV.js Documentation](https://docs.opencv.org/4.7.0/d5/d10/tutorial_js_root.html)

---

## Change History

| Date | Version | Change | Commits |
|------|---------|--------|---------|
| 2026-01-01 | 1.0 | Initial creation after full implementation | 2e10297, 1e07b3c, 420d874, f523eee, ed0b81b |
| 2026-01-01 | 1.0 | iOS Safari TTS fix, partial document support, edge-based guidance | 2e10297 |
| 2026-01-01 | 1.0 | iOS audio fix, instant TTS feedback, auto-crop feature | 1e07b3c |
| 2025-12-31 | 1.0 | iOS Safari audio tones fix (on-demand oscillators) | 420d874 |
| 2025-12-31 | 1.0 | Hysteresis and contextual feedback for edge detection | f523eee |
| 2025-12-31 | 1.0 | i18n translations and auto-capture corner validation | ed0b81b |

---

**Feature Owner**: PDF/A Service Team
**Stakeholders**: Blind and visually impaired users, Compliance Team
**Priority**: High (Legal Requirement - WCAG 2.1 AA)
**Complexity**: High (Audio APIs, Computer Vision, iOS Quirks)
**Estimated Effort**: 5-8 days (already implemented)

---

## INVEST Check ✅

- ✅ **I**ndependent - Standalone feature, no dependencies on other stories
- ✅ **N**egotiable - Core features fixed, UX details iteratively improved
- ✅ **V**aluable - Enables new user segment (blind users) to use service
- ✅ **E**stimable - Clearly defined scope, known technology
- ✅ **S**mall - Implementable in one iteration (5-8 days)
- ✅ **T**estable - Clear acceptance criteria, Gherkin scenarios available
