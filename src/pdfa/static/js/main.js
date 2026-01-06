/**
 * Main entry point for PDF/A Converter Web UI
 * Initializes all modules and bootstraps the application
 */

// Import translations and utilities
import { translations } from './i18n/translations.js';
import {
    detectAndRedirectToPreferredLanguage,
    getCurrentLanguage,
    applyTranslations,
    initLanguageDropdown,
    t,
    formatFileSize,
    showStatus
} from './utils/helpers.js';

// Import application classes
import { AuthManager } from './auth/AuthManager.js';
import { ConversionClient } from './conversion/ConversionClient.js';
import { AccountManager } from './account/AccountManager.js';
import { JobsManager } from './jobs/JobsManager.js';
import { CameraManager } from './camera/CameraManager.js';
import { AccessibleCameraAssistant } from './camera/AccessibleCameraAssistant.js';
import { FloatingProgressBar } from './ui/FloatingProgressBar.js';

// ============================================================================
// Language Detection and Setup
// ============================================================================

const currentLang = detectAndRedirectToPreferredLanguage();
window.currentLang = currentLang;
window.applyTranslations = applyTranslations;

// Apply translations on page load
applyTranslations(currentLang);

// Initialize language dropdown
initLanguageDropdown();

// ============================================================================
// Global Manager Instances
// ============================================================================

const authManager = new AuthManager();
window.authManager = authManager; // Make available globally for compatibility

const accountManager = new AccountManager(authManager);
window.accountManager = accountManager;

const jobsManager = new JobsManager(authManager);
window.jobsManager = jobsManager;

const cameraManager = new CameraManager();
window.cameraManager = cameraManager;

// FloatingProgressBar will be initialized after DOM is ready
let floatingProgressBar = null;

// Note: ConversionClient will be initialized after auth check

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Check if WebSocket is supported
 */
function supportsWebSocket() {
    return 'WebSocket' in window && window.WebSocket !== null;
}

/**
 * Initialize WebSocket after auth check
 */
function initializeWebSocket() {
    if (supportsWebSocket()) {
        window.conversionClient = new ConversionClient(authManager);
        window.conversionClient.connect();
        console.log('[WebSocket] Initialized after auth check');
    }
}

/**
 * Global cancel function (called from cancel button onclick)
 */
window.cancelJob = function() {
    if (window.conversionClient) {
        window.conversionClient.cancelJob();
    }
};

/**
 * Announce message to screen readers
 */
function announceToScreenReader(message) {
    const srAnnouncements = document.getElementById('srAnnouncements');
    if (srAnnouncements) {
        srAnnouncements.textContent = '';
        setTimeout(() => {
            srAnnouncements.textContent = message;
        }, 100);
    }
}

/**
 * Initialize tab navigation
 */
function initTabNavigation() {
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabPanels = document.querySelectorAll('.tab-panel');

    let currentTab = 'tab-konverter';

    function switchTab(tabId, pushHistory = true) {
        if (tabId === currentTab) return;

        console.log(`[Tabs] Switching from ${currentTab} to ${tabId}`);

        // Update buttons
        tabButtons.forEach(btn => {
            const isActive = btn.getAttribute('aria-controls') === tabId;
            btn.classList.toggle('active', isActive);
            btn.setAttribute('aria-selected', isActive);
            btn.setAttribute('tabindex', isActive ? '0' : '-1');
        });

        // Update panels
        tabPanels.forEach(panel => {
            const isActive = panel.id === tabId;
            panel.classList.toggle('active', isActive);
            panel.hidden = !isActive;
        });

        currentTab = tabId;

        // Load account data when switching to account tab
        if (tabId === 'tab-account') {
            console.log('[Tabs] Switching to account tab, loading data...');
            if (window.accountManager) {
                window.accountManager.loadAccountData();
            } else {
                console.error('[Tabs] AccountManager not available!');
            }
        }

        // Apply user preferences when switching to camera tab
        if (tabId === 'tab-kamera' && window.accountManager) {
            window.accountManager.applyPreferencesToCameraTab();
        }

        // Reapply translations
        if (window.currentLang) {
            applyTranslations(window.currentLang);
        }

        // Update URL hash
        const hash = tabId.replace('tab-', '');
        if (pushHistory && history.pushState) {
            // Create new history entry for user-initiated tab switches
            history.pushState(null, null, `#${hash}`);
        } else if (history.replaceState) {
            // Replace current entry for programmatic switches (e.g., on page load)
            history.replaceState(null, null, `#${hash}`);
        }

        // Announce to screen readers
        const tabName = document.querySelector(`[aria-controls="${tabId}"]`)?.textContent || tabId;
        announceToScreenReader(`Switched to ${tabName} tab`);
    }

    // Tab click handlers
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const targetTabId = button.getAttribute('aria-controls');
            switchTab(targetTabId);
        });

        // Keyboard navigation
        button.addEventListener('keydown', (e) => {
            let newIndex = -1;
            const currentIndex = Array.from(tabButtons).indexOf(button);

            if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
                e.preventDefault();
                newIndex = (currentIndex + 1) % tabButtons.length;
            } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
                e.preventDefault();
                newIndex = (currentIndex - 1 + tabButtons.length) % tabButtons.length;
            } else if (e.key === 'Home') {
                e.preventDefault();
                newIndex = 0;
            } else if (e.key === 'End') {
                e.preventDefault();
                newIndex = tabButtons.length - 1;
            }

            if (newIndex !== -1) {
                tabButtons[newIndex].focus();
                const targetTabId = tabButtons[newIndex].getAttribute('aria-controls');
                switchTab(targetTabId);
            }
        });
    });

    // Initialize from URL hash or default to first tab
    const hash = window.location.hash.slice(1);
    if (hash) {
        const tabId = `tab-${hash}`;
        const targetPanel = document.getElementById(tabId);
        if (targetPanel) {
            switchTab(tabId, false); // Don't push history on initial load
        } else {
            // Hash exists but panel not found - fall back to first tab
            switchTab('tab-konverter', false);
        }
    } else {
        // No hash on initial load - show first tab
        switchTab('tab-konverter', false);
    }

    // Handle hash changes (back/forward navigation)
    window.addEventListener('hashchange', () => {
        const hash = window.location.hash.slice(1);
        if (hash) {
            const tabId = `tab-${hash}`;
            const targetPanel = document.getElementById(tabId);
            if (targetPanel) {
                switchTab(tabId, false); // Don't push history for browser navigation
            }
        } else {
            // No hash means we're at the root - switch to first tab
            switchTab('tab-konverter', false);
        }
    });
}

