/**
 * Authentication Module
 * Handles JWT token management and authentication state
 */

class AuthManager {
  constructor() {
    this.accessToken = localStorage.getItem('access_token');
    this.refreshToken = localStorage.getItem('refresh_token');
  }

  /**
   * Store tokens in localStorage
   */
  setTokens(accessToken, refreshToken) {
    this.accessToken = accessToken;
    this.refreshToken = refreshToken;
    localStorage.setItem('access_token', accessToken);
    localStorage.setItem('refresh_token', refreshToken);
  }

  /**
   * Get the current access token
   */
  getAccessToken() {
    return this.accessToken;
  }

  /**
   * Get the current refresh token
   */
  getRefreshToken() {
    return this.refreshToken;
  }

  /**
   * Check if user is authenticated
   */
  isAuthenticated() {
    return !!this.accessToken;
  }

  /**
   * Refresh the access token using the refresh token
   */
  async refreshAccessToken() {
    if (!this.refreshToken) {
      this.logout();
      return false;
    }

    try {
      const response = await fetch('/api/auth/refresh', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          refresh_token: this.refreshToken,
        }),
      });

      if (!response.ok) {
        this.logout();
        return false;
      }

      const data = await response.json();
      this.setTokens(data.access_token, data.refresh_token);
      return true;
    } catch (error) {
      console.error('Token refresh failed:', error);
      this.logout();
      return false;
    }
  }

  /**
   * Clear authentication data and logout
   */
  logout() {
    this.accessToken = null;
    this.refreshToken = null;
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    window.location.href = '/login';
  }

  /**
   * Get authorization header for API calls
   */
  getAuthHeader() {
    if (!this.accessToken) {
      return null;
    }
    return {
      'Authorization': `Bearer ${this.accessToken}`,
    };
  }

  /**
   * Decode JWT token (basic, doesn't verify signature)
   */
  decodeToken(token) {
    try {
      const base64Url = token.split('.')[1];
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
      const jsonPayload = decodeURIComponent(
        atob(base64)
          .split('')
          .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
          .join('')
      );
      return JSON.parse(jsonPayload);
    } catch (error) {
      console.error('Token decode failed:', error);
      return null;
    }
  }

  /**
   * Check if token is expired
   */
  isTokenExpired(token) {
    const payload = this.decodeToken(token);
    if (!payload || !payload.exp) {
      return true;
    }
    return Date.now() >= payload.exp * 1000;
  }

  /**
   * Ensure valid token before API call
   */
  async ensureValidToken() {
    if (!this.accessToken) {
      this.logout();
      return false;
    }

    if (this.isTokenExpired(this.accessToken)) {
      return this.refreshAccessToken();
    }

    return true;
  }
}

// Create global auth manager instance
window.authManager = new AuthManager();

// Check authentication on page load
document.addEventListener('DOMContentLoaded', () => {
  // Protect dashboard and history pages
  const protectedPages = ['/dashboard', '/history'];
  const currentPath = window.location.pathname;

  if (protectedPages.includes(currentPath) && !window.authManager.isAuthenticated()) {
    window.location.href = '/login';
  }
});
