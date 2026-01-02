/**
 * CameraManager - Camera capture and page staging
 * Handles camera access, photo capture, image editing, and page management
 */

import { t, showStatus } from '../utils/helpers.js';

export class CameraManager {
    constructor() {
        this.stream = null;
        this.videoElement = null;
        this.canvasElement = null;
        this.currentDeviceId = null;
        this.availableCameras = [];
        this.stagedPages = [];  // {id, imageData, timestamp}
        this.nextPageId = 1;
    }

    async init() {
        console.log('[Camera] Initializing CameraManager');

        // Get DOM elements
        this.videoElement = document.getElementById('cameraPreview');
        this.canvasElement = document.getElementById('captureCanvas');

        if (!this.videoElement || !this.canvasElement) {
            console.error('[Camera] Required elements not found');
            return;
        }

        // Security: Add cleanup on page unload to prevent resource leaks
        window.addEventListener('beforeunload', () => this.cleanup());

        // Pause camera when tab becomes hidden
        document.addEventListener('visibilitychange', () => {
            if (document.hidden && this.stream) {
                console.log('[Camera] Tab hidden, stopping camera to save resources');
                this.stopCamera();
            }
        });

        // Enumerate cameras
        await this.enumerateCameras();

        // Setup event listeners
        this.setupEventListeners();

        // Initialize accessibility assistant
        this.a11yAssistant = new AccessibleCameraAssistant(this);
        await this.a11yAssistant.init();

        console.log('[Camera] CameraManager initialized');
    }

    async enumerateCameras() {
        try {
            const devices = await navigator.mediaDevices.enumerateDevices();
            this.availableCameras = devices.filter(d => d.kind === 'videoinput');

            console.log('[Camera] Found cameras:', this.availableCameras.length);

            // Populate camera selector
            const select = document.getElementById('cameraSelect');
            if (select) {
                select.innerHTML = '';
                this.availableCameras.forEach((camera, index) => {
                    const option = document.createElement('option');
                    option.value = camera.deviceId;
                    option.text = camera.label || `Camera ${index + 1}`;
                    select.appendChild(option);
                });
            }
        } catch (err) {
            console.error('[Camera] Error enumerating cameras:', err);
        }
    }

    setupEventListeners() {
        // Start Camera button
        const startBtn = document.getElementById('startCameraBtn');
        if (startBtn) {
            startBtn.addEventListener('click', () => this.startCamera());
        }

        // Stop Camera button
        const stopBtn = document.getElementById('stopCameraBtn');
        if (stopBtn) {
            stopBtn.addEventListener('click', () => this.stopCamera());
        }

        // Capture button
        const captureBtn = document.getElementById('captureBtn');
        if (captureBtn) {
            captureBtn.addEventListener('click', () => this.capturePhoto());
        }

        // Switch Camera button
        const switchBtn = document.getElementById('switchCameraBtn');
        if (switchBtn) {
            switchBtn.addEventListener('click', () => this.switchCamera());
        }

        // Camera selector
        const cameraSelect = document.getElementById('cameraSelect');
        if (cameraSelect) {
            cameraSelect.addEventListener('change', (e) => {
                this.stopCamera();
                this.startCamera(e.target.value);
            });
        }

        // Add Page button
        const addPageBtn = document.getElementById('addPageBtn');
        if (addPageBtn) {
            addPageBtn.addEventListener('click', () => {
                if (this.stream) {
                    this.capturePhoto();
                }
            });
        }

        // Clear All button
        const clearAllBtn = document.getElementById('clearAllBtn');
        if (clearAllBtn) {
            clearAllBtn.addEventListener('click', () => this.clearAllPages());
        }

        // Submit Pages button
        const submitBtn = document.getElementById('submitPagesBtn');
        if (submitBtn) {
            submitBtn.addEventListener('click', () => this.submitMultiPageJob());
        }

        // Image Editor - Rotate Left button
        const rotateLeftBtn = document.getElementById('rotateLeftBtn');
        if (rotateLeftBtn) {
            rotateLeftBtn.addEventListener('click', () => this.applyRotation(-90));
        }

        // Image Editor - Rotate Right button
        const rotateRightBtn = document.getElementById('rotateRightBtn');
        if (rotateRightBtn) {
            rotateRightBtn.addEventListener('click', () => this.applyRotation(90));
        }

        // Image Editor - Brightness slider
        const brightnessSlider = document.getElementById('brightnessSlider');
        if (brightnessSlider) {
            brightnessSlider.addEventListener('input', (e) => {
                const value = parseInt(e.target.value);
                document.getElementById('brightnessValue').textContent = value;
                this.applyBrightness(value);
            });
        }

        // Image Editor - Contrast slider
        const contrastSlider = document.getElementById('contrastSlider');
        if (contrastSlider) {
            contrastSlider.addEventListener('input', (e) => {
                const value = parseInt(e.target.value);
                document.getElementById('contrastValue').textContent = value;
                this.applyContrast(value);
            });
        }

        // Image Editor - Accept button
        const acceptEditBtn = document.getElementById('acceptEditBtn');
        if (acceptEditBtn) {
            acceptEditBtn.addEventListener('click', () => this.acceptEdit());
        }

        // Image Editor - Cancel/Retake button
        const cancelEditBtn = document.getElementById('cancelEditBtn');
        if (cancelEditBtn) {
            cancelEditBtn.addEventListener('click', () => this.cancelEdit());
        }
    }

