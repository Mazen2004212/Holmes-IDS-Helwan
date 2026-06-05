/**
 * API client for HOLMES IDS React SPA.
 * Handles CSRF tokens and cookie-session credentials.
 *
 * Cookie/SameSite notes for dev (Vite :5174 → Flask :8000):
 *   - Vite proxy forwards /api/* to Flask, so from the browser's perspective
 *     all requests go to the same origin (:5174).
 *   - credentials: 'include' ensures session cookies are sent.
 *   - CSRF token is fetched once and cached; refreshed on 403.
 */

let _csrfToken = null;

/**
 * Fetch a fresh CSRF token from the backend.
 */
export async function fetchCsrfToken() {
    const res = await fetch('/api/auth/csrf', { credentials: 'include' });
    if (res.ok) {
        const data = await res.json();
        _csrfToken = data.csrf_token;
    }
    return _csrfToken;
}

/**
 * Core API request function.
 * Automatically includes CSRF token for mutating requests.
 */
export async function apiRequest(url, options = {}) {
    const method = (options.method || 'GET').toUpperCase();
    const headers = { ...(options.headers || {}) };

    // Add CSRF token for mutating requests
    if (['POST', 'PUT', 'DELETE', 'PATCH'].includes(method)) {
        if (!_csrfToken) {
            await fetchCsrfToken();
        }
        if (_csrfToken) {
            headers['X-CSRFToken'] = _csrfToken;
        }
    }

    // Set JSON content type if body is an object (not FormData)
    if (options.body && !(options.body instanceof FormData)) {
        headers['Content-Type'] = 'application/json';
        options.body = JSON.stringify(options.body);
    }

    const res = await fetch(url, {
        ...options,
        method,
        headers,
        credentials: 'include',
    });

    // If CSRF token expired, refresh and retry once
    if (res.status === 403 && !options._retried) {
        await fetchCsrfToken();
        return apiRequest(url, { ...options, _retried: true });
    }

    return res;
}

/**
 * Convenience helpers.
 */
export const api = {
    get: (url) => apiRequest(url),
    post: (url, body) => apiRequest(url, { method: 'POST', body }),
    put: (url, body) => apiRequest(url, { method: 'PUT', body }),
    delete: (url) => apiRequest(url, { method: 'DELETE' }),

    /**
     * POST with FormData (file uploads).
     * Does NOT set Content-Type — browser sets multipart boundary automatically.
     */
    upload: (url, formData) =>
        apiRequest(url, { method: 'POST', body: formData }),
};
