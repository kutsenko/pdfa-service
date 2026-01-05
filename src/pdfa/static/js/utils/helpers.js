/**
 * Utility functions for PDF/A Converter
 * Contains language detection, translation helpers, file utilities, and UI helpers
 */

import { translations } from '../i18n/translations.js';

/**
 * Detect browser language preference and redirect if needed
 * @returns {string} Detected or default language code
 */
export function detectAndRedirectToPreferredLanguage() {
    const dataLang = document.documentElement.getAttribute('data-lang');

    // Only auto-detect if data-lang is "auto" (root path /)
    if (dataLang !== 'auto') {
        return dataLang;
    }

    // Get browser language preferences
    const browserLangs = navigator.languages || [navigator.language || navigator.userLanguage];
    const supportedLangs = ['en', 'de', 'es', 'fr'];

    // Find first matching supported language
    for (const browserLang of browserLangs) {
        // Extract language code (e.g., "de-DE" -> "de", "en-US" -> "en")
        const langCode = browserLang.split('-')[0].toLowerCase();

        if (supportedLangs.includes(langCode)) {
            // Redirect to language-specific URL, preserving hash if present
            const hash = window.location.hash || '';
            window.location.href = `/${langCode}${hash}`;
            return langCode; // Return while redirecting
        }
    }

    // Default to English if no match found
    return 'en';
}

/**
 * Get current language from window or detect it
 * @returns {string} Current language code
 */
export function getCurrentLanguage() {
    return window.currentLang || detectAndRedirectToPreferredLanguage();
}

/**
 * Get nested value from object using dot notation
 * @param {Object} obj - Object to search in
 * @param {string} key - Dot-notated key (e.g., "modal.title")
 * @returns {*} Value if found, undefined otherwise
 */
export function getNestedValue(obj, key) {
    // First try direct key (flat structure)
    if (obj[key] !== undefined) {
        return obj[key];
    }

    // Then try nested structure (e.g., "modal.title" -> obj.modal.title)
    const keys = key.split('.');
    let value = obj;
    for (const k of keys) {
        if (value && value[k] !== undefined) {
            value = value[k];
        } else {
            return undefined;
        }
    }
    return value;
}

/**
 * Apply translations to all elements with data-i18n attribute
 * @param {string} lang - Language code to apply
 */
export function applyTranslations(lang) {
    const t = translations[lang] || translations.en;

    // Translate all elements with data-i18n attribute
    document.querySelectorAll('[data-i18n]').forEach(element => {
        const key = element.getAttribute('data-i18n');
        const translatedText = getNestedValue(t, key);
        if (translatedText !== undefined) {
            element.textContent = translatedText;
        }
    });

    // Update page title
    const pageTitle = getNestedValue(t, 'page.title');
    if (pageTitle) {
        document.title = pageTitle;
    }

    // Mark active language in switcher
    document.querySelectorAll('.language-switcher a').forEach(link => {
        const linkLang = link.getAttribute('data-lang-code');
        if (linkLang === lang) {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });
}

/**
 * Get translated text with placeholder replacement
 * @param {string} key - Translation key
 * @param {Object} replacements - Placeholder values (e.g., {size: "5MB", max: "100MB"})
 * @returns {string} Translated text with placeholders replaced
 */
export function t(key, replacements = {}) {
    const currentLang = getCurrentLanguage();
    const translations_current = translations[currentLang] || translations.en;
    let text = getNestedValue(translations_current, key) || key;

    // Replace placeholders like {size}, {max}, etc.
    Object.keys(replacements).forEach(placeholder => {
        text = text.replace(`{${placeholder}}`, replacements[placeholder]);
    });

    return text;
}

/**
 * Format file size in human-readable format
 * @param {number} bytes - File size in bytes
 * @returns {string} Formatted file size (e.g., "5.23 MB")
 */
export function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
}

/**
 * Show status message with optional action button
 * @param {string} message - Status message HTML
 * @param {string} type - Status type: 'info', 'success', 'error', 'warning'
 * @param {Object} action - Optional action button: {label: string, onClick: function}
 */
export function showStatus(message, type, action = null) {
    const statusDiv = document.getElementById('status');
    if (!statusDiv) {
        console.error('Status div not found');
        return;
    }

    // Security: Use textContent to prevent XSS
    statusDiv.textContent = message;
    statusDiv.className = 'status ' + type;

    // Add action button if provided
    if (action && action.label && action.onClick) {
        const actionsDiv = document.createElement('div');
        actionsDiv.className = 'status-actions';

        const actionBtn = document.createElement('button');
        actionBtn.className = 'status-btn status-btn-primary';
        actionBtn.textContent = action.label;
        actionBtn.onclick = action.onClick;

        actionsDiv.appendChild(actionBtn);
        statusDiv.appendChild(actionsDiv);
    }

    if (type === 'success' || type === 'error') {
        // Don't auto-hide if there's an action button
        if (!action) {
            setTimeout(() => {
                statusDiv.style.display = 'none';
            }, 5000);
        }
    }
}

/**
 * Show a toast notification
 * @param {string} message - Toast message
 * @param {string} type - Toast type: 'info', 'success', 'error', 'warning'
 * @param {number} duration - Duration in milliseconds (default 3000)
 */
export function showToast(message, type = 'info', duration = 3000) {
    // Create or get toast container
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container';
        document.body.appendChild(container);
    }

    // Create toast element
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'polite');

    // Add to container
    container.appendChild(toast);

    // Trigger animation
    requestAnimationFrame(() => {
        toast.classList.add('toast-visible');
    });

    // Remove after duration
    setTimeout(() => {
        toast.classList.remove('toast-visible');
        toast.addEventListener('transitionend', () => {
            toast.remove();
            // Remove container if empty
            if (container.children.length === 0) {
                container.remove();
            }
        }, { once: true });
    }, duration);
}
