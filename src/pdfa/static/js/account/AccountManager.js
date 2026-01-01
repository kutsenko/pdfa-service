/**
 * AccountManager - User account management and preferences
 * Handles account tab, user profile, settings, and account deletion
 */

import { t, formatFileSize } from '../utils/helpers.js';

export class AccountManager {
    constructor(authManager) {
        this.authManager = authManager;
        this.profileData = null;
        this.preferences = null;
        this.lastFetchTime = 0;
        this.cacheDuration = 30000; // 30 seconds
    }

    /**
     * Initialize account tab
     */
    async init() {
        // Bind event listeners
        document.getElementById('accountRetryBtn')?.addEventListener('click', () => {
            this.loadAccountData();
        });

        document.getElementById('preferencesForm')?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.savePreferences();
        });

        document.getElementById('resetPreferencesBtn')?.addEventListener('click', () => {
            this.resetPreferences();
        });

        document.getElementById('deleteAccountBtn')?.addEventListener('click', () => {
            this.showDeleteConfirmation();
        });

        // Delete modal listeners
        const deleteModal = document.getElementById('deleteAccountModal');
        document.getElementById('deleteModalCloseBtn')?.addEventListener('click', () => {
            deleteModal?.close();
        });

        document.getElementById('cancelDeleteBtn')?.addEventListener('click', () => {
            deleteModal?.close();
        });

        document.getElementById('deleteEmailInput')?.addEventListener('input', (e) => {
            this.validateDeleteEmail(e.target.value);
        });

        document.getElementById('confirmDeleteBtn')?.addEventListener('click', () => {
            this.deleteAccount();
        });

        console.log('[Account] Account manager initialized');
    }

    /**
     * Load all account data
     */
    async loadAccountData() {
        const now = Date.now();

        // Check cache
        if (this.profileData && (now - this.lastFetchTime) < this.cacheDuration) {
            console.log('[Account] Using cached data');
            this.renderAccountData();
            return;
        }

        // Show loading state
        this.showLoading();

        try {
            // Fetch profile data
            const profileResponse = await fetch('/api/v1/user/profile', {
                headers: this.authManager.getAuthHeaders()
            });

            if (!profileResponse.ok) {
                throw new Error('Failed to fetch profile');
            }

            this.profileData = await profileResponse.json();

            // Fetch preferences
            const prefsResponse = await fetch('/api/v1/user/preferences', {
                headers: this.authManager.getAuthHeaders()
            });

            if (!prefsResponse.ok) {
                throw new Error('Failed to fetch preferences');
            }

            this.preferences = await prefsResponse.json();

            this.lastFetchTime = now;
            this.renderAccountData();

        } catch (error) {
            console.error('[Account] Failed to load data:', error);
            this.showError();
        }
    }

    /**
     * Show loading state
     */
    showLoading() {
        document.getElementById('accountLoading').style.display = 'block';
        document.getElementById('accountError').style.display = 'none';
        document.getElementById('accountContent').style.display = 'none';
    }

    /**
     * Show error state
     */
    showError() {
        document.getElementById('accountLoading').style.display = 'none';
        document.getElementById('accountError').style.display = 'block';
        document.getElementById('accountContent').style.display = 'none';
    }

    /**
     * Render all account data
     */
    renderAccountData() {
        document.getElementById('accountLoading').style.display = 'none';
        document.getElementById('accountError').style.display = 'none';
        document.getElementById('accountContent').style.display = 'block';

        // Render profile
        this.renderProfile();

        // Render login stats
        this.renderLoginStats();

        // Render job stats
        this.renderJobStats();

        // Render activity log
        this.renderActivityLog();

        // Render preferences form
        this.renderPreferences();

        // Handle delete button visibility
        this.handleDeleteButton();
    }

    /**
     * Render profile information
     */
    renderProfile() {
        const user = this.profileData.user;

        document.getElementById('accountName').textContent = user.name || '-';
        document.getElementById('accountEmail').textContent = user.email || '-';
        document.getElementById('accountUserId').textContent = user.user_id || '-';

        const picture = document.getElementById('accountProfilePicture');
        if (user.picture) {
            picture.src = user.picture;
            picture.style.display = 'block';
        } else {
            picture.style.display = 'none';
        }
    }

    /**
     * Render login statistics
     */
    renderLoginStats() {
        const stats = this.profileData.login_stats;

        if (stats.created_at) {
            const created = new Date(stats.created_at);
            document.getElementById('accountCreatedAt').textContent = created.toLocaleDateString(currentLang);
        } else {
            document.getElementById('accountCreatedAt').textContent = '-';
        }

        if (stats.last_login_at) {
            const lastLogin = new Date(stats.last_login_at);
            document.getElementById('accountLastLogin').textContent = lastLogin.toLocaleString(currentLang);
        } else {
            document.getElementById('accountLastLogin').textContent = '-';
        }

        document.getElementById('accountLoginCount').textContent = stats.login_count || '-';
    }

    /**
     * Render job statistics
     */
    renderJobStats() {
        const stats = this.profileData.job_stats;

        document.getElementById('accountTotalJobs').textContent = stats.total_jobs || 0;

        if (stats.total_jobs > 0) {
            const successRate = ((stats.completed_jobs / stats.total_jobs) * 100).toFixed(1);
            document.getElementById('accountSuccessRate').textContent = `${successRate}%`;
        } else {
            document.getElementById('accountSuccessRate').textContent = '-';
        }

        if (stats.avg_duration_seconds) {
            const avgMin = (stats.avg_duration_seconds / 60).toFixed(1);
            document.getElementById('accountAvgDuration').textContent = `${avgMin} min`;
        } else {
            document.getElementById('accountAvgDuration').textContent = '-';
        }

        if (stats.total_input_bytes || stats.total_output_bytes) {
            const totalMB = ((stats.total_input_bytes + stats.total_output_bytes) / 1024 / 1024).toFixed(1);
            document.getElementById('accountDataProcessed').textContent = `${totalMB} MB`;
        } else {
            document.getElementById('accountDataProcessed').textContent = '-';
        }
    }

    /**
     * Render activity log
     */
    renderActivityLog() {
        const container = document.getElementById('accountActivityLog');
        container.innerHTML = '';

        const activities = this.profileData.recent_activity || [];

        if (activities.length === 0) {
            container.innerHTML = '<p style="color: #9ca3af;">No recent activity</p>';
            return;
        }

        activities.forEach(activity => {
            const item = document.createElement('div');
            item.className = `activity-item ${activity.event_type}`;

            const icon = this.getActivityIcon(activity.event_type);
            const time = new Date(activity.timestamp);
            const timeStr = time.toLocaleString(currentLang);

            item.innerHTML = `
                <div class="activity-icon">${icon}</div>
                <div class="activity-content">
                    <div class="activity-type">${activity.event_type}</div>
                    <div class="activity-time">${timeStr}</div>
                    <div class="activity-details">${activity.ip_address || ''}</div>
                </div>
            `;

            container.appendChild(item);
        });
    }

    /**
     * Get activity icon
     */
    getActivityIcon(eventType) {
        const icons = {
            'user_login': '🔓',
            'user_logout': '🔒',
            'auth_failure': '⚠️',
            'job_created': '📄',
            'job_completed': '✅',
            'job_failed': '❌',
            'api_call': '🔌'
        };
        return icons[eventType] || '📝';
    }

    /**
     * Render preferences form
     */
    renderPreferences() {
        if (!this.preferences) return;

        document.getElementById('prefPdfaLevel').value = this.preferences.default_pdfa_level || '2';
        document.getElementById('prefOcrLanguage').value = this.preferences.default_ocr_language || 'deu+eng';
        document.getElementById('prefCompression').value = this.preferences.default_compression_profile || 'balanced';
        document.getElementById('prefOcrEnabled').checked = this.preferences.default_ocr_enabled !== false;
        document.getElementById('prefSkipTagged').checked = this.preferences.default_skip_ocr_on_tagged !== false;
    }

    /**
     * Save preferences
     */
    async savePreferences() {
        const form = document.getElementById('preferencesForm');
        const formData = new FormData(form);

        const preferences = {
            default_pdfa_level: formData.get('default_pdfa_level'),
            default_ocr_language: formData.get('default_ocr_language'),
            default_compression_profile: formData.get('default_compression_profile'),
            default_ocr_enabled: document.getElementById('prefOcrEnabled').checked,
            default_skip_ocr_on_tagged: document.getElementById('prefSkipTagged').checked
        };

        try {
            const response = await fetch('/api/v1/user/preferences', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    ...authManager.getAuthHeaders()
                },
                body: JSON.stringify(preferences)
            });

            if (!response.ok) {
                throw new Error('Failed to save preferences');
            }

            this.preferences = await response.json();
            this.showStatus('success', t('konto.preferencesSaved'));

            // Apply to converter form
            this.applyPreferencesToConverterForm();

        } catch (error) {
            console.error('[Account] Failed to save preferences:', error);
            this.showStatus('error', t('konto.preferencesSaveFailed'));
        }
    }

    /**
     * Reset preferences to defaults
     */
    resetPreferences() {
        document.getElementById('prefPdfaLevel').value = '2';
        document.getElementById('prefOcrLanguage').value = 'deu+eng';
        document.getElementById('prefCompression').value = 'balanced';
        document.getElementById('prefOcrEnabled').checked = true;
        document.getElementById('prefSkipTagged').checked = true;
    }

    /**
     * Apply preferences to converter form
     */
    applyPreferencesToConverterForm() {
        if (!this.preferences) return;

        const converterForm = document.getElementById('converterForm');
        if (!converterForm) return;

        converterForm.querySelector('#pdfa_level').value = this.preferences.default_pdfa_level;
        converterForm.querySelector('#language').value = this.preferences.default_ocr_language;
        converterForm.querySelector('#compression_profile').value = this.preferences.default_compression_profile;
        converterForm.querySelector('#ocr_enabled').checked = this.preferences.default_ocr_enabled;
        converterForm.querySelector('#skip_ocr_on_tagged_pdfs').checked = this.preferences.default_skip_ocr_on_tagged;

        console.log('[Account] Preferences applied to converter form');
    }

    /**
     * Apply user preferences to camera tab
     */
    applyPreferencesToCameraTab() {
        if (!this.preferences) return;

        const cameraPdfType = document.getElementById('cameraPdfType');
        const cameraOcrLanguage = document.getElementById('cameraOcrLanguage');
        const cameraCompression = document.getElementById('cameraCompression');
        const cameraOcrEnabled = document.getElementById('cameraOcrEnabled');

        if (cameraPdfType) {
            cameraPdfType.value = this.preferences.default_pdfa_level || '2';
        }
        if (cameraOcrLanguage) {
            cameraOcrLanguage.value = this.preferences.default_ocr_language || 'eng';
        }
        if (cameraCompression) {
            cameraCompression.value = this.preferences.default_compression_profile || 'balanced';
        }
        if (cameraOcrEnabled) {
            cameraOcrEnabled.checked = this.preferences.default_ocr_enabled !== false;
        }

        console.log('[Account] Preferences applied to camera tab');
    }

    /**
     * Show status message
     */
    showStatus(type, message) {
        const status = document.getElementById('preferenceStatus');
        status.className = `status-message ${type}`;
        status.textContent = message;
        status.style.display = 'block';

        setTimeout(() => {
            status.style.display = 'none';
        }, 5000);
    }

    /**
     * Handle delete button visibility
     */
    handleDeleteButton() {
        const deleteBtn = document.getElementById('deleteAccountBtn');
        const disabledMsg = document.getElementById('deleteDisabledMessage');

        // Disable deletion for local user (auth disabled)
        const userId = this.profileData?.user?.user_id || '';
        if (!this.authManager.authEnabled || userId === 'local-default') {
            deleteBtn.style.display = 'none';
            disabledMsg.style.display = 'block';
        } else {
            deleteBtn.style.display = 'block';
            disabledMsg.style.display = 'none';
        }
    }

    /**
     * Show delete confirmation modal
     */
    showDeleteConfirmation() {
        const modal = document.getElementById('deleteAccountModal');
        const emailInput = document.getElementById('deleteEmailInput');
        const confirmBtn = document.getElementById('confirmDeleteBtn');

        emailInput.value = '';
        confirmBtn.disabled = true;
        document.getElementById('deleteEmailError').style.display = 'none';

        modal.showModal();
    }

    /**
     * Validate delete email input
     */
    validateDeleteEmail(input) {
        const userEmail = this.profileData?.user?.email || '';
        const confirmBtn = document.getElementById('confirmDeleteBtn');
        const errorText = document.getElementById('deleteEmailError');

        if (input === userEmail) {
            confirmBtn.disabled = false;
            errorText.style.display = 'none';
        } else {
            confirmBtn.disabled = true;
            if (input.length > 0) {
                errorText.style.display = 'block';
            } else {
                errorText.style.display = 'none';
            }
        }
    }

    /**
     * Delete account
     */
    async deleteAccount() {
        const emailInput = document.getElementById('deleteEmailInput').value;

        try {
            const response = await fetch('/api/v1/user/account', {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                    ...authManager.getAuthHeaders()
                },
                body: JSON.stringify({ email_confirmation: emailInput })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to delete account');
            }

            // Close modal
            document.getElementById('deleteAccountModal').close();

            // Show success message
            alert(t('konto.accountDeleted'));

            // Logout
            this.authManager.logout();

        } catch (error) {
            console.error('[Account] Failed to delete account:', error);
            alert(t('konto.deleteFailed') + ': ' + error.message);
        }
    }
}

