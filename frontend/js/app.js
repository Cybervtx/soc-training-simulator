/**
 * SOC Training Simulator - Frontend Application
 * 
 * This file contains the core JavaScript functionality for the frontend.
 */

// API Configuration
const API_BASE_URL = '/api';

// ============================================
// Authentication Module
// ============================================
const Auth = {
    /**
     * Get the access token from localStorage
     * @returns {string|null} Access token or null
     */
    getToken() {
        return localStorage.getItem('access_token');
    },

    /**
     * Get the refresh token from localStorage
     * @returns {string|null} Refresh token or null
     */
    getRefreshToken() {
        return localStorage.getItem('refresh_token');
    },

    /**
     * Check if user is logged in
     * @returns {boolean} True if logged in
     */
    isLoggedIn() {
        const token = this.getToken();
        return !!token;
    },

    /**
     * Get current user from localStorage
     * @returns {object|null} User object or null
     */
    getUser() {
        const userData = localStorage.getItem('user');
        return userData ? JSON.parse(userData) : null;
    },

    /**
     * Login user
     * @param {string} email - User email
     * @param {string} password - User password
     * @returns {Promise<object>} User data and tokens
     */
    async login(email, password) {
        const response = await fetch(`${API_BASE_URL}/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email, password })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Erro ao fazer login');
        }

        // Store tokens and user data
        localStorage.setItem('access_token', data.access_token);
        localStorage.setItem('refresh_token', data.refresh_token);
        localStorage.setItem('user', JSON.stringify(data.user));

        return data;
    },

    /**
     * Register new user
     * @param {string} name - User name
     * @param {string} email - User email
     * @param {string} password - User password
     * @returns {Promise<object>} User data
     */
    async register(name, email, password) {
        const response = await fetch(`${API_BASE_URL}/auth/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ nome: name, email, password })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Erro ao registrar usuário');
        }

        return data;
    },

    /**
     * Logout user
     */
    logout() {
        // Clear localStorage
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
    },

    /**
     * Get authorization header
     * @returns {object} Authorization header object
     */
    getAuthHeader() {
        const token = this.getToken();
        return token ? { 'Authorization': `Bearer ${token}` } : {};
    }
};

// ============================================
// API Module
// ============================================
const API = {
    /**
     * Make authenticated API request
     * @param {string} endpoint - API endpoint
     * @param {object} options - Fetch options
     * @returns {Promise<object>} Response data
     */
    async request(endpoint, options = {}) {
        const headers = {
            'Content-Type': 'application/json',
            ...Auth.getAuthHeader(),
            ...options.headers
        };

        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            ...options,
            headers
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || `Erro na API: ${response.status}`);
        }

        return data;
    },

    /**
     * Get current user profile
     * @returns {Promise<object>} User data
     */
    async getProfile() {
        return this.request('/auth/me');
    },

    /**
     * Refresh access token
     * @returns {Promise<string>} New access token
     */
    async refreshToken() {
        const refreshToken = Auth.getRefreshToken();
        
        const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ refresh_token: refreshToken })
        });

        const data = await response.json();

        if (!response.ok) {
            Auth.logout();
            throw new Error(data.error || 'Sessão expirada');
        }

        // Update stored token
        localStorage.setItem('access_token', data.access_token);
        return data.access_token;
    },

    /**
     * Check IP address for abuse reports
     * @param {string} ip - IP address to check
     * @param {boolean} forceRefresh - Force refresh from API
     * @returns {Promise<object>} IP check results
     */
    async checkIP(ip, forceRefresh = false) {
        return this.request(`/abuseipdb/check?ip=${ip}&force_refresh=${forceRefresh}`);
    },

    /**
     * Get reports for an IP address
     * @param {string} ip - IP address
     * @param {number} page - Page number
     * @returns {Promise<object>} Reports data
     */
    async getIPReports(ip, page = 1) {
        return this.request(`/abuseipdb/reports?ip=${ip}&page=${page}`);
    },

    /**
     * Get AbuseIPDB statistics
     * @returns {Promise<object>} Statistics data
     */
    async getStats() {
        return this.request('/abuseipdb/stats');
    },

    /**
     * Get API rate limit status
     * @returns {Promise<object>} Rate limit status
     */
    async getRateLimit() {
        return this.request('/abuseipdb/rate-limit');
    },

    /**
     * Get API usage statistics
     * @param {number} hours - Hours to look back
     * @returns {Promise<object>} Usage statistics
     */
    async getAPIUsage(hours = 24) {
        return this.request(`/abuseipdb/usage?hours=${hours}`);
    },

    /**
     * Get cache statistics
     * @returns {Promise<object>} Cache statistics
     */
    async getCacheStats() {
        return this.request('/abuseipdb/cache');
    },

    /**
     * Get popular/high-risk IPs from cache
     * @param {number} limit - Number of entries
     * @returns {Promise<object>} Popular IPs data
     */
    async getPopularIPs(limit = 10) {
        return this.request(`/abuseipdb/popular?limit=${limit}`);
    },

    /**
     * Refresh IP cache entry
     * @param {string} ip - IP address to refresh
     * @returns {Promise<object>} Refresh result
     */
    async refreshIP(ip) {
        return this.request('/abuseipdb/refresh', {
            method: 'POST',
            body: JSON.stringify({ ip })
        });
    },

    /**
     * Clear all cache entries (admin only)
     * @returns {Promise<object>} Clear result
     */
    async clearCache() {
        return this.request('/abuseipdb/cache', {
            method: 'DELETE'
        });
    },

    /**
     * Get health check status
     * @returns {Promise<object>} Health status
     */
    async healthCheck() {
        const response = await fetch(`${API_BASE_URL}/health`);
        return response.json();
    },

    /**
     * Get public configuration
     * @returns {Promise<object>} Public configuration
     */
    async getConfig() {
        const response = await fetch(`${API_BASE_URL}/config`);
        return response.json();
    }
};

