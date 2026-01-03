# US-007: Job History Tab (Aufträge)

**Status**: 🚧 In Progress
**Date**: 2025-12-27
**Priority**: Medium
**Dependencies**: US-005 (Tab Interface), US-004 (Live Job Events)

---

## User Story

```
As a pdfa-service user
I want to view my conversion job history with detailed events
So that I can track conversions, understand processing steps, and retry failed jobs
```

---

## Business Value

- **Transparency**: Users can see detailed conversion history with step-by-step events
- **Debugging**: Event logs help understand why conversions succeed or fail
- **Productivity**: Quick access to download completed PDFs and retry failed jobs
- **Real-time Awareness**: WebSocket updates keep job list current without page refresh
- **Filtering**: Status filters help users focus on relevant jobs (completed, failed, processing)

---

## Acceptance Criteria

### 1. Job List Display

**Job Table Columns:**
- [ ] Status badge (color-coded: completed=green, failed=red, processing=blue)
- [ ] Filename (truncated if >40 chars with tooltip)
- [ ] Created timestamp (formatted with relative time)
- [ ] Duration (formatted as "2.3s" or "1m 45s")
- [ ] File sizes (input → output with compression ratio)
- [ ] Event count badge (e.g., "8 events")
- [ ] Actions (Download, Retry, Expand buttons)

**Job Row Behavior:**
- [ ] Clickable row to expand/collapse event details
- [ ] Hover effect for interactivity
- [ ] Expanded row shows full event timeline
- [ ] Only one row expanded at a time (accordion pattern)

**Empty States:**
- [ ] "No jobs found" message when list is empty
- [ ] "No jobs match filter" when filter returns no results
- [ ] Friendly illustration and helpful text

**Loading States:**
- [ ] Skeleton rows during initial load
- [ ] Loading spinner for pagination
- [ ] Smooth transitions when updating

### 2. Event Expansion (Inline Timeline)

**Event Display:**
- [ ] Icon-based timeline with event type icons:
  - `format_conversion`: 📄 (Office/Image → PDF)
  - `ocr_decision`: 👁️ (OCR Logic)
  - `compression_selected`: 🗜️ (Compression)
  - `passthrough_mode`: ⚡ (Fast-Path)
  - `fallback_applied`: 🔄 (Fallback Tier)
  - `job_timeout`: ⏱️ (Timeout)
  - `job_cleanup`: 🧹 (Cleanup)
- [ ] Event message displayed prominently
- [ ] Timestamp relative to job start
- [ ] Structured details rendering (key-value pairs)
- [ ] JSON fallback for complex details

**Event Loading:**
- [ ] Events lazy-loaded on first expansion (performance)
- [ ] Loading indicator during event fetch
- [ ] Cached after first load (no re-fetch on re-expand)
- [ ] Error state with retry option

### 3. Status Filtering

**Filter Options:**
- [ ] "All" (default, shows all jobs)
- [ ] "Completed" (status=completed)
- [ ] "Failed" (status=failed)
- [ ] "Processing" (status=processing)

**Filter Behavior:**
- [ ] Button group UI with active state highlight
- [ ] Filter applied immediately (no submit button)
- [ ] Preserves pagination state when filtering
- [ ] Count badge per filter (e.g., "Failed (3)")
- [ ] Query param in URL for shareable filtered views

### 4. Pagination

**Pagination Controls:**
- [ ] "Previous" button (disabled on first page)
- [ ] "Next" button (disabled on last page)
- [ ] Page indicator (e.g., "Page 2 of 8" or "21-40 of 156 jobs")
- [ ] 20 jobs per page (fixed, not configurable)

**Pagination Behavior:**
- [ ] Keyboard shortcuts (← previous, → next)
- [ ] Preserves filter when changing pages
- [ ] Scrolls to top on page change
- [ ] URL reflects current page (e.g., `?page=2&status=completed`)

### 5. Download Action

**Download Button:**
- [ ] Visible only for completed jobs
- [ ] Downloads PDF with original filename
- [ ] Shows loading spinner during download
- [ ] Error message if download fails
- [ ] Respects authentication (Bearer token if auth enabled)

**Download Behavior:**
- [ ] Triggers browser download via `GET /download/{job_id}`
- [ ] Content-Disposition header sets filename
- [ ] Works with auth enabled/disabled modes
- [ ] Graceful error handling (404, 403, 500)

### 6. Retry Action

**Retry Button:**
- [ ] Visible only for failed/cancelled jobs
- [ ] Pre-fills Converter tab with original config
- [ ] Switches user to Converter tab automatically
- [ ] Shows notification: "Please upload {filename} to retry"
- [ ] All form fields populated (PDF type, OCR language, compression, checkboxes)

**Retry Workflow:**
1. [ ] User clicks "Retry" button
2. [ ] Fetch job details including config
3. [ ] Switch to Konverter tab (activate tab)
4. [ ] Pre-fill form with job config
5. [ ] Show toast notification with filename
6. [ ] User manually uploads file and submits

**Rationale:**
- Original file not stored in MongoDB (security/storage)
- Gives user opportunity to modify config
- Transparent retry process

### 7. Real-time Updates (WebSocket)

