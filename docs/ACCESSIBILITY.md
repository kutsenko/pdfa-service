# Accessibility: Audio-Guided Document Scanning

The camera tab includes audio guidance to help blind and low-vision users scan documents independently using real-time edge detection and voice feedback.

## Features

- **Automatic Screen Reader Detection**: Auto-enables when screen readers (NVDA, JAWS, VoiceOver) are detected
- **Real-Time Edge Detection**: Uses [jscanify](https://github.com/puffinsoft/jscanify) to detect document edges in live camera feed
- **Audio Feedback**:
  - 🎵 **Ascending tones** when document edges are detected
  - 🎵 **Descending tones** when edges are lost
  - 🎵 **Continuous feedback** tone varies with detection confidence
  - 🔊 **Voice announcements** for status and positional guidance
- **Auto-Capture**: Automatically captures photo after 2-second countdown when document is centered
- **Positional Guidance**: Voice instructions like "Move camera left", "Move closer to document"
- **Multi-Language Support**: Voice announcements in English, German, Spanish, and French
- **Customizable**:
  - Volume control (0-100%)
  - Enable/disable auto-capture
  - Test audio button
- **Visual Indicators**: Complementary visual feedback for low-vision users

## How to Use

1. **Open Camera Tab** in the Web UI
2. **Click "Start Camera"** and grant permission
3. **Enable "Accessibility Assistance"** (or let it auto-enable with screen reader)
4. **Point camera at document** (A4/Letter paper)
5. **Listen for ascending tones** = edges detected
6. **Adjust position** based on voice guidance ("Move left", "Move up", etc.)
7. **Hold steady** when centered = auto-capture countdown begins
8. **Hear "Photo captured"** = page added to staging area
9. **Repeat** for multi-page documents
10. **Click "Convert to PDF/A"** when done

## Technical Details

- **Edge Detection**: jscanify library (~200 KB), processes frames at 10 FPS
- **Audio Engine**: Web Audio API for tone generation
- **Voice Synthesis**: Web Speech API with language auto-detection
- **Performance**: <200ms latency from detection to audio feedback
- **Compatibility**: Chrome 90+, Firefox 88+, Safari 14+ (iOS/macOS)
- **WCAG Compliance**: WCAG 2.1 AAA compliant

## Browser Requirements

| Browser | Edge Detection | Audio Tones | Voice | Status |
|---------|---------------|-------------|-------|--------|
| Chrome 90+ (Desktop/Android) | ✅ | ✅ | ✅ | Full support |
| Edge 90+ | ✅ | ✅ | ✅ | Full support |
| Firefox 88+ | ✅ | ✅ | ✅ | Full support |
| Safari 14+ (macOS/iOS) | ✅ | ✅ | ✅ | Full support |

**Note**: iOS Safari requires HTTPS for camera access. Use `ngrok` or similar for testing on mobile devices.

## Supported Languages

Voice announcements are available in:
- 🇬🇧 English (en-US)
- 🇩🇪 German (de-DE)
- 🇪🇸 Spanish (es-ES)
- 🇫🇷 French (fr-FR)

The system automatically selects the voice language based on your UI language preference.

## Troubleshooting

**Problem**: No audio feedback
- **Solution**: Check volume slider (should be >0%), click "Test Audio" button
- **Solution**: Verify browser supports Web Audio API and Web Speech API

**Problem**: Camera permission denied
- **Solution**: Grant camera permission in browser settings
- **Solution**: On iOS, ensure you're using HTTPS (not HTTP)

**Problem**: Edge detection not working
- **Solution**: Ensure good lighting and white/light-colored background
- **Solution**: Hold document flat and fill 20-80% of camera view
- **Solution**: Use A4, Letter, or similarly sized paper

**Problem**: Auto-capture not triggering
- **Solution**: Center the document in the camera view
- **Solution**: Hold steady for at least 1 second
- **Solution**: Check that "Enable automatic capture" is checked

For more details, see E2E test documentation at `tests/e2e/ACCESSIBILITY_TEST_STATUS.md`.

---

# Accessibility: QR Code Pairing (Keyboard Navigation)

The QR code pairing UI has been made fully accessible for blind users and keyboard navigation.

## Features

### 1. **Keyboard Navigation** (WCAG 2.1.1)

- QR code element is keyboard-focusable with `tabindex="0"`
- Users can Tab through the pairing UI
- Sequential navigation works correctly

### 2. **Visible Focus Indicator** (WCAG 2.4.7)

- **3px outline** in brand color (#667eea)
- **4px offset** for clear visibility
- **Rounded corners** (4px border-radius)
- **Subtle glow** effect with box-shadow

```css
.qr-container canvas:focus,
.qr-container img:focus {
    outline: 3px solid #667eea;
    outline-offset: 4px;
    border-radius: 4px;
    box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.1);
}
```

### 3. **Screen Reader Support** (WCAG 4.1.2)

- `role="img"` identifies QR code as an image
- `aria-label` provides descriptive text with pairing code
- `title` attribute for tooltip on hover

**What Screen Readers Announce:**
> "QR code for mobile pairing. Pairing code: A-B-C-1-2-3. Scan this QR code with your mobile device or manually enter the pairing code."

### 4. **Text Alternative**

The pairing code is also displayed as large, high-contrast text:
- **Large font** (32px, monospace)
- **Letter-spaced** (4px) for clarity
- **Copyable** text
- **Screen reader accessible**

## How to Use (Keyboard Users)

1. **Navigate to Camera Tab**
   - Press `Tab` until "Camera" tab is focused
   - Press `Enter` to activate

2. **Start Pairing**
   - Press `Tab` until "Start Mobile Pairing" button is focused
   - Press `Enter` to start

3. **Access QR Code**
   - Press `Tab` to move through pairing UI
   - When QR code is focused, visible outline appears
   - Screen reader announces pairing code and instructions

4. **Use Pairing Code**
   - Tab to pairing code text
   - Read or copy the code
   - Manually enter on mobile device

## WCAG 2.1 Level AA Compliance

| Criterion | Level | Status | Implementation |
|-----------|-------|--------|----------------|
| 2.1.1 Keyboard | A | ✅ Pass | tabindex="0" on QR element |
| 2.4.7 Focus Visible | AA | ✅ Pass | 3px outline with 4px offset |
| 4.1.2 Name, Role, Value | A | ✅ Pass | role="img" + aria-label |
| 1.1.1 Non-text Content | A | ✅ Pass | Text alternative provided |
| 1.4.3 Contrast (Minimum) | AA | ✅ Pass | 3:1 ratio for focus indicator |

## Implementation

**Files Modified:**
- `src/pdfa/static/js/camera/MobilePairingManager.js:153-174`
- `src/pdfa/static/css/camera.css:255-262`

**Test Coverage:**
- `tests/unit/test_qr_accessibility.py` - Documentation tests

**Commit:**
- `efdbe2c` - feat(a11y): Make QR code keyboard navigable for screen readers
