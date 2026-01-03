/**
 * AuthManager - OAuth authentication and session management
 * Handles Google OAuth login, token storage, and user session state
 */

import { t } from '../utils/helpers.js';

export class AuthManager {
    constructor() {
        this.token = localStorage.getItem('auth_token');
        this.user = null;
        this.authEnabled = null;
        console.log('[Auth] AuthManager initialized, token:', this.token ? 'present' : 'missing');

        // Security: Validate token on initialization
        if (this.token) {
            const payload = this.parseJWT(this.token);
            if (!payload) {
                // Token invalid or expired, remove it
                this.token = null;
                localStorage.removeItem('auth_token');
            }
        }
    }

    async init() {
        console.log('[Auth] Initializing authentication...');

        // Set up login button click handler
        this.setupLoginButton();

        // Set up logout button click handler
        this.setupLogoutButton();

        // Try to get user info to detect if auth is enabled
        try {
            const response = await fetch('/auth/user', {
                headers: this.getAuthHeaders()
            });

            if (response.status === 404) {
                // Auth endpoint doesn't exist - auth is disabled
                this.authEnabled = false;
                console.log('[Auth] Authentication is DISABLED');
                this.showMainUI();
            } else if (response.status === 401) {
                // Auth is enabled but user is not authenticated
                this.authEnabled = true;
                console.log('[Auth] Authentication is ENABLED - user not logged in');
                this.showLoginScreen();
            } else if (response.ok) {
                // Auth is enabled and user is authenticated
                this.authEnabled = true;
                this.user = await response.json();
                console.log('[Auth] Authentication is ENABLED - user logged in:', this.user.email);
                this.showAuthBar();
                this.showMainUI();
            } else {
                // Unexpected status
                console.warn('[Auth] Unexpected auth status:', response.status);
                this.authEnabled = false;
                this.showMainUI();
            }
        } catch (error) {
            console.error('[Auth] Error detecting auth status:', error);
            // On error, assume auth is disabled
            this.authEnabled = false;
            this.showMainUI();
        }
    }

    setupLoginButton() {
        const loginBtn = document.getElementById('googleLoginBtn');
        if (loginBtn) {
            loginBtn.addEventListener('click', (e) => {
                e.preventDefault();
                console.log('[Auth] Google login button clicked');
                this.login();
            });
            console.log('[Auth] Login button event listener attached');
        } else {
            console.warn('[Auth] Google login button not found in DOM');
        }
    }

