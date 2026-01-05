/**
 * ConversionClient - WebSocket-based PDF/A conversion client
 * Handles real-time conversion progress updates, job management, and event tracking
 */

import { showStatus, t, formatFileSize } from '../utils/helpers.js';

export class ConversionClient {
    constructor(authManager) {
        this.authManager = authManager;
        this.ws = null;
        this.currentJobId = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 30; // Increased from 5 for long conversions
        this.reconnectDelay = 2000; // Base delay: 2 seconds
        this.maxReconnectDelay = 30000; // Cap delay at 30 seconds
        this.reconnectResetTime = 60000; // Reset counter after 60s stable connection
        this.isIntentionallyClosed = false;
        this.pingInterval = null;
        this.statusPollInterval = null;
        this.connectionStableTimer = null;
        this.lastAnnouncementTime = 0;
        this.announcementThrottle = 5000; // Announce max every 5 seconds
        this.lastAnnouncedPercentage = -1; // Track last announced percentage
        this.percentageMilestones = [0, 25, 50, 75, 100]; // Always announce these
        // Event tracking for live event display
        this.events = []; // Store events for current job
        this.eventListVisible = false; // Track visibility state

        // Modal state tracking (NEW)
        this.modalDownloadUrl = null;
        this.modalFilename = null;
        this.lastDownloadUrl = null;
        this.lastFilename = null;

        // Initialize modal event listeners (NEW)
        this.initModalListeners();
    }

            connect() {
                if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                    return; // Already connected
                }

                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const wsUrl = `${protocol}//${window.location.host}/ws`;

                // Security: Token will be sent via AuthMessage after connection
                // (not in URL to prevent logging)
                this.updateWSStatus('connecting');

