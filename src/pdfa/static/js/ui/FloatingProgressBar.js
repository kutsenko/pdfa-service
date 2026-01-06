/**
 * FloatingProgressBar - A persistent progress indicator that floats at the bottom of the screen
 *
 * Features:
 * - Visible across all tabs
 * - Minimizable/expandable
 * - Shows progress, current step, and events
 * - Auto-download and view options on completion
 */

import { t } from '../utils/helpers.js';

export class FloatingProgressBar {
    constructor() {
        this.container = null;
        this.isMinimized = false;
        this.isVisible = false;
        this.currentJob = null;
        this.events = [];
        this.eventsExpanded = false;

        this.init();
    }

    init() {
        this.container = document.getElementById('floatingProgressBar');
        if (!this.container) {
            console.error('[FloatingProgressBar] Container not found');
            return;
        }

        this.bindEvents();
        console.log('[FloatingProgressBar] Initialized');
    }

    bindEvents() {
        // Minimize/expand button
        const minimizeBtn = this.container.querySelector('.fpb-minimize-btn');
        if (minimizeBtn) {
            minimizeBtn.addEventListener('click', () => this.toggleMinimize());
        }

        // Close button
        const closeBtn = this.container.querySelector('.fpb-close-btn');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.hide());
        }

        // Events toggle
        const eventsToggle = this.container.querySelector('.fpb-events-toggle');
        if (eventsToggle) {
            eventsToggle.addEventListener('click', () => this.toggleEvents());
        }

        // Cancel button
        const cancelBtn = this.container.querySelector('.fpb-cancel-btn');
        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => this.cancelJob());
        }

        // Go to Jobs button
        const jobsBtn = this.container.querySelector('.fpb-jobs-btn');
        if (jobsBtn) {
            jobsBtn.addEventListener('click', () => this.goToJobs());
        }
    }

    show(filename) {
        if (!this.container) return;

        this.currentJob = {
            filename: filename,
            percentage: 0,
            step: t('floatingProgress.starting'),
            status: 'processing'
        };
        this.events = [];
        this.isVisible = true;
        this.isMinimized = false;

        // Reset UI
        this.updateFilename(filename);
        this.updateProgress(0, t('floatingProgress.starting'));
        this.updateEvents([]);

        // Show container
        this.container.classList.add('visible');
        this.container.classList.remove('minimized', 'completed', 'error');

        // Show processing UI, hide completed UI
        this.showProcessingUI();

        console.log('[FloatingProgressBar] Showing for:', filename);
    }

    hide() {
        if (!this.container) return;

        this.container.classList.remove('visible');
        this.isVisible = false;
        this.currentJob = null;
        this.events = [];

        console.log('[FloatingProgressBar] Hidden');
    }

    toggleMinimize() {
        if (!this.container) return;

        this.isMinimized = !this.isMinimized;
        this.container.classList.toggle('minimized', this.isMinimized);

        // Update button icon
        const minimizeBtn = this.container.querySelector('.fpb-minimize-btn');
        if (minimizeBtn) {
            minimizeBtn.textContent = this.isMinimized ? '▲' : '▼';
            minimizeBtn.setAttribute('aria-label',
                this.isMinimized ? t('floatingProgress.expand') : t('floatingProgress.minimize')
            );
        }
    }

    toggleEvents() {
        this.eventsExpanded = !this.eventsExpanded;
        const eventsList = this.container.querySelector('.fpb-events-list');
        const toggle = this.container.querySelector('.fpb-events-toggle');

        if (eventsList) {
            eventsList.classList.toggle('expanded', this.eventsExpanded);
        }
        if (toggle) {
            const icon = toggle.querySelector('.toggle-icon');
            if (icon) {
                icon.textContent = this.eventsExpanded ? '▼' : '▶';
            }
        }
    }

    updateFilename(filename) {
        const filenameEl = this.container.querySelector('.fpb-filename');
        if (filenameEl) {
            filenameEl.textContent = filename;
            filenameEl.title = filename;
        }
    }

    updateProgress(percentage, step, message) {
        if (!this.container || !this.currentJob) return;

        this.currentJob.percentage = percentage;
        this.currentJob.step = step || this.currentJob.step;

        // Update progress bar
        const progressFill = this.container.querySelector('.fpb-progress-fill');
        if (progressFill) {
            progressFill.style.width = `${percentage}%`;
        }

        // Update percentage text
        const percentageText = this.container.querySelector('.fpb-percentage');
        if (percentageText) {
            percentageText.textContent = `${Math.round(percentage)}%`;
        }

        // Update step/message
        const stepText = this.container.querySelector('.fpb-step');
        if (stepText && step) {
            stepText.textContent = step;
        }

        // Update mini progress (for minimized state)
        const miniProgress = this.container.querySelector('.fpb-mini-progress');
        if (miniProgress) {
            miniProgress.textContent = `${Math.round(percentage)}%`;
        }
    }

    addEvent(event) {
        if (!event) return;

        this.events.push(event);
        this.updateEvents(this.events);
    }

    updateEvents(events) {
        const eventsList = this.container.querySelector('.fpb-events-list');
        const eventsCount = this.container.querySelector('.fpb-events-count');

        if (eventsCount) {
            eventsCount.textContent = `(${events.length})`;
        }

        if (eventsList) {
            eventsList.innerHTML = events.map(event => {
                const icon = this.getEventIcon(event.type || event.event_type);
                const message = event.message || event.description || '';
                return `<div class="fpb-event-item">${icon} ${message}</div>`;
            }).join('');
        }
    }

    getEventIcon(eventType) {
        const icons = {
            'format_conversion': '🔄',
            'ocr_progress': '👁️',
            'ocr_start': '👁️',
            'ocr_complete': '✅',
            'compression_selected': '📦',
            'validation': '✓',
            'error': '❌',
            'warning': '⚠️'
        };
        return icons[eventType] || '•';
    }

    showProcessingUI() {
        const processingContent = this.container.querySelector('.fpb-processing');
        const completedContent = this.container.querySelector('.fpb-completed');

        if (processingContent) processingContent.style.display = 'block';
        if (completedContent) completedContent.style.display = 'none';
    }

    showCompletedUI(downloadUrl, viewUrl, filename) {
        const processingContent = this.container.querySelector('.fpb-processing');
        const completedContent = this.container.querySelector('.fpb-completed');

        if (processingContent) processingContent.style.display = 'none';
        if (completedContent) {
            completedContent.style.display = 'block';

            // Update completed filename
            const completedFilename = completedContent.querySelector('.fpb-completed-filename');
            if (completedFilename) {
                completedFilename.textContent = filename;
            }

            // Set download button
            const downloadBtn = completedContent.querySelector('.fpb-download-btn');
            if (downloadBtn && downloadUrl) {
                downloadBtn.onclick = () => {
                    window.location.href = downloadUrl;
                };
            }

            // Set view button
            const viewBtn = completedContent.querySelector('.fpb-view-btn');
            if (viewBtn && viewUrl) {
                viewBtn.onclick = () => {
                    window.open(viewUrl, '_blank');
                };
            }
        }

        this.container.classList.add('completed');
        this.container.classList.remove('error');
    }

    showErrorUI(errorMessage) {
        if (!this.container) return;

        const stepText = this.container.querySelector('.fpb-step');
        if (stepText) {
            stepText.textContent = errorMessage || t('floatingProgress.error');
        }

        this.container.classList.add('error');
        this.container.classList.remove('completed');

        // Hide cancel button on error
        const cancelBtn = this.container.querySelector('.fpb-cancel-btn');
        if (cancelBtn) {
            cancelBtn.style.display = 'none';
        }
    }

    cancelJob() {
        if (window.conversionClient) {
            window.conversionClient.cancelJob();
        }
    }

    goToJobs() {
        const jobsTabBtn = document.getElementById('tab-jobs-btn');
        if (jobsTabBtn) {
            jobsTabBtn.click();
        }
    }

    // Called when job completes successfully
    onComplete(result) {
        if (!this.container || !this.currentJob) return;

        this.currentJob.status = 'completed';
        this.updateProgress(100, t('floatingProgress.complete'));

        // Extract URLs from result
        const downloadUrl = result.download_url || result.downloadUrl;
        const viewUrl = result.view_url || result.viewUrl;
        const filename = result.output_filename || result.filename || this.currentJob.filename;

        this.showCompletedUI(downloadUrl, viewUrl, filename);

        console.log('[FloatingProgressBar] Job completed:', filename);
    }

    // Called when job fails
    onError(error) {
        if (!this.container) return;

        this.currentJob.status = 'error';
        const errorMsg = error.message || error.error || t('floatingProgress.error');
        this.showErrorUI(errorMsg);

        console.log('[FloatingProgressBar] Job failed:', errorMsg);
    }

    // Called when job is cancelled
    onCancelled() {
        if (!this.container) return;

        this.currentJob.status = 'cancelled';
        const stepText = this.container.querySelector('.fpb-step');
        if (stepText) {
            stepText.textContent = t('floatingProgress.cancelled');
        }

        // Auto-hide after a short delay
        setTimeout(() => this.hide(), 2000);

        console.log('[FloatingProgressBar] Job cancelled');
    }
}
