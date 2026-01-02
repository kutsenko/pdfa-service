/**
 * AccessibleCameraAssistant - Accessibility features for camera capture
 * Provides audio feedback, voice guidance, and auto-capture for visually impaired users
 * Features: edge detection audio tones, voice announcements, screen reader detection
 */

import { t } from '../utils/helpers.js';

export class AccessibleCameraAssistant {
    constructor(cameraManager) {
        this.cameraManager = cameraManager;
        this.enabled = false;
        this.screenReaderDetected = false;
        this.volume = 0.8; // 80% default volume

        // Configuration loaded from API endpoint (see loadConfig())
        this.config = {};
        this.configLoaded = false;
        this.debugEnabled = false;

        // Audio components
        this.audioContext = null;
        // Note: oscillators are created on-demand for each tone (iOS compatibility)

        // VoiceOver detection and speech synthesis
        this.voiceOverManualOverride = null; // null = auto-detect, true/false = manual override
        this.voiceOverActive = this.detectVoiceOver();
        this.synth = window.speechSynthesis;
        this.currentLang = 'en-US';
        this.useTTS = !this.voiceOverActive; // Disable TTS if VoiceOver is active

        // Detection state
        this.lastEdgeConfidence = 0;
        this.lastAnnouncementTime = 0;
        this.announcementThrottle = 2000; // Will be updated from config in init()
        this.edgeState = 'lost'; // Current state: 'detected' or 'lost'
        this.lastStatusTime = 0; // For periodic status updates

        // Frame processing
        this.analysisCanvas = null;
        this.analysisCtx = null;
        this.processingFrame = false;
        this.analysisLoopId = null;

        // jscanify scanner
        this.scanner = null;
        this.degradedMode = false; // True if running without edge detection

        // Auto-capture state
        this.autoCaptureEnabled = true;
        this.stableFrameCount = 0;
        this.stableThreshold = 10; // Will be updated from config in init()
        this.captureCountdown = null;
        this.isCountingDown = false;

        // Auto-crop feature
        this.lastDetectedCorners = null; // Store last detected corners for perspective correction

        console.log('[A11y] AccessibleCameraAssistant created (config will be loaded in init)');
    }

    log(...args) {
        // Only log if debug is enabled
        if (this.debugEnabled) {
            console.log(...args);
        }
    }

    /**
     * Load accessibility camera configuration from API endpoint.
     * This replaces the previous approach of injecting config via window object.
     */
    async loadConfig() {
        try {
            this.log('[A11y] Loading config from API...');
            const response = await fetch('/api/config/a11y-camera');

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            this.config = await response.json();
            this.configLoaded = true;

            // Update config-dependent properties
            this.debugEnabled = this.config.debug_enabled || false;
            this.announcementThrottle = this.config.announcement_throttle_ms || 2000;
            this.stableThreshold = this.config.stable_frame_count || 10;

            console.log('[A11y] Config loaded successfully:', this.config);
        } catch (error) {
            console.error('[A11y] Failed to load config, using defaults:', error);
            // Keep default values set in constructor
            this.config = {};
            this.configLoaded = true; // Mark as loaded even if it failed
        }
    }

    async init() {
        console.log('[A11y] Initializing AccessibleCameraAssistant');

        // Load configuration from API first
        await this.loadConfig();

        this.log('[A11y] Initialization continuing after config load');

        // Log VoiceOver detection status
        console.log('[A11y] VoiceOver active:', this.voiceOverActive);
        console.log('[A11y] Web Speech API enabled:', this.useTTS);

        // Detect screen reader
        this.screenReaderDetected = this.detectScreenReader();

        // Setup UI controls first (this sets up event listeners)
        this.setupControls();

        // Auto-check checkbox if screen reader detected, but DON'T call enable()
        // Enable will be called by the checkbox change event handler when user interacts
        // This prevents AudioContext creation without user gesture
        const checkbox = document.getElementById('enableA11yAssistance');
        if (this.screenReaderDetected && checkbox) {
            console.log(
                '[A11y] Screen reader detected - checkbox will be pre-checked for user'
            );
            console.log(
                '[A11y] User must click to enable (required for AudioContext user gesture)'
            );
            checkbox.checked = true; // Pre-check, but don't enable yet
        }

        console.log('[A11y] Initialization complete');
    }

    detectScreenReader() {
        // Method 1: Check for prefers-reduced-motion (common with assistive tech)
        const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

        // Method 2: Check if user has interacted with ARIA live regions
        const liveRegion = document.getElementById('srAnnouncements');
        const hasAriaActivity = liveRegion && liveRegion.textContent.trim().length > 0;

        // Method 3: Check for high contrast mode (Windows Narrator, NVDA)
        const highContrast = window.matchMedia('(-ms-high-contrast: active)').matches;

        // Heuristic: any of these suggest screen reader use
        const detected = prefersReducedMotion || hasAriaActivity || highContrast;
        console.log('[A11y] Screen reader detection:', {
            prefersReducedMotion,
            hasAriaActivity,
            highContrast,
            detected
        });

        return detected;
    }

    detectVoiceOver() {
        /**
         * Detect if VoiceOver (iOS/macOS screen reader) is active.
         *
         * VoiceOver may conflict with Web Speech Synthesis API on iOS Safari,
         * causing TTS not to start or interrupting speech. When detected,
         * we rely solely on ARIA live regions which VoiceOver reads natively.
         *
         * Detection methods:
         * 1. Check manual override from localStorage (user preference)
         * 2. Check for iOS Safari user agent
         * 3. Check for accessibility features enabled
         * 4. Heuristic: iOS + screen reader hints = likely VoiceOver
         */

        // Check for manual override first
        const manualOverride = localStorage.getItem('voiceOverManualOverride');
        if (manualOverride !== null) {
            const isManuallyEnabled = manualOverride === 'true';
            console.log('[A11y] VoiceOver manual override:', isManuallyEnabled);
            this.voiceOverManualOverride = isManuallyEnabled;

            if (isManuallyEnabled) {
                console.log('[A11y] ⚠️ VoiceOver MANUALLY ENABLED - Web Speech API will be DISABLED');
                console.log('[A11y] Using ARIA live regions only (VoiceOver reads these natively)');
            } else {
                console.log('[A11y] VoiceOver MANUALLY DISABLED - Web Speech API will be ENABLED');
            }

            return isManuallyEnabled;
        }

        // Auto-detect if no manual override
        // Check if iOS Safari
        const isIOSSafari = /iPad|iPhone|iPod/.test(navigator.userAgent) &&
                           /Safari/.test(navigator.userAgent) &&
                           !/CriOS|FxiOS/.test(navigator.userAgent); // Exclude Chrome/Firefox on iOS

        // Check for accessibility hints
        const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        const invertedColors = window.matchMedia('(inverted-colors: inverted)').matches;

        // VoiceOver is likely if:
        // - iOS Safari AND (reduced motion OR inverted colors)
        // - OR explicitly detected via other means
        const likelyVoiceOver = isIOSSafari && (prefersReducedMotion || invertedColors);

        console.log('[A11y] VoiceOver auto-detection:', {
            isIOSSafari,
            prefersReducedMotion,
            invertedColors,
            detected: likelyVoiceOver
        });

        if (likelyVoiceOver) {
            console.log('[A11y] ⚠️ VoiceOver AUTO-DETECTED - Web Speech API will be DISABLED');
            console.log('[A11y] Using ARIA live regions only (VoiceOver reads these natively)');
        }

        return likelyVoiceOver;
    }

