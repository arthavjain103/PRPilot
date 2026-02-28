/**
 * API Client Module
 * Handles all API calls with automatic authentication and error handling
 */

class APIClient {
  constructor(baseUrl = '') {
    this.baseUrl = baseUrl || window.location.origin;
  }

  /**
   * Make an API request with authentication
   */
  async request(endpoint, options = {}) {
    // Ensure valid token before request
    if (window.authManager && !await window.authManager.ensureValidToken()) {
      throw new Error('Authentication failed');
    }

    const url = `${this.baseUrl}${endpoint}`;
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    // Add authorization header if authenticated
    if (window.authManager && window.authManager.isAuthenticated()) {
      const authHeader = window.authManager.getAuthHeader();
      if (authHeader) {
        Object.assign(headers, authHeader);
      }
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      // Handle 401 Unauthorized (token expired/invalid)
      if (response.status === 401) {
        if (window.authManager) {
          window.authManager.logout();
        }
        throw new Error('Unauthorized');
      }

      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        throw new Error(
          data.detail || 
          data.message || 
          `API Error: ${response.status}`
        );
      }

      return {
        ok: true,
        status: response.status,
        data,
      };
    } catch (error) {
      return {
        ok: false,
        status: 0,
        error: error.message,
      };
    }
  }

  /**
   * GET request
   */
  async get(endpoint) {
    return this.request(endpoint, {
      method: 'GET',
    });
  }

  /**
   * POST request
   */
  async post(endpoint, body) {
    return this.request(endpoint, {
      method: 'POST',
      body: JSON.stringify(body),
    });
  }

  /**
   * PUT request
   */
  async put(endpoint, body) {
    return this.request(endpoint, {
      method: 'PUT',
      body: JSON.stringify(body),
    });
  }

  /**
   * DELETE request
   */
  async delete(endpoint) {
    return this.request(endpoint, {
      method: 'DELETE',
    });
  }

  /**
   * Register a new user
   */
  async register(email, password, username) {
    return this.post('/api/auth/register', {
      email,
      password,
      username,
    });
  }

  /**
   * Login user
   */
  async login(email, password) {
    return this.post('/api/auth/login', {
      email,
      password,
    });
  }

  /**
   * Refresh access token
   */
  async refreshToken(refreshToken) {
    return this.post('/api/auth/refresh', {
      refresh_token: refreshToken,
    });
  }

  /**
   * Get current user info
   */
  async getCurrentUser() {
    return this.get('/api/auth/me');
  }

  /**
   * Logout user
   */
  async logout() {
    return this.post('/api/auth/logout', {});
  }

  /**
   * Start PR analysis
   */
  async startAnalysis(repoUrl, prNumber, githubToken = null) {
    return this.post('/api/analyze/start', {
      repo_url: repoUrl,
      pr_number: prNumber,
      github_token: githubToken,
    });
  }

  /**
   * Get analysis status
   */
  async getAnalysisStatus(taskId) {
    return this.get(`/api/analyze/status/${taskId}`);
  }

  /**
   * Get analysis history
   */
  async getAnalysisHistory() {
    return this.get('/api/analyze/history');
  }

  /**
   * Health check
   */
  async healthCheck() {
    return this.get('/api/health');
  }
}

// Create global API client instance
window.apiClient = new APIClient();

/**
 * Error handler utility
 */
window.handleAPIError = (error) => {
  console.error('API Error:', error);
  
  // Show user-friendly error message
  const message = typeof error === 'string' ? error : error.message || 'An error occurred';
  
  // Try to find error alert element on page
  const errorAlert = document.getElementById('error-alert') || 
                     document.getElementById('error-message');
  
  if (errorAlert) {
    errorAlert.textContent = message;
    errorAlert.classList.add('show');
    errorAlert.style.display = 'block';
  } else {
    alert(`Error: ${message}`);
  }
};

/**
 * Success handler utility
 */
window.handleAPISuccess = (message, callback) => {
  console.log('Success:', message);
  
  const successElement = document.getElementById('success-message') || 
                        document.getElementById('success-alert');
  
  if (successElement) {
    successElement.textContent = message;
    successElement.classList.add('show');
    successElement.style.display = 'block';
  }
  
  if (callback) {
    setTimeout(callback, 1500);
  }
};