**WebSocket Integration:**
- [ ] Shared WebSocket connection (reuse existing converter WebSocket)
- [ ] Message routing for `completed`, `failed`, `job_event` types
- [ ] Updates job status in real-time (no page refresh)
- [ ] Updates event count badge when new events arrive
- [ ] Smooth UI transitions (fade-in new status)

**Fallback Polling:**
- [ ] Poll every 5 seconds when WebSocket unavailable
- [ ] Only poll when Jobs tab is active (performance)
- [ ] Stop polling when tab inactive
- [ ] Resume polling on tab activation

**Connection Status:**
- [ ] No obtrusive connection indicator (WebSocket handles reconnection)
- [ ] Graceful degradation to polling
- [ ] No data loss during WebSocket reconnection

### 8. Authentication Modes

**Auth Enabled (PDFA_ENABLE_AUTH=true):**
- [ ] Shows authenticated user's jobs only (filtered by user_id)
- [ ] Download requires Bearer token
- [ ] Job count reflects user's jobs

**Auth Disabled (PDFA_ENABLE_AUTH=false):**
- [ ] Shows all jobs (no user_id filter)
- [ ] Download works without authentication
- [ ] Job count reflects all jobs in database

### 9. Localization (i18n)

**Translations Required (EN, DE, ES, FR):**
- [ ] Tab title ("Jobs" / "Aufträge" / "Trabajos" / "Tâches")
- [ ] Filter labels ("All", "Completed", "Failed", "Processing")
- [ ] Table headers ("Status", "Filename", "Created", "Duration", "Size", "Events", "Actions")
- [ ] Action buttons ("Download", "Retry", "Expand", "Collapse")
- [ ] Status labels ("Completed", "Failed", "Processing", "Queued", "Cancelled")
- [ ] Event type messages (localized event descriptions)
- [ ] Empty state messages
- [ ] Error messages
- [ ] Pagination labels ("Previous", "Next", "Page X of Y")
- [ ] Toast notifications ("Please upload {filename} to retry")

**Total Translation Keys:** ~80 keys × 4 languages = 320 lines

### 10. Responsive Design

**Desktop (>800px):**
- [ ] Full table with all 7 columns
- [ ] Horizontal scrolling if table overflows
- [ ] Expand/collapse icon visible

**Tablet (600-800px):**
- [ ] Condensed table (hide compression ratio column)
- [ ] Adjusted spacing

**Mobile (<600px):**
- [ ] Card-based layout (not table)
- [ ] Stack job info vertically
- [ ] Full-width action buttons
- [ ] Touch-friendly targets (≥44px)

### 11. Performance

**Optimization Strategies:**
- [ ] Lazy-load events (only on expansion)
- [ ] 5-second cache for job list (prevent excessive queries)
- [ ] Virtual scrolling if >100 jobs (future enhancement)
- [ ] Debounced filter changes (if text search added in future)
- [ ] Pagination limit prevents loading all jobs

**Backend Optimization:**
- [ ] Job list excludes `events` array (send `events_count` instead)
- [ ] MongoDB index on `user_id` + `created_at` for fast pagination
- [ ] Aggregation pipeline for efficient filtering

### 12. Accessibility (a11y)

**Keyboard Navigation:**
- [ ] Tab through all interactive elements (buttons, filters, pagination)
- [ ] Enter/Space to expand job rows
- [ ] Arrow keys for pagination (← previous, → next)
- [ ] Escape to collapse expanded row

**Screen Reader Support:**
- [ ] ARIA labels on all buttons
- [ ] ARIA live region for real-time updates
- [ ] ARIA expanded state on job rows
- [ ] Table headers properly associated with cells
- [ ] Descriptive alt text for icons

**Visual Accessibility:**
- [ ] Color contrast ≥4.5:1 (WCAG AA)
- [ ] Status not conveyed by color alone (use icons + text)
- [ ] Focus indicators visible on all interactive elements
- [ ] Dark mode support (respects prefers-color-scheme)

---

## Technical Implementation

### Backend Implementation

**Modified Repository: JobRepository**

File: `src/pdfa/repositories.py`

```python
async def get_user_jobs(
    self,
    user_id: str | None,
    limit: int = 50,
    offset: int = 0,
    status: str | None = None
) -> list[dict]:
    """Get paginated job history.

    Returns jobs WITHOUT events array (performance optimization).
    Adds events_count field for UI badge display.
    """
    query = {}
    if user_id:
        query["user_id"] = user_id
    if status:
        query["status"] = status

    cursor = self.collection.find(query).sort("created_at", -1).skip(offset).limit(limit)

    jobs_data = await cursor.to_list(length=limit)

    # Performance optimization: exclude events array, add events_count
    for job_data in jobs_data:
        job_data['events_count'] = len(job_data.get('events', []))
        job_data.pop('events', None)

    return jobs_data
```

**Lines Changed:** +15

**Existing API Endpoints (No Changes Needed):**

1. **GET /api/v1/jobs/history**
   - Already supports: limit, offset, status query params
   - Returns: `{ jobs: [...], total: int, limit: int, offset: int }`
   - Works with modified `get_user_jobs()` (no events array)

