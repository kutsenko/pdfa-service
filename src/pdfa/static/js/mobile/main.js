/**
 * Mobile Camera - Entry Point
 * Initializes the mobile camera client for document capture
 */

import { MobileCameraClient } from './MobileCameraClient.js';

// Initialize mobile camera client
const mobileClient = new MobileCameraClient();

// Make available globally for debugging
window.mobileClient = mobileClient;

console.log('[Mobile] PDF/A Converter Mobile Camera initialized');