// ============================================================================
// File Upload Handlers
// ============================================================================

function initFileUpload() {
    const fileInput = document.getElementById('file');
    const uploadArea = document.getElementById('uploadArea');
    const fileName = document.getElementById('fileName');

    if (!fileInput || !uploadArea || !fileName) {
        console.error('[FileUpload] Required elements not found');
        return;
    }

    const MAX_FILE_SIZE = 300 * 1024 * 1024; // 300 MB

    function updateFileName() {
        if (fileInput.files.length > 0) {
            const file = fileInput.files[0];

            // Validate file size
            if (file.size > MAX_FILE_SIZE) {
                showStatus(t('status.fileTooLarge', {
                    size: formatFileSize(file.size),
                    max: formatFileSize(MAX_FILE_SIZE)
                }), 'error');
                fileInput.value = '';
                fileName.textContent = '';
                return;
            }

            fileName.textContent = '✓ ' + file.name + ' (' + formatFileSize(file.size) + ')';
        } else {
            fileName.textContent = '';
        }
    }

    // File upload area click
    uploadArea.addEventListener('click', () => fileInput.click());

    // Keyboard accessibility for upload area
    uploadArea.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            fileInput.click();
        }
    });

    // Drag and drop
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });

    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('dragover');
    });

    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            fileInput.files = files;
            updateFileName();
        }
    });

    // File selection change
    fileInput.addEventListener('change', updateFileName);
}

// ============================================================================
// WebSocket Form Submission Handler
// ============================================================================

function initFormSubmission() {
    if (!supportsWebSocket()) {
        console.warn('[WebSocket] WebSocket not supported - form submission may not work');
        return;
    }

    const form = document.getElementById('converterForm');
    const fileInput = document.getElementById('file');

    if (!form || !fileInput) {
        console.error('[Form] Form or file input not found');
        return;
    }

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        if (!fileInput.files.length) {
            showStatus(t('status.selectFile'), 'error');
            return;
        }

        const file = fileInput.files[0];
        const formData = new FormData(form);

        // Build config object from form data
        const config = {
            ocr_enabled: formData.get('ocr_enabled') === 'on',
            ocr_language: formData.get('ocr_language') || 'deu',
            pdfa_level: formData.get('pdfa_level') || 'pdfa-2b',
            compression_profile: formData.get('compression_profile') || 'default',
            skip_ocr_on_tagged_pdfs: formData.get('skip_ocr_on_tagged_pdfs') === 'on'
        };

        // Convert to WebSocket job submission
        if (window.conversionClient) {
            try {
                await window.conversionClient.submitJob(file, config);
            } catch (error) {
                console.error('[Form] Submission error:', error);
                showStatus(error.message || 'Submission failed', 'error');
            }
        } else {
            showStatus('WebSocket client not initialized', 'error');
        }
    });
}

// ============================================================================
// Jobs Tab Observer
// ============================================================================

function initJobsTabObserver() {
    const jobsTabObserver = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
            if (mutation.target.id === 'tab-jobs') {
                if (mutation.target.hasAttribute('hidden')) {
                    jobsManager.onTabDeactivated();
                } else {
                    jobsManager.onTabActivated();
                }
            }
        });
    });

    const jobsTab = document.getElementById('tab-jobs');
    if (jobsTab) {
        jobsTabObserver.observe(jobsTab, {
            attributes: true,
            attributeFilter: ['hidden']
        });
    }
}

// ============================================================================
// Event List Toggle Initialization
// ============================================================================

/**
 * Initialize the event list toggle button in the conversion progress panel
 */