// ============================================
// UI Utilities
// ============================================
const UI = {
    /**
     * Show loading overlay
     */
    showLoading() {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            overlay.classList.remove('hidden');
        }
    },

    /**
     * Hide loading overlay
     */
    hideLoading() {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            overlay.classList.add('hidden');
        }
    },

    /**
     * Show toast notification
     * @param {string} message - Message to display
     * @param {string} type - Notification type (success, error, warning, info)
     * @param {number} duration - Duration in milliseconds
     */
    showToast(message, type = 'info', duration = 3000) {
        const container = document.getElementById('toast-container');
        if (!container) return;

        const toast = document.createElement('div');
        
        const icons = {
            success: 'fa-check-circle',
            error: 'fa-times-circle',
            warning: 'fa-exclamation-triangle',
            info: 'fa-info-circle'
        };

        const colors = {
            success: 'bg-green-500',
            error: 'bg-red-500',
            warning: 'bg-yellow-500',
            info: 'bg-blue-500'
        };

        toast.className = `flex items-center px-4 py-3 rounded-lg shadow-lg text-white ${colors[type]} bg-opacity-90`;
        toast.innerHTML = `
            <i class="fas ${icons[type]} mr-3"></i>
            <span>${message}</span>
        `;

        container.appendChild(toast);

        // Remove after duration
        setTimeout(() => {
            toast.classList.add('opacity-0', 'transition-opacity', 'duration-300');
            setTimeout(() => toast.remove(), 300);
        }, duration);
    }
};

// ============================================
// Global Error Handler
// ============================================
window.addEventListener('unhandledrejection', function(event) {
    console.error('Unhandled Promise Rejection:', event.reason);
    UI.showToast('Ocorreu um erro. Por favor, tente novamente.', 'error');
});

// ============================================
// Initialize Application
// ============================================
document.addEventListener('DOMContentLoaded', function() {
    console.log('SOC Training Simulator initialized');
    
    // Check authentication status
    if (Auth.isLoggedIn()) {
        console.log('User is logged in');
        const user = Auth.getUser();
        if (user) {
            console.log('User:', user.email, '- Role:', user.role);
        }
    } else {
        console.log('User is not logged in');
    }
});