    async startCamera(deviceId = null) {
        console.log('[Camera] Starting camera...');

        const constraints = {
            video: {
                deviceId: deviceId ? { exact: deviceId } : undefined,
                facingMode: deviceId ? undefined : { ideal: 'environment' },
                width: { ideal: 1920 },
                height: { ideal: 1080 }
            }
        };

        try {
            this.stream = await navigator.mediaDevices.getUserMedia(constraints);
            this.videoElement.srcObject = this.stream;
            this.currentDeviceId = deviceId;

            console.log('[Camera] Camera started successfully');

            // Start accessibility analysis if enabled
            if (this.a11yAssistant && this.a11yAssistant.enabled) {
                this.a11yAssistant.startAnalysis();
            }

            // Update UI
            document.getElementById('startCameraBtn').hidden = true;
            document.getElementById('stopCameraBtn').hidden = false;
            document.getElementById('captureBtn').hidden = false;
            if (this.availableCameras.length > 1) {
                document.getElementById('switchCameraBtn').hidden = false;
                document.querySelector('.camera-selector').hidden = false;
            }

        } catch (err) {
            console.error('[Camera] Failed to start camera:', err);
            alert('Camera permission denied or not available. Please allow camera access.');
        }
    }

    stopCamera() {
        console.log('[Camera] Stopping camera...');

        // Stop accessibility analysis
        if (this.a11yAssistant && this.a11yAssistant.enabled) {
            this.a11yAssistant.stopAnalysis();
        }

        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.stream = null;
            this.videoElement.srcObject = null;
        }

