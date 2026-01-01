# language: en
Feature: Camera Tab for Multi-Page Document Capture
  As a user of the PDF/A service
  I want to capture multi-page documents using my device's camera directly in the browser
  So that I can create searchable PDF/A documents without needing a physical scanner

  Background:
    Given the user opens the Camera tab
    And the browser supports getUserMedia API
    And the browser supports Canvas API

  # ============================================================================
  # Feature 1: Camera Access and Preview
  # ============================================================================

  Scenario: Camera permission is requested on page load
    Given the Camera tab is opened
    When the page loads
    Then browser should request camera permission
    And permission prompt should be displayed

  Scenario: Camera preview displays after permission granted
    Given camera permission is granted
    When getUserMedia() succeeds
    Then live camera preview should be displayed
    And video element should show camera feed
    And preview should be responsive to screen size

  Scenario: Rear camera is selected by default on mobile
    Given the user is on a mobile device
    And device has multiple cameras
    When camera is initialized
    Then rear camera (environment-facing) should be selected
    And facingMode should be "environment"

  Scenario: Camera selection dropdown shows available cameras
    Given device has multiple cameras
    When camera initializes
    Then camera selection dropdown should be populated
    And dropdown should list all available cameras
    And each camera should have a descriptive label

  Scenario: User can switch between cameras
    Given camera preview is active
    And device has multiple cameras
    When user selects a different camera from dropdown
    Then camera stream should switch to selected device
    And preview should continue without page reload
    And selected camera ID should be stored in localStorage

  Scenario: Camera permission denied shows error message
    Given the Camera tab is opened
    When user denies camera permission
    Then error message should be displayed
    And message should say "Camera permission denied"
    And instructions to enable permission should be shown
    And application should not crash

  Scenario: No camera available shows fallback message
    Given the user's device has no camera
    When Camera tab loads
    Then error message should be displayed
    And message should suggest using file upload instead
    And file upload tab should remain accessible

  # ============================================================================
  # Feature 2: Photo Capture
  # ============================================================================

  Scenario: Capture button triggers photo capture
    Given camera preview is active
    When user clicks the Capture button
    Then current video frame should be captured
    And image should be at full camera resolution
    And captured image should be stored in memory

  Scenario: Space bar triggers photo capture
    Given camera preview is active
    When user presses Space bar
    Then current video frame should be captured
    And photo editor should open with captured image

  Scenario: Full camera resolution is used for capture
    Given camera preview is 1280x720 (720p)
    And camera supports 1920x1080 (1080p)
    When photo is captured
    Then capture canvas should be 1920x1080
    And image quality should be maximized
    And preview resolution should not limit capture quality

  Scenario: Camera shutter sound plays on capture
    Given camera preview is active
    When user captures a photo
    Then camera shutter sound should be played
    And sound should be audible to user

  Scenario: Photo editor opens after capture
    Given camera preview is active
    When photo is captured
    Then photo editor should open
    And captured photo should be displayed full-size
    And editor controls should be visible

  Scenario: Capture works in both portrait and landscape
    Given camera preview is active
    When device is in portrait orientation
    And user captures a photo
    Then photo should be captured correctly
    And when device is rotated to landscape
    And user captures another photo
    Then second photo should also be captured correctly

  # ============================================================================
  # Feature 3: Photo Editor
  # ============================================================================

  Scenario: Photo editor displays captured image
    Given a photo was captured
    When photo editor opens
    Then captured image should be displayed
    And image should be centered in editor
    And image should fit viewport

  Scenario: Rotate left button rotates image 90° counter-clockwise
    Given photo editor is open
    When user clicks "Rotate Left" button
    Then image should rotate 90° counter-clockwise
    And rotation should apply immediately
    And rotation should be reflected in preview

  Scenario: Rotate right button rotates image 90° clockwise
    Given photo editor is open
    When user clicks "Rotate Right" button
    Then image should rotate 90° clockwise
    And rotation should apply immediately

  Scenario: Multiple rotations accumulate correctly
    Given photo editor is open
    When user clicks "Rotate Right" 3 times
    Then image should be rotated 270° clockwise (or 90° counter-clockwise)
    And rotation should wrap at 360°

  Scenario: Brightness slider adjusts image brightness
    Given photo editor is open
    When user moves brightness slider to +50
    Then image brightness should increase
    And adjustment should apply in real-time
    And canvas filter should use brightness(150%)

  Scenario: Contrast slider adjusts image contrast
    Given photo editor is open
    When user moves contrast slider to +30
    Then image contrast should increase
    And adjustment should apply in real-time
    And canvas filter should use contrast(130%)

  Scenario: Multiple adjustments combine correctly
    Given photo editor is open
    When user sets brightness to +20
    And user sets contrast to +40
    And user rotates right once
    Then all adjustments should be visible
    And adjustments should not interfere with each other

  Scenario: Accept button saves edited photo
    Given photo editor is open
    And user has made adjustments
    When user clicks "Accept" button
    Then photo should be added to page list
    And editor should close
    And user should return to camera preview

  Scenario: Retake button discards photo and returns to camera
    Given photo editor is open
    When user clicks "Retake" button
    Then current photo should be discarded
    And editor should close
    And camera preview should be active again

  Scenario: Escape key closes editor (retake)
    Given photo editor is open
    When user presses Escape key
    Then editor should close
    And photo should be discarded
    And camera preview should resume

  # ============================================================================
  # Feature 4: Multi-Page Support
  # ============================================================================

  Scenario: First accepted photo is added as page 1
    Given user captures and accepts first photo
    When photo is accepted
    Then page should be added to page list
    And page counter should show "Page 1/1"
    And thumbnail should be generated and displayed

  Scenario: Second accepted photo is added as page 2
    Given user has already captured page 1
    When user captures and accepts second photo
    Then page should be added as page 2
    And page counter should show "Page 2/2"
    And both thumbnails should be visible

  Scenario: Page counter updates with each new page
    Given user has captured 3 pages
    When user captures and accepts page 4
    Then page counter should show "Page 4/4"
    And all 4 thumbnails should be displayed

  Scenario: Thumbnail shows preview of captured page
    Given user has captured a page
    When thumbnail is generated
    Then thumbnail should show miniature version of photo
    And thumbnail should be 120x160 pixels
    And thumbnail should reflect rotation and adjustments

  Scenario: Unlimited pages can be captured (memory permitting)
    Given user has captured 10 pages
    When user captures page 11
    Then page 11 should be added successfully
    And no artificial page limit should be enforced
    And memory usage should be reasonable (~100-500 KB per page)

  Scenario: Camera preview remains active between captures
    Given user captures and accepts page 1
    When editor closes
    Then camera preview should immediately resume
    And user can capture page 2 without restarting camera

  Scenario: Convert button is disabled with no pages
    Given user has not captured any pages
    When Camera tab loads
    Then Convert button should be disabled
    And button should have visual indication of disabled state

  Scenario: Convert button is enabled with at least one page
    Given user has captured and accepted one page
    When page is added to list
    Then Convert button should be enabled
    And button should be clickable

  # ============================================================================
  # Feature 5: Page Management
  # ============================================================================

  Scenario: User can reorder pages by drag and drop
    Given user has captured 3 pages
    When user drags page 3 to position 1
    Then page order should update to [old-page-3, old-page-1, old-page-2]
    And thumbnails should reorder visually
    And page counter should reflect new order

  Scenario: Delete button removes individual page
    Given user has captured 3 pages
    When user clicks delete button on page 2
    Then page 2 should be removed from list
    And page counter should show "Page 2/2"
    And remaining pages should be [page-1, page-3]

  Scenario: Deleting all pages disables Convert button
    Given user has captured 1 page
    When user deletes the only page
    Then page list should be empty
    And Convert button should be disabled
    And page counter should not be visible

  Scenario: Retake button on page opens editor
    Given user has captured 2 pages
    When user clicks "Retake" button on page 1
    Then page 1 image should open in editor
    And user can make new adjustments
    And changes should update page 1 in list

  Scenario: Thumbnails update immediately after reorder
    Given user has 4 pages with distinct content
    When user drags page 4 to position 1
    Then thumbnails should reorder without delay
    And visual order should match data order

  Scenario: Page numbers update after deletion
    Given user has pages [1, 2, 3, 4, 5]
    When user deletes page 2
    Then page counter should show "Page 4/4"
    And old page 3 should become page 2
    And numbering should be sequential

  # ============================================================================
  # Feature 6: Document Submission
  # ============================================================================

  Scenario: Single page submission to conversion API
    Given user has captured 1 page
    When user clicks Convert button
    Then FormData should contain 1 file
    And POST request should be sent to /convert
    And file should be JPEG format
    And selected PDF/A level should be included

  Scenario: Multi-page submission combines all pages
    Given user has captured 3 pages
    When user clicks Convert button
    Then FormData should contain 3 files
    And all files should be sent in single request
    And backend should concatenate into single PDF

  Scenario: Progress indicator shows during upload
    Given user has captured 5 pages
    When user clicks Convert button
    Then progress indicator should be displayed
    And indicator should show upload progress
    And user should not be able to capture more pages during upload

  Scenario: PDF/A settings are applied to camera captures
    Given user has selected PDF/A Level 2
    And OCR is enabled
    When user submits camera-captured pages
    Then pdfa_level should be "2" in request
    And ocr_enabled should be true
    And backend should apply settings to result

  Scenario: Compression profile is configurable
    Given user has selected "quality" compression profile
    When user submits pages
    Then compression_profile should be "quality" in request
    And backend should use quality-optimized settings

  Scenario: Successful conversion shows download link
    Given user submits pages
    When conversion succeeds
    Then download link should be displayed
    And user can download resulting PDF/A file
    And page list should be cleared (optional)

  Scenario: Conversion error shows error message
    Given user submits pages
    When conversion fails (e.g., server error)
    Then error message should be displayed
    And error details should be shown to user
    And pages should remain in list for retry

  Scenario: Network failure is handled gracefully
    Given user submits pages
    When network request fails (no connection)
    Then error message should indicate network issue
    And user should be prompted to retry
    And pages should not be lost

  # ============================================================================
  # Feature 7: Accessibility Integration (US-008)
  # ============================================================================

  Scenario: Accessibility assistance checkbox is visible
    Given Camera tab is open
    When page loads
    Then accessibility assistance checkbox should be visible
    And checkbox should have clear label
    And label should describe audio guidance feature

  Scenario: Screen reader auto-enables accessibility features
    Given user has screen reader active (VoiceOver, NVDA, JAWS)
    When Camera tab loads
    Then accessibility checkbox should be automatically checked
    And audio guidance should initialize
    And "Camera assistance enabled" should be announced

  Scenario: Manual activation enables audio guidance
    Given no screen reader is active
    When user manually checks accessibility checkbox
    Then audio guidance should initialize
    And jscanify edge detection should start
    And audio tones should be enabled

  Scenario: Auto-capture works with accessibility mode
    Given accessibility assistance is enabled
    And document edges are detected
    When document is stable for 10 frames
    Then countdown should start ("2", "1")
    And photo should auto-capture after countdown
    And "Photo captured" should be announced

  Scenario: Auto-crop applies to accessibility captures
    Given accessibility assistance enabled
    And document edges were detected
    When auto-capture occurs
    Then photo should be auto-cropped to detected edges
    And perspective correction should be applied
    And resulting image should be high quality (90% JPEG)

  Scenario: Accessibility features work across multiple pages
    Given accessibility assistance enabled
    When user captures page 1 with auto-capture
    And user captures page 2 with auto-capture
    Then both pages should have auto-crop applied
    And audio guidance should announce page numbers
    And user can build multi-page document hands-free

  # ============================================================================
  # Feature 8: Camera Settings
  # ============================================================================

  Scenario: Camera preference is persisted in localStorage
    Given user selects rear camera
    When camera is switched
    Then camera ID should be saved to localStorage
    And on next visit, rear camera should be preselected

  Scenario: Camera switches without page reload
    Given camera preview is active with front camera
    When user selects rear camera
    Then stream should switch seamlessly
    And video preview should continue without interruption
    And no page reload should occur

  Scenario: Camera preference survives page reload
    Given user selected rear camera in previous session
    When user reopens Camera tab
    Then rear camera should be selected by default
    And user preference should be respected

  # ============================================================================
  # Feature 9: Error Handling
  # ============================================================================

  Scenario: Camera permission error provides helpful instructions
    Given camera permission is denied
    When error message is displayed
    Then instructions should explain how to enable permission
    And instructions should be browser-specific if possible
    And fallback to file upload should be suggested

  Scenario: getUserMedia error is caught and displayed
    Given getUserMedia() fails (e.g., camera in use by another app)
    When error occurs
    Then error message should be user-friendly
    And technical details should be logged to console
    And application should not crash

  Scenario: Canvas error is handled gracefully
    Given canvas.getContext('2d') fails
    When attempting to capture photo
    Then error should be caught
    And error message should be displayed
    And camera preview should remain functional

  Scenario: API error on submission shows retry option
    Given user submits pages
    When API returns 500 error
    Then error message should be displayed
    And "Retry" button should be available
    And pages should remain in list

  # ============================================================================
  # Feature 10: Responsive Design
  # ============================================================================

  Scenario: Camera tab works on desktop
    Given user is on desktop browser (Chrome, Firefox, Safari)
    When Camera tab loads
    Then camera preview should display correctly
    And all controls should be accessible
    And layout should use available screen space

  Scenario: Camera tab works on mobile
    Given user is on mobile device (iOS, Android)
    When Camera tab loads
    Then camera preview should fill screen appropriately
    And touch controls should be optimized
    And buttons should be touch-friendly (44x44px minimum)

  Scenario: Camera tab works on tablet
    Given user is on tablet device (iPad, Android tablet)
    When Camera tab loads
    Then layout should adapt to tablet screen size
    And both portrait and landscape should work

  Scenario: Portrait orientation is supported
    Given user is on mobile device
    When device is in portrait orientation
    Then camera preview should be vertical
    And controls should be positioned appropriately
    And all features should work normally

  Scenario: Landscape orientation is supported
    Given user is on mobile device
    When device is in landscape orientation
    Then camera preview should be horizontal
    And controls should reposition for landscape
    And all features should work normally

  Scenario: Orientation change is handled smoothly
    Given user has camera active in portrait
    When user rotates device to landscape
    Then camera preview should adapt without restart
    And no data should be lost
    And captured pages should remain in list