2. **GET /api/v1/jobs/{job_id}/status**
   - Returns full JobDocument with events array
   - Used for on-demand event loading

3. **GET /download/{job_id}**
   - Downloads completed PDF
   - Handles authentication if enabled

### Frontend Implementation

**File:** `src/pdfa/web_ui.html`

**HTML Structure** (Lines 2010-2018, replace placeholder):

```html
<div id="tab-auftraege" class="tab-panel" role="tabpanel"
     aria-labelledby="tab-auftraege-btn" hidden>

    <!-- Header with Filter -->
    <div class="jobs-header">
        <h2 data-i18n="jobs.title">Job History</h2>

        <div class="jobs-filter" role="radiogroup" aria-label="Filter jobs by status">
            <button class="filter-btn active" data-status="all" data-i18n="jobs.filter.all">All</button>
            <button class="filter-btn" data-status="completed" data-i18n="jobs.filter.completed">Completed</button>
            <button class="filter-btn" data-status="failed" data-i18n="jobs.filter.failed">Failed</button>
            <button class="filter-btn" data-status="processing" data-i18n="jobs.filter.processing">Processing</button>
        </div>
    </div>

    <!-- Loading State -->
    <div id="jobsLoading" class="loading-state" style="display: none;">
        <div class="spinner"></div>
        <p data-i18n="jobs.loading">Loading jobs...</p>
    </div>

    <!-- Error State -->
    <div id="jobsError" class="error-state" style="display: none;">
        <p class="error-message"></p>
        <button class="retry-btn" data-i18n="jobs.retry">Retry</button>
    </div>

    <!-- Empty State -->
    <div id="jobsEmpty" class="empty-state" style="display: none;">
        <div class="icon">📋</div>
        <h3 data-i18n="jobs.empty.title">No jobs found</h3>
        <p data-i18n="jobs.empty.description">Start a conversion to see jobs here</p>
    </div>

    <!-- Jobs Table -->
    <div id="jobsContent" style="display: none;">
        <div class="table-responsive">
            <table class="jobs-table">
                <thead>
                    <tr>
                        <th data-i18n="jobs.table.status">Status</th>
                        <th data-i18n="jobs.table.filename">Filename</th>
                        <th data-i18n="jobs.table.created">Created</th>
                        <th data-i18n="jobs.table.duration">Duration</th>
                        <th data-i18n="jobs.table.size">Size</th>
                        <th data-i18n="jobs.table.events">Events</th>
                        <th data-i18n="jobs.table.actions">Actions</th>
                    </tr>
                </thead>
                <tbody id="jobsTableBody">
                    <!-- Dynamically populated -->
                </tbody>
            </table>
        </div>

        <!-- Pagination -->
        <div class="jobs-pagination">
            <button id="jobsPrevBtn" class="pagination-btn" data-i18n="jobs.pagination.previous">Previous</button>
            <span id="jobsPageInfo" class="page-info"></span>
            <button id="jobsNextBtn" class="pagination-btn" data-i18n="jobs.pagination.next">Next</button>
        </div>
    </div>
</div>
```

**Lines:** +200

**CSS Styling** (After line 900):

```css
/* Jobs Tab Styles */
.jobs-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1.5rem;
}

.jobs-filter {
    display: flex;
    gap: 0.5rem;
}

.filter-btn {
    padding: 0.5rem 1rem;
    border: 1px solid var(--border-color);
    background: var(--card-bg);
    border-radius: 0.375rem;
    cursor: pointer;
    transition: all 0.2s;
}

.filter-btn.active {
    background: var(--primary-color);
    color: white;
    border-color: var(--primary-color);
}

.jobs-table {
    width: 100%;
    border-collapse: collapse;
}

.jobs-table th,
.jobs-table td {
    padding: 0.75rem;
    text-align: left;
    border-bottom: 1px solid var(--border-color);
}

.jobs-table tbody tr {
    cursor: pointer;
    transition: background-color 0.2s;
}

.jobs-table tbody tr:hover {
    background-color: var(--hover-bg);
}

.status-badge {
    display: inline-block;
    padding: 0.25rem 0.75rem;
    border-radius: 9999px;
    font-size: 0.875rem;
    font-weight: 500;
}

.status-badge.completed {
    background: #d4edda;
    color: #155724;
}

.status-badge.failed {
    background: #f8d7da;
    color: #721c24;
}

.status-badge.processing {
    background: #d1ecf1;
    color: #0c5460;
}

.event-timeline {
    padding: 1rem;
    background: var(--card-bg);
    border-left: 3px solid var(--primary-color);
}

.event-item {
    display: flex;
    gap: 1rem;
    padding: 0.75rem 0;
    border-bottom: 1px solid var(--border-color);
}

.event-item:last-child {
    border-bottom: none;
}

.event-icon {
    font-size: 1.5rem;
    flex-shrink: 0;
}

.event-content {
    flex: 1;
}

.event-message {
    font-weight: 500;
    margin-bottom: 0.25rem;
}

.event-details {
    font-size: 0.875rem;
    color: var(--text-secondary);
}

.action-btn {
    padding: 0.375rem 0.75rem;
    border: 1px solid var(--border-color);
    background: white;
    border-radius: 0.375rem;
    cursor: pointer;
    font-size: 0.875rem;
    transition: all 0.2s;
}

.action-btn:hover {
    background: var(--hover-bg);
}

.action-btn.download {
    color: var(--success-color);
    border-color: var(--success-color);
}

.action-btn.retry {
    color: var(--warning-color);
    border-color: var(--warning-color);
}

.jobs-pagination {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 1rem;
    margin-top: 1.5rem;
    padding: 1rem;
}

.pagination-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

/* Responsive Design */
@media (max-width: 800px) {
    .jobs-header {
        flex-direction: column;
        align-items: flex-start;
        gap: 1rem;
    }

    .jobs-table {
        font-size: 0.875rem;
    }

    .jobs-table th:nth-child(5),
    .jobs-table td:nth-child(5) {
        display: none; /* Hide compression ratio on tablet */
    }
}

@media (max-width: 600px) {
    /* Mobile: Card-based layout instead of table */
    .jobs-table thead {
        display: none;
    }

    .jobs-table,
    .jobs-table tbody,
    .jobs-table tr,
    .jobs-table td {
        display: block;
        width: 100%;
    }

    .jobs-table tr {
        margin-bottom: 1rem;
        border: 1px solid var(--border-color);
        border-radius: 0.5rem;
        padding: 1rem;
    }

    .jobs-table td {
        border: none;
        padding: 0.5rem 0;
    }

    .jobs-table td::before {
        content: attr(data-label);
        font-weight: 600;
        margin-right: 0.5rem;
    }
}

/* Dark Mode */
@media (prefers-color-scheme: dark) {
    .status-badge.completed {
        background: #1e4620;
        color: #a3cfbb;
    }

    .status-badge.failed {
        background: #4a1c1c;
        color: #f5c6cb;
    }

    .status-badge.processing {
        background: #1c3d47;
        color: #bee5eb;
    }
}
```