    setupControls() {
        // Enable/disable toggle
        const checkbox = document.getElementById('enableA11yAssistance');
        if (checkbox) {
            checkbox.addEventListener('change', async (e) => {
                if (e.target.checked) {
                    // iOS Fix: Create and resume AudioContext HERE in direct user gesture
                    // This is CRITICAL for iOS - AudioContext.resume() must be called
                    // synchronously in a user gesture handler, not in an async callback
                    try {
                        console.log('[A11y] ========== User clicked enable checkbox ==========');
                        console.log('[A11y] Creating AudioContext in direct user gesture');

                        // Pre-create AudioContext while still in user gesture context
                        if (!this.audioContext || this.audioContext.state === 'closed') {
                            // Clean up old context if it exists but is closed
                            if (this.audioContext && this.audioContext.state === 'closed') {
                                console.log('[A11y] Cleaning up closed AudioContext from previous session');
                                this.audioContext = null;
                            }

                            // Check browser support
                            if (!window.AudioContext && !window.webkitAudioContext) {
                                throw new Error('AudioContext not supported in this browser');
                            }

                            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
                            console.log('[A11y] AudioContext created in user gesture. State:', this.audioContext.state);

                            // Resume immediately while still in user gesture (critical for iOS)
                            if (this.audioContext.state === 'suspended') {
                                console.log('[A11y] AudioContext suspended, resuming NOW in user gesture...');
                                await this.audioContext.resume();
                                console.log('[A11y] ✓ AudioContext resumed in user gesture. State:', this.audioContext.state);

                                // Give iOS a moment to process
                                await new Promise(resolve => setTimeout(resolve, 50));
                                console.log('[A11y] Final AudioContext state:', this.audioContext.state);
                            } else {
                                console.log('[A11y] AudioContext already running (state:', this.audioContext.state + ')');
                            }
                        } else {
                            // AudioContext exists and is not closed, just resume if needed
                            console.log('[A11y] AudioContext already exists. State:', this.audioContext.state);
                            if (this.audioContext.state === 'suspended') {
                                console.log('[A11y] Resuming existing AudioContext...');
                                await this.audioContext.resume();
                                console.log('[A11y] ✓ AudioContext resumed. State:', this.audioContext.state);
                            }
                        }

                        // iOS Safari Audio Unlock: Play audible tone IMMEDIATELY in user gesture
                        // This is CRITICAL - iOS Safari requires actual sound in user gesture
                        console.log('[A11y] Playing unlock tone in user gesture (iOS Safari requirement)...');
                        try {
                            const now = this.audioContext.currentTime;
                            const unlockOsc = this.audioContext.createOscillator();
                            const unlockGain = this.audioContext.createGain();

                            unlockOsc.connect(unlockGain);
                            unlockGain.connect(this.audioContext.destination);

                            // Audible tone (not silent) - iOS Safari needs to hear something
                            unlockOsc.frequency.setValueAtTime(523, now); // C5
                            unlockGain.gain.setValueAtTime(0.3, now); // Audible volume
                            unlockGain.gain.exponentialRampToValueAtTime(0.01, now + 0.15);

                            unlockOsc.start(now);
                            unlockOsc.stop(now + 0.15);

                            console.log('[A11y] ✓ Unlock tone playing...');

                            // Wait for tone to finish
                            await new Promise(resolve => setTimeout(resolve, 200));
                        } catch (audioError) {
                            console.error('[A11y] ✗ Audio unlock tone failed:', audioError);
                        }

                        // iOS Safari TTS Fix: SPEAK IMMEDIATELY in user gesture to unlock
                        // This is CRITICAL - must happen SYNCHRONOUSLY in the click handler
                        // SKIP if VoiceOver detected (VoiceOver conflicts with Web Speech API)
                        if (window.speechSynthesis && this.useTTS) {
                            console.log('[A11y] Unlocking TTS by speaking in user gesture...');
                            try {
                                // Clear any pending speech
                                window.speechSynthesis.cancel();

                                // Speak SHORT word IMMEDIATELY in user gesture
                                // This unlocks TTS for all subsequent announcements
                                const unlockUtterance = new SpeechSynthesisUtterance('Aktiviert');
                                unlockUtterance.lang = this.currentLang;
                                unlockUtterance.volume = 0.8;
                                unlockUtterance.rate = 1.5; // Fast

                                unlockUtterance.onstart = () => {
                                    console.log('[A11y] ✓ TTS unlock speech started');
                                };

                                unlockUtterance.onend = () => {
                                    console.log('[A11y] ✓ TTS unlocked successfully');
                                };

                                unlockUtterance.onerror = (e) => {
                                    console.error('[A11y] ✗ TTS unlock failed:', e.error);
                                };

                                // CRITICAL: Speak BEFORE any async operations
                                window.speechSynthesis.speak(unlockUtterance);
                                console.log('[A11y] TTS unlock utterance queued');
                            } catch (speechError) {
                                console.error('[A11y] ✗ Could not unlock TTS:', speechError);
                            }
                        } else if (this.voiceOverActive) {
                            console.log('[A11y] Skipping TTS unlock (VoiceOver detected - using ARIA only)');
                        }

                        // Now call enable() which can assume AudioContext is ready
                        await this.enable();
                    } catch (error) {
                        console.error('[A11y] ✗ Failed to initialize in user gesture:', error);
                        alert('Failed to enable audio: ' + error.message + '\n\nPlease try clicking the checkbox again.');
                        e.target.checked = false;
                        // Clean up if AudioContext was created
                        if (this.audioContext) {
                            try {
                                await this.audioContext.close();
                            } catch (closeError) {
                                console.error('[A11y] Failed to close AudioContext:', closeError);
                            }
                            this.audioContext = null;
                        }
                    }
                } else {
                    await this.disable();
                }
            });
        }

        // Volume slider
        const volumeSlider = document.getElementById('a11yVolume');
        const volumeValue = document.getElementById('a11yVolumeValue');
        if (volumeSlider && volumeValue) {
            volumeSlider.addEventListener('input', (e) => {
                const value = parseInt(e.target.value);
                this.volume = value / 100;
                volumeValue.textContent = `${value}%`;
                console.log('[A11y] Volume set to', this.volume);
            });
        }

        // Test audio button
        const testBtn = document.getElementById('testA11yAudioBtn');
        if (testBtn) {
            testBtn.addEventListener('click', () => {
                this.testAudio();
            });
        }

        // Auto-capture toggle
        const autoCaptureCheckbox = document.getElementById('enableAutoCapture');
        if (autoCaptureCheckbox) {
            autoCaptureCheckbox.addEventListener('change', (e) => {
                this.autoCaptureEnabled = e.target.checked;
                console.log('[A11y] Auto-capture', this.autoCaptureEnabled ? 'enabled' : 'disabled');
            });
        }

        // VoiceOver manual override toggle
        const voiceOverCheckbox = document.getElementById('voiceOverOverride');
        if (voiceOverCheckbox) {
            // Set initial state from localStorage
            const savedOverride = localStorage.getItem('voiceOverManualOverride');
            if (savedOverride !== null) {
                voiceOverCheckbox.checked = savedOverride === 'true';
            }

            // Handle changes
            voiceOverCheckbox.addEventListener('change', (e) => {
                const isEnabled = e.target.checked;

                // Save to localStorage
                localStorage.setItem('voiceOverManualOverride', String(isEnabled));

                // Update VoiceOver detection
                this.voiceOverManualOverride = isEnabled;
                this.voiceOverActive = isEnabled;
                this.useTTS = !isEnabled;

                console.log('[A11y] VoiceOver manual override:', isEnabled);
                console.log('[A11y] Web Speech API (TTS):', this.useTTS ? 'ENABLED' : 'DISABLED');

                // Show/hide Web Speech API controls based on override
                this.updateVoiceOverUI();

                // Notify user
                const message = isEnabled
                    ? 'VoiceOver mode enabled. Web Speech API disabled.'
                    : 'VoiceOver mode disabled. Web Speech API enabled.';
                this.announce(message, 'assertive');
            });
        }

        // Update UI based on VoiceOver status (initial state)
        this.updateVoiceOverUI();
    }

