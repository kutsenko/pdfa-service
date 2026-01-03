/**
 * Mobile Camera - Entry Point
 * Initializes the mobile camera client for document capture
 */

import { MobileCameraClient } from './MobileCameraClient.js';
import { translations } from '../i18n/translations.js';
import { applyTranslations } from '../utils/helpers.js';

// ============================================================================
// Language Detection and Setup
// ============================================================================

// Get language from URL parameter or default to 'en'
const urlParams = new URLSearchParams(window.location.search);
const lang = urlParams.get('lang') || 'en';

// Store current language globally
window.currentLang = lang;
window.applyTranslations = applyTranslations;
window.translations = translations;

// Apply translations on page load
console.log('[Mobile] Applying translations for language:', lang);
applyTranslations(lang);

// ============================================================================
// Initialize Mobile Camera Client
// ============================================================================

const mobileClient = new MobileCameraClient();

// Make available globally for debugging
window.mobileClient = mobileClient;

console.log('[Mobile] PDF/A Converter Mobile Camera initialized');
