/**
 * MobilePairingManager - Mobile-desktop camera pairing
 * Manages mobile-desktop pairing sessions for real-time image sync
 */

import { showStatus } from '../utils/helpers.js';

export class MobilePairingManager {
    constructor(cameraManager) {
        this.cameraManager = cameraManager;
        this.currentSession = null;
        this.countdownInterval = null;
        this.qrCode = null;

        console.log('[Pairing] Initializing MobilePairingManager');
        this.init();
    }

    init() {
        this.setupEventListeners();
    }

    setupEventListeners() {
        const startBtn = document.getElementById('startPairingBtn');
        const cancelBtn = document.getElementById('cancelPairingBtn');

        if (startBtn) {
            startBtn.addEventListener('click', () => {
                console.log('[Pairing] Start button clicked');
                this.createSession();
            });
        }

        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => {
                console.log('[Pairing] Cancel button clicked');
                this.cancelSession();
            });
        }
    }

    async createSession() {
        try {
            console.log('[Pairing] Creating new pairing session');

            // Get auth token if available
            const authToken = window.authManager?.token || '';

            const response = await fetch('/api/v1/camera/pairing/create', {
                method: 'POST',
                headers: {
                    'Authorization': authToken ? `Bearer ${authToken}` : ''
                }
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to create pairing session');
            }

            const session = await response.json();
            this.currentSession = session;

            console.log('[Pairing] Session created:', session.session_id);

            // Show pairing UI
            this.showPairingUI(session);

            // Generate QR code
            this.generateQRCode(session.qr_data);

            // Start countdown
            this.startCountdown(session.ttl_seconds);

            // Register WebSocket for pairing
            this.registerForPairing(session.session_id);

            showStatus('Pairing session started. Scan QR code with mobile device.', 'info');

        } catch (error) {
            console.error('[Pairing] Failed to create session:', error);
            showStatus(`Failed to start pairing: ${error.message}`, 'error');
        }
    }

    showPairingUI(session) {
        // Hide start button
        const startBtn = document.getElementById('startPairingBtn');
        if (startBtn) {
            startBtn.hidden = true;
        }

        // Show active pairing view
        const activeView = document.getElementById('pairingActiveView');
        if (activeView) {
            activeView.hidden = false;
        }

        // Display pairing code
        const codeDisplay = document.getElementById('pairingCodeDisplay');
        if (codeDisplay) {
            codeDisplay.textContent = session.pairing_code;
        }

        // Reset counter
        const counter = document.getElementById('imagesSyncedCount');
        if (counter) {
            counter.textContent = '0';
        }

        // Reset status
        const statusBadge = document.getElementById('pairingStatusBadge');
        const statusText = document.getElementById('pairingStatusText');
        if (statusBadge) {
            statusBadge.classList.remove('connected');
        }
        if (statusText) {
            statusText.setAttribute('data-i18n', 'camera.pairing.waiting');
            // Apply translation using global function
            if (window.applyTranslations && window.currentLang) {
                window.applyTranslations(window.currentLang);
            }
        }
    }

    generateQRCode(qrData) {
        const container = document.getElementById('qrCodeContainer');
        if (!container) {
            console.warn('[Pairing] QR container not found');
            return;
        }

        // Clear previous QR code
        container.innerHTML = '';

        // Check if QRCode library is available
        if (typeof QRCode === 'undefined') {
            console.error('[Pairing] QRCode library not loaded');
            container.innerHTML = '<p style="color: #dc3545;">QR code library not available</p>';
            return;
        }

        try {
            this.qrCode = new QRCode(container, {
                text: qrData,
                width: 200,
                height: 200,
                colorDark: '#000000',
                colorLight: '#ffffff',
                correctLevel: QRCode.CorrectLevel.H
            });

            console.log('[Pairing] QR code generated');
        } catch (error) {
            console.error('[Pairing] Failed to generate QR code:', error);
            container.innerHTML = '<p style="color: #dc3545;">Failed to generate QR code</p>';
        }
    }

    startCountdown(seconds) {
        let remaining = seconds;

        const updateDisplay = () => {
            const minutes = Math.floor(remaining / 60);
            const secs = remaining % 60;
            const timeDisplay = document.getElementById('countdownTime');
            if (timeDisplay) {
                timeDisplay.textContent = `${minutes}:${String(secs).padStart(2, '0')}`;
            }
        };

        // Initial display
        updateDisplay();

        // Clear any existing interval
        if (this.countdownInterval) {
            clearInterval(this.countdownInterval);
        }

        this.countdownInterval = setInterval(() => {
            remaining--;
            updateDisplay();

            if (remaining <= 0) {
                this.expireSession('timeout');
            }
        }, 1000);

        console.log('[Pairing] Countdown started:', seconds, 'seconds');
    }

    registerForPairing(sessionId) {
        const ws = window.conversionClient?.ws;

        if (!ws || ws.readyState !== WebSocket.OPEN) {
            console.error('[Pairing] WebSocket not connected');
            showStatus('WebSocket not connected. Please refresh the page.', 'error');
            return;
        }

        const message = {
            type: 'register_pairing',
            session_id: sessionId,
            role: 'desktop'
        };

        try {
            ws.send(JSON.stringify(message));
            console.log('[Pairing] Registered as desktop for session:', sessionId);
        } catch (error) {
            console.error('[Pairing] Failed to register WebSocket:', error);
            showStatus('Failed to register pairing session', 'error');
        }
    }

    handleImageSynced(message) {
        console.log('[Pairing] Image synced:', message.image_index);

        // Add image to camera staging area
        const imageData = 'data:image/jpeg;base64,' + message.image_data;

        if (this.cameraManager && typeof this.cameraManager.addPageToStaging === 'function') {
            this.cameraManager.addPageToStaging(imageData);
        } else {
            console.warn('[Pairing] CameraManager not available or addPageToStaging not found');
        }

        // Update counter
        const count = parseInt(document.getElementById('imagesSyncedCount')?.textContent || '0') + 1;
        const counter = document.getElementById('imagesSyncedCount');
        if (counter) {
            counter.textContent = count;
        }

        // Show notification
        showStatus(`Image ${message.image_index + 1} received from mobile`, 'success');

        // Play notification sound (optional)
        this.playNotificationSound();
    }

    handlePeerStatus(message) {
        console.log('[Pairing] Peer status update:', message.peer_role, message.connected);

        if (message.peer_role === 'mobile') {
            const statusBadge = document.getElementById('pairingStatusBadge');
            const statusText = document.getElementById('pairingStatusText');

            if (message.connected) {
                // Mobile connected
                if (statusBadge) {
                    statusBadge.classList.add('connected');
                }
                if (statusText) {
                    statusText.textContent = 'Mobile connected ✓';
                    statusText.setAttribute('data-i18n', 'camera.pairing.connected');
                }
                showStatus('Mobile device connected', 'success');
            } else {
                // Mobile disconnected
                if (statusBadge) {
                    statusBadge.classList.remove('connected');
                }
                if (statusText) {
                    statusText.textContent = 'Mobile disconnected';
                    statusText.setAttribute('data-i18n', 'camera.pairing.disconnected');
                }
                showStatus('Mobile device disconnected', 'warning');
            }
        }
    }

    handlePairingExpired(message) {
        console.log('[Pairing] Session expired:', message.reason);
        this.expireSession(message.reason);
    }

    async cancelSession() {
        if (!this.currentSession) {
            console.warn('[Pairing] No active session to cancel');
            return;
        }

        try {
            const authToken = window.authManager?.token || '';

            await fetch(`/api/v1/camera/pairing/cancel/${this.currentSession.session_id}`, {
                method: 'POST',
                headers: {
                    'Authorization': authToken ? `Bearer ${authToken}` : ''
                }
            });

            console.log('[Pairing] Session cancelled');
            showStatus('Pairing session cancelled', 'info');

        } catch (error) {
            console.error('[Pairing] Failed to cancel session:', error);
        }

        this.cleanup();
    }

    expireSession(reason) {
        console.log('[Pairing] Session expired:', reason);

        const message = reason === 'timeout'
            ? 'Pairing session expired. Please start a new pairing.'
            : 'Pairing session ended.';

        showStatus(message, 'warning');
        this.cleanup();
    }

    cleanup() {
        console.log('[Pairing] Cleaning up session');

        // Stop countdown
        if (this.countdownInterval) {
            clearInterval(this.countdownInterval);
            this.countdownInterval = null;
        }

        // Clear session
        this.currentSession = null;
        this.qrCode = null;

        // Reset UI
        const startBtn = document.getElementById('startPairingBtn');
        if (startBtn) {
            startBtn.hidden = false;
        }

        const activeView = document.getElementById('pairingActiveView');
        if (activeView) {
            activeView.hidden = true;
        }

        const qrContainer = document.getElementById('qrCodeContainer');
        if (qrContainer) {
            qrContainer.innerHTML = '';
        }

        const counter = document.getElementById('imagesSyncedCount');
        if (counter) {
            counter.textContent = '0';
        }
    }

    playNotificationSound() {
        // Optional: play a subtle notification sound
        // For now, just use a visual feedback flash
        const counter = document.querySelector('.pairing-stats');
        if (counter) {
            counter.style.background = 'rgba(40, 167, 69, 0.2)';
            setTimeout(() => {
                counter.style.background = 'white';
            }, 500);
        }
    }
}