**Lines:** +300

**JavaScript: JobsManager Class** (After line 5600):

```javascript
class JobsManager {
    constructor() {
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
    }

    async init() {
        // Bind event listeners
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.handleFilterChange(e.target.dataset.status));
        });

        document.getElementById('jobsPrevBtn').addEventListener('click', () => this.previousPage());
        document.getElementById('jobsNextBtn').addEventListener('click', () => this.nextPage());

        document.getElementById('jobsError').querySelector('.retry-btn')
            .addEventListener('click', () => this.loadJobs(true));

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (!document.getElementById('tab-auftraege').hasAttribute('hidden')) {
                if (e.key === 'ArrowLeft') this.previousPage();
                if (e.key === 'ArrowRight') this.nextPage();
                if (e.key === 'Escape' && this.expandedJobId) this.collapseJob();
            }
        });

        // Tab activation listener
        document.getElementById('tab-auftraege-btn').addEventListener('click', () => {
            this.onTabActivated();
        });
    }

    onTabActivated() {
        this.loadJobs();
        this.startPolling();
    }

    onTabDeactivated() {
        this.stopPolling();
    }

    async loadJobs(forceRefresh = false) {
        // Check cache
        const now = Date.now();
        if (!forceRefresh && now - this.lastFetchTime < this.cacheDuration) {
            return;
        }

        this.showLoading();

        try {
            const offset = (this.currentPage - 1) * this.limit;
            const statusParam = this.currentFilter === 'all' ? '' : `&status=${this.currentFilter}`;
            const url = `/api/v1/jobs/history?limit=${this.limit}&offset=${offset}${statusParam}`;

            const response = await fetch(url, {
                headers: authManager.getAuthHeaders()
            });

            if (!response.ok) throw new Error('Failed to fetch jobs');

            const data = await response.json();
            this.jobs = data.jobs;
            this.total = data.total;
            this.lastFetchTime = now;

            this.renderJobs();
        } catch (error) {
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
        tbody.innerHTML = this.jobs.map(job => this.createJobRow(job)).join('');

        // Bind row click handlers
        tbody.querySelectorAll('tr.job-row').forEach(row => {
            row.addEventListener('click', (e) => {
                if (!e.target.closest('button')) {
                    this.toggleJobExpansion(row.dataset.jobId);
                }
            });
        });

        // Bind action buttons
        tbody.querySelectorAll('.download-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.downloadJob(btn.dataset.jobId, btn.dataset.filename);
            });
        });

        tbody.querySelectorAll('.retry-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.retryJob(btn.dataset.jobId);
            });
        });

        this.updatePagination();
    }

    createJobRow(job) {
        const statusClass = job.status.toLowerCase();
        const statusText = i18n.t(`jobs.status.${job.status}`);
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

        return `
            <tr class="job-row" data-job-id="${job.job_id}">
                <td><span class="status-badge ${statusClass}">${statusText}</span></td>
                <td title="${job.filename}">${this.truncateFilename(job.filename, 40)}</td>
                <td title="${createdDate.toLocaleString()}">${relativeTime}</td>
                <td>${duration}</td>
                <td>${sizeInfo}</td>
                <td><span class="badge">${eventsCount} events</span></td>
                <td class="actions">
                    ${downloadBtn}
                    ${retryBtn}
                    <button class="action-btn expand-btn" data-i18n="jobs.actions.expand">Expand</button>
                </td>
            </tr>
        `;
    }

    async toggleJobExpansion(jobId) {
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
        row.querySelector('.expand-btn').textContent = i18n.t('jobs.actions.collapse');
    }

    collapseJob() {
        if (!this.expandedJobId) return;

        document.querySelector('.events-row')?.remove();
        const row = document.querySelector(`tr[data-job-id="${this.expandedJobId}"]`);
        row.querySelector('.expand-btn').textContent = i18n.t('jobs.actions.expand');
        this.expandedJobId = null;
    }

    async loadJobEvents(jobId) {
        try {
            const response = await fetch(`/api/v1/jobs/${jobId}/status`, {
                headers: authManager.getAuthHeaders()
            });

            if (!response.ok) throw new Error('Failed to load events');

            const job = await response.json();
            this.eventsCache.set(jobId, job.events || []);
        } catch (error) {
            this.eventsCache.set(jobId, []);
            console.error('Error loading events:', error);
        }
    }

    renderEvents(events) {
        if (!events || events.length === 0) {
            return '<p data-i18n="jobs.events.empty">No events recorded</p>';
        }

        return events.map(event => {
            const icon = this.getEventIcon(event.event_type);
            const details = this.formatEventDetails(event.details);

            return `
                <div class="event-item">
                    <div class="event-icon">${icon}</div>
                    <div class="event-content">
                        <div class="event-message">${event.message}</div>
                        <div class="event-timestamp">${new Date(event.timestamp).toLocaleTimeString()}</div>
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
            const response = await fetch(`/download/${jobId}`, {
                headers: authManager.getAuthHeaders()
            });

            if (!response.ok) throw new Error('Download failed');

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } catch (error) {
            alert(i18n.t('jobs.download.error'));
            console.error('Download error:', error);
        }
    }

    async retryJob(jobId) {
        try {
            const response = await fetch(`/api/v1/jobs/${jobId}/status`, {
                headers: authManager.getAuthHeaders()
            });

            if (!response.ok) throw new Error('Failed to load job details');

            const job = await response.json();

            // Pre-fill converter form
            document.getElementById('pdfa_level').value = job.config.pdfa_level || '2';
            document.getElementById('ocr_language').value = job.config.ocr_language || 'deu+eng';
            document.getElementById('compression_profile').value = job.config.compression_profile || 'balanced';
            document.getElementById('enable_ocr').checked = job.config.enable_ocr !== false;
            document.getElementById('skip_ocr_on_tagged').checked = job.config.skip_ocr_on_tagged !== false;

            // Switch to converter tab
            document.getElementById('tab-konverter-btn').click();

            // Show notification
            showToast(i18n.t('jobs.retry.notification', { filename: job.filename }));
        } catch (error) {
            alert(i18n.t('jobs.retry.error'));
            console.error('Retry error:', error);
        }
    }

    handleFilterChange(status) {
        this.currentFilter = status;
        this.currentPage = 1;

        // Update active button
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.status === status);
        });

        this.loadJobs(true);
    }

    previousPage() {
        if (this.currentPage > 1) {
            this.currentPage--;
            this.loadJobs(true);
        }
    }

    nextPage() {
        const totalPages = Math.ceil(this.total / this.limit);
        if (this.currentPage < totalPages) {
            this.currentPage++;
            this.loadJobs(true);
        }
    }

    updatePagination() {
        const totalPages = Math.ceil(this.total / this.limit);
        const startIndex = (this.currentPage - 1) * this.limit + 1;
        const endIndex = Math.min(this.currentPage * this.limit, this.total);

        document.getElementById('jobsPrevBtn').disabled = this.currentPage === 1;
        document.getElementById('jobsNextBtn').disabled = this.currentPage >= totalPages;
        document.getElementById('jobsPageInfo').textContent =
            i18n.t('jobs.pagination.info', { start: startIndex, end: endIndex, total: this.total });
    }

    handleWebSocketMessage(message) {
        if (['completed', 'failed', 'job_event'].includes(message.type)) {
            // Update job in list
            const jobIndex = this.jobs.findIndex(j => j.job_id === message.job_id);
            if (jobIndex !== -1) {
                // Refresh job data
                this.loadJobs(true);
            }
        }
    }

    startPolling() {
        if (this.pollingInterval) return;

        // Only poll if WebSocket is not connected
        if (!window.ws || window.ws.readyState !== WebSocket.OPEN) {
            this.pollingInterval = setInterval(() => {
                if (!document.getElementById('tab-auftraege').hasAttribute('hidden')) {
                    this.loadJobs();
                }
            }, 5000);
        }
    }

    stopPolling() {
        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
            this.pollingInterval = null;
        }
    }

    // Utility methods
    getRelativeTime(date) {
        const seconds = Math.floor((new Date() - date) / 1000);

        const intervals = {
            year: 31536000,
            month: 2592000,
            week: 604800,
            day: 86400,
            hour: 3600,
            minute: 60
        };

        for (const [unit, secondsInUnit] of Object.entries(intervals)) {
            const interval = Math.floor(seconds / secondsInUnit);
            if (interval >= 1) {
                return i18n.t(`jobs.time.${unit}`, { count: interval });
            }
        }

        return i18n.t('jobs.time.just_now');
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
}