    /**
     * Update UI to show/hide Web Speech API controls based on VoiceOver status.
     * Called on initialization and when user toggles VoiceOver override.
     */
    updateVoiceOverUI() {
        const volumeSlider = document.getElementById('a11yVolume');
        const testBtn = document.getElementById('testA11yAudioBtn');

        if (this.voiceOverActive) {
            console.log('[A11y] Hiding Web Speech API controls (VoiceOver mode - ARIA only)');

            // Hide volume control (not needed for ARIA)
            if (volumeSlider) {
                const volumeGroup = volumeSlider.closest('.form-group');
                if (volumeGroup) {
                    volumeGroup.style.display = 'none';
                }
            }

            // Hide test audio button (Web Speech API test)
            if (testBtn) {
                const testGroup = testBtn.closest('.form-group');
                if (testGroup) {
                    testGroup.style.display = 'none';
                }
            }
        } else {
            console.log('[A11y] Showing Web Speech API controls');

            // Show volume control
            if (volumeSlider) {
                const volumeGroup = volumeSlider.closest('.form-group');
                if (volumeGroup) {
                    volumeGroup.style.display = '';
                }
            }

            // Show test audio button
            if (testBtn) {
                const testGroup = testBtn.closest('.form-group');
                if (testGroup) {
                    testGroup.style.display = '';
                }
            }
        }
    }

    async enable() {
        if (this.enabled) return;

        console.log('[A11y] ========== Starting enable() ==========');
        console.log('[A11y] User Agent:', navigator.userAgent);
        console.log('[A11y] Platform:', navigator.platform);

        try {
            // Show loading indicator
            console.log('[A11y] Step 1: Showing loading indicator');
            const loadingIndicator = document.getElementById('a11yLoadingIndicator');
            if (loadingIndicator) {
                loadingIndicator.hidden = false;
            }

            // AudioContext should already be created and resumed in setupControls()
            // This is critical for iOS - resume() must be called in direct user gesture
            console.log('[A11y] Step 2: Checking AudioContext (should be pre-created)');
            if (!this.audioContext) {
                throw new Error('AudioContext was not pre-created. This should not happen.');
            }
            console.log('[A11y] ✓ AudioContext exists. State:', this.audioContext.state);

            // Verify AudioContext is running (should be after setupControls resume)
            if (this.audioContext.state !== 'running') {
                console.warn('[A11y] ⚠ WARNING: AudioContext not running. State:', this.audioContext.state);
                console.warn('[A11y] This may indicate iOS user gesture was lost. Audio may not work.');
            }

            // iOS Fix: Don't create persistent oscillator (causes issues on iOS)
            // Instead, each tone creates its own oscillator (see playTone method)
            console.log('[A11y] Step 3: Audio setup ready (using on-demand oscillators for iOS compatibility)');

            // Audio and TTS were already unlocked in setupControls() user gesture
            // (This is critical - iOS Safari requires unlock to happen IN the user gesture)
            console.log('[A11y] Step 4: Audio and TTS already unlocked in user gesture');

            // IMMEDIATELY announce to user (before loading libraries)
            // This gives instant feedback instead of waiting for jscanify to load
            this.enabled = true; // Enable now so announce() works
            console.log('[A11y] Step 5: Immediate user announcement');
            this.announce(this.translate('camera.a11y.enabled'), 'force');
            console.log('[A11y] ✓ User notified (loading libraries in background...)');

            // Create analysis canvas
            console.log('[A11y] Step 6: Creating analysis canvas');
            this.analysisCanvas = document.createElement('canvas');
            this.analysisCtx = this.analysisCanvas.getContext('2d');
            if (!this.analysisCtx) {
                throw new Error('Failed to create canvas 2d context');
            }
            console.log('[A11y] ✓ Canvas created');

            // Load edge detection library (jscanify)
            console.log('[A11y] Step 7: Loading jscanify library from CDN (with fallbacks)');
            await this.loadEdgeDetectionLibrary();

            if (this.degradedMode) {
                console.warn('[A11y] ⚠️ Running in degraded mode (no edge detection)');
                console.log('[A11y] ✓ jscanify library loaded (degraded mode - audio only)');
            } else {
                console.log('[A11y] ✓ jscanify library loaded successfully');
            }

            // Hide loading indicator
            if (loadingIndicator) {
                loadingIndicator.hidden = true;
            }

            // enabled = true was already set earlier for immediate user feedback

            // Start frame analysis loop (will skip edge detection if degradedMode)
            console.log('[A11y] Step 7: Starting frame analysis');
            this.startAnalysis();
            console.log('[A11y] ✓ Frame analysis started');

            // Announce degraded mode if applicable (user already heard "enabled")
            console.log('[A11y] Step 8: Final status check');
            if (this.degradedMode) {
                // Inform user about degraded mode limitation
                this.announce('Edge detection unavailable. Audio guidance only.', 'force');
                console.warn('[A11y] User notified about degraded mode');
            }

            console.log('[A11y] ========== ✓ Camera assistance enabled successfully ==========');
            if (this.degradedMode) {
                console.log('[A11y] Mode: DEGRADED (audio only, no edge detection)');
            } else {
                console.log('[A11y] Mode: FULL (audio + edge detection)');
            }
        } catch (error) {
            console.error('[A11y] ========== ✗ FAILED to enable assistance ==========');
            console.error('[A11y] Error name:', error.name);
            console.error('[A11y] Error message:', error.message);
            console.error('[A11y] Error stack:', error.stack);

            // Provide user-friendly error messages
            let errorMessage = 'Failed to enable accessibility assistance.';
            let detailedLog = '';

            if (error.message && error.message.includes('user')) {
                // iOS-specific error
                errorMessage = 'iOS requires a direct tap to enable audio. Please tap the checkbox again.';
                detailedLog = 'User interaction required';
            } else if (error.name === 'NotAllowedError') {
                errorMessage = 'Audio permission denied. Please check browser settings.';
                detailedLog = 'NotAllowedError';
            } else if (error.message && error.message.includes('jscanify')) {
                errorMessage = 'Failed to load edge detection library. Check internet connection.';
                detailedLog = 'jscanify CDN failed';
            } else if (error.message && error.message.includes('AudioContext')) {
                errorMessage = 'Audio system not available. Your browser may not support Web Audio API.';
                detailedLog = 'AudioContext not supported';
            } else if (error.message && error.message.includes('canvas')) {
                errorMessage = 'Canvas not supported. Please use a modern browser.';
                detailedLog = 'Canvas 2D context failed';
            } else {
                errorMessage = 'Initialization failed: ' + error.message;
                detailedLog = error.message;
            }

            console.error('[A11y] User-facing error:', errorMessage);
            console.error('[A11y] Technical detail:', detailedLog);

            alert(errorMessage + '\n\nTechnical details (for support): ' + detailedLog);

            // Reset checkbox
            const checkbox = document.getElementById('enableA11yAssistance');
            if (checkbox) {
                checkbox.checked = false;
            }

            // Hide loading indicator
            const loadingIndicator = document.getElementById('a11yLoadingIndicator');
            if (loadingIndicator) {
                loadingIndicator.hidden = true;
            }

            // Clean up audio context if it was created
            if (this.audioContext) {
                try {
                    await this.audioContext.close();
                    console.log('[A11y] AudioContext cleaned up');
                } catch (closeError) {
                    console.error('[A11y] Error closing AudioContext:', closeError);
                }
                this.audioContext = null;
            }
        }
    }

