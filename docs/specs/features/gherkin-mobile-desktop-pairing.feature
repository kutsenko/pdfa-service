Feature: Mobile-Desktop Camera Pairing
  As a desktop user
  I want to link my mobile device to my desktop session
  So that I can capture high-quality images using my phone camera

  Background:
    Given I am on the camera tab of the pdfa-service web application
    And I am using a desktop browser

  Scenario: Desktop user starts pairing session
    When I click the "Start Mobile Pairing" button
    Then I should see a 6-character pairing code displayed
    And I should see a QR code displayed
    And I should see a countdown timer showing "15:00"
    And the pairing status should show "Waiting for mobile..."

  Scenario: Mobile user joins pairing session via QR code
    Given a desktop pairing session is active with code "ABC123"
    When I scan the QR code with my mobile device
    Then I should be navigated to "/mobile/camera?code=ABC123"
    And the pairing code input should be pre-filled with "ABC123"
    When I click "Connect"
    Then I should see the mobile camera view
    And the desktop should show "Mobile connected ✓"

  Scenario: Mobile user joins pairing session manually
    Given a desktop pairing session is active with code "ABC123"
    When I navigate to "/mobile/camera" on my mobile device
    And I enter "ABC123" in the pairing code input
    And I click "Connect"
    Then I should see the mobile camera view
    And the desktop should show "Mobile connected ✓"

  Scenario: Mobile user captures and sends image to desktop
    Given I am connected to a desktop session on my mobile device
    And I have granted camera permissions
    When I click the capture button
    Then I should see the image editor screen
    And I can rotate the image left or right
    When I click "Send to Desktop"
    Then the image should appear in the desktop staging area
    And the mobile counter should show "1 sent"
    And the desktop counter should show "1 images received"
    And I should return to the camera view

  Scenario: Multiple images synced to desktop
    Given I am connected to a desktop session on my mobile device
    When I capture and send 3 images
    Then the desktop staging area should contain 3 pages
    And each page should be numbered (1, 2, 3)
    And I can drag and drop to reorder the pages on desktop

  Scenario: Pairing session expires
    Given a pairing session is active for 30 minutes
    When the session expires
    Then the desktop should show "Pairing session expired"
    And the mobile device should show "Pairing session expired"
    And the QR code should be hidden
    And the "Start Mobile Pairing" button should be visible again

  Scenario: User cancels pairing session
    Given a pairing session is active
    When I click "Cancel Pairing" on desktop
    Then the pairing session should be cancelled
    And the mobile device should show "Pairing session expired"
    And the desktop should return to initial state

  Scenario: Mobile device disconnects
    Given I am connected to a desktop session on my mobile device
    When I click "Disconnect" on mobile
    Then the desktop should show "Mobile disconnected"
    And the mobile should return to the pairing code entry screen

  Scenario: Desktop user submits multi-page document from mobile images
    Given I have captured 5 images from my mobile device
    And all 5 images appear in the desktop staging area
    When I reorder the pages on desktop
    And I click "Convert to PDF/A"
    Then a conversion job should be submitted with all 5 pages in the correct order
    And I should be switched to the Jobs tab

  Scenario: Invalid pairing code
    Given I am on the mobile camera page
    When I enter "INVALID" as the pairing code
    And I click "Connect"
    Then I should see an error message "Invalid pairing code"
    And I should remain on the pairing screen

  Scenario: Attempting to join with different user account
    Given a desktop pairing session is active for user "alice@example.com"
    And I am logged in as "bob@example.com" on my mobile device
    When I enter the pairing code
    And I click "Connect"
    Then I should see an error message "Must use same account on both devices"

Feature: Camera Switching on Mobile
  As a mobile user
  I want to switch between front and rear cameras
  So that I can choose the best camera for document capture

  Scenario: Switch from rear to front camera
    Given I am on the mobile camera view
    And the rear camera is active
    When I click the "Switch" button
    Then the front camera should become active
    And the video preview should update

  Scenario: Switch back to rear camera
    Given I am on the mobile camera view
    And the front camera is active
    When I click the "Switch" button
    Then the rear camera should become active

Feature: Mobile Image Editing
  As a mobile user
  I want to rotate captured images before sending
  So that document orientation is correct

  Scenario: Rotate image 90 degrees right
    Given I have captured an image on mobile
    And I am on the image editor screen
    When I click "Rotate Right"
    Then the image should be rotated 90 degrees clockwise

  Scenario: Rotate image 90 degrees left
    Given I have captured an image on mobile
    And I am on the image editor screen
    When I click "Rotate Left"
    Then the image should be rotated 90 degrees counter-clockwise

  Scenario: Multiple rotations
    Given I have captured an image on mobile
    And I am on the image editor screen
    When I click "Rotate Right" 3 times
    Then the image should be rotated 270 degrees clockwise
    And clicking "Rotate Right" once more should return to original orientation

