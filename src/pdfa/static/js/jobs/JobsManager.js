/**
 * JobsManager - Job history and conversion tracking
 * Handles jobs tab, job list display, filtering, pagination, and retry functionality
 */

import { t, formatFileSize, showStatus } from '../utils/helpers.js';

export class JobsManager {
    constructor(authManager) {
        this.authManager = authManager;
        this.jobs = [];
        this.total = 0;
        this.currentPage = 1;
        this.currentFilter = 'all';
        this.limit = 20;
        this.lastFetchTime = 0;
        this.cacheDuration = 5000; // 5 seconds
        this.expandedJobId = null;
        this.eventsCache = new Map(); // Cache loaded events
        this.pollingInterval = null;
        this.keyboardNavigationDetected = false;

        // Auto-refresh settings (enhanced accessibility detection)
        // Disable auto-refresh if ANY assistive technology indicator is detected
        this.autoRefreshEnabled = this.detectAccessibilityPreferences();

        // Monitor keyboard navigation for dynamic detection
        this.setupKeyboardNavigationDetection();
    }

    /**
     * Multi-Signal Accessibility Detection
     * Detects assistive technology usage via multiple browser signals
     * @returns {boolean} true if auto-refresh should be ENABLED, false if DISABLED
     */
    detectAccessibilityPreferences() {
        const signals = {
            reducedMotion: window.matchMedia('(prefers-reduced-motion: reduce)').matches,
            highContrast: window.matchMedia('(prefers-contrast: more)').matches,
            reducedTransparency: window.matchMedia('(prefers-reduced-transparency: reduce)').matches,
            forcedColors: window.matchMedia('(forced-colors: active)').matches
        };

        // Detect active signals
        const activeSignals = Object.entries(signals)
            .filter(([_, value]) => value)
            .map(([key, _]) => key);

        const assistiveTechDetected = activeSignals.length > 0;

        // Logging for transparency
        console.log('[Jobs] Accessibility Detection:');
        console.log('  - prefers-reduced-motion:', signals.reducedMotion);
        console.log('  - prefers-contrast (high):', signals.highContrast);
        console.log('  - prefers-reduced-transparency:', signals.reducedTransparency);
        console.log('  - forced-colors (Windows High Contrast):', signals.forcedColors);

        if (assistiveTechDetected) {
            console.log('  ⚠️  Assistive Technology detected:', activeSignals.join(', '));
            console.log('  → Auto-refresh DEFAULT: DISABLED (user can enable manually)');
            return false; // Disable auto-refresh
        } else {
            console.log('  ✓ No accessibility preferences detected');
            console.log('  → Auto-refresh DEFAULT: ENABLED');
            return true; // Enable auto-refresh
        }
    }

    /**
     * Setup keyboard navigation detection
     * Detects if user is navigating with keyboard (Tab key)
     */
    setupKeyboardNavigationDetection() {
        // Listen for Tab key to detect keyboard-only users
        const tabKeyHandler = (e) => {
            if (e.key === 'Tab' && !this.keyboardNavigationDetected) {
                this.keyboardNavigationDetected = true;
                console.log('[Jobs] Keyboard navigation detected (Tab key used)');

                // If auto-refresh is currently enabled AND keyboard nav detected,
                // suggest disabling it (non-intrusive)
                if (this.autoRefreshEnabled) {
                    console.log('[Jobs] ℹ️  Tip: Consider disabling auto-refresh for keyboard navigation');
                    console.log('[Jobs]     Click the "Auto-Refresh" toggle button to disable');
                }

                // Remove listener after first detection (performance)
                document.removeEventListener('keydown', tabKeyHandler);
            }
        };

        document.addEventListener('keydown', tabKeyHandler);
    }