    setupLogoutButton() {
        const logoutBtn = document.getElementById('logoutBtn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', (e) => {
                e.preventDefault();
                console.log('[Auth] Logout button clicked');
                this.logout();
            });
            console.log('[Auth] Logout button event listener attached');
        } else {
            console.debug('[Auth] Logout button not found in DOM (expected if not logged in)');
        }
    }

    parseJWT(token) {
        try {
            const base64Url = token.split('.')[1];
            const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
            const jsonPayload = decodeURIComponent(atob(base64).split('').map(c => {
                return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
            }).join(''));
            const payload = JSON.parse(jsonPayload);

            // Security: Validate token expiration
            if (payload.exp && payload.exp * 1000 < Date.now()) {
                console.warn('[Auth] Token expired, logging out');
                this.logout();
                return null;
            }

            return payload;
        } catch (e) {
            console.error('[Auth] Failed to parse JWT:', e);
            return null;
        }
    }

    getAuthHeaders() {
        if (!this.token) return {};
        return {
            'Authorization': `Bearer ${this.token}`
        };
    }

    async login() {
        console.log('[Auth] Initiating login redirect...');
        console.log('[Auth] Current URL:', window.location.href);
        console.log('[Auth] Redirect target: /auth/login');

        try {
            // Check if endpoint is accessible first
            const response = await fetch('/auth/login', {
                method: 'HEAD',
                redirect: 'manual'
            });
            console.log('[Auth] Pre-flight check status:', response.status);

            if (response.status === 404) {
                console.error('[Auth] Authentication endpoint not found (404) - auth may be disabled');
                alert('Authentication is not available. Please check server configuration.');
                return;
            }

            // Proceed with redirect
            console.log('[Auth] Redirecting to login endpoint...');
            window.location.href = '/auth/login';
        } catch (error) {
            console.error('[Auth] Login redirect failed:', error);
            alert('Failed to initiate login. Please check browser console for details.');
        }
    }

    logout() {
        console.log('[Auth] Logging out...');
        localStorage.removeItem('auth_token');
        this.token = null;
        this.user = null;

        // Clear URL hash to prevent tab navigation from restoring the last tab
        // after reload (which would make tab content visible on login screen)
        if (window.location.hash) {
            // Use replaceState to avoid adding to history
            history.replaceState(null, null, window.location.pathname + window.location.search);
        }

        window.location.reload();
    }

    showAuthBar() {
        const authBar = document.getElementById('authBar');
        const userPicture = document.getElementById('userPicture');
        const userName = document.getElementById('userName');
        const userEmail = document.getElementById('userEmail');
        const container = document.querySelector('.container');

        if (authBar && this.user) {
            authBar.classList.add('visible');
            userName.textContent = this.user.name || '';
            userEmail.textContent = this.user.email || '';

            if (this.user.picture) {
                userPicture.src = this.user.picture;
                userPicture.style.display = 'block';
            }

            // Add top margin to container for fixed auth bar
            if (container) {
                container.classList.add('auth-enabled');
            }
        }
    }

    showLoginScreen() {
        const loginScreen = document.getElementById('loginScreen');
        const welcomeScreen = document.getElementById('welcomeScreen');
        const container = document.querySelector('.container');
        const tabNavigation = document.querySelector('.tab-navigation');
        const tabPanels = document.querySelectorAll('.tab-panel');

        // Show login screen
        if (loginScreen) {
            loginScreen.classList.add('visible');
        }

        // Show welcome description instead of tabs
        if (welcomeScreen) {
            welcomeScreen.style.display = 'block';
            console.log('[Auth] Showing welcome screen');
        }

        // Hide tabs when not authenticated
        if (tabNavigation) {
            tabNavigation.style.display = 'none';
            console.log('[Auth] Hiding tabs - user not authenticated');
        }

        // Hide all tab panels - remove 'active' class because CSS .tab-panel.active
        // sets display:block which overrides the hidden attribute
        tabPanels.forEach(panel => {
            panel.hidden = true;
            panel.classList.remove('active');
        });

        // Also deactivate tab buttons
        const tabButtons = document.querySelectorAll('.tab-button');
        tabButtons.forEach(btn => {
            btn.classList.remove('active');
            btn.setAttribute('aria-selected', 'false');
        });

        // Keep container visible for header
        if (container) {
            container.style.display = 'block';
        }
    }

    showMainUI() {
        const loginScreen = document.getElementById('loginScreen');
        const welcomeScreen = document.getElementById('welcomeScreen');
        const container = document.querySelector('.container');
        const tabNavigation = document.querySelector('.tab-navigation');
        const tabPanels = document.querySelectorAll('.tab-panel');

        // Hide login screen
        if (loginScreen) {
            loginScreen.classList.remove('visible');
        }

        // Hide welcome screen - user is authenticated or auth is disabled
        if (welcomeScreen) {
            welcomeScreen.style.display = 'none';
            console.log('[Auth] Hiding welcome screen');
        }

        // Show tabs when authenticated or auth is disabled
        if (tabNavigation) {
            tabNavigation.style.display = '';  // Remove inline style, let CSS handle it
            console.log('[Auth] Showing tabs');
        }

        // Restore tab panel visibility - remove hidden attribute and let CSS handle it
        // The tab navigation (main.js) will set the correct active panel based on URL hash
        tabPanels.forEach(panel => {
            panel.hidden = false;
        });

        // Ensure at least the first tab panel is active if none are active
        // (can happen if showLoginScreen removed all active classes)
        const hasActivePanel = Array.from(tabPanels).some(p => p.classList.contains('active'));
        if (!hasActivePanel && tabPanels.length > 0) {
            tabPanels[0].classList.add('active');
            // Also activate the corresponding tab button
            const firstTabBtn = document.querySelector('.tab-button');
            if (firstTabBtn) {
                firstTabBtn.classList.add('active');
                firstTabBtn.setAttribute('aria-selected', 'true');
            }
        }

        // Show container
        if (container) {
            container.style.display = 'block';
        }
    }

    handleOAuthCallback() {
        // Check if we're on the callback page
        const urlParams = new URLSearchParams(window.location.search);
        const code = urlParams.get('code');
        const state = urlParams.get('state');

        if (code && window.location.pathname === '/auth/callback') {
            console.log('[Auth] Handling OAuth callback...');
            // Let the backend handle the callback
            // IMPORTANT: Set Accept header to get JSON instead of HTML
            fetch('/auth/callback' + window.location.search, {
                headers: {
                    'Accept': 'application/json'
                }
            })
                .then(res => res.json())
                .then(data => {
                    if (data.access_token) {
                        localStorage.setItem('auth_token', data.access_token);
                        console.log('[Auth] Token saved, redirecting to home...');
                        window.location.href = '/';
                    } else {
                        console.error('[Auth] No access token in callback response');
                        alert(t('auth.loginFailed'));
                        window.location.href = '/';
                    }
                })
                .catch(error => {
                    console.error('[Auth] OAuth callback error:', error);
                    alert(t('auth.loginFailed'));
                    window.location.href = '/';
                });
            return true;
        }
        return false;
    }
}