Feature: Real-Time Synchronization
  As a desktop user
  I want to see images appear immediately when mobile sends them
  So that I have real-time feedback of the capture process

  Scenario: Instant image sync via WebSocket
    Given my mobile device is connected to desktop
    When I capture and send an image from mobile
    Then the image should appear on desktop within 1 second
    And a success notification should be shown on mobile
    And the desktop should display the image in the staging area

  Scenario: Peer connection status updates
    Given I have an active pairing session
    When the mobile device connects
    Then the desktop status should change to "Mobile connected ✓"
    When the mobile device disconnects
    Then the desktop status should change to "Mobile disconnected"

Feature: Security and Access Control
  As a system administrator
  I want pairing sessions to be secure and time-limited
  So that unauthorized access is prevented

  Scenario: Same-user authentication enforcement
    Given a pairing session created by "user@example.com"
    When a different user "other@example.com" tries to join
    Then the join request should be rejected
    And an error "Must use same account on both devices" should be shown

  Scenario: Pairing code uniqueness
    Given 100 pairing sessions are created simultaneously
    Then all pairing codes should be unique
    And each code should be exactly 6 characters
    And codes should not contain confusing characters (0, O, 1, I, L)

  Scenario: Session expiration cleanup
    Given a pairing session has expired
    When 30 minutes have passed since creation
    Then the session should be automatically deleted from database
    And the session should no longer be joinable

  Scenario: Rate limiting on session creation
    Given I am a desktop user
    When I create 11 pairing sessions within 1 minute
    Then the 11th request should be rate-limited
    And I should receive a 429 Too Many Requests error

Feature: Error Handling and Recovery
  As a user
  I want clear error messages when something goes wrong
  So that I know how to resolve issues

  Scenario: Camera permission denied on mobile
    Given I am on the mobile camera page
    And I have denied camera permissions
    When I try to connect to a pairing session
    Then I should see an error "Failed to access camera"
    And I should be prompted to check permissions

  Scenario: WebSocket connection lost during sync
    Given I am sending an image from mobile to desktop
    When the WebSocket connection is lost
    Then I should see an error "Connection lost"
    And I should be prompted to reconnect

  Scenario: Desktop WebSocket not connected
    Given I am on the desktop camera tab
    And the WebSocket is disconnected
    When I try to start a pairing session
    Then I should see an error "WebSocket not connected"
    And I should be prompted to refresh the page

  Scenario: Session already active
    Given a pairing session with code "ABC123" is already active
    When another user tries to join the same code
    Then they should see an error "Session already active"

Feature: Mobile UI Responsiveness
  As a mobile user
  I want the interface to adapt to my device
  So that I have an optimal user experience

  Scenario: Portrait orientation on phone
    Given I am using a smartphone in portrait mode
    When I open the mobile camera page
    Then the layout should be optimized for portrait
    And touch targets should be at least 44x44 pixels
    And the camera preview should fill the viewport

  Scenario: Landscape orientation on phone
    Given I am using a smartphone in landscape mode
    When I open the mobile camera page
    Then the layout should adapt to landscape
    And controls should remain accessible
    And the camera preview should maintain aspect ratio

  Scenario: Tablet viewport
    Given I am using a tablet device
    When I open the mobile camera page
    Then the layout should use larger spacing
    And buttons should be appropriately sized for tablet
    And the QR code input should be centered

Feature: Accessibility
  As a user with accessibility needs
  I want the pairing feature to be fully accessible
  So that I can use it with assistive technology

  Scenario: Keyboard navigation on desktop
    Given I am on the desktop camera tab
    When I use Tab key to navigate
    Then I should be able to reach all pairing controls
    And the focus should be clearly visible
    And I can activate buttons with Enter key

  Scenario: Screen reader support
    Given I am using a screen reader
    When I navigate the pairing interface
    Then all controls should have descriptive labels
    And status updates should be announced
    And error messages should be announced

  Scenario: Touch target sizes
    Given I am on the mobile camera page
    When I inspect touch targets
    Then all buttons should be at least 44x44 pixels
    And there should be adequate spacing between targets
    And targets should have clear visual feedback on tap

Feature: Internationalization
  As an international user
  I want the pairing interface in my language
  So that I can understand and use it effectively

  Scenario: German language support
    Given I have set my browser language to German
    When I open the camera tab
    Then all pairing UI elements should be in German
    And error messages should be in German
    And the countdown timer format should follow German conventions

  Scenario: Spanish language support
    Given I have set my browser language to Spanish
    When I open the mobile camera page
    Then all UI elements should be in Spanish
    And button labels should be translated
    And status messages should be in Spanish

  Scenario: French language support
    Given I have set my browser language to French
    When I navigate the pairing workflow
    Then all text should be in French
    And date/time formatting should follow French conventions
