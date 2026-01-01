# language: en
Feature: Accessibility Camera Assistance for Blind Users
  As a blind or visually impaired user
  I want to photograph documents using audio guidance
  So that I can create high-quality document scans without visual control

  Background:
    Given the user opens the camera page
    And the browser supports Web Audio API
    And the browser supports getUserMedia

  # ============================================================================
  # Feature 1: Screen Reader Auto-Detection & Initialization
  # ============================================================================

  Scenario: Screen reader is automatically detected and feature enabled
    Given a screen reader is active (VoiceOver, NVDA, JAWS)
    When the camera page is loaded
    Then the Accessibility checkbox should be automatically enabled
    And audio guidance should be initialized
    And a voice announcement "Camera assistance enabled" should occur

  Scenario: No screen reader detected - feature remains disabled
    Given no screen reader is active
    When the camera page is loaded
    Then the Accessibility checkbox should remain disabled
    And no automatic initialization should occur

  Scenario: Manual activation without screen reader
    Given no screen reader is active
    And the Accessibility checkbox is disabled
    When the user enables the checkbox
    Then audio guidance should be initialized
    And a voice announcement "Camera assistance enabled" should occur

  # ============================================================================
  # Feature 2: iOS Safari Audio/TTS Unlock
  # ============================================================================

  Scenario: iOS Safari AudioContext unlock in user gesture
    Given the user is using iOS Safari
    And the Accessibility checkbox is disabled
    When the user enables the checkbox
    Then AudioContext should be created in direct user gesture
    And AudioContext should be immediately resumed
    And the AudioContext state should be "running"
    And no "AudioContext not available" error message should appear

  Scenario: iOS Safari SpeechSynthesis unlock
    Given the user is using iOS Safari
    And the Accessibility checkbox is disabled
    When the user enables the checkbox
    Then speechSynthesis.cancel() should be called
    And an empty SpeechSynthesisUtterance should be spoken
    And subsequent voice announcements should work

  Scenario: iOS Safari unlock tone is played
    Given the user is using iOS Safari
    And the Accessibility checkbox is disabled
    When the user enables the checkbox
    Then a brief unlock tone (440 Hz, 50ms) should be played
    And the audio pipeline should be unlocked

  Scenario: Immediate TTS announcement before library loading
    Given the user enables audio guidance
    When AudioContext unlock is complete
    Then "Camera assistance enabled" should be announced immediately
    And the announcement should occur BEFORE jscanify loading
    And the user should not wait for library download

  # ============================================================================
  # Feature 3: Page Reload AudioContext Handling
  # ============================================================================

  Scenario: AudioContext after page reload is closed
    Given the user had audio guidance enabled
    And the page is reloaded
    When the AudioContext state is "closed"
    Then a new AudioContext should be created
    And no "Audio system not available" error message should appear
    And audio guidance should work normally

  Scenario: AudioContext exists but is suspended
    Given the AudioContext exists but is suspended
    When the user enables audio guidance
    Then the existing AudioContext should be resumed
    And no new AudioContext should be created

  # ============================================================================
  # Feature 4: Edge Detection with jscanify
  # ============================================================================

  Scenario: jscanify loads successfully from CDN
    Given audio guidance is enabled
    When jscanify is loaded from CDN
    Then jscanify.Scanner should be initialized
    And degradedMode should be false
    And edge detection should be available

  Scenario: jscanify CDN failed - degraded mode
    Given audio guidance is enabled
    When all jscanify CDN URLs fail
    Then degradedMode should be set to true
    And a warning should be output to console
    And audio tones should still work
    But edge detection should not be available

  Scenario: OpenCV.js loads successfully
    Given audio guidance is enabled
    And jscanify is loaded
    When OpenCV.js is loaded from CDN
    Then window.cv should be available
    And cv.imread and cv.imshow should work

  Scenario: Edges are detected in real-time
    Given audio guidance is active
    And a document is in the camera view
    When analyzeFrame() runs
    Then jscanify.findPaperContour() should be called
    And result.success should be true
    And result.corners should contain 4 corners
    And each corner should have x and y coordinates

  # ============================================================================
  # Feature 5: Confidence Calculation with Partial Capture
  # ============================================================================

  Scenario: Document fills 40% of area - optimal confidence
    Given document edges are detected
    When the document fills 40% of canvas area
    Then confidence should be 1.0 (100%)

  Scenario: Document fills 33% of area - acceptable confidence
    Given document edges are detected
    When the document fills 33% of canvas area
    Then confidence should be > 0.5
    And auto-capture should be possible

  Scenario: Document fills 10% of area - minimum confidence
    Given document edges are detected
    When the document fills 10% of canvas area
    Then confidence should be ≈ 0.25
    And edge detection should work

  Scenario: Document fills 5% of area - too small
    Given a very small object is in the image
    When the object fills only 5% of canvas area
    Then confidence should be 0
    And no edge detection should occur

  Scenario: Document fills 95% of area - too close
    Given the document is too close to camera
    When the document fills 95% of canvas area
    Then confidence should be 0
    And "Move farther from document" should be announced

  # ============================================================================
  # Feature 6: Hysteresis to Prevent Flickering
  # ============================================================================

  Scenario: Confidence rises above upper threshold - transition to "detected"
    Given edgeState is "lost"
    And confidence is 0.30
    When confidence rises to 0.45
    Then edgeState should change to "detected"
    And a success tone (880 Hz) should be played
    And "Document edges detected" should be announced

  Scenario: Confidence fluctuates around 40% - stays "detected" (hysteresis)
    Given edgeState is "detected"
    And confidence is 0.45
    When confidence drops to 0.38 (between 35% and 45%)
    Then edgeState should remain "detected"
    And no state change should occur
    And no warning tone should be played

  Scenario: Confidence falls below lower threshold - transition to "lost"
    Given edgeState is "detected"
    And confidence is 0.38
    When confidence drops to 0.33
    Then edgeState should change to "lost"
    And a warning tone (440 Hz) should be played
    And "Edges lost. Adjust camera position." should be announced

  # ============================================================================
  # Feature 7: Audio Feedback (Tones + TTS)
  # ============================================================================

  Scenario: Success tone on edge detection
    Given edges are detected for the first time
    When edgeState changes to "detected"
    Then a success tone (880 Hz, 200ms) should be played

  Scenario: Warning tone on edges lost
    Given edgeState changes to "lost"
    When edges are lost
    Then a warning tone (440 Hz, 150ms) should be played

  Scenario: Continuous tone indicates confidence
    Given edgeState is "detected"
    And confidence is 0.8
    When continuous feedback runs
    Then tone pitch should be confidence-dependent (300-800 Hz)
    And higher confidence should produce higher pitch

  Scenario: TTS announcement is throttled
    Given an announcement was made 1 second ago
    When a new announcement is requested (priority != 'force')
    Then the announcement should be suppressed
    And announcementThrottle (2000ms) should be enforced

  Scenario: Force-priority announcement bypasses throttling
    Given an announcement was made 1 second ago
    When an announcement with priority='force' is requested
    Then the announcement should occur immediately
    And throttling should be bypassed

  # ============================================================================
  # Feature 8: Edge-Based Guidance (not directional)
  # ============================================================================

  Scenario: Top edge too close to frame edge
    Given edges are detected
    When a document corner has y < 20
    Then getMissingEdges() should return "Top edge"
    And "Top edge not visible" should be announced

  Scenario: Multiple edges not visible
    Given edges are detected
    When corners are at x < 20 and y > 460 (640x480 canvas)
    Then getMissingEdges() should return ["Left edge", "Bottom edge"]
    And "Left edge, Bottom edge not visible" should be announced

  Scenario: All edges visible - centered document
    Given edges are detected
    When all corners are > 20px from edge
    Then getMissingEdges() should return empty array
    And isDocumentCentered() should return true
    And no edge warnings should occur

  Scenario: Periodic guidance update (every 10 seconds)
    Given edges are detected but not centered
    And lastStatusTime was 11 seconds ago
    When provideFeedback() runs
    Then missing edges should be announced
    And lastStatusTime should be updated

  # ============================================================================
  # Feature 9: Auto-Capture on Stable Recognition
  # ============================================================================

  Scenario: Stability counter increments on good frame
    Given edgeState is "detected"
    And document is centered
    And auto-capture is enabled
    When a stable frame is detected
    Then stableFrameCount should increase by 1

  Scenario: Auto-capture countdown starts after 10 stable frames
    Given stableFrameCount reaches 10
    And auto-capture is enabled
    When the next stable frame occurs
    Then initiateAutoCapture() should be called
    And "Hold camera steady" should be announced
    And a 2-second countdown should start

  Scenario: Countdown announcements "2", "1"
    Given auto-capture countdown is running
    When each second passes
    Then a beep (523 Hz, 100ms) should be played
    And "2" or "1" should be announced

  Scenario: Photo taken after countdown
    Given countdown has elapsed
    When performAutoCapture() is executed
    Then a camera shutter tone should be played (880 Hz + 440 Hz)
    And "Photo captured" should be announced
    And cameraManager.capturePhoto() should be called

  Scenario: Auto-capture canceled on edge loss
    Given countdown is running
    When edges are lost (edgeState → "lost")
    Then cancelAutoCapture() should be called
    And countdown should be stopped
    And stableFrameCount should be reset to 0

  # ============================================================================
  # Feature 10: Auto-Crop and Perspective Correction
  # ============================================================================

  Scenario: lastDetectedCorners are stored during frame analysis
    Given analyzeFrame() detects edges
    When corners are extracted
    Then lastDetectedCorners should be updated
    And corners should be available for auto-crop

  Scenario: Auto-crop is applied when corners are available
    Given capturePhoto() is called
    And lastDetectedCorners is set
    And degradedMode is false
    When the photo is processed
    Then autoCropAndCorrect() should be called
    And corners should be scaled from analysis canvas to full resolution

  Scenario: Corner scaling from 640x480 to full resolution
    Given analysis canvas is 640x480
    And video resolution is 1920x1080
    When corners are {x: 320, y: 240}
    Then scaled corners should be {x: 960, y: 540} (3x factor)

  Scenario: OpenCV.js perspective correction
    Given autoCropAndCorrect() is running
    And scaled corners are calculated
    When cv.imread(canvas) is executed
    Then a cv.Mat should be created
    And scanner.extractPaper(mat, corners) should be called
    And a perspective-corrected Mat should be returned

  Scenario: Mat to Canvas conversion and cleanup
    Given extractPaper() returned corrected Mat
    When cv.imshow(outputCanvas, correctedMat) is executed
    Then outputCanvas should contain the corrected image
    And mat.delete() should be called (memory cleanup)
    And correctedImage.delete() should be called

  Scenario: High-quality JPEG for auto-crop images
    Given auto-crop was successful
    When outputCanvas.toDataURL() is called
    Then JPEG quality should be 90%
    And image should have higher quality than non-cropped (85%)

  Scenario: Fallback on auto-crop error
    Given autoCropAndCorrect() fails (exception)
    When an error occurs during perspective correction
    Then original canvas should be used
    And canvas.toDataURL('image/jpeg', 0.85) should be returned
    And error should be logged to console

  # ============================================================================
  # Feature 11: Multilingualism (i18n)
  # ============================================================================

  Scenario: German announcements
    Given window.currentLang is "de"
    When audio announcements are made
    Then announcements should be in German
    And "Oberer Rand nicht sichtbar" should be announced
    And speechSynthesis.lang should be "de-DE"

  Scenario: English announcements
    Given window.currentLang is "en"
    When audio announcements are made
    Then announcements should be in English
    And "Top edge not visible" should be announced
    And speechSynthesis.lang should be "en-US"

  Scenario: Spanish announcements
    Given window.currentLang is "es"
    When audio announcements are made
    Then announcements should be in Spanish
    And "Borde superior no visible" should be announced
    And speechSynthesis.lang should be "es-ES"

  Scenario: French announcements
    Given window.currentLang is "fr"
    When audio announcements are made
    Then announcements should be in French
    And "Bord supérieur non visible" should be announced
    And speechSynthesis.lang should be "fr-FR"

  # ============================================================================
  # Feature 12: Visual Indicators for Visually Impaired
  # ============================================================================

  Scenario: Green overlay on successful recognition
    Given edges are detected
    When showVisualIndicator('success') is called
    Then a green color overlay should be displayed
    And overlay should disappear after 500ms

  Scenario: Yellow overlay on warning
    Given edges are lost
    When showVisualIndicator('warning') is called
    Then a yellow color overlay should be displayed
    And overlay should disappear after 500ms

  # ============================================================================
  # Feature 13: ARIA Live Regions for Screen Readers
  # ============================================================================

  Scenario: ARIA Live Region is updated
    Given a screen reader is active
    When announce() is called
    Then <div id="srAnnouncements"> should be updated
    And screen reader should read text
    And aria-live="polite" should be enforced

  # ============================================================================
  # Feature 14: Volume Control
  # ============================================================================

  Scenario: Volume slider changes volume
    Given audio guidance is active
    When volume slider is set to 50%
    Then this.volume should be set to 0.5
    And GainNode.gain should be 0.5 * 0.3 (30% max for tones)
    And SpeechSynthesisUtterance.volume should be 0.5

  # ============================================================================
  # Feature 15: Test Audio Button
  # ============================================================================

  Scenario: Test audio plays tone and TTS
    Given audio guidance is active
    When "Test Audio" button is clicked
    Then testAudio() should be called
    And a success tone should be played
    And "Audio test. If you can hear this, audio is working." should be announced

  # ============================================================================
  # Feature 16: Disable Feature
  # ============================================================================

  Scenario: Audio guidance is disabled
    Given audio guidance is active
    When checkbox is disabled
    Then disable() should be called
    And analysisLoopId should be stopped (clearInterval)
    And "Camera assistance disabled" should be announced
    And enabled should be false

  Scenario: AudioContext is closed on disable
    Given audio guidance is active
    When disable() is called
    Then AudioContext.close() should be called
    And audioContext should be set to null

  # ============================================================================
  # Feature 17: Error Handling
  # ============================================================================

  Scenario: Browser does not support Web Audio API
    Given window.AudioContext is undefined
    When audio guidance is enabled
    Then an error should be thrown
    And "AudioContext not supported in this browser" should be the error message
    And checkbox should be disabled

  Scenario: getUserMedia failed
    Given camera permission is denied
    When camera access is requested
    Then CameraManager should throw an error
    But audio guidance should still be initializable

  Scenario: Canvas 2D Context error
    Given Canvas.getContext('2d') fails
    When analysis canvas is created
    Then an error should be thrown
    And "Failed to create canvas 2d context" should be the error message

  # ============================================================================
  # Feature 18: Performance & Memory
  # ============================================================================

  Scenario: Frame analysis runs at 10 FPS
    Given audio guidance is active
    When startAnalysis() is called
    Then analysisLoopId should have an interval of 100ms
    And analyzeFrame() should be called every 100ms

  Scenario: Analysis canvas is performance-optimized
    Given analyzeFrame() is running
    When video frame is drawn to canvas
    Then analysis canvas should be 640x480 pixels (not full resolution)
    And performance should be acceptable on older devices

  Scenario: Capture canvas uses full resolution for quality
    Given capturePhoto() is called
    When video frame is captured
    Then capture canvas should be video.videoWidth × video.videoHeight
    And maximum quality should be ensured

  Scenario: OpenCV Mat is explicitly freed
    Given autoCropAndCorrect() is called
    When cv.Mat objects are created
    Then mat.delete() should be called in finally block
    And correctedImage.delete() should also be called
    And no memory leaks should occur