function initEventListToggle() {
    const eventListToggle = document.getElementById('eventListToggle');
    if (eventListToggle) {
        eventListToggle.addEventListener('click', () => {
            if (window.conversionClient) {
                window.conversionClient.toggleEventList();

                // Update toggle icon
                const icon = eventListToggle.querySelector('.toggle-icon');
                const isExpanded = eventListToggle.getAttribute('aria-expanded') === 'true';
                if (icon) {
                    icon.textContent = isExpanded ? '▼' : '▶';
                }
            }
        });
        console.log('[Events] Event list toggle initialized');
    }
}

// ============================================================================
// Debug Console Initialization (iOS Debugging)
// ============================================================================

async function initDebugConsole() {
    const debugConsole = document.getElementById('debugConsole');
    const debugContent = document.getElementById('debugConsoleContent');
    const toggleBtn = document.getElementById('toggleDebugBtn');
    const clearBtn = document.getElementById('clearDebugBtn');

    if (!debugConsole || !debugContent) return;

    // Check if debug mode is enabled from config API
    let debugEnabled = false;
    try {
        const response = await fetch('/api/config/a11y-camera');
        if (response.ok) {
            const config = await response.json();
            debugEnabled = config.debug_enabled || false;
        }
    } catch (error) {
        console.error('[Debug] Failed to load config:', error);
    }

    // If debug is disabled, completely remove debug console from DOM
    if (!debugEnabled) {
        console.log('[A11y] Debug console DISABLED - removing from DOM');
        debugConsole.remove();
        return;
    }

    // Debug is enabled - initialize console functionality
    console.log('[A11y] Debug console ENABLED');

    let isVisible = true;

    toggleBtn.addEventListener('click', () => {
        isVisible = !isVisible;
        debugConsole.classList.toggle('hidden', !isVisible);
        toggleBtn.textContent = isVisible ? 'Hide' : 'Show';
    });

    clearBtn.addEventListener('click', () => {
        debugContent.innerHTML = '';
    });

    // Security: Store original console methods for cleanup
    const originalLog = console.log;
    const originalWarn = console.warn;
    const originalError = console.error;

    // Store cleanup function globally for potential cleanup
    window._debugConsoleCleanup = () => {
        console.log = originalLog;
        console.warn = originalWarn;
        console.error = originalError;
    };

    function logToDebugConsole(message, type = 'log') {
        const entry = document.createElement('div');
        entry.className = `debug-entry debug-${type}`;
        const timestamp = new Date().toLocaleTimeString();
        entry.textContent = `[${timestamp}] ${message}`;
        debugContent.appendChild(entry);
        debugContent.scrollTop = debugContent.scrollHeight;
    }

    console.log = function(...args) {
        originalLog.apply(console, args);
        logToDebugConsole(args.join(' '), 'log');
    };

    console.warn = function(...args) {
        originalWarn.apply(console, args);
        logToDebugConsole(args.join(' '), 'warn');
    };

    console.error = function(...args) {
        originalError.apply(console, args);
        logToDebugConsole(args.join(' '), 'error');
    };

    // Capture window errors
    window.addEventListener('error', (event) => {
        logToDebugConsole(`ERROR: ${event.message} at ${event.filename}:${event.lineno}`, 'error');
    });

    // Capture unhandled promise rejections
    window.addEventListener('unhandledrejection', (event) => {
        logToDebugConsole(`UNHANDLED REJECTION: ${event.reason}`, 'error');
    });
}

// ============================================================================
// Application Initialization
// ============================================================================

async function initializeApp() {
    console.log('[App] Starting PDF/A Converter initialization...');

    // Handle OAuth callback if present
    if (!authManager.handleOAuthCallback()) {
        // Normal page load - initialize auth
        await authManager.init();
        console.log('[Auth] Authentication initialized');

        // Initialize WebSocket AFTER auth check
        if (!authManager.authEnabled || (authManager.authEnabled && authManager.user)) {
            console.log('[Auth] WebSocket connection allowed');
            initializeWebSocket();
        } else {
            console.log('[Auth] WebSocket connection skipped - user not authenticated');
        }

        // Initialize tab navigation only if user is authenticated or auth is disabled
        if (!authManager.authEnabled || (authManager.authEnabled && authManager.user)) {
            initTabNavigation();
        } else {
            console.log('[Auth] Tab navigation skipped - user not authenticated');
        }

        // Initialize managers
        accountManager.init();
        jobsManager.init();
        cameraManager.init();

        // Initialize floating progress bar
        floatingProgressBar = new FloatingProgressBar();
        window.floatingProgressBar = floatingProgressBar;

        // Initialize event list toggle button
        initEventListToggle();

        // Initialize file upload handlers
        initFileUpload();

        // Initialize form submission handler
        initFormSubmission();

        // Initialize jobs tab observer
        initJobsTabObserver();

        // Initialize debug console
        await initDebugConsole();

        console.log('[App] PDF/A Converter initialized successfully');
    }
}

// ============================================================================
// Start Application
// ============================================================================

// Wait for DOM to be ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeApp);
} else {
    initializeApp();
}