        // Update UI
        document.getElementById('startCameraBtn').hidden = false;
        document.getElementById('stopCameraBtn').hidden = true;
        document.getElementById('captureBtn').hidden = true;
        document.getElementById('switchCameraBtn').hidden = true;
        document.querySelector('.camera-selector').hidden = true;
    }

    /**
     * Security: Cleanup resources to prevent leaks
     */
    cleanup() {
        console.log('[Camera] Cleaning up resources...');
        this.stopCamera();
        if (this.a11yAssistant) {
            this.a11yAssistant.cleanup?.();
        }
    }

    async switchCamera() {
        if (this.availableCameras.length < 2) return;

        // Find next camera
        const currentIndex = this.availableCameras.findIndex(
            c => c.deviceId === this.currentDeviceId
        );
        const nextIndex = (currentIndex + 1) % this.availableCameras.length;
        const nextCamera = this.availableCameras[nextIndex];

        // Switch to next camera
        this.stopCamera();
        await this.startCamera(nextCamera.deviceId);

        // Update selector
        const select = document.getElementById('cameraSelect');
        if (select) {
            select.value = nextCamera.deviceId;
        }
    }

    capturePhoto() {
        if (!this.stream) {
            console.warn('[Camera] Cannot capture: camera not started');
            return;
        }

        const video = this.videoElement;
        const canvas = this.canvasElement;
        const ctx = canvas.getContext('2d');

        // Set canvas to high resolution for better quality
        // Use actual video resolution instead of display size
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;

        // Draw current frame at full resolution
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

        // Auto-crop if accessibility assistant has detected edges
        let imageData;
        if (this.a11yAssistant &&
            this.a11yAssistant.enabled &&
            this.a11yAssistant.lastDetectedCorners &&
            !this.a11yAssistant.degradedMode) {

            console.log('[Camera] Auto-crop enabled: applying perspective correction');
            imageData = this.autoCropAndCorrect(canvas, this.a11yAssistant.lastDetectedCorners);
        } else {
            // No auto-crop, use full frame
            const jpegQuality = this.a11yAssistant?.config.jpeg_quality_normal || 0.85;
            imageData = canvas.toDataURL('image/jpeg', jpegQuality);
            console.log('[Camera] Photo captured (no auto-crop)');
        }

        // Open editor for adjustments
        this.openEditor(imageData);
    }

    autoCropAndCorrect(sourceCanvas, corners) {
        try {
            console.log('[Camera] Applying auto-crop with corners:', corners);

            // Scale corners from analysis canvas to full video resolution
            const scaleX = sourceCanvas.width / this.a11yAssistant.analysisCanvas.width;
            const scaleY = sourceCanvas.height / this.a11yAssistant.analysisCanvas.height;

            const scaledCorners = {
                topLeftCorner: { x: corners.topLeftCorner.x * scaleX, y: corners.topLeftCorner.y * scaleY },
                topRightCorner: { x: corners.topRightCorner.x * scaleX, y: corners.topRightCorner.y * scaleY },
                bottomRightCorner: { x: corners.bottomRightCorner.x * scaleX, y: corners.bottomRightCorner.y * scaleY },
                bottomLeftCorner: { x: corners.bottomLeftCorner.x * scaleX, y: corners.bottomLeftCorner.y * scaleY }
            };

            console.log('[Camera] Scaled corners for full resolution:', scaledCorners);

            // Use jscanify to extract and correct perspective
            // First convert canvas to cv.Mat
            const mat = cv.imread(sourceCanvas);

            // Apply perspective correction using jscanify
            const correctedImage = this.a11yAssistant.scanner.extractPaper(mat, scaledCorners);

            // Create output canvas for corrected image
            const outputCanvas = document.createElement('canvas');
            cv.imshow(outputCanvas, correctedImage);

            // Clean up OpenCV mats
            mat.delete();
            correctedImage.delete();

            // Convert to dataURL
            const jpegQuality = this.a11yAssistant?.config.jpeg_quality_autocrop || 0.90;
            const result = outputCanvas.toDataURL('image/jpeg', jpegQuality);
            console.log('[Camera] ✓ Auto-crop and perspective correction applied');

            return result;
        } catch (error) {
            console.error('[Camera] Auto-crop failed, using original:', error);
            // Fallback to original image if auto-crop fails
            const jpegQuality = this.a11yAssistant?.config.jpeg_quality_normal || 0.85;
            return sourceCanvas.toDataURL('image/jpeg', jpegQuality);
        }
    }

    openEditor(imageData) {
        console.log('[Camera] Opening image editor');

        // Store original image
        this.currentEditImage = new Image();
        this.currentEditImage.onload = () => {
            this.editCanvas = document.getElementById('editCanvas');
            this.editCtx = this.editCanvas.getContext('2d');

            // Initialize edit state
            this.editRotation = 0;
            this.editBrightness = 0;
            this.editContrast = 0;

            // Set canvas size
            this.editCanvas.width = this.currentEditImage.width;
            this.editCanvas.height = this.currentEditImage.height;

            // Initial draw
            this.redrawEditCanvas();

            // Show editor, hide camera controls
            document.getElementById('cameraControls').hidden = true;
            document.getElementById('imageEditor').hidden = false;

            // Reset sliders
            document.getElementById('brightnessSlider').value = 0;
            document.getElementById('contrastSlider').value = 0;
            document.getElementById('brightnessValue').textContent = '0';
            document.getElementById('contrastValue').textContent = '0';
        };
        this.currentEditImage.src = imageData;
    }

    closeEditor() {
        console.log('[Camera] Closing image editor');

        // Hide editor, show camera controls
        document.getElementById('imageEditor').hidden = true;
        document.getElementById('cameraControls').hidden = false;

        // Clear edit state
        this.currentEditImage = null;
        this.editCanvas = null;
        this.editCtx = null;
        this.editRotation = 0;
        this.editBrightness = 0;
        this.editContrast = 0;
    }

    applyRotation(degrees) {
        this.editRotation = (this.editRotation + degrees + 360) % 360;
        console.log('[Camera] Rotation applied:', this.editRotation, 'degrees');
        this.redrawEditCanvas();
    }

    applyBrightness(value) {
        this.editBrightness = value;
        console.log('[Camera] Brightness:', this.editBrightness);
        this.redrawEditCanvas();
    }

    applyContrast(value) {
        this.editContrast = value;
        console.log('[Camera] Contrast:', this.editContrast);
        this.redrawEditCanvas();
    }

    redrawEditCanvas() {
        if (!this.editCanvas || !this.currentEditImage) return;

        const ctx = this.editCtx;
        const img = this.currentEditImage;

        // Adjust canvas size for rotation
        if (this.editRotation === 90 || this.editRotation === 270) {
            this.editCanvas.width = img.height;
            this.editCanvas.height = img.width;
        } else {
            this.editCanvas.width = img.width;
            this.editCanvas.height = img.height;
        }

        // Clear canvas
        ctx.clearRect(0, 0, this.editCanvas.width, this.editCanvas.height);

        // Save context state
        ctx.save();

        // Apply rotation
        if (this.editRotation !== 0) {
            ctx.translate(this.editCanvas.width / 2, this.editCanvas.height / 2);
            ctx.rotate((this.editRotation * Math.PI) / 180);
            ctx.translate(-img.width / 2, -img.height / 2);
        } else {
            ctx.translate(0, 0);
        }

        // Apply brightness and contrast filters
        const brightnessPercent = 100 + this.editBrightness;
        const contrastPercent = 100 + this.editContrast;
        ctx.filter = `brightness(${brightnessPercent}%) contrast(${contrastPercent}%)`;

        // Draw image
        ctx.drawImage(img, 0, 0);

        // Restore context
        ctx.restore();
    }

    acceptEdit() {
        console.log('[Camera] Accepting edited image');

        if (!this.editCanvas) {
            console.error('[Camera] No edit canvas found');
            return;
        }

        // Get final edited image as base64
        const editedImageData = this.editCanvas.toDataURL('image/jpeg', 0.85);

        // Add to staging
        this.addPageToStaging(editedImageData);

        // Close editor
        this.closeEditor();
    }

    cancelEdit() {
        console.log('[Camera] Cancelling edit, retaking photo');

        // Just close editor, return to camera
        this.closeEditor();
    }

    addPageToStaging(imageData) {
        const page = {
            id: this.nextPageId++,
            imageData: imageData,
            timestamp: Date.now()
        };

        this.stagedPages.push(page);
        console.log('[Camera] Page added to staging. Total pages:', this.stagedPages.length);

        this.renderPageThumbnails();
        this.updateSubmitButton();
    }

    renderPageThumbnails() {
        const container = document.getElementById('pageList');
        if (!container) return;

        container.innerHTML = '';

        this.stagedPages.forEach((page, index) => {
            const thumb = document.createElement('div');
            thumb.className = 'page-thumbnail';
            thumb.dataset.pageId = page.id;
            thumb.dataset.pageIndex = index;
            thumb.draggable = true;

            thumb.innerHTML = `
                <img src="${page.imageData}" alt="Page ${index + 1}">
                <span class="page-number">${index + 1}</span>
                <button class="delete-page" data-page-id="${page.id}" aria-label="Delete page ${index + 1}">×</button>
            `;

            // Delete button handler
            const deleteBtn = thumb.querySelector('.delete-page');
            deleteBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.deletePage(page.id);
            });

            // Drag-and-drop handlers
            thumb.addEventListener('dragstart', (e) => this.handleDragStart(e));
            thumb.addEventListener('dragover', (e) => this.handleDragOver(e));
            thumb.addEventListener('drop', (e) => this.handleDrop(e));
            thumb.addEventListener('dragend', (e) => this.handleDragEnd(e));

            container.appendChild(thumb);
        });

        // Update page count
        document.getElementById('pageCount').textContent = this.stagedPages.length;
    }

    handleDragStart(e) {
        const pageIndex = parseInt(e.currentTarget.dataset.pageIndex);
        e.dataTransfer.effectAllowed = 'move';
        e.dataTransfer.setData('text/plain', pageIndex);
        e.currentTarget.classList.add('dragging');
        console.log('[Camera] Drag start: page', pageIndex);
    }

    handleDragOver(e) {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';

        // Visual feedback
        const draggingElement = document.querySelector('.dragging');
        const afterElement = this.getDragAfterElement(e.currentTarget.parentElement, e.clientY);

        if (afterElement == null) {
            e.currentTarget.parentElement.appendChild(draggingElement);
        } else {
            e.currentTarget.parentElement.insertBefore(draggingElement, afterElement);
        }
    }

    handleDrop(e) {
        e.preventDefault();
        e.stopPropagation();

        const fromIndex = parseInt(e.dataTransfer.getData('text/plain'));
        const toElement = e.currentTarget;
        const toIndex = parseInt(toElement.dataset.pageIndex);

        console.log('[Camera] Drop: moving page from', fromIndex, 'to', toIndex);

        if (fromIndex !== toIndex) {
            this.reorderPages(fromIndex, toIndex);
        }
    }

    handleDragEnd(e) {
        e.currentTarget.classList.remove('dragging');
        console.log('[Camera] Drag end');
    }

    getDragAfterElement(container, y) {
        const draggableElements = [...container.querySelectorAll('.page-thumbnail:not(.dragging)')];

        return draggableElements.reduce((closest, child) => {
            const box = child.getBoundingClientRect();
            const offset = y - box.top - box.height / 2;

            if (offset < 0 && offset > closest.offset) {
                return { offset: offset, element: child };
            } else {
                return closest;
            }
        }, { offset: Number.NEGATIVE_INFINITY }).element;
    }

    reorderPages(fromIndex, toIndex) {
        console.log('[Camera] Reordering pages:', fromIndex, '→', toIndex);

        // Remove page from old position
        const [movedPage] = this.stagedPages.splice(fromIndex, 1);

        // Insert at new position
        this.stagedPages.splice(toIndex, 0, movedPage);

        // Re-render thumbnails
        this.renderPageThumbnails();
    }

    deletePage(pageId) {
        const index = this.stagedPages.findIndex(p => p.id === pageId);
        if (index !== -1) {
            this.stagedPages.splice(index, 1);
            console.log('[Camera] Page deleted. Remaining:', this.stagedPages.length);
            this.renderPageThumbnails();
            this.updateSubmitButton();
        }
    }

    clearAllPages() {
        if (this.stagedPages.length === 0) return;

        if (confirm('Clear all captured pages?')) {
            this.stagedPages = [];
            console.log('[Camera] All pages cleared');
            this.renderPageThumbnails();
            this.updateSubmitButton();
        }
    }

    updateSubmitButton() {
        const btn = document.getElementById('submitPagesBtn');
        if (btn) {
            btn.disabled = this.stagedPages.length === 0;
        }
    }

    async submitMultiPageJob() {
        if (this.stagedPages.length === 0) {
            alert('Please capture at least one page');
            return;
        }

        console.log('[Camera] Submitting multi-page job with', this.stagedPages.length, 'pages');

        // Get conversion settings from camera tab's own selectors
        const config = {
            ocr_language: document.getElementById('cameraOcrLanguage')?.value || 'eng',
            pdfa_level: document.getElementById('cameraPdfType')?.value || '2',
            enable_ocr: document.getElementById('cameraOcrEnabled')?.checked ?? true,
            compression_profile: document.getElementById('cameraCompression')?.value || 'balanced'
        };

        // Create multi-file WebSocket message
        const message = {
            type: 'submit',
            multi_file_mode: true,
            filenames: this.stagedPages.map((page, i) => `page_${String(i + 1).padStart(3, '0')}.jpg`),
            filesData: this.stagedPages.map(page => {
                // Remove data:image/jpeg;base64, prefix
                return page.imageData.split(',')[1];
            }),
            config: config
        };

        // Submit via existing WebSocket client
        if (window.conversionClient && window.conversionClient.ws && window.conversionClient.ws.readyState === WebSocket.OPEN) {
            window.conversionClient.ws.send(JSON.stringify(message));
            console.log('[Camera] Multi-page job submitted');

            // Clear staging after successful submission
            this.stagedPages = [];
            this.renderPageThumbnails();
            this.updateSubmitButton();

            // Switch to Jobs tab to see progress
            const jobsTabBtn = document.getElementById('tab-jobs-btn');
            if (jobsTabBtn) {
                jobsTabBtn.click();
            }
        } else {
            console.error('[Camera] WebSocket not connected');
            alert('Connection error. Please ensure you are connected.');
        }
    }
}

// ============================================================================
// Accessible Camera Assistant Class
// ============================================================================

/**
 * AccessibleCameraAssistant provides audio guidance for blind and low-vision users
 * when capturing documents with the camera.
 *
 * Features:
 * - Real-time document edge detection using jscanify
 * - Audio tone feedback (pitch varies with confidence)
 * - Voice announcements for guidance
 * - Auto-detection of screen readers
 * - Manual controls (toggle, volume, test)
 * - Auto-capture when document is stable
 */
