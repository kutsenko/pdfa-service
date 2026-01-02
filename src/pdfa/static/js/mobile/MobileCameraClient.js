/**
 * MobileCameraClient - Mobile camera capture and sync
 * Handles camera access, image capture, editing, and desktop synchronization
 */

export class MobileCameraClient {
    constructor() {
        this.ws = null;
        this.sessionId = null;
        this.imageCounter = 0;
        this.stream = null;
        this.currentDeviceId = null;
        this.rotation = 0;
        this.editingImage = null;

        console.log('[Mobile] Initializing MobileCameraClient');
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.checkUrlPairingCode();
    }

    setupEventListeners() {
        // Pairing form
        const pairingForm = document.getElementById('pairingForm');
        if (pairingForm) {
            pairingForm.addEventListener('submit', (e) => {
                e.preventDefault();
                const code = document.getElementById('pairingCodeInput')?.value.trim().toUpperCase();
                if (code) {
                    this.joinSession(code);
                }
            });
        }

        // Camera controls
        document.getElementById('mobileCaptureBtn')?.addEventListener('click', () => {
            this.capturePhoto();
        });

        document.getElementById('switchCameraBtn')?.addEventListener('click', () => {
            this.switchCamera();
        });

        document.getElementById('disconnectBtn')?.addEventListener('click', () => {
            this.disconnect();
        });

        // Editor controls
        document.getElementById('rotateLeftBtn')?.addEventListener('click', () => {
            this.rotateImage(-90);
        });

        document.getElementById('rotateRightBtn')?.addEventListener('click', () => {
            this.rotateImage(90);
        });

        document.getElementById('sendBtn')?.addEventListener('click', () => {
            this.sendImage();
        });

        document.getElementById('retakeBtn')?.addEventListener('click', () => {
            this.showScreen('cameraScreen');
        });

        // Prevent accidental page refresh
        window.addEventListener('beforeunload', (e) => {
            if (this.sessionId) {
                e.preventDefault();
                e.returnValue = '';
            }
        });
    }

    checkUrlPairingCode() {
        // Auto-fill pairing code from URL parameter
        const urlParams = new URLSearchParams(window.location.search);
        const code = urlParams.get('code');
        if (code) {
            const input = document.getElementById('pairingCodeInput');
            if (input) {
                input.value = code.toUpperCase();
                // Auto-focus the connect button for easy tap
                setTimeout(() => {
                    const submitBtn = document.querySelector('.pairing-form button[type="submit"]');
                    submitBtn?.focus();
                }, 100);
            }
        }
    }

    async joinSession(pairingCode) {
        try {
            console.log('[Mobile] Joining session with code:', pairingCode);

            const formData = new FormData();
            formData.append('pairing_code', pairingCode);

            const response = await fetch('/api/v1/camera/pairing/join', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to join session');
            }

            const session = await response.json();
            this.sessionId = session.session_id;

            console.log('[Mobile] Joined session:', this.sessionId);

            // Connect WebSocket
            await this.connectWebSocket();

            // Start camera
            await this.startCamera();

            // Show camera screen
            this.showScreen('cameraScreen');

        } catch (error) {
            console.error('[Mobile] Failed to join session:', error);
            alert(error.message || 'Failed to connect. Please check the code and try again.');
        }
    }