    async disable() {
        if (!this.enabled) return;

        console.log('[A11y] Disabling camera assistance');

        this.stopAnalysis();

        // Announce BEFORE closing AudioContext to avoid "Audio System not available" error
        this.enabled = false;
        this.announce(this.translate('camera.a11y.disabled'));

        // Now close AudioContext (after announcement)
        if (this.audioContext) {
            console.log('[A11y] Closing AudioContext...');
            try {
                await this.audioContext.close();
                console.log('[A11y] AudioContext closed successfully');
            } catch (error) {
                console.error('[A11y] Error closing AudioContext:', error);
            }
            this.audioContext = null;
        }

        // Hide status indicator
        const statusEl = document.getElementById('edgeDetectionStatus');
        if (statusEl) {
            statusEl.hidden = true;
        }

        console.log('[A11y] Camera assistance disabled');
    }

    async loadEdgeDetectionLibrary() {
        console.log('[A11y] Loading edge detection libraries (OpenCV.js + jscanify)');

        // Check if already loaded
        if (window.jscanify && window.cv) {
            this.scanner = new window.jscanify();
            console.log('[A11y] jscanify and OpenCV already loaded');
            return;
        }

        // Step 1: Load OpenCV.js (required dependency for jscanify)
        console.log('[A11y] Step 1: Loading OpenCV.js...');
        try {
            await this.loadOpenCV();
            console.log('[A11y] ✓ OpenCV.js loaded successfully');
        } catch (error) {
            console.error('[A11y] Failed to load OpenCV.js:', error);
            this.enableDegradedMode('OpenCV.js loading failed');
            return;
        }

        // Step 2: Load jscanify
        console.log('[A11y] Step 2: Loading jscanify library with CDN fallbacks');

        // Multiple CDN URLs as fallbacks (iOS often blocks certain CDNs)
        // Using v1.4.0 (latest as of 2025-02)
        const cdnUrls = [
            'https://cdn.jsdelivr.net/npm/jscanify@1.4.0/dist/jscanify.min.js',
            'https://unpkg.com/jscanify@1.4.0/dist/jscanify.min.js',
            'https://cdnjs.cloudflare.com/ajax/libs/jscanify/1.4.0/jscanify.min.js'
        ];

        let lastError = null;

        // Try each CDN URL in sequence
        for (let i = 0; i < cdnUrls.length; i++) {
            const url = cdnUrls[i];
            console.log(`[A11y] Attempting to load jscanify from CDN ${i + 1}/${cdnUrls.length}: ${url}`);

            try {
                await this.loadScriptFromUrl(url, 10000); // 10 second timeout

                if (window.jscanify) {
                    this.scanner = new window.jscanify();
                    console.log(`[A11y] ✓ jscanify loaded successfully from CDN ${i + 1}`);
                    return; // Success!
                } else {
                    throw new Error('jscanify global not found after script loaded');
                }
            } catch (error) {
                console.warn(`[A11y] jscanify CDN ${i + 1} failed:`, error.message);
                lastError = error;
                // Continue to next CDN
            }
        }

        // All CDNs failed - enable degraded mode without edge detection
        console.error('[A11y] All jscanify CDN attempts failed.');
        console.error('[A11y] Last error:', lastError);
        this.enableDegradedMode('jscanify loading failed');
    }

    async loadOpenCV() {
        // Check if OpenCV is already loaded
        if (window.cv && window.cv.Mat) {
            console.log('[A11y] OpenCV.js already loaded');
            return;
        }

        // OpenCV.js CDN URLs with fallbacks
        const opencvUrls = [
            'https://docs.opencv.org/4.7.0/opencv.js',
            'https://cdn.jsdelivr.net/npm/@techstark/opencv-js@4.7.0-release.1/dist/opencv.js',
            'https://unpkg.com/@techstark/opencv-js@4.7.0-release.1/dist/opencv.js'
        ];

        let lastError = null;

        for (let i = 0; i < opencvUrls.length; i++) {
            const url = opencvUrls[i];
            console.log(`[A11y] Attempting to load OpenCV.js from CDN ${i + 1}/${opencvUrls.length}: ${url}`);

            try {
                await this.loadScriptFromUrl(url, 30000); // 30 second timeout (OpenCV is large)

                // Wait for OpenCV to initialize
                await this.waitForOpenCVReady();

                console.log(`[A11y] ✓ OpenCV.js loaded and initialized from CDN ${i + 1}`);
                return; // Success!
            } catch (error) {
                console.warn(`[A11y] OpenCV.js CDN ${i + 1} failed:`, error.message);
                lastError = error;
                // Continue to next CDN
            }
        }

        throw new Error('Failed to load OpenCV.js from all CDN sources: ' + lastError.message);
    }

    waitForOpenCVReady() {
        return new Promise((resolve, reject) => {
            const timeout = setTimeout(() => {
                reject(new Error('OpenCV.js initialization timeout'));
            }, 30000); // 30 second timeout

            // If cv is already initialized
            if (window.cv && window.cv.Mat) {
                clearTimeout(timeout);
                resolve();
                return;
            }

            // Wait for cv.onRuntimeInitialized callback
            if (window.cv) {
                window.cv.onRuntimeInitialized = () => {
                    clearTimeout(timeout);
                    console.log('[A11y] OpenCV.js runtime initialized');
                    resolve();
                };
            } else {
                // Poll for cv to be available
                const checkInterval = setInterval(() => {
                    if (window.cv && window.cv.Mat) {
                        clearInterval(checkInterval);
                        clearTimeout(timeout);
                        console.log('[A11y] OpenCV.js detected via polling');
                        resolve();
                    }
                }, 100);
            }
        });
    }