    async init() {
        console.log('[Jobs] Initializing Jobs Manager...');

        // Bind refresh controls
        const refreshBtn = document.getElementById('refreshJobsBtn');
        const toggleAutoRefreshBtn = document.getElementById('toggleAutoRefreshBtn');

        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                console.log('[Jobs] Manual refresh triggered');
                this.loadJobs(true, true); // Show loading indicator for manual refresh
            });
        }

        if (toggleAutoRefreshBtn) {
            toggleAutoRefreshBtn.addEventListener('click', () => {
                this.toggleAutoRefresh();
            });

            // Set initial state
            this.updateAutoRefreshButton();
        }

        // Bind filter buttons
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                this.handleFilterChange(btn.dataset.status);
            });
        });

        // Bind pagination buttons
        const prevBtn = document.getElementById('jobsPrevBtn');
        const nextBtn = document.getElementById('jobsNextBtn');

        if (prevBtn) prevBtn.addEventListener('click', () => this.previousPage());
        if (nextBtn) nextBtn.addEventListener('click', () => this.nextPage());

        // Bind retry button in error state
        const errorRetryBtn = document.querySelector('#jobsError .retry-btn');
        if (errorRetryBtn) {
            errorRetryBtn.addEventListener('click', () => this.loadJobs(true, true)); // Show loading on retry
        }

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (!document.getElementById('tab-jobs').hasAttribute('hidden')) {
                if (e.key === 'ArrowLeft' && !e.ctrlKey && !e.metaKey) {
                    e.preventDefault();
                    this.previousPage();
                }
                if (e.key === 'ArrowRight' && !e.ctrlKey && !e.metaKey) {
                    e.preventDefault();
                    this.nextPage();
                }
                if (e.key === 'Escape' && this.expandedJobId) {
                    e.preventDefault();
                    this.collapseJob();
                }
            }
        });

        // Tab activation listener
        const auftraegeBtn = document.getElementById('tab-jobs-btn');
        if (auftraegeBtn) {
            auftraegeBtn.addEventListener('click', () => {
                this.onTabActivated();
            });
        }

        console.log('[Jobs] Jobs Manager initialized');
    }

    onTabActivated() {
        console.log('[Jobs] Tab activated');
        this.loadJobs(false, true); // Show loading indicator on initial tab activation
        this.startPolling();
    }

    onTabDeactivated() {
        console.log('[Jobs] Tab deactivated');
        this.stopPolling();
    }

    async loadJobs(forceRefresh = false, showLoadingIndicator = false) {
        // Check cache
        const now = Date.now();
        if (!forceRefresh && now - this.lastFetchTime < this.cacheDuration) {
            console.log('[Jobs] Using cached job list');
            return;
        }

        // Only show loading indicator if explicitly requested (initial load, manual refresh)
        // Silent loading for auto-refresh to avoid screenreader interruptions
        if (showLoadingIndicator) {
            this.showLoading();
        }

        try {
            const offset = (this.currentPage - 1) * this.limit;
            const statusParam = this.currentFilter === 'all' ? '' : `&status=${this.currentFilter}`;
            const url = `/api/v1/jobs/history?limit=${this.limit}&offset=${offset}${statusParam}`;

            console.log(`[Jobs] Fetching jobs: ${url} (silent: ${!showLoadingIndicator})`);

            const response = await fetch(url, {
                headers: this.authManager.getAuthHeaders()
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            this.jobs = data.jobs || [];
            this.total = data.total || 0;
            this.lastFetchTime = now;

            console.log(`[Jobs] Loaded ${this.jobs.length} jobs (total: ${this.total})`);

            this.renderJobs();
        } catch (error) {
            console.error('[Jobs] Failed to load jobs:', error);
            this.showError(error.message);
        }
    }

    showLoading() {
        document.getElementById('jobsLoading').style.display = 'block';
        document.getElementById('jobsError').style.display = 'none';
        document.getElementById('jobsEmpty').style.display = 'none';
        document.getElementById('jobsContent').style.display = 'none';
    }

    showError(message) {
        document.getElementById('jobsLoading').style.display = 'none';
        document.getElementById('jobsError').style.display = 'block';
        document.getElementById('jobsError').querySelector('.error-message').textContent = message;
        document.getElementById('jobsEmpty').style.display = 'none';
        document.getElementById('jobsContent').style.display = 'none';
    }

    renderJobs() {
        document.getElementById('jobsLoading').style.display = 'none';
        document.getElementById('jobsError').style.display = 'none';

        if (this.jobs.length === 0) {
            document.getElementById('jobsEmpty').style.display = 'block';
            document.getElementById('jobsContent').style.display = 'none';
            return;
        }

        document.getElementById('jobsEmpty').style.display = 'none';
        document.getElementById('jobsContent').style.display = 'block';

        const tbody = document.getElementById('jobsTableBody');

        // SMART DOM UPDATE: Preserve focus and minimize DOM changes

        // Save current focus and expanded state
        const activeElement = document.activeElement;
        const wasFocused = tbody.contains(activeElement);
        const focusedJobId = wasFocused ? activeElement.closest('.job-row')?.dataset.jobId : null;
        const expandedJobId = this.expandedJobId;

        // Index existing rows by job_id
        const existingRows = new Map();
        tbody.querySelectorAll('tr.job-row').forEach(row => {
            existingRows.set(row.dataset.jobId, row);
        });

        // Track which rows to keep
        const processedJobIds = new Set();

        // Update or create rows
        this.jobs.forEach((job, index) => {
            processedJobIds.add(job.job_id);
            const existingRow = existingRows.get(job.job_id);

            if (existingRow) {
                // Row exists - check if update is needed
                if (this.jobHasChanged(job, existingRow)) {
                    console.log(`[Jobs] Updating changed job: ${job.job_id}`);
                    const newRow = this.createJobRowElement(job);
                    existingRow.replaceWith(newRow);

                    // Preserve expanded state
                    if (expandedJobId === job.job_id) {
                        this.expandedJobId = null; // Reset to trigger re-expansion
                        this.toggleJobExpansion(job.job_id);
                    }
                } else {
                    // No changes - keep existing row, just check position
                    const currentIndex = Array.from(tbody.children).indexOf(existingRow);
                    const expectedIndex = index * 2; // Account for event rows

                    if (currentIndex !== expectedIndex) {
                        const referenceNode = tbody.children[expectedIndex];
                        if (referenceNode && referenceNode !== existingRow) {
                            tbody.insertBefore(existingRow, referenceNode);
                        }
                    }
                }
            } else {
                // New job - create and insert
                console.log(`[Jobs] Adding new job: ${job.job_id}`);
                const newRow = this.createJobRowElement(job);

                // Find correct position (accounting for event rows)
                let insertBeforeNode = null;
                const jobRows = Array.from(tbody.querySelectorAll('tr.job-row'));
                if (index < jobRows.length) {
                    insertBeforeNode = jobRows[index];
                }

                if (insertBeforeNode) {
                    tbody.insertBefore(newRow, insertBeforeNode);
                } else {
                    tbody.appendChild(newRow);
                }
            }
        });

        // Remove deleted jobs
        existingRows.forEach((row, jobId) => {
            if (!processedJobIds.has(jobId)) {
                console.log(`[Jobs] Removing deleted job: ${jobId}`);

                // Remove event row if exists
                const eventRow = row.nextElementSibling;
                if (eventRow && eventRow.classList.contains('events-row')) {
                    eventRow.remove();
                }

                row.remove();

                // Clear expanded state if this was the expanded job
                if (this.expandedJobId === jobId) {
                    this.expandedJobId = null;
                }
            }
        });

        // Restore focus if it was in the table
        if (wasFocused && focusedJobId) {
            const focusTarget = tbody.querySelector(`tr[data-job-id="${focusedJobId}"]`);
            if (focusTarget) {
                // Small delay to ensure DOM is ready
                setTimeout(() => focusTarget.focus(), 0);
            }
        }

        this.updatePagination();

        // Apply i18n to dynamically created content
        if (window.applyI18n) {
            window.applyI18n();
        }
    }

    createJobRow(job) {
        const statusClass = job.status.toLowerCase();
        const statusText = t(`jobs.status.${job.status}`) || job.status;
        const createdDate = new Date(job.created_at);
        const relativeTime = this.getRelativeTime(createdDate);
        const duration = job.duration_seconds ? this.formatDuration(job.duration_seconds) : '-';
        const sizeInfo = this.formatSizeInfo(job);
        const eventsCount = job.events_count || 0;

        const downloadBtn = job.status === 'completed'
            ? `<button class="action-btn download download-btn" data-job-id="${job.job_id}" data-filename="${job.filename}" data-i18n="jobs.actions.download">Download</button>`
            : '';

        const retryBtn = (job.status === 'failed' || job.status === 'cancelled')
            ? `<button class="action-btn retry retry-btn" data-job-id="${job.job_id}" data-i18n="jobs.actions.retry">Retry</button>`
            : '';

        const expandBtnText = t('jobs.actions.expand') || 'Expand';

        return `
            <tr class="job-row" data-job-id="${job.job_id}" role="row">
                <td role="cell" data-label="Status"><span class="status-badge ${statusClass}">${statusText}</span></td>
                <td role="cell" data-label="Filename" title="${this.escapeHtml(job.filename)}">${this.truncateFilename(job.filename, 40)}</td>
                <td role="cell" data-label="Created" title="${createdDate.toLocaleString()}">${relativeTime}</td>
                <td role="cell" data-label="Duration">${duration}</td>
                <td role="cell" data-label="Size" class="hide-mobile">${sizeInfo}</td>
                <td role="cell" data-label="Events"><span class="badge">${eventsCount} events</span></td>
                <td role="cell" data-label="Actions" class="actions">
                    ${downloadBtn}
                    ${retryBtn}
                    <button class="action-btn expand expand-btn" data-i18n="jobs.actions.expand">${expandBtnText}</button>
                </td>
            </tr>
        `;
    }

    /**
     * Create job row as DOM element (for smart update)
     * @param {Object} job - Job object
     * @returns {HTMLElement} Row element
     */
    createJobRowElement(job) {
        const template = document.createElement('template');
        template.innerHTML = this.createJobRow(job).trim();
        const row = template.content.firstChild;
        this.bindJobRowHandlers(row, job.job_id);
        return row;
    }

    /**
     * Check if job data has changed compared to existing row
     * @param {Object} job - New job object
     * @param {HTMLElement} existingRow - Existing DOM row
     * @returns {boolean} True if job has changed
     */
    jobHasChanged(job, existingRow) {
        // Extract current data from row
        const currentStatus = existingRow.querySelector('.status-badge').textContent.trim();
        const currentEventsCount = existingRow.querySelector('.badge').textContent.match(/\d+/);
        const currentDuration = existingRow.querySelector('[data-label="Duration"]').textContent.trim();

        // Compare key fields
        const newStatus = t(`jobs.status.${job.status}`) || job.status;
        const newEventsCount = String(job.events_count || 0);
        const newDuration = job.duration_seconds ? this.formatDuration(job.duration_seconds) : '-';

        return (
            currentStatus !== newStatus ||
            (currentEventsCount && currentEventsCount[0] !== newEventsCount) ||
            currentDuration !== newDuration
        );
    }

    /**
     * Bind event handlers to job row
     * @param {HTMLElement} row - Row element
     * @param {string} jobId - Job ID
     */
    bindJobRowHandlers(row, jobId) {
        // Row click handler
        row.addEventListener('click', (e) => {
            if (!e.target.closest('button')) {
                this.toggleJobExpansion(jobId);
            }
        });

        // Keyboard accessibility
        row.setAttribute('tabindex', '0');
        row.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                this.toggleJobExpansion(jobId);
            }
        });

        // Download button
        const downloadBtn = row.querySelector('.download-btn');
        if (downloadBtn) {
            downloadBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.downloadJob(downloadBtn.dataset.jobId, downloadBtn.dataset.filename);
            });
        }

        // Retry button
        const retryBtn = row.querySelector('.retry-btn');
        if (retryBtn) {
            retryBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.retryJob(retryBtn.dataset.jobId);
            });
        }

        // Expand button - handler is managed by toggleJobExpansion
    }

    async toggleJobExpansion(jobId) {
        console.log(`[Jobs] Toggle expansion for job: ${jobId}`);

        // Collapse if already expanded
        if (this.expandedJobId === jobId) {
            this.collapseJob();
            return;
        }

        // Collapse previous
        if (this.expandedJobId) {
            this.collapseJob();
        }

        // Expand new job
        this.expandedJobId = jobId;

        // Load events if not cached
        if (!this.eventsCache.has(jobId)) {
            await this.loadJobEvents(jobId);
        }

        // Render event panel
        const row = document.querySelector(`tr[data-job-id="${jobId}"]`);
        if (!row) return;

        const eventsRow = document.createElement('tr');
        eventsRow.className = 'events-row';
        eventsRow.innerHTML = `
            <td colspan="7">
                <div class="event-timeline" id="events-${jobId}">
                    ${this.renderEvents(this.eventsCache.get(jobId))}
                </div>
            </td>
        `;
        row.after(eventsRow);

        const expandBtn = row.querySelector('.expand-btn');
        if (expandBtn) {
            expandBtn.textContent = t('jobs.actions.collapse') || 'Collapse';
            expandBtn.setAttribute('data-i18n', 'jobs.actions.collapse');
        }
    }

    collapseJob() {
        if (!this.expandedJobId) return;

        console.log(`[Jobs] Collapsing job: ${this.expandedJobId}`);

        const eventsRow = document.querySelector('.events-row');
        if (eventsRow) eventsRow.remove();

        const row = document.querySelector(`tr[data-job-id="${this.expandedJobId}"]`);
        if (row) {
            const expandBtn = row.querySelector('.expand-btn');
            if (expandBtn) {
                expandBtn.textContent = t('jobs.actions.expand') || 'Expand';
                expandBtn.setAttribute('data-i18n', 'jobs.actions.expand');
            }
        }

        this.expandedJobId = null;
    }

    async loadJobEvents(jobId) {
        try {
            console.log(`[Jobs] Loading events for job: ${jobId}`);

            const response = await fetch(`/api/v1/jobs/${jobId}/status`, {
                headers: this.authManager.getAuthHeaders()
            });

            if (!response.ok) throw new Error('Failed to load events');

            const job = await response.json();
            this.eventsCache.set(jobId, job.events || []);

            console.log(`[Jobs] Loaded ${job.events?.length || 0} events`);
        } catch (error) {
            console.error('[Jobs] Error loading events:', error);
            this.eventsCache.set(jobId, []);
        }
    }

    renderEvents(events) {
        if (!events || events.length === 0) {
            return `<p data-i18n="jobs.events.empty">No events recorded</p>`;
        }

        return events.map(event => {
            const icon = this.getEventIcon(event.event_type);
            const details = this.formatEventDetails(event.details);
            const timestamp = new Date(event.timestamp).toLocaleTimeString();

            return `
                <div class="event-item">
                    <div class="event-icon" aria-hidden="true">${icon}</div>
                    <div class="event-content">
                        <div class="event-message">${this.escapeHtml(event.message)}</div>
                        <div class="event-timestamp">${timestamp}</div>
                        ${details ? `<div class="event-details">${details}</div>` : ''}
                    </div>
                </div>
            `;
        }).join('');
    }

    getEventIcon(eventType) {
        const icons = {
            'format_conversion': '📄',
            'ocr_decision': '👁️',
            'compression_selected': '🗜️',
            'passthrough_mode': '⚡',
            'fallback_applied': '🔄',
            'job_timeout': '⏱️',
            'job_cleanup': '🧹'
        };
        return icons[eventType] || '📌';
    }

    formatEventDetails(details) {
        if (!details || Object.keys(details).length === 0) return '';

        return Object.entries(details)
            .map(([key, value]) => `${key}: ${value}`)
            .join(' | ');
    }

    async downloadJob(jobId, filename) {
        try {
            console.log(`[Jobs] Downloading job: ${jobId}`);

            const response = await fetch(`/download/${jobId}`, {
                headers: this.authManager.getAuthHeaders()
            });

            if (!response.ok) {
                throw new Error(`Download failed: HTTP ${response.status}`);
            }

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);

            console.log(`[Jobs] Downloaded: ${filename}`);
        } catch (error) {
            console.error('[Jobs] Download error:', error);
            alert(t('jobs.download.error') || 'Download failed. Please try again.');
        }
    }

    async retryJob(jobId) {
        try {
            console.log(`[Jobs] Retrying job: ${jobId}`);

            const response = await fetch(`/api/v1/jobs/${jobId}/status`, {
                headers: this.authManager.getAuthHeaders()
            });

            if (!response.ok) {
                throw new Error(`Failed to load job details: HTTP ${response.status}`);
            }

            const job = await response.json();

            // Pre-fill converter form
            const pdfaLevelSelect = document.getElementById('pdfa_level');
            const ocrLanguageSelect = document.getElementById('ocr_language');
            const compressionSelect = document.getElementById('compression_profile');
            const enableOcrCheckbox = document.getElementById('enable_ocr');
            const skipTaggedCheckbox = document.getElementById('skip_ocr_on_tagged');

            if (pdfaLevelSelect && job.config.pdfa_level !== undefined) {
                pdfaLevelSelect.value = job.config.pdfa_level;
            }
            if (ocrLanguageSelect && job.config.ocr_language) {
                ocrLanguageSelect.value = job.config.ocr_language;
            }
            if (compressionSelect && job.config.compression_profile) {
                compressionSelect.value = job.config.compression_profile;
            }
            if (enableOcrCheckbox) {
                enableOcrCheckbox.checked = job.config.enable_ocr !== false;
            }
            if (skipTaggedCheckbox) {
                skipTaggedCheckbox.checked = job.config.skip_ocr_on_tagged !== false;
            }

            // Switch to converter tab
            const konverterBtn = document.getElementById('tab-konverter-btn');
            if (konverterBtn) konverterBtn.click();

            // Show notification
            const message = t('jobs.retry.notification').replace('{filename}', job.filename) ||
                          `Please upload ${job.filename} to retry this conversion`;
            showToast(message, 'info', 5000);

            console.log(`[Jobs] Pre-filled form for retry: ${job.filename}`);
        } catch (error) {
            console.error('[Jobs] Retry error:', error);
            alert(t('jobs.retry.error') || 'Failed to load job details. Please try again.');
        }
    }

    handleFilterChange(status) {
        console.log(`[Jobs] Filter changed to: ${status}`);

        this.currentFilter = status;
        this.currentPage = 1; // Reset to first page

        // Update active button
        document.querySelectorAll('.filter-btn').forEach(btn => {
            const isActive = btn.dataset.status === status;
            btn.classList.toggle('active', isActive);
            btn.setAttribute('aria-pressed', isActive.toString());
        });

        this.loadJobs(true, true); // Show loading indicator when changing filter
    }

    previousPage() {
        if (this.currentPage > 1) {
            this.currentPage--;
            this.loadJobs(true, true); // Show loading indicator when changing page
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }
    }

    nextPage() {
        const totalPages = Math.ceil(this.total / this.limit);
        if (this.currentPage < totalPages) {
            this.currentPage++;
            this.loadJobs(true, true); // Show loading indicator when changing page
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }
    }

    updatePagination() {
        const totalPages = Math.ceil(this.total / this.limit);
        const startIndex = (this.currentPage - 1) * this.limit + 1;
        const endIndex = Math.min(this.currentPage * this.limit, this.total);

        const prevBtn = document.getElementById('jobsPrevBtn');
        const nextBtn = document.getElementById('jobsNextBtn');
        const pageInfo = document.getElementById('jobsPageInfo');

        if (prevBtn) prevBtn.disabled = this.currentPage === 1;
        if (nextBtn) nextBtn.disabled = this.currentPage >= totalPages;

        if (pageInfo) {
            const infoText = t('jobs.pagination.info')
                .replace('{start}', startIndex)
                .replace('{end}', endIndex)
                .replace('{total}', this.total) ||
                `${startIndex}-${endIndex} of ${this.total} jobs`;
            pageInfo.textContent = infoText;
        }
    }

    handleWebSocketMessage(message) {
        if (['completed', 'failed', 'job_event'].includes(message.type)) {
            console.log(`[Jobs] WebSocket update: ${message.type} for job ${message.job_id}`);

            // Refresh job list if the job is in current view
            const jobIndex = this.jobs.findIndex(j => j.job_id === message.job_id);
            if (jobIndex !== -1) {
                this.loadJobs(true);
            }
        }
    }

    startPolling() {
        if (this.pollingInterval) return;

        // Check if auto-refresh is enabled (accessibility)
        if (!this.autoRefreshEnabled) {
            console.log('[Jobs] Polling disabled (auto-refresh OFF)');
            return;
        }

        // Only poll if WebSocket is not connected
        if (!window.ws || window.ws.readyState !== WebSocket.OPEN) {
            console.log('[Jobs] Starting polling (WebSocket unavailable)');
            this.pollingInterval = setInterval(() => {
                if (!document.getElementById('tab-jobs').hasAttribute('hidden')) {
                    this.loadJobs();
                }
            }, 5000); // Poll every 5 seconds
        }
    }

    stopPolling() {
        if (this.pollingInterval) {
            console.log('[Jobs] Stopping polling');
            clearInterval(this.pollingInterval);
            this.pollingInterval = null;
        }
    }

    /**
     * Toggle auto-refresh on/off
     */
    toggleAutoRefresh() {
        this.autoRefreshEnabled = !this.autoRefreshEnabled;

        console.log('[Jobs] Auto-refresh toggled:', this.autoRefreshEnabled ? 'ON' : 'OFF');

        if (this.autoRefreshEnabled) {
            // Enable: Start polling if tab is active
            if (!document.getElementById('tab-jobs').hasAttribute('hidden')) {
                this.startPolling();
            }
        } else {
            // Disable: Stop polling
            this.stopPolling();
        }

        this.updateAutoRefreshButton();
    }

    /**
     * Update auto-refresh button visual state
     */
    updateAutoRefreshButton() {
        const btn = document.getElementById('toggleAutoRefreshBtn');
        if (!btn) return;

        const statusSpan = btn.querySelector('.toggle-status');
        if (!statusSpan) return;

        // Update ARIA pressed state
        btn.setAttribute('aria-pressed', this.autoRefreshEnabled ? 'true' : 'false');

        // Update text with i18n
        const key = this.autoRefreshEnabled ? 'jobs.autoRefresh.on' : 'jobs.autoRefresh.off';
        statusSpan.setAttribute('data-i18n', key);

        // Apply translation immediately
        const translation = t(key);
        if (translation) {
            statusSpan.textContent = translation;
        } else {
            // Fallback
            statusSpan.textContent = this.autoRefreshEnabled ? 'Auto-Refresh: ON' : 'Auto-Refresh: OFF';
        }
    }

    // ============================================================================
    // Utility Methods
    // ============================================================================

    getRelativeTime(date) {
        const seconds = Math.floor((new Date() - date) / 1000);

        if (seconds < 30) return t('jobs.time.just_now') || 'Just now';

        const intervals = [
            { unit: 'year', seconds: 31536000 },
            { unit: 'month', seconds: 2592000 },
            { unit: 'week', seconds: 604800 },
            { unit: 'day', seconds: 86400 },
            { unit: 'hour', seconds: 3600 },
            { unit: 'minute', seconds: 60 }
        ];

        for (const { unit, seconds: secondsInUnit } of intervals) {
            const interval = Math.floor(seconds / secondsInUnit);
            if (interval >= 1) {
                const key = `jobs.time.${unit}`;
                return t(key).replace('{count}', interval) || `${interval} ${unit}${interval > 1 ? 's' : ''} ago`;
            }
        }

        return t('jobs.time.just_now') || 'Just now';
    }

    formatDuration(seconds) {
        if (seconds < 60) return `${seconds.toFixed(1)}s`;
        const minutes = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${minutes}m ${secs}s`;
    }

    formatSizeInfo(job) {
        if (!job.file_size_input) return '-';

        const input = this.formatBytes(job.file_size_input);
        const output = job.file_size_output ? this.formatBytes(job.file_size_output) : '-';
        const ratio = job.compression_ratio ? `(${job.compression_ratio.toFixed(1)}x)` : '';

        return `${input} → ${output} ${ratio}`;
    }

    formatBytes(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
    }

    truncateFilename(filename, maxLength) {
        if (filename.length <= maxLength) return filename;
        const extension = filename.split('.').pop();
        const nameLength = maxLength - extension.length - 4; // 4 for "..." and "."
        return filename.substring(0, nameLength) + '...' + extension;
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}