    async connectWebSocket() {
        return new Promise((resolve, reject) => {
            const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${location.host}/ws`;

            console.log('[Mobile] Connecting to WebSocket:', wsUrl);

            this.ws = new WebSocket(wsUrl);

            this.ws.onopen = () => {
                console.log('[Mobile] WebSocket connected');

                // Register for pairing
                this.ws.send(JSON.stringify({
                    type: 'register_pairing',
                    session_id: this.sessionId,
                    role: 'mobile'
                }));

                resolve();
            };

            this.ws.onmessage = (event) => {
                this.handleMessage(event);
            };

            this.ws.onerror = (error) => {
                console.error('[Mobile] WebSocket error:', error);
                reject(error);
            };

            this.ws.onclose = () => {
                console.log('[Mobile] WebSocket closed');
                this.handleDisconnection();
            };
        });
    }

    handleMessage(event) {
        try {
            const message = JSON.parse(event.data);
            console.log('[Mobile] WebSocket message:', message);

            switch (message.type) {
                case 'pairing_peer_status':
                    console.log('[Mobile] Desktop status:', message.connected ? 'connected' : 'disconnected');
                    break;

                case 'pairing_expired':
                    console.log('[Mobile] Pairing expired:', message.reason);
                    alert('Pairing session expired');
                    this.disconnect();
                    break;

                case 'error':
                    console.error('[Mobile] Error:', message.message);
                    if (message.error_code === 'SESSION_NOT_JOINED' || message.error_code === 'INVALID_SESSION') {
                        alert('Session no longer valid. Please scan a new QR code.');
                        this.disconnect();
                    }
                    break;
            }
        } catch (error) {
            console.error('[Mobile] Failed to parse message:', error);
        }
    }

    async startCamera() {
        try {
            console.log('[Mobile] Starting camera');

            const constraints = {
                video: {
                    facingMode: { ideal: 'environment' }, // Back camera
                    width: { ideal: 1920 },
                    height: { ideal: 1080 }
                }
            };

            this.stream = await navigator.mediaDevices.getUserMedia(constraints);

            const video = document.getElementById('mobileCamera');
            if (video) {
                video.srcObject = this.stream;
            }

            console.log('[Mobile] Camera started');

        } catch (error) {
            console.error('[Mobile] Camera error:', error);
            alert('Failed to access camera. Please check permissions and try again.');
            this.disconnect();
        }
    }

    async switchCamera() {
        try {
            console.log('[Mobile] Switching camera');

            // Get available cameras
            const devices = await navigator.mediaDevices.enumerateDevices();
            const cameras = devices.filter(d => d.kind === 'videoinput');

            if (cameras.length < 2) {
                console.warn('[Mobile] No other camera available');
                return;
            }

            // Find current camera
            const currentTrack = this.stream.getVideoTracks()[0];
            const currentSettings = currentTrack.getSettings();
            const currentId = currentSettings.deviceId;

            // Find next camera
            const currentIndex = cameras.findIndex(c => c.deviceId === currentId);
            const nextIndex = (currentIndex + 1) % cameras.length;
            const nextCamera = cameras[nextIndex];

            // Stop current stream
            this.stream.getTracks().forEach(track => track.stop());

            // Start new camera
            this.stream = await navigator.mediaDevices.getUserMedia({
                video: {
                    deviceId: { exact: nextCamera.deviceId },
                    width: { ideal: 1920 },
                    height: { ideal: 1080 }
                }
            });

            const video = document.getElementById('mobileCamera');
            if (video) {
                video.srcObject = this.stream;
            }

            console.log('[Mobile] Switched to camera:', nextCamera.label || nextCamera.deviceId);

        } catch (error) {
            console.error('[Mobile] Failed to switch camera:', error);
        }
    }

    capturePhoto() {
        console.log('[Mobile] Capturing photo');

        const video = document.getElementById('mobileCamera');
        if (!video || !video.videoWidth) {
            console.error('[Mobile] Video not ready');
            return;
        }

        const canvas = document.createElement('canvas');
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;

        const ctx = canvas.getContext('2d');
        ctx.drawImage(video, 0, 0);

        // Save for editing
        this.editingImage = canvas;
        this.rotation = 0;

        // Show editor
        this.showEditor();
    }

    showEditor() {
        const editCanvas = document.getElementById('mobileEditCanvas');
        if (!editCanvas || !this.editingImage) {
            console.error('[Mobile] Editor not ready');
            return;
        }

        editCanvas.width = this.editingImage.width;
        editCanvas.height = this.editingImage.height;

        this.renderEditCanvas();
        this.showScreen('editorScreen');
    }

    rotateImage(degrees) {
        this.rotation = (this.rotation + degrees) % 360;
        if (this.rotation < 0) {
            this.rotation += 360;
        }

        console.log('[Mobile] Rotated to:', this.rotation);
        this.renderEditCanvas();
    }

    renderEditCanvas() {
        const canvas = document.getElementById('mobileEditCanvas');
        if (!canvas || !this.editingImage) {
            return;
        }

        const ctx = canvas.getContext('2d');

        // Handle rotation dimensions
        if (this.rotation === 90 || this.rotation === 270) {
            canvas.width = this.editingImage.height;
            canvas.height = this.editingImage.width;
        } else {
            canvas.width = this.editingImage.width;
            canvas.height = this.editingImage.height;
        }

        // Clear canvas
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // Apply rotation
        ctx.save();
        ctx.translate(canvas.width / 2, canvas.height / 2);
        ctx.rotate((this.rotation * Math.PI) / 180);
        ctx.drawImage(
            this.editingImage,
            -this.editingImage.width / 2,
            -this.editingImage.height / 2
        );
        ctx.restore();
    }

    sendImage() {
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
            console.error('[Mobile] WebSocket not connected');
            alert('Connection lost. Please reconnect.');
            return;
        }

        const canvas = document.getElementById('mobileEditCanvas');
        if (!canvas) {
            console.error('[Mobile] Canvas not found');
            return;
        }

        console.log('[Mobile] Sending image', this.imageCounter);

        // Convert to JPEG base64
        const imageData = canvas.toDataURL('image/jpeg', 0.85).split(',')[1];

        const message = {
            type: 'sync_image',
            session_id: this.sessionId,
            image_data: imageData,
            image_index: this.imageCounter,
            metadata: {
                timestamp: new Date().toISOString(),
                width: canvas.width,
                height: canvas.height,
                rotation: this.rotation
            }
        };

        try {
            this.ws.send(JSON.stringify(message));

            this.imageCounter++;
            const counter = document.getElementById('imageCount');
            if (counter) {
                counter.textContent = this.imageCounter;
            }

            // Show success feedback
            this.showSyncFeedback();

            // Return to camera
            this.showScreen('cameraScreen');

            console.log('[Mobile] Image sent successfully');

        } catch (error) {
            console.error('[Mobile] Failed to send image:', error);
            alert('Failed to send image. Please try again.');
        }
    }

    showSyncFeedback() {
        // Flash the counter with success color
        const counter = document.querySelector('.counter');
        if (counter) {
            counter.style.background = 'rgba(40, 167, 69, 0.9)';
            setTimeout(() => {
                counter.style.background = 'rgba(0, 0, 0, 0.7)';
            }, 500);
        }

        // Optional: Play haptic feedback (iOS/Android)
        if (navigator.vibrate) {
            navigator.vibrate(50);
        }
    }

    showScreen(screenId) {
        document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
        const screen = document.getElementById(screenId);
        if (screen) {
            screen.classList.add('active');
        }
    }

    handleDisconnection() {
        console.log('[Mobile] Handling disconnection');

        // Show alert if we were connected
        if (this.sessionId) {
            alert('Disconnected from desktop. Please reconnect.');
        }

        this.disconnect();
    }

    disconnect() {
        console.log('[Mobile] Disconnecting');

        // Stop camera
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.stream = null;
        }

        // Close WebSocket
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }

        // Reset state
        this.sessionId = null;
        this.imageCounter = 0;
        this.rotation = 0;
        this.editingImage = null;

        // Reset counter
        const counter = document.getElementById('imageCount');
        if (counter) {
            counter.textContent = '0';
        }

        // Show pairing screen
        this.showScreen('pairingScreen');
    }
}