    enableDegradedMode(reason) {
        console.error(`[A11y] Enabling degraded mode: ${reason}`);

        // Set scanner to null to indicate degraded mode
        this.scanner = null;
        this.degradedMode = true;

        // Show warning to user but don't fail completely
        console.warn('[A11y] ⚠️ Edge detection disabled. Audio features will work but without document edge detection.');
    }

    loadScriptFromUrl(url, timeout = 10000) {
        return new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.src = url;

            // Timeout handler
            const timeoutId = setTimeout(() => {
                script.onload = null;
                script.onerror = null;
                document.head.removeChild(script);
                reject(new Error(`Timeout loading script from ${url}`));
            }, timeout);

            script.onload = () => {
                clearTimeout(timeoutId);
                console.log(`[A11y] Script loaded from ${url}`);
                resolve();
            };

            script.onerror = () => {
                clearTimeout(timeoutId);
                document.head.removeChild(script);
                reject(new Error(`Failed to load script from ${url}`));
            };

            document.head.appendChild(script);
        });
    }

    startAnalysis() {
        console.log('[A11y] startAnalysis() called - enabled:', this.enabled, 'analysisLoopId:', this.analysisLoopId);

        if (!this.enabled || this.analysisLoopId) {
            console.warn('[A11y] Skipping startAnalysis - enabled:', this.enabled, 'analysisLoopId:', this.analysisLoopId);
            return;
        }

        console.log('[A11y] Starting frame analysis loop');

        const processFrame = async () => {
            if (!this.enabled) {
                console.log('[A11y] Stopping frame analysis - not enabled');
                this.analysisLoopId = null;
                return;
            }

            if (!this.processingFrame) {
                this.processingFrame = true;

                try {
                    await this.analyzeFrame();
                } catch (error) {
                    console.error('[A11y] Error in processFrame:', error);
                }

                this.processingFrame = false;
            }

            // Continue loop at configured FPS
            const fps = this.config.analysis_fps || 10;
            const delay = Math.round(1000 / fps);
            setTimeout(() => {
                this.analysisLoopId = requestAnimationFrame(processFrame);
            }, delay);
        };

        console.log('[A11y] Calling processFrame() for first time');
        processFrame();
        console.log('[A11y] processFrame() call initiated');
    }

    stopAnalysis() {
        if (this.analysisLoopId) {
            cancelAnimationFrame(this.analysisLoopId);
            this.analysisLoopId = null;
        }
        this.processingFrame = false;
        this.cancelAutoCapture();
        console.log('[A11y] Stopped frame analysis');
    }

    async analyzeFrame() {
        // Debug: Log that analyzeFrame is being called (only once)
        if (!this._analyzeFrameLogged) {
            console.log('[A11y] analyzeFrame() called for first time');
            this._analyzeFrameLogged = true;
        }

        // Get current video element
        const video = this.cameraManager.videoElement;
        if (!video) {
            if (!this._noVideoLogged) {
                console.warn('[A11y] No video element found - cameraManager.videoElement is null');
                this._noVideoLogged = true;
            }
            return;
        }

        if (video.readyState !== video.HAVE_ENOUGH_DATA) {
            if (!this._videoNotReadyLogged) {
                console.warn('[A11y] Video not ready - readyState:', video.readyState, '(need', video.HAVE_ENOUGH_DATA, ')');
                this._videoNotReadyLogged = true;
            }
            return;
        }

        // Log that we passed the video check (only once)
        if (!this._videoReadyLogged) {
            console.log('[A11y] ✓ Video ready - readyState:', video.readyState);
            this._videoReadyLogged = true;
        }

        // iOS Fix: Check if in degraded mode (no edge detection)
        if (this.degradedMode) {
            console.log('[A11y] In degraded mode - skipping edge detection');
            return;
        }

        if (!this.scanner) {
            console.warn('[A11y] Scanner not initialized - skipping frame');
            return;
        }

        try {
            // iOS Fix: Validate video dimensions before processing
            if (video.videoWidth === 0 || video.videoHeight === 0) {
                console.warn('[A11y] Video dimensions are 0 - skipping frame');
                return;
            }

            // Draw to analysis canvas
            // iOS Fix: Increase scale from 0.5 to 0.75 for better edge detection
            const scale = 0.75; // Process at 75% resolution (better quality for iOS)
            const targetWidth = Math.floor(video.videoWidth * scale);
            const targetHeight = Math.floor(video.videoHeight * scale);

            // iOS Fix: Ensure dimensions are valid
            if (targetWidth < 1 || targetHeight < 1) {
                console.warn('[A11y] Calculated dimensions too small - skipping frame');
                return;
            }

            this.analysisCanvas.width = targetWidth;
            this.analysisCanvas.height = targetHeight;

            // Only log dimensions once per session
            if (!this._dimensionsLogged) {
                console.log('[A11y] Drawing frame:', targetWidth, 'x', targetHeight);
                this._dimensionsLogged = true;
            }

            this.analysisCtx.drawImage(video, 0, 0, targetWidth, targetHeight);

            // iOS Fix: Verify canvas has content (only check on first few frames)
            if (!this._canvasVerified) {
                const imageData = this.analysisCtx.getImageData(0, 0, Math.min(10, targetWidth), Math.min(10, targetHeight));
                const hasContent = imageData.data.some(byte => byte !== 0);
                if (!hasContent) {
                    console.warn('[A11y] Canvas appears empty after drawImage - skipping frame');
                    return;
                }
                console.log('[A11y] ✓ Canvas verified - has content');
                this._canvasVerified = true;
            }

            // Detect document edges using jscanify v1.4.0 API
            // Convert canvas to OpenCV Mat (jscanify expects cv.Mat, not Canvas/ImageData)
            const mat = cv.imread(this.analysisCanvas);
            const contour = this.scanner.findPaperContour(mat);
            // Clean up OpenCV Mat to prevent memory leaks
            mat.delete();

            // iOS Debug: Log detection status every 5 seconds
            const now = Date.now();
            if (!this._lastDetectionLog || now - this._lastDetectionLog > 5000) {
                console.log('[A11y] Detection status:', contour ? 'CONTOUR FOUND' : 'NO CONTOUR');
                this._lastDetectionLog = now;
            }

            let corners = null;
            if (contour) {
                // Extract corner points from contour
                corners = this.scanner.getCornerPoints(contour);

                // Store corners for auto-crop feature
                this.lastDetectedCorners = corners;

                // Log when edges are first detected
                if (!this._edgesDetectedLogged) {
                    console.log('[A11y] ✓ Edges detected:', corners);
                    this._edgesDetectedLogged = true;
                }
            } else {
                // Reset flag when edges are lost
                this._edgesDetectedLogged = false;
                // Keep last corners for a while (don't clear immediately)
            }

            // Build result object compatible with old code
            const result = {
                success: !!corners,
                corners: corners ? [
                    corners.topLeftCorner,
                    corners.topRightCorner,
                    corners.bottomRightCorner,
                    corners.bottomLeftCorner
                ] : null,
                contour: contour
            };

            // Calculate confidence (0-1)
            const confidence = this.calculateConfidence(result);

            // iOS Debug: Log confidence every 5 seconds regardless of change
            if (!this._lastConfidenceLog || now - this._lastConfidenceLog > 5000) {
                console.log('[A11y] Edge confidence:', confidence.toFixed(2), 'threshold: 0.40');
                this._lastConfidenceLog = now;
            }

            // Provide feedback based on confidence
            this.provideFeedback(confidence, result);

            // Update last confidence
            this.lastEdgeConfidence = confidence;
        } catch (error) {
            console.error('[A11y] Error analyzing frame:', error);
            console.error('[A11y] Error stack:', error.stack);
            // Don't throw - just skip this frame
            // Show error in debug console for iOS testing
            this.announce('Error analyzing frame: ' + error.message, 'force');
        }
    }

    calculateConfidence(result) {
        if (!result || !result.success || !result.corners || result.corners.length !== 4) return 0;

        const corners = result.corners;
        if (corners.length !== 4) return 0;

        // Calculate area of detected document
        const area = this.calculatePolygonArea(corners);
        const canvasArea = this.analysisCanvas.width * this.analysisCanvas.height;
        const areaRatio = area / canvasArea;

        // Accept documents based on configured area range
        const minArea = this.config.confidence_min_area || 0.10;
        const maxArea = this.config.confidence_max_area || 0.90;
        const peakArea = this.config.confidence_peak_area || 0.40;

        let confidence = 0;
        if (areaRatio > minArea && areaRatio < maxArea) {
            // Peak confidence at configured coverage
            // Scale linearly from minArea to peakArea (0.25 -> 1.0), then from peakArea to maxArea (1.0 -> 0.5)
            if (areaRatio <= peakArea) {
                confidence = 0.25 + (areaRatio - minArea) * (0.75 / (peakArea - minArea));
            } else {
                confidence = 1.0 - (areaRatio - peakArea) * (0.5 / (maxArea - peakArea));
            }
            confidence = Math.max(0, Math.min(1.0, confidence));
        }

        return confidence;
    }

    calculatePolygonArea(corners) {
        // Validate that all corners exist and have x/y properties
        if (!corners || corners.length !== 4) return 0;
        for (const corner of corners) {
            if (!corner || typeof corner.x !== 'number' || typeof corner.y !== 'number') {
                return 0;
            }
        }

        let area = 0;
        for (let i = 0; i < corners.length; i++) {
            const j = (i + 1) % corners.length;
            area += corners[i].x * corners[j].y;
            area -= corners[j].x * corners[i].y;
        }
        return Math.abs(area / 2);
    }

    provideFeedback(confidence, result) {
        // Hysteresis thresholds to prevent flip-flopping
        const upperThreshold = this.config.hysteresis_upper || 0.45;
        const lowerThreshold = this.config.hysteresis_lower || 0.35;

        // Determine current state based on hysteresis
        const wasDetected = this.edgeState === 'detected';
        const isDetected = wasDetected
            ? confidence >= lowerThreshold  // Stay detected until drops below 35%
            : confidence >= upperThreshold;  // Need 45% to become detected

        // State transition handling
        if (isDetected && !wasDetected) {
            // Transition: lost → detected
            console.log('[A11y] ✓ Edges detected! Confidence:', confidence.toFixed(2));
            this.edgeState = 'detected';
            this.playSuccessTone();

            // Check document quality for better feedback
            const isCentered = this.isDocumentCentered(result);
            const area = this.calculatePolygonArea(result.corners);
            const canvasArea = this.analysisCanvas.width * this.analysisCanvas.height;
            const areaRatio = area / canvasArea;

            // Provide contextual announcement with specific edge information
            if (areaRatio < 0.15) {
                this.announce(this.translate('camera.a11y.moveCloser'));
            } else if (areaRatio > 0.85) {
                this.announce(this.translate('camera.a11y.moveFarther'));
            } else if (!isCentered) {
                // Tell user which edges are not visible for better guidance
                const missingEdges = this.getMissingEdges(result);
                if (missingEdges.length > 0) {
                    const edgesMsg = missingEdges.join(', ');
                    this.announce(this.translate('camera.a11y.edgesDetected') + '. ' + edgesMsg + ' ' + this.translate('camera.a11y.notVisible'));
                } else {
                    this.announce(this.translate('camera.a11y.edgesDetected') + '. ' + this.translate('camera.a11y.centerDocument'));
                }
            } else {
                this.announce(this.translate('camera.a11y.edgesDetected'));
            }

            this.showVisualIndicator('success');
            this.stableFrameCount = 0;
            this.lastStatusTime = Date.now();

        } else if (!isDetected && wasDetected) {
            // Transition: detected → lost
            console.log('[A11y] ⚠ Edges lost! Confidence:', confidence.toFixed(2));
            this.edgeState = 'lost';
            this.playWarningTone();
            this.announce(this.translate('camera.a11y.edgesLost'));
            this.showVisualIndicator('warning');
            this.stableFrameCount = 0;
            this.cancelAutoCapture();
            this.lastStatusTime = Date.now();

        } else if (isDetected) {
            // Continuous detected state
            this.playContinuousFeedbackTone(confidence);

            // Periodic status updates (every 10 seconds)
            const now = Date.now();
            if (now - this.lastStatusTime > 10000) {
                const isCentered = this.isDocumentCentered(result);
                if (!isCentered) {
                    // Tell user which edges are missing for better guidance
                    const missingEdges = this.getMissingEdges(result);
                    if (missingEdges.length > 0) {
                        const edgesMsg = missingEdges.join(', ');
                        this.announce(edgesMsg + ' ' + this.translate('camera.a11y.notVisible'));
                    } else {
                        this.announce(this.translate('camera.a11y.centerDocument'));
                    }
                    this.lastStatusTime = now;
                }
            }

            // Check if document is well-centered for auto-capture
            const isCentered = this.isDocumentCentered(result);
            if (isCentered) {
                this.stableFrameCount++;

                // If stable for required frames, initiate auto-capture
                if (this.stableFrameCount >= this.stableThreshold &&
                    !this.isCountingDown &&
                    this.autoCaptureEnabled) {
                    this.initiateAutoCapture();
                }
            } else {
                // Reset if document moves
                if (this.stableFrameCount > 0) {
                    this.stableFrameCount = 0;
                    this.cancelAutoCapture();
                }
                // Provide positional guidance (throttled)
                this.providePositionalGuidance(result);
            }
        }

        // Store for next frame
        this.lastEdgeConfidence = confidence;
    }

    getMissingEdges(result) {
        // Determine which edges of the document are not visible or too close to frame edges
        // Returns array of edge names (e.g., ["Top edge", "Left edge"])
        if (!result || !result.corners || result.corners.length !== 4) return [];

        const corners = result.corners;
        const canvas = this.analysisCanvas;
        const margin = this.config.edge_margin_pixels || 20;
        const missingEdges = [];

        // Validate all corners
        for (const corner of corners) {
            if (!corner || typeof corner.x !== 'number' || typeof corner.y !== 'number') {
                return [];
            }
        }

        // Check each edge
        // Top edge: if any corner is too close to top
        const hasTopEdgeIssue = corners.some(c => c.y < margin);
        if (hasTopEdgeIssue) {
            missingEdges.push(this.translate('camera.a11y.topEdge'));
        }

        // Bottom edge: if any corner is too close to bottom
        const hasBottomEdgeIssue = corners.some(c => c.y > canvas.height - margin);
        if (hasBottomEdgeIssue) {
            missingEdges.push(this.translate('camera.a11y.bottomEdge'));
        }

        // Left edge: if any corner is too close to left
        const hasLeftEdgeIssue = corners.some(c => c.x < margin);
        if (hasLeftEdgeIssue) {
            missingEdges.push(this.translate('camera.a11y.leftEdge'));
        }

        // Right edge: if any corner is too close to right
        const hasRightEdgeIssue = corners.some(c => c.x > canvas.width - margin);
        if (hasRightEdgeIssue) {
            missingEdges.push(this.translate('camera.a11y.rightEdge'));
        }

        return missingEdges;
    }

    isDocumentCentered(result) {
        if (!result || !result.corners || result.corners.length !== 4) return false;

        const corners = result.corners;
        const canvas = this.analysisCanvas;

        // Validate all corners have x/y coordinates
        for (const corner of corners) {
            if (!corner || typeof corner.x !== 'number' || typeof corner.y !== 'number') {
                return false;
            }
        }

        // Calculate center of detected document
        const docCenterX = corners.reduce((sum, c) => sum + c.x, 0) / 4;
        const docCenterY = corners.reduce((sum, c) => sum + c.y, 0) / 4;

        // Calculate center of canvas
        const canvasCenterX = canvas.width / 2;
        const canvasCenterY = canvas.height / 2;

        // Calculate offset
        const offsetX = Math.abs(docCenterX - canvasCenterX);
        const offsetY = Math.abs(docCenterY - canvasCenterY);

        // Document is centered if within 30 pixels of center
        const centerThreshold = 30;
        return offsetX < centerThreshold && offsetY < centerThreshold;
    }

    initiateAutoCapture() {
        if (this.isCountingDown) return; // Already counting down

        console.log('[A11y] Initiating auto-capture countdown');
        this.isCountingDown = true;

        // Announce to hold steady
        this.announce(this.translate('camera.a11y.holdSteady'));
        this.playTone(440, 200); // A4 note for "get ready"

        // Start 2-second countdown
        let countdown = 2;

        const countdownInterval = setInterval(() => {
            if (countdown > 0) {
                // Beep for each second
                const freq = this.config.tone_countdown_freq || 523;
                const duration = this.config.tone_countdown_duration || 100;
                this.playTone(freq, duration);
                this.announce(countdown.toString()); // "2", "1"
                countdown--;
            } else {
                clearInterval(countdownInterval);

                // Capture!
                this.performAutoCapture();
            }
        }, 1000); // Every 1 second

        // Store interval ID so we can cancel if needed
        this.captureCountdown = countdownInterval;
    }

    async performAutoCapture() {
        console.log('[A11y] Auto-capturing photo');

        // Play capture sound (camera shutter simulation)
        this.playTone(880, 50); // High A5
        setTimeout(() => this.playTone(440, 50), 60); // Lower A4

        // Announce capture
        this.announce(this.translate('camera.a11y.photoCaptured'));

        // Trigger the actual camera capture
        if (this.cameraManager && typeof this.cameraManager.capturePhoto === 'function') {
            this.cameraManager.capturePhoto();
        }

        // Reset state
        this.isCountingDown = false;
        this.stableFrameCount = 0;
        this.captureCountdown = null;

        // Visual feedback
        this.showVisualIndicator('success');
    }

    cancelAutoCapture() {
        if (this.captureCountdown) {
            clearInterval(this.captureCountdown);
            this.captureCountdown = null;
            this.isCountingDown = false;
            console.log('[A11y] Auto-capture cancelled');
        }
    }

    providePositionalGuidance(result) {
        // Provide edge-based guidance instead of directional ("left edge not visible" vs "move camera right")
        if (!result || !result.corners || result.corners.length !== 4) return;

        const now = Date.now();
        // Only provide guidance every 3 seconds
        if (now - this.lastAnnouncementTime < 3000) return;

        // Get missing edges
        const missingEdges = this.getMissingEdges(result);

        if (missingEdges.length > 0) {
            // Announce which edges are not visible
            const edgesMsg = missingEdges.join(', ');
            this.announce(edgesMsg + ' ' + this.translate('camera.a11y.notVisible'));
        }
    }

    async playTone(frequency, duration = 200) {
        // Check if AudioContext is available and not closed
        if (!this.audioContext || !this.enabled) {
            console.warn('[A11y] playTone: AudioContext not available or not enabled');
            return;
        }

        if (this.audioContext.state === 'closed') {
            console.warn('[A11y] playTone: AudioContext is closed, cannot play tone');
            return;
        }

        // iOS Safari Fix: Resume AudioContext if suspended (can happen at any time)
        if (this.audioContext.state === 'suspended') {
            console.warn('[A11y] AudioContext suspended during playTone - attempting resume');
            try {
                await this.audioContext.resume();
                console.log('[A11y] AudioContext resumed successfully');
            } catch (error) {
                console.error('[A11y] Failed to resume AudioContext for playTone:', error);
                // Warn user that audio stopped working
                if (!this._audioSuspendedWarned) {
                    this.announce('Audio suspended. Please toggle accessibility off and on again.');
                    this._audioSuspendedWarned = true;
                }
                return;
            }
        }

        if (this.audioContext.state !== 'running') {
            console.warn('[A11y] AudioContext not running. State:', this.audioContext.state);
            return;
        }

        try {
            // iOS Fix: Create a new oscillator for each tone instead of reusing
            // This is more reliable on iOS Safari which can suspend persistent oscillators
            const now = this.audioContext.currentTime;
            const osc = this.audioContext.createOscillator();
            const gain = this.audioContext.createGain();

            osc.connect(gain);
            gain.connect(this.audioContext.destination);

            // Set frequency
            osc.frequency.setValueAtTime(frequency, now);

            // Fade in
            gain.gain.setValueAtTime(0, now);
            gain.gain.linearRampToValueAtTime(this.volume * 0.3, now + 0.01);

            // Fade out
            gain.gain.linearRampToValueAtTime(0, now + (duration / 1000));

            // Start and stop
            osc.start(now);
            osc.stop(now + (duration / 1000));

            // Log first successful tone
            if (!this._firstTonePlayed) {
                console.log('[A11y] ✓ First tone played successfully (iOS-friendly mode)');
                this._firstTonePlayed = true;
            }
        } catch (error) {
            console.error('[A11y] Error in playTone:', error);
        }
    }

    playSuccessTone() {
        const freq = this.config.tone_success_freq || 880;
        const duration = this.config.tone_success_duration || 200;
        this.playTone(freq, duration);
    }

    playWarningTone() {
        const freq = this.config.tone_warning_freq || 440;
        const duration = this.config.tone_warning_duration || 150;
        this.playTone(freq, duration);
    }

    playContinuousFeedbackTone(confidence) {
        // Map confidence (0-1) to frequency (200-800 Hz)
        // Higher confidence = higher pitch
        const minFreq = 200;
        const maxFreq = 800;
        const frequency = minFreq + (confidence * (maxFreq - minFreq));

        this.playTone(frequency, 100);
    }

    async testAudio() {
        console.log('[A11y] ===== Testing Audio =====');
        console.log('[A11y] Platform:', navigator.platform);
        console.log('[A11y] User Agent:', navigator.userAgent);

        if (!this.audioContext) {
            alert('Audio not initialized. Please enable accessibility assistance first.');
            return;
        }

        console.log('[A11y] AudioContext state:', this.audioContext.state);

        // iOS Fix: Resume AudioContext if needed (must be in user gesture)
        if (this.audioContext.state === 'suspended') {
            console.log('[A11y] AudioContext suspended, resuming...');
            try {
                await this.audioContext.resume();
                await new Promise(resolve => setTimeout(resolve, 100));
                console.log('[A11y] AudioContext state after resume:', this.audioContext.state);
            } catch (error) {
                console.error('[A11y] Failed to resume AudioContext:', error);
                alert('Failed to resume audio: ' + error.message);
                return;
            }
        }

        if (this.audioContext.state !== 'running') {
            alert('AudioContext not running. State: ' + this.audioContext.state);
            return;
        }

        // Test 1: Play tone
        console.log('[A11y] Test 1: Playing tone...');
        try {
            await this.playSuccessTone();
            console.log('[A11y] ✓ Tone played');
        } catch (error) {
            console.error('[A11y] ✗ Tone failed:', error);
        }

        // Test 2: Try speech (may not work on iOS Safari)
        console.log('[A11y] Test 2: Testing speech synthesis...');
        const testText = this.translate('camera.a11y.testAnnouncement') || 'Audio test. If you can hear this, audio is working.';

        if (window.speechSynthesis) {
            console.log('[A11y] Speech synthesis available');
            setTimeout(() => {
                try {
                    window.speechSynthesis.cancel(); // Cancel any pending speech
                    const utterance = new SpeechSynthesisUtterance(testText);
                    utterance.lang = this.getLangCode();
                    utterance.volume = this.volume;
                    utterance.rate = 1.0;

                    utterance.onstart = () => console.log('[A11y] ✓ Speech started');
                    utterance.onend = () => console.log('[A11y] ✓ Speech ended');
                    utterance.onerror = (e) => console.error('[A11y] ✗ Speech error:', e);

                    window.speechSynthesis.speak(utterance);
                } catch (error) {
                    console.error('[A11y] ✗ Speech failed:', error);
                }
            }, 600);
        } else {
            console.warn('[A11y] ⚠️ Speech synthesis NOT available (expected on iOS Safari)');
            alert('Speech synthesis not available on this browser. Tones should work.');
        }

        console.log('[A11y] ===== Test Complete =====');
    }

    announce(text, priority = 'polite') {
        if (!this.enabled && priority !== 'force') return;

        // Throttle announcements (prevent spam)
        const now = Date.now();
        if (priority !== 'force' && now - this.lastAnnouncementTime < this.announcementThrottle) {
            return;
        }
        this.lastAnnouncementTime = now;

        // Update ARIA live region (for screen readers)
        // This is CRITICAL for VoiceOver - it reads ARIA live regions natively
        const liveRegion = document.getElementById('srAnnouncements');
        if (liveRegion) {
            liveRegion.textContent = text;
        }

        // Skip Web Speech API if VoiceOver is detected
        // VoiceOver reads ARIA live regions natively and may conflict with Web Speech API
        if (!this.useTTS) {
            console.log('[A11y] Announced (ARIA only, VoiceOver mode):', text.substring(0, 50) + '...');
            return;
        }

        // Try Web Speech API (only if VoiceOver not detected)
        if (this.synth && window.speechSynthesis) {
            try {
                const utterance = new SpeechSynthesisUtterance(text);
                utterance.lang = this.getLangCode();
                utterance.volume = this.volume;
                utterance.rate = 1.2; // Slightly faster

                // iOS Safari: Add detailed event logging
                utterance.onstart = () => {
                    console.log('[A11y] ✓ Speech started:', text.substring(0, 50));
                };

                utterance.onend = () => {
                    console.log('[A11y] ✓ Speech completed');
                };

                utterance.onerror = (e) => {
                    console.error('[A11y] ✗ Speech error:', e.error, '-', e.message);
                    // iOS Safari: If "not-allowed", try to resume and retry
                    if (e.error === 'not-allowed' && priority === 'force') {
                        console.log('[A11y] Retrying speech after "not-allowed" error...');
                        setTimeout(() => {
                            this.synth.cancel();
                            this.synth.speak(utterance);
                        }, 100);
                    }
                };

                console.log('[A11y] Speaking:', text.substring(0, 50) + '...');

                // iOS Safari: Cancel any previous speech and give it time to clear
                if (this.synth.speaking || this.synth.pending) {
                    this.synth.cancel();
                }

                this.synth.speak(utterance);
            } catch (error) {
                console.error('[A11y] ✗ Speech failed:', error);
                // Fallback: ARIA only
            }
        } else {
            console.log('[A11y] Announced (ARIA only, no TTS):', text);
        }
    }

    getLangCode() {
        // Map UI language to speech synthesis language codes
        const langMap = {
            'en': 'en-US',
            'de': 'de-DE',
            'es': 'es-ES',
            'fr': 'fr-FR'
        };
        return langMap[window.currentLang] || 'en-US';
    }

    translate(key) {
        // Use existing i18n infrastructure
        const translations = window.translations && window.translations[window.currentLang];
        if (!translations) {
            console.warn('[A11y] No translations found for lang:', window.currentLang);
            return key;
        }

        // First try flat key (e.g., "camera.a11y.edgesDetected" as single key)
        if (translations[key]) {
            return translations[key];
        }

        // Fall back to nested navigation for backwards compatibility
        const keys = key.split('.');
        let value = translations;
        for (const k of keys) {
            value = value[k];
            if (!value) {
                console.warn('[A11y] Translation not found:', key);
                return key;
            }
        }
        return value;
    }

    showVisualIndicator(type) {
        // For low-vision users (complementary to audio)
        const statusEl = document.getElementById('edgeDetectionStatus');
        if (!statusEl) return;

        statusEl.hidden = false;
        statusEl.className = `edge-status ${type}`;

        const textEl = document.getElementById('edgeStatusText');
        if (textEl) {
            textEl.textContent = type === 'success'
                ? this.translate('camera.a11y.edgesDetected')
                : this.translate('camera.a11y.edgesLost');
        }
    }
}