                try {
                    this.ws = new WebSocket(wsUrl);

                    this.ws.onopen = () => this.handleOpen();
                    this.ws.onmessage = (event) => this.handleMessage(event);
                    this.ws.onclose = (event) => this.handleClose(event);
                    this.ws.onerror = (error) => this.handleError(error);
                } catch (error) {
                    console.error('WebSocket connection failed:', error);
                    this.updateWSStatus('disconnected');
                }
            }

            handleOpen() {
                console.log('WebSocket connected');
                this.updateWSStatus('connected');

                // Security: Send authentication token via AuthMessage (not in URL)
                if (this.authManager.authEnabled && this.authManager.token) {
                    console.log('[WebSocket] Sending AuthMessage for secure authentication');
                    this.ws.send(JSON.stringify({
                        type: 'auth',
                        token: this.authManager.token
                    }));
                } else if (this.authManager.authEnabled && !this.authManager.token) {
                    console.warn('[WebSocket] Auth enabled but no token available');
                }

                // Stop status polling if it was running
                if (this.statusPollInterval) {
                    clearInterval(this.statusPollInterval);
                    this.statusPollInterval = null;
                }

                // Start ping interval (every 30 seconds)
                this.pingInterval = setInterval(() => {
                    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                        this.ws.send(JSON.stringify({ type: 'ping' }));
                    }
                }, 30000);

                // Reset reconnect counter after stable connection (60 seconds)
                if (this.connectionStableTimer) {
                    clearTimeout(this.connectionStableTimer);
                }
                this.connectionStableTimer = setTimeout(() => {
                    console.log('Connection stable - resetting reconnect counter');
                    this.reconnectAttempts = 0;
                }, this.reconnectResetTime);
            }

            handleMessage(event) {
                try {
                    const message = JSON.parse(event.data);
                    console.log('WebSocket message:', message);

                    switch (message.type) {
                        case 'job_accepted':
                            this.handleJobAccepted(message);
                            break;
                        case 'progress':
                            this.handleProgress(message);
                            break;
                        case 'completed':
                            this.handleCompleted(message);
                            // Notify JobsManager of completion
                            this.notifyJobsManager(message);
                            break;
                        case 'error':
                            this.handleJobError(message);
                            // Notify JobsManager of failure
                            this.notifyJobsManager({ ...message, type: 'failed' });
                            break;
                        case 'cancelled':
                            this.handleCancelled(message);
                            // Notify JobsManager of cancellation
                            this.notifyJobsManager(message);
                            break;
                        case 'pong':
                            // Keepalive response
                            break;
                        case 'job_event':
                            this.handleJobEvent(message);
                            // Notify JobsManager of job event
                            this.notifyJobsManager(message);
                            break;
                        case 'image_synced':
                            // Handle mobile-to-desktop image sync
                            if (window.cameraManager?.pairingManager) {
                                window.cameraManager.pairingManager.handleImageSynced(message);
                            }
                            break;
                        case 'pairing_peer_status':
                            // Handle peer connection status updates
                            if (window.cameraManager?.pairingManager) {
                                window.cameraManager.pairingManager.handlePeerStatus(message);
                            }
                            break;
                        case 'pairing_expired':
                            // Handle pairing session expiration
                            if (window.cameraManager?.pairingManager) {
                                window.cameraManager.pairingManager.handlePairingExpired(message);
                            }
                            break;
                        default:
                            console.warn('Unknown message type:', message.type);
                    }
                } catch (error) {
                    console.error('Error parsing WebSocket message:', error);
                }
            }

            handleClose(event) {
                console.log('WebSocket closed:', event.code, event.reason);

                // Clear ping interval
                if (this.pingInterval) {
                    clearInterval(this.pingInterval);
                    this.pingInterval = null;
                }

                // Clear stable connection timer
                if (this.connectionStableTimer) {
                    clearTimeout(this.connectionStableTimer);
                    this.connectionStableTimer = null;
                }

                if (!this.isIntentionallyClosed) {
                    this.updateWSStatus('disconnected');

                    // If we have an active job, start status polling as fallback
                    if (this.currentJobId) {
                        this.startStatusPolling();
                    }

                    this.attemptReconnect();
                }
            }

            handleError(error) {
                console.error('WebSocket error:', error);
                this.updateWSStatus('disconnected');
            }

            attemptReconnect() {
                if (this.reconnectAttempts >= this.maxReconnectAttempts) {
                    console.error('Max reconnection attempts reached');
                    showStatus(
                        `${t('error.ws_connection')} - Using status polling as fallback`,
                        'warning'
                    );
                    // Continue with status polling if job is active
                    return;
                }

                this.reconnectAttempts++;
                // Exponential backoff with max delay cap
                const calculatedDelay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
                const delay = Math.min(calculatedDelay, this.maxReconnectDelay);

                console.log(
                    `Reconnecting in ${delay / 1000}s (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`
                );

                // Show user-friendly status
                if (this.reconnectAttempts > 3) {
                    showStatus(
                        `Connection lost - Reconnecting (attempt ${this.reconnectAttempts})...`,
                        'warning'
                    );
                }

                setTimeout(() => {
                    this.connect();
                }, delay);
            }

            async submitJob(file, config) {
                if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
                    throw new Error(t('error.ws_connection'));
                }

                // Security: Validate file size before encoding
                const MAX_FILE_SIZE = 300 * 1024 * 1024; // 300MB
                if (file.size > MAX_FILE_SIZE) {
                    throw new Error(t('status.fileTooLarge', {
                        size: formatFileSize(file.size),
                        max: formatFileSize(MAX_FILE_SIZE)
                    }));
                }

                // Show progress container
                this.showProgress();

                // Base64-encode file
                const base64 = await this.fileToBase64(file);

                // Send submit message
                const message = {
                    type: 'submit',
                    filename: file.name,
                    fileData: base64,
                    config: config
                };

                this.ws.send(JSON.stringify(message));
            }

            async fileToBase64(file) {
                return new Promise((resolve, reject) => {
                    const reader = new FileReader();
                    reader.onload = () => {
                        // Remove data URL prefix (e.g., "data:application/pdf;base64,")
                        const base64 = reader.result.split(',')[1];
                        resolve(base64);
                    };
                    reader.onerror = reject;
                    reader.readAsDataURL(file);
                });
            }

            handleJobAccepted(message) {
                console.log('[handleJobAccepted] Job accepted:', message.job_id);
                this.currentJobId = message.job_id;

                // Clear previous events for new job
                console.log('[handleJobAccepted] Clearing previous events');
                this.clearEvents();

                this.updateProgress({
                    step: t('status.queued'),
                    percentage: 0,
                    message: t('status.queued')
                });
            }

            handleProgress(message) {
                // Translate progress step if translation exists
                const translatedStep = this.translateProgressStep(message.step);

                this.updateProgress({
                    step: translatedStep,
                    percentage: message.percentage,
                    current: message.current,
                    total: message.total,
                    message: message.message
                });
            }

            /**
             * Translate progress step message
             */
            translateProgressStep(step) {
                // Check if translations are available
                if (typeof translations === 'undefined' || typeof currentLang === 'undefined') {
                    return step; // Return original if translations not loaded
                }

                const translations_current = translations[currentLang] || translations.en;
                if (translations_current && translations_current.progressSteps && translations_current.progressSteps[step]) {
                    return translations_current.progressSteps[step];
                }
                return step; // Fallback to original if no translation found
            }

            handleCompleted(message) {
                console.log('[handleCompleted] Called with message:', message);
                this.hideProgress();

                // Store download info for modal (NEW)
                this.lastDownloadUrl = message.download_url;
                this.lastFilename = message.filename;

                // Download the file
                const downloadUrl = message.download_url;
                const filename = message.filename;
                console.log('[handleCompleted] Download URL:', downloadUrl, 'Filename:', filename);

                // Use fetch with auth token if available
                const headers = {};
                if (this.authManager.token) {
                    headers['Authorization'] = `Bearer ${this.authManager.token}`;
                }

                fetch(downloadUrl, { headers })
                    .then(response => response.blob())
                    .then(blob => {
                        // Create download link from blob
                        const link = document.createElement('a');
                        link.href = URL.createObjectURL(blob);
                        link.download = filename;
                        document.body.appendChild(link);
                        link.click();
                        document.body.removeChild(link);
                        URL.revokeObjectURL(link.href);
                    })
                    .catch(error => {
                        console.error('[Download] Failed:', error);
                        alert(t('auth.downloadFailed'));
                    });

                // Show success message
                showStatus(t('status.success'), 'success', {
                    label: t('status.viewPdf'),
                    onClick: () => {
                        // Fetch PDF with auth and open in new tab
                        const headers = {};
                        if (this.authManager.token) {
                            headers['Authorization'] = `Bearer ${this.authManager.token}`;
                        }

                        fetch(downloadUrl, { headers })
                            .then(response => response.blob())
                            .then(blob => {
                                const blobUrl = URL.createObjectURL(blob);
                                window.open(blobUrl, '_blank');
                            })
                            .catch(error => {
                                console.error('[View PDF] Failed:', error);
                                alert(t('auth.viewPdfFailed'));
                            });
                    }
                });

                // Announce completion to screen readers
                this.announceToScreenReader(t('status.success') + '. ' + t('status.viewPdf'));

                // Auto-hide success message after 10 seconds
                setTimeout(() => {
                    const statusDiv = document.getElementById('status');
                    if (statusDiv && statusDiv.classList.contains('success')) {
                        statusDiv.style.display = 'none';
                        statusDiv.className = 'status';
                    }
                }, 10000);

                // Show event summary modal after download (NEW)
                if (this.events.length > 0) {
                    setTimeout(() => {
                        this.showEventSummaryModal();
                    }, 500);
                }

                // Reset form
                const form = document.getElementById('converterForm');
                if (form) {
                    form.reset();
                }
                const fileName = document.getElementById('fileName');
                if (fileName) {
                    fileName.textContent = '';
                }
                this.currentJobId = null;
            }

            handleJobError(message) {
                this.hideProgress();

                let errorMsg = message.message;

                // Map error codes to translated messages
                if (message.error_code === 'JOB_TIMEOUT') {
                    errorMsg = t('error.job_timeout');
                } else if (message.error_code === 'JOB_CANCELLED') {
                    errorMsg = t('error.job_cancelled');
                }

                showStatus(t('status.error', { message: errorMsg }), 'error');

                // Announce error to screen readers
                this.announceToScreenReader(t('status.error', { message: errorMsg }));

                this.currentJobId = null;
            }

            handleCancelled(message) {
                this.hideProgress();
                showStatus(t('status.cancelled'), 'error');

                // Announce cancellation to screen readers
                this.announceToScreenReader(t('status.cancelled'));

                this.currentJobId = null;
            }

            cancelJob() {
                if (!this.currentJobId) return;

                // Disable cancel button
                const cancelBtn = document.getElementById('cancelBtn');
                if (cancelBtn) {
                    cancelBtn.disabled = true;
                }

                // Update status
                this.updateProgress({
                    step: t('status.cancelling'),
                    percentage: 0,
                    message: t('status.cancelling')
                });

                // Send cancel message
                if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                    this.ws.send(JSON.stringify({
                        type: 'cancel',
                        job_id: this.currentJobId
                    }));
                }
            }

            showProgress() {
                const progressContainer = document.getElementById('progressContainer');
                const progressBarWrapper = document.getElementById('progressBarWrapper');
                const progressFill = document.getElementById('progressFill');
                const progressPercentage = document.getElementById('progressPercentage');
                const progressMessage = document.getElementById('progressMessage');
                const progressStep = document.getElementById('progressStep');

                if (progressContainer) {
                    progressContainer.classList.add('visible');
                }

                // Initialize progress bar to 0%
                if (progressFill) {
                    progressFill.style.width = '0%';
                }

                if (progressPercentage) {
                    progressPercentage.textContent = '0%';
                }

                // Initialize progress messages
                if (progressMessage) {
                    progressMessage.textContent = t('status.processing');
                }

                if (progressStep) {
                    progressStep.textContent = t('status.processing');
                }

                // Set ARIA busy state
                if (progressBarWrapper) {
                    progressBarWrapper.setAttribute('aria-busy', 'true');
                    progressBarWrapper.setAttribute('aria-valuenow', '0');
                }

                // Hide status div
                const statusDiv = document.getElementById('status');
                if (statusDiv) {
                    statusDiv.style.display = 'none';
                }

                // Disable convert button and mark as busy
                const convertBtn = document.getElementById('convertBtn');
                if (convertBtn) {
                    convertBtn.disabled = true;
                    convertBtn.setAttribute('aria-busy', 'true');
                }

                // Enable cancel button
                const cancelBtn = document.getElementById('cancelBtn');
                if (cancelBtn) {
                    cancelBtn.disabled = false;
                }

                // Announce start of conversion
                this.announceToScreenReader(t('status.processing'));
            }

            hideProgress() {
                const progressContainer = document.getElementById('progressContainer');
                const progressBarWrapper = document.getElementById('progressBarWrapper');
                const progressFill = document.getElementById('progressFill');
                const progressPercentage = document.getElementById('progressPercentage');
                const progressMessage = document.getElementById('progressMessage');
                const progressStep = document.getElementById('progressStep');

                if (progressContainer) {
                    progressContainer.classList.remove('visible');
                }

                // Reset progress bar to 0
                if (progressFill) {
                    progressFill.style.width = '0%';
                }

                if (progressPercentage) {
                    progressPercentage.textContent = '0%';
                }

                // Clear progress messages
                if (progressMessage) {
                    progressMessage.textContent = '';
                }

                if (progressStep) {
                    progressStep.textContent = 'Processing...';
                }

                // Clear ARIA busy state
                if (progressBarWrapper) {
                    progressBarWrapper.setAttribute('aria-busy', 'false');
                    progressBarWrapper.setAttribute('aria-valuenow', '0');
                }

                // Enable convert button and clear busy state
                const convertBtn = document.getElementById('convertBtn');
                if (convertBtn) {
                    convertBtn.disabled = false;
                    convertBtn.setAttribute('aria-busy', 'false');
                }
            }

            updateProgress({ step, percentage, current, total, message }) {
                const progressStep = document.getElementById('progressStep');
                const progressFill = document.getElementById('progressFill');
                const progressPercentage = document.getElementById('progressPercentage');
                const progressMessage = document.getElementById('progressMessage');
                const progressBarWrapper = document.getElementById('progressBarWrapper');

                if (progressStep) {
                    progressStep.textContent = step || t('status.processing');
                }

                if (progressFill && progressPercentage && percentage !== undefined) {
                    progressFill.style.width = `${percentage}%`;
                    progressPercentage.textContent = `${Math.round(percentage)}%`;

                    // Update ARIA attributes for screen readers
                    if (progressBarWrapper) {
                        progressBarWrapper.setAttribute('aria-valuenow', Math.round(percentage));
                        progressBarWrapper.setAttribute('aria-busy', 'true');
                    }
                }

                let srMessage = '';
                if (progressMessage && message) {
                    // Translate OCR progress message if applicable
                    if (current !== undefined && total !== undefined) {
                        progressMessage.textContent = t('progress.ocr', { current, total });
                        srMessage = `${step}: ${Math.round(percentage)}%. Page ${current} of ${total}`;
                    } else {
                        progressMessage.textContent = message;
                        srMessage = `${step}: ${Math.round(percentage)}%. ${message}`;
                    }
                } else if (step && percentage !== undefined) {
                    srMessage = `${step}: ${Math.round(percentage)}%`;
                }

                // Announce progress to screen readers (intelligently throttled)
                if (srMessage && percentage !== undefined) {
                    this.announceToScreenReader(srMessage, Math.round(percentage));
                }
            }

            updateWSStatus(status) {
                const wsStatus = document.getElementById('wsStatus');
                const wsStatusText = document.getElementById('wsStatusText');

                if (wsStatus) {
                    wsStatus.className = 'ws-status ' + status;
                }

                if (wsStatusText) {
                    if (status === 'connected') {
                        wsStatusText.textContent = t('ws.connected');
                    } else if (status === 'connecting') {
                        wsStatusText.textContent = t('ws.connecting');
                    } else if (status === 'disconnected') {
                        wsStatusText.textContent = t('ws.disconnected');
                    }
                }
            }

            startStatusPolling() {
                // If already polling, don't start again
                if (this.statusPollInterval) {
                    return;
                }

                console.log('Starting status polling fallback for job:', this.currentJobId);

                // Poll every 2 seconds
                this.statusPollInterval = setInterval(async () => {
                    try {
                        const response = await fetch(`/api/v1/jobs/${this.currentJobId}/status`);

                        if (!response.ok) {
                            if (response.status === 404) {
                                // Job not found - might have been cleaned up
                                console.log('Job not found in status polling');
                                this.stopStatusPolling();
                                return;
                            }
                            throw new Error(`Status poll failed: ${response.status}`);
                        }

                        const status = await response.json();
                        console.log('Status poll result:', status);

                        // Update progress if available
                        if (status.progress !== undefined && status.message) {
                            this.updateProgress(status.progress, status.message, status.step || 'processing');
                        }

                        // Handle completion
                        if (status.status === 'completed' && status.download_url) {
                            console.log('Job completed (via polling)');
                            this.stopStatusPolling();
                            this.handleCompletedViaPolling({
                                job_id: status.job_id,
                                download_url: status.download_url,
                                filename: status.filename_output || status.filename,
                                size_bytes: 0 // Not available in status endpoint
                            });
                        } else if (status.status === 'failed') {
                            console.error('Job failed (via polling)');
                            this.stopStatusPolling();
                            showStatus(status.error || t('error.conversion'), 'error');
                            this.hideProgress();
                        }

                    } catch (error) {
                        console.error('Status polling error:', error);
                        // Don't stop polling on error - keep trying
                    }
                }, 2000);
            }

            stopStatusPolling() {
                if (this.statusPollInterval) {
                    clearInterval(this.statusPollInterval);
                    this.statusPollInterval = null;
                    console.log('Stopped status polling');
                }
            }

            handleCompletedViaPolling(data) {
                // Similar to handleCompleted but triggered by polling instead of WebSocket
                console.log('Conversion completed (via polling):', data.filename);

                // Update UI
                this.updateProgress(100, t('status.complete'), 'completed');

                // Show download button
                const downloadBtn = document.getElementById('downloadBtn');
                if (downloadBtn) {
                    downloadBtn.style.display = 'inline-block';
                    downloadBtn.onclick = () => {
                        // Use fetch with auth token if available
                        const headers = {};
                        if (this.authManager.token) {
                            headers['Authorization'] = `Bearer ${this.authManager.token}`;
                        }

                        fetch(data.download_url, { headers })
                            .then(response => response.blob())
                            .then(blob => {
                                const link = document.createElement('a');
                                link.href = URL.createObjectURL(blob);
                                link.download = data.filename || 'converted.pdf';
                                document.body.appendChild(link);
                                link.click();
                                document.body.removeChild(link);
                                URL.revokeObjectURL(link.href);
                            })
                            .catch(error => {
                                console.error('[Download] Failed:', error);
                                alert('Download failed. Please try again.');
                            });
                    };
                }

                // Hide progress after a delay
                setTimeout(() => {
                    this.hideProgress();
                }, 2000);

                // Show success message
                showStatus(t('status.success'), 'success');

                // Announce completion
                this.announceToScreenReader(`${t('status.complete')}. ${t('status.success')}`, 100);
            }

            updateProgress(percentage, message, step) {
                const progressFill = document.getElementById('progressFill');
                const progressPercentage = document.getElementById('progressPercentage');
                const progressMessage = document.getElementById('progressMessage');
                const progressStep = document.getElementById('progressStep');
                const progressBarWrapper = document.getElementById('progressBarWrapper');

                if (progressFill) {
                    progressFill.style.width = `${percentage}%`;
                }

                if (progressPercentage) {
                    progressPercentage.textContent = `${Math.round(percentage)}%`;
                }

                if (progressMessage) {
                    progressMessage.textContent = message;
                }

                if (progressStep) {
                    progressStep.textContent = step;
                }

                if (progressBarWrapper) {
                    progressBarWrapper.setAttribute('aria-valuenow', Math.round(percentage));
                }
            }

            disconnect() {
                this.isIntentionallyClosed = true;

                // Stop status polling
                this.stopStatusPolling();

                if (this.ws) {
                    this.ws.close();
                }
                if (this.pingInterval) {
                    clearInterval(this.pingInterval);
                    this.pingInterval = null;
                }
                if (this.connectionStableTimer) {
                    clearTimeout(this.connectionStableTimer);
                    this.connectionStableTimer = null;
                }
            }

            /**
             * Handle incoming job event from WebSocket
             */
            handleJobEvent(message) {
                console.log('[handleJobEvent] Job event received:', message);
                console.log('[handleJobEvent] Current events count:', this.events.length);

                // Store event
                this.events.push(message);

                // Update UI
                this.addEventToList(message);
                this.updateEventCount();

                // Show container if first event
                if (this.events.length === 1) {
                    this.showEventListContainer();
                }

                // Announce to screen reader (selective)
                this.announceEventToScreenReader(message);
            }

            /**
             * Add event to visual list (newest first)
             */
            addEventToList(event) {
                const eventList = document.getElementById('eventList');
                if (!eventList) {
                    console.error('[addEventToList] eventList element not found');
                    return;
                }

                console.log('[addEventToList] Adding event:', event.event_type, '| Current DOM items:', eventList.children.length);

                const eventItem = document.createElement('div');
                eventItem.className = `event-item event-${event.event_type}`;
                eventItem.setAttribute('role', 'article');

                // Icon
                const icon = this.getEventIcon(event.event_type);

                // Timestamp formatting
                const timestamp = new Date(event.timestamp);
                const timeStr = timestamp.toLocaleTimeString(
                    typeof currentLang !== 'undefined' ? currentLang : 'en'
                );

                // Translate message (with fallback to English)
                const localizedMessage = this.translateEventMessage(event);

                // Build HTML
                let html = `
                    <span class="event-icon" aria-hidden="true">${icon}</span>
                    <div class="event-content">
                        <div class="event-header">
                            <span class="event-message">${this.escapeHtml(localizedMessage)}</span>
                            <time class="event-timestamp" datetime="${event.timestamp}">
                                ${timeStr}
                            </time>
                        </div>
                `;

                // Add details if present (filter out i18n internal keys)
                const displayDetails = this.filterDetailsForDisplay(event.details);
                if (displayDetails && Object.keys(displayDetails).length > 0) {
                    html += `
                        <details class="event-details">
                            <summary>${t('events.details')}</summary>
                            <pre>${this.escapeHtml(JSON.stringify(displayDetails, null, 2))}</pre>
                        </details>
                    `;
                }

                html += `</div>`;
                eventItem.innerHTML = html;

                // Insert at top (newest first)
                eventList.insertBefore(eventItem, eventList.firstChild);

                console.log('[addEventToList] Event inserted | Total DOM items now:', eventList.children.length);
            }

            /**
             * Translate event message using i18n key or fallback to English
             */
            translateEventMessage(event) {
                // Check if translations are available
                if (typeof translations === 'undefined' || typeof currentLang === 'undefined') {
                    return event.message; // Return original message if translations not loaded
                }

                // Try to get translation from i18n key
                if (event.details && event.details._i18n_key) {
                    const key = event.details._i18n_key;
                    const params = event.details._i18n_params || {};

                    // Navigate nested key (e.g., "ocr_decision.skip.tagged_pdf")
                    const keys = key.split('.');
                    let translation = translations[currentLang]?.events?.messages;

                    for (const k of keys) {
                        if (translation && translation[k]) {
                            translation = translation[k];
                        } else {
                            translation = null;
                            break;
                        }
                    }

                    // If translation found, substitute parameters
                    if (translation && typeof translation === 'string') {
                        return this.substituteParams(translation, params);
                    }
                }

                // Fallback to English message from backend
                return event.message;
            }

            /**
             * Substitute parameters in translation template
             * Example: "OCR {decision}: {reason}" + {decision: "skip", reason: "tagged PDF"}
             *         -> "OCR skip: tagged PDF"
             */
            substituteParams(template, params) {
                let result = template;
                for (const [key, value] of Object.entries(params)) {
                    result = result.replace(new RegExp(`\\{${key}\\}`, 'g'), value);
                }
                return result;
            }

            /**
             * Filter out internal i18n keys from details object for display
             */
            filterDetailsForDisplay(details) {
                if (!details) return null;

                const filtered = {};
                for (const [key, value] of Object.entries(details)) {
                    // Skip internal i18n keys (prefixed with _i18n_)
                    if (!key.startsWith('_i18n_')) {
                        filtered[key] = value;
                    }
                }
                return filtered;
            }

            /**
             * Get emoji icon for event type
             */
            getEventIcon(eventType) {
                const icons = {
                    'format_conversion': '🔄',
                    'ocr_decision': '🔍',
                    'compression_selected': '📦',
                    'passthrough_mode': '⚡',
                    'fallback_applied': '⚠️',
                    'job_timeout': '⏱️',
                    'job_cleanup': '🧹'
                };
                return icons[eventType] || '📌';
            }

            /**
             * Update event count badge
             */
            updateEventCount() {
                const countBadge = document.getElementById('eventCount');
                if (countBadge) {
                    countBadge.textContent = this.events.length;
                }
            }

            /**
             * Show event list container
             */
            showEventListContainer() {
                const container = document.getElementById('eventListContainer');
                if (container) {
                    container.style.display = 'block';
                }
            }

            /**
             * Hide event list container
             */
            hideEventListContainer() {
                const container = document.getElementById('eventListContainer');
                if (container) {
                    container.style.display = 'none';
                }
            }

            /**
             * Toggle event list visibility
             */
            toggleEventList() {
                const toggle = document.getElementById('eventListToggle');
                const list = document.getElementById('eventList');

                if (!toggle || !list) return;

                this.eventListVisible = !this.eventListVisible;

                toggle.setAttribute('aria-expanded', this.eventListVisible.toString());
                list.hidden = !this.eventListVisible;
            }

            /**
             * Announce event to screen reader (selective)
             * Only high-priority events: ocr_decision, fallback_applied, job_timeout
             */
            announceEventToScreenReader(event) {
                const highPriorityEvents = [
                    'ocr_decision',
                    'fallback_applied',
                    'job_timeout'
                ];

                if (highPriorityEvents.includes(event.event_type)) {
                    // Translate message before announcing (in user's language)
                    const localizedMessage = this.translateEventMessage(event);
                    this.announceToScreenReader(localizedMessage);
                }
            }

            /**
             * Clear events (on new job or reset)
             */
            clearEvents() {
                this.events = [];

                const eventList = document.getElementById('eventList');
                if (eventList) {
                    eventList.innerHTML = '';
                }

                this.updateEventCount();
                this.hideEventListContainer();

                // Reset toggle state
                const toggle = document.getElementById('eventListToggle');
                if (toggle) {
                    toggle.setAttribute('aria-expanded', 'false');
                }

                const list = document.getElementById('eventList');
                if (list) {
                    list.hidden = true;
                }

                this.eventListVisible = false;
            }

            /**
             * Show event summary modal after successful completion
             */
            showEventSummaryModal() {
                const modal = document.getElementById('eventSummaryModal');
                const modalEventList = document.getElementById('modalEventList');

                console.log('[showEventSummaryModal] Total events in array:', this.events.length);
                console.log('[showEventSummaryModal] Events:', this.events);

                if (!modal || !modalEventList) {
                    console.error('[showEventSummaryModal] Modal elements not found');
                    return;
                }
                if (this.events.length === 0) {
                    console.log('[showEventSummaryModal] No events to display');
                    return;
                }

                // Clear and populate modal
                modalEventList.innerHTML = '';
                const sortedEvents = [...this.events].reverse();
                console.log('[showEventSummaryModal] Sorted events count:', sortedEvents.length);

                sortedEvents.forEach((event, index) => {
                    console.log(`[showEventSummaryModal] Adding event ${index + 1}/${sortedEvents.length}:`, event.event_type);
                    modalEventList.appendChild(this.createModalEventItem(event));
                });

                console.log('[showEventSummaryModal] Modal populated with', modalEventList.children.length, 'event items');

                // Store download info for modal download button
                this.modalDownloadUrl = this.lastDownloadUrl;
                this.modalFilename = this.lastFilename;

                // Open modal
                modal.showModal();
                document.getElementById('modalOkBtn')?.focus();

                // Announce to screen reader
                this.announceToScreenReader(t('modal.opened'));
            }

            /**
             * Create simplified event item for modal
             */
            createModalEventItem(event) {
                const eventItem = document.createElement('div');
                eventItem.className = `event-item event-${event.event_type}`;
                eventItem.setAttribute('role', 'listitem');

                const icon = this.getEventIcon(event.event_type);
                const timestamp = new Date(event.timestamp);
                const timeStr = timestamp.toLocaleTimeString(
                    typeof currentLang !== 'undefined' ? currentLang : 'en'
                );
                const message = this.translateEventMessage(event);

                eventItem.innerHTML = `
                    <span class="event-icon" aria-hidden="true">${icon}</span>
                    <div class="event-content">
                        <div class="event-header">
                            <span class="event-message">${this.escapeHtml(message)}</span>
                            <time class="event-timestamp" datetime="${event.timestamp}">
                                ${timeStr}
                            </time>
                        </div>
                    </div>
                `;

                return eventItem;
            }

            /**
             * Close event summary modal
             */
            closeEventSummaryModal() {
                document.getElementById('eventSummaryModal')?.close();
            }

            /**
             * Handle download button click in modal
             */
            handleDownloadFromModal() {
                if (!this.modalDownloadUrl || !this.modalFilename) return;

                const headers = {};
                if (this.authManager.token) {
                    headers['Authorization'] = `Bearer ${this.authManager.token}`;
                }

                fetch(this.modalDownloadUrl, { headers })
                    .then(response => response.blob())
                    .then(blob => {
                        const link = document.createElement('a');
                        link.href = URL.createObjectURL(blob);
                        link.download = this.modalFilename;
                        document.body.appendChild(link);
                        link.click();
                        document.body.removeChild(link);
                        URL.revokeObjectURL(link.href);
                    })
                    .catch(error => {
                        console.error('[Modal Download] Failed:', error);
                        alert(t('auth.downloadFailed'));
                    });
            }

            /**
             * Initialize modal event listeners
             */
            initModalListeners() {
                const modal = document.getElementById('eventSummaryModal');
                if (!modal) return;

                // Close button
                document.getElementById('modalCloseBtn')?.addEventListener('click', () => {
                    this.closeEventSummaryModal();
                });

                // OK button
                document.getElementById('modalOkBtn')?.addEventListener('click', () => {
                    this.closeEventSummaryModal();
                });

                // Download button
                document.getElementById('modalDownloadBtn')?.addEventListener('click', () => {
                    this.handleDownloadFromModal();
                });

                // Backdrop click
                modal.addEventListener('click', (e) => {
                    const rect = modal.getBoundingClientRect();
                    if (e.clientY < rect.top || e.clientY > rect.bottom ||
                        e.clientX < rect.left || e.clientX > rect.right) {
                        this.closeEventSummaryModal();
                    }
                });
            }

            /**
             * HTML escape utility
             */
            escapeHtml(unsafe) {
                return unsafe
                    .replace(/&/g, "&amp;")
                    .replace(/</g, "&lt;")
                    .replace(/>/g, "&gt;")
                    .replace(/"/g, "&quot;")
                    .replace(/'/g, "&#039;");
            }

            announceToScreenReader(message, percentage = null) {
                const now = Date.now();

                // Intelligent announcement logic:
                // 1. Always announce milestones (0%, 25%, 50%, 75%, 100%)
                // 2. Throttle other announcements to avoid overwhelming
                const isMilestone = percentage !== null &&
                    this.percentageMilestones.includes(percentage) &&
                    percentage !== this.lastAnnouncedPercentage;

                const timeSinceLastAnnouncement = now - this.lastAnnouncementTime;
                const shouldThrottle = timeSinceLastAnnouncement < this.announcementThrottle;

                if (!isMilestone && shouldThrottle) {
                    return; // Skip this announcement (not milestone, too soon)
                }

                this.lastAnnouncementTime = now;
                if (percentage !== null) {
                    this.lastAnnouncedPercentage = percentage;
                }

                const srAnnouncements = document.getElementById('srAnnouncements');
                if (srAnnouncements) {
                    // Clear and update the announcement
                    srAnnouncements.textContent = '';
                    // Use setTimeout to ensure screen reader picks up the change
                    setTimeout(() => {
                        srAnnouncements.textContent = message;
                    }, 100);
                }
            }

            /**
             * Notify JobsManager of WebSocket updates
             * This enables real-time job list updates without polling
             * @param {Object} message - WebSocket message with type and job_id
             */
            notifyJobsManager(message) {
                if (window.jobsManager && typeof window.jobsManager.handleWebSocketMessage === 'function') {
                    try {
                        window.jobsManager.handleWebSocketMessage(message);
                    } catch (error) {
                        console.error('[ConversionClient] Error notifying JobsManager:', error);
                    }
                }
            }
        }