// Initialize Jobs Manager
const jobsManager = new JobsManager();
document.addEventListener('DOMContentLoaded', () => {
    jobsManager.init();
});

// WebSocket integration
if (window.ws) {
    const originalOnMessage = window.ws.onmessage;
    window.ws.onmessage = function(event) {
        const message = JSON.parse(event.data);
        jobsManager.handleWebSocketMessage(message);
        if (originalOnMessage) originalOnMessage.call(this, event);
    };
}
```

**Lines:** +500

**Integration** (After line 5680):

```javascript
// Tab visibility detection
const tabObserver = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
        if (mutation.target.id === 'tab-auftraege') {
            if (mutation.target.hasAttribute('hidden')) {
                jobsManager.onTabDeactivated();
            } else {
                jobsManager.onTabActivated();
            }
        }
    });
});

document.querySelectorAll('.tab-panel').forEach(panel => {
    tabObserver.observe(panel, { attributes: true, attributeFilter: ['hidden'] });
});
```

**Lines:** +30

### i18n Translations

**File:** `src/pdfa/web_ui.html` (After line 2464)

**Translation Keys (~80 keys):**

```javascript
const translations = {
    en: {
        jobs: {
            title: "Job History",
            loading: "Loading jobs...",
            retry: "Retry",
            filter: {
                all: "All",
                completed: "Completed",
                failed: "Failed",
                processing: "Processing"
            },
            table: {
                status: "Status",
                filename: "Filename",
                created: "Created",
                duration: "Duration",
                size: "Size",
                events: "Events",
                actions: "Actions"
            },
            status: {
                completed: "Completed",
                failed: "Failed",
                processing: "Processing",
                queued: "Queued",
                cancelled: "Cancelled"
            },
            actions: {
                download: "Download",
                retry: "Retry",
                expand: "Expand",
                collapse: "Collapse"
            },
            events: {
                empty: "No events recorded"
            },
            download: {
                error: "Download failed. Please try again."
            },
            retry: {
                notification: "Please upload {filename} to retry this conversion",
                error: "Failed to load job details. Please try again."
            },
            empty: {
                title: "No jobs found",
                description: "Start a conversion to see jobs here"
            },
            pagination: {
                previous: "Previous",
                next: "Next",
                info: "{start}-{end} of {total} jobs"
            },
            time: {
                year: "{count} year ago | {count} years ago",
                month: "{count} month ago | {count} months ago",
                week: "{count} week ago | {count} weeks ago",
                day: "{count} day ago | {count} days ago",
                hour: "{count} hour ago | {count} hours ago",
                minute: "{count} minute ago | {count} minutes ago",
                just_now: "Just now"
            }
        }
    },
    de: {
        jobs: {
            title: "Aufträge",
            loading: "Lade Aufträge...",
            retry: "Wiederholen",
            filter: {
                all: "Alle",
                completed: "Abgeschlossen",
                failed: "Fehlgeschlagen",
                processing: "In Bearbeitung"
            },
            table: {
                status: "Status",
                filename: "Dateiname",
                created: "Erstellt",
                duration: "Dauer",
                size: "Größe",
                events: "Ereignisse",
                actions: "Aktionen"
            },
            status: {
                completed: "Abgeschlossen",
                failed: "Fehlgeschlagen",
                processing: "In Bearbeitung",
                queued: "Warteschlange",
                cancelled: "Abgebrochen"
            },
            actions: {
                download: "Herunterladen",
                retry: "Wiederholen",
                expand: "Erweitern",
                collapse: "Einklappen"
            },
            events: {
                empty: "Keine Ereignisse aufgezeichnet"
            },
            download: {
                error: "Download fehlgeschlagen. Bitte erneut versuchen."
            },
            retry: {
                notification: "Bitte laden Sie {filename} hoch, um diese Konvertierung zu wiederholen",
                error: "Fehler beim Laden der Auftragsdetails. Bitte erneut versuchen."
            },
            empty: {
                title: "Keine Aufträge gefunden",
                description: "Starten Sie eine Konvertierung, um Aufträge hier zu sehen"
            },
            pagination: {
                previous: "Zurück",
                next: "Weiter",
                info: "{start}-{end} von {total} Aufträgen"
            },
            time: {
                year: "vor {count} Jahr | vor {count} Jahren",
                month: "vor {count} Monat | vor {count} Monaten",
                week: "vor {count} Woche | vor {count} Wochen",
                day: "vor {count} Tag | vor {count} Tagen",
                hour: "vor {count} Stunde | vor {count} Stunden",
                minute: "vor {count} Minute | vor {count} Minuten",
                just_now: "Gerade eben"
            }
        }
    },
    es: {
        jobs: {
            title: "Historial de Trabajos",
            loading: "Cargando trabajos...",
            retry: "Reintentar",
            filter: {
                all: "Todos",
                completed: "Completados",
                failed: "Fallidos",
                processing: "Procesando"
            },
            table: {
                status: "Estado",
                filename: "Nombre de Archivo",
                created: "Creado",
                duration: "Duración",
                size: "Tamaño",
                events: "Eventos",
                actions: "Acciones"
            },
            status: {
                completed: "Completado",
                failed: "Fallido",
                processing: "Procesando",
                queued: "En Cola",
                cancelled: "Cancelado"
            },
            actions: {
                download: "Descargar",
                retry: "Reintentar",
                expand: "Expandir",
                collapse: "Contraer"
            },
            events: {
                empty: "No hay eventos registrados"
            },
            download: {
                error: "Error al descargar. Inténtelo de nuevo."
            },
            retry: {
                notification: "Por favor suba {filename} para reintentar esta conversión",
                error: "Error al cargar los detalles del trabajo. Inténtelo de nuevo."
            },
            empty: {
                title: "No se encontraron trabajos",
                description: "Inicie una conversión para ver trabajos aquí"
            },
            pagination: {
                previous: "Anterior",
                next: "Siguiente",
                info: "{start}-{end} de {total} trabajos"
            },
            time: {
                year: "hace {count} año | hace {count} años",
                month: "hace {count} mes | hace {count} meses",
                week: "hace {count} semana | hace {count} semanas",
                day: "hace {count} día | hace {count} días",
                hour: "hace {count} hora | hace {count} horas",
                minute: "hace {count} minuto | hace {count} minutos",
                just_now: "Justo ahora"
            }
        }
    },
    fr: {
        jobs: {
            title: "Historique des Tâches",
            loading: "Chargement des tâches...",
            retry: "Réessayer",
            filter: {
                all: "Tous",
                completed: "Terminés",
                failed: "Échoués",
                processing: "En Cours"
            },
            table: {
                status: "Statut",
                filename: "Nom de Fichier",
                created: "Créé",
                duration: "Durée",
                size: "Taille",
                events: "Événements",
                actions: "Actions"
            },
            status: {
                completed: "Terminé",
                failed: "Échoué",
                processing: "En Cours",
                queued: "En Attente",
                cancelled: "Annulé"
            },
            actions: {
                download: "Télécharger",
                retry: "Réessayer",
                expand: "Développer",
                collapse: "Réduire"
            },
            events: {
                empty: "Aucun événement enregistré"
            },
            download: {
                error: "Échec du téléchargement. Veuillez réessayer."
            },
            retry: {
                notification: "Veuillez télécharger {filename} pour réessayer cette conversion",
                error: "Échec du chargement des détails de la tâche. Veuillez réessayer."
            },
            empty: {
                title: "Aucune tâche trouvée",
                description: "Démarrez une conversion pour voir les tâches ici"
            },
            pagination: {
                previous: "Précédent",
                next: "Suivant",
                info: "{start}-{end} sur {total} tâches"
            },
            time: {
                year: "il y a {count} an | il y a {count} ans",
                month: "il y a {count} mois",
                week: "il y a {count} semaine | il y a {count} semaines",
                day: "il y a {count} jour | il y a {count} jours",
                hour: "il y a {count} heure | il y a {count} heures",
                minute: "il y a {count} minute | il y a {count} minutes",
                just_now: "À l'instant"
            }
        }
    }
};
```

**Lines:** +320 (80 keys × 4 languages)

---

## Files Modified

| File | Lines | Description |
|------|-------|-------------|
| `docs/specs/user-stories/US-007-auftraege-tab.md` | 400 | User story document (English only) |
| `docs/specs/features/gherkin-auftraege-tab.feature` | 500 | Gherkin scenarios |
| `src/pdfa/repositories.py` | +15 | Add events_count field |
| `src/pdfa/web_ui.html` (HTML) | +200 | Tab structure and components |
| `src/pdfa/web_ui.html` (CSS) | +300 | Styling and responsive design |
| `src/pdfa/web_ui.html` (JavaScript) | +500 | JobsManager class |
| `src/pdfa/web_ui.html` (Integration) | +30 | Tab visibility observer |
| `src/pdfa/web_ui.html` (i18n) | +320 | 4-language translations |
| `tests/e2e/test_auftraege_tab.py` | 600 | E2E test suite |

**Total:** ~2,865 new lines

---

## Testing Plan

### Manual Testing Checklist

**Job List Display:**
- [ ] Jobs table displays all columns correctly
- [ ] Status badges color-coded (green/red/blue)
- [ ] Filenames truncated with tooltip
- [ ] Timestamps show relative time
- [ ] File sizes formatted (KB/MB)
- [ ] Event count badge visible
- [ ] Empty state shows when no jobs

**Event Expansion:**
- [ ] Click row to expand events
- [ ] Events display with icons and timeline
- [ ] Event details formatted as key-value pairs
- [ ] Only one row expanded at a time (accordion)
- [ ] Collapse with Escape key

**Filtering:**
- [ ] Filter buttons work (All, Completed, Failed, Processing)
- [ ] Active filter highlighted
- [ ] Job count updates after filtering
- [ ] Pagination resets to page 1

**Pagination:**
- [ ] Previous/Next buttons work
- [ ] Buttons disabled at boundaries
- [ ] Page indicator shows correct range
- [ ] Keyboard shortcuts (← →) work
- [ ] URL reflects current page

**Download Action:**
- [ ] Download button visible only for completed jobs
- [ ] PDF downloads with correct filename
- [ ] Loading spinner during download
- [ ] Error message on failure
- [ ] Works with auth enabled/disabled

**Retry Action:**
- [ ] Retry button visible only for failed jobs
- [ ] Pre-fills converter form
- [ ] Switches to Konverter tab
- [ ] Shows toast notification
- [ ] All config fields populated

**Real-time Updates:**
- [ ] WebSocket updates job status
- [ ] Event count updates live
- [ ] Fallback to polling when WebSocket down
- [ ] Polling only when tab active

**i18n:**
- [ ] All text translated (EN, DE, ES, FR)
- [ ] Language switcher updates tab content
- [ ] No hardcoded text

**Responsive Design:**
- [ ] Desktop: Full 7-column table
- [ ] Tablet: Hide compression ratio column
- [ ] Mobile: Card-based layout
- [ ] Touch targets ≥44px

**Accessibility:**
- [ ] Keyboard navigation works
- [ ] ARIA labels present
- [ ] Screen reader friendly
- [ ] Color contrast ≥4.5:1
- [ ] Focus indicators visible

### E2E Test Coverage

**40+ Playwright Tests:**
- Job list rendering (5 tests)
- Filtering functionality (4 tests)
- Pagination (4 tests)
- Event expansion (6 tests)
- Download action (4 tests)
- Retry action (5 tests)
- Real-time updates (5 tests)
- Localization (4 tests)
- Responsive design (3 tests)

---

## Risks and Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| WebSocket message routing conflicts | High | Low | Thorough testing, separate handler registration |
| Performance with 1000+ jobs | Medium | Medium | Pagination limit, future virtualization |
| Event details too complex | Medium | Low | JSON pretty-print fallback |
| Retry workflow confusing | Medium | Medium | Clear notifications, inline help text |
| i18n translation quality | Low | Medium | Native speaker review |
| Mobile layout breaks | Low | Low | Comprehensive responsive testing |

---

## Future Enhancements (Out of Scope)

1. **Advanced Filtering**
   - Date range picker
   - Filename search (text input)
   - Config filters (PDF type, OCR language)

2. **Bulk Actions**
   - Multi-select jobs (checkboxes)
   - Batch download (ZIP archive)
   - Batch retry

3. **Job Comparison**
   - Compare events between two jobs
   - Side-by-side config diff

4. **Export**
   - CSV export of job list
   - JSON export for API integration

5. **Direct Retry**
   - Store encrypted file URLs for 24h
   - One-click retry without re-upload

6. **Job Sharing**
   - Share job results via link
   - Public/private toggle

7. **Notifications**
   - Email notifications for job completion
   - Push notifications (PWA)

8. **Visualization**
   - Charts for job statistics
   - Success/failure trends over time
   - Performance metrics dashboard

---

## Definition of Done

### Documentation
- [ ] User Story US-007 created (English only)
- [ ] Gherkin Feature Spec created
- [ ] Feature branch created (`feature/auftraege-tab`)

### Implementation
- [ ] Backend: `events_count` added to job list
- [ ] Frontend: HTML structure implemented
- [ ] Frontend: CSS styles implemented
- [ ] Frontend: JobsManager class implemented
- [ ] Frontend: i18n translations (EN, DE, ES, FR)
- [ ] WebSocket integration: Real-time updates
- [ ] Retry logic: Pre-fill converter tab
- [ ] Download logic: PDF download with auth

### Testing
- [ ] E2E test suite implemented (40+ tests)
- [ ] All E2E tests passing (≥90%)
- [ ] Manual tests (100% pass)
- [ ] Cross-browser testing (Chrome, Firefox, Safari)
- [ ] Mobile responsive testing
- [ ] Performance testing (100+ jobs)
- [ ] WebSocket reconnection tested
- [ ] i18n complete (all 4 languages)

### Quality
- [ ] Code formatted (Black)
- [ ] Linting clean (Ruff)
- [ ] No regressions in existing features
- [ ] Accessibility (a11y) verified:
  - [ ] ARIA labels present
  - [ ] Keyboard navigation works
  - [ ] Color contrast WCAG AA (≥4.5:1)

### Deployment
- [ ] Code committed with descriptive message
- [ ] Pull request created
- [ ] GitHub Actions ✅
- [ ] Code review completed
- [ ] Merged to main
- [ ] Feature branch deleted
- [ ] Status → ✅ Implemented

---

## References

- **Related User Stories**: US-004 (Live Job Events), US-005 (Tab Interface), US-006 (Konto Tab)
- **Design Pattern**: Repository Pattern for data access
  - Existing patterns in `src/pdfa/repositories.py`
- **WebSocket Protocol**: Shared connection with message routing
  - Existing implementation in converter tab
- **Accessibility**: WCAG 2.1 Level AA compliance
  - Following patterns from US-005/US-006 tabs

---

**Created**: 2025-12-27
**Last Updated**: 2025-12-27
**Author**: AI Assistant (Claude Sonnet 4.5)
