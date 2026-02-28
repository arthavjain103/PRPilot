/**
 * General Page Interactions
 * Shared functionality and enhancements for all pages
 */

/**
 * Initialize tooltips
 */
function initTooltips() {
  const tooltips = document.querySelectorAll('[data-tooltip]');
  tooltips.forEach(element => {
    element.addEventListener('mouseenter', (e) => {
      const tooltip = document.createElement('div');
      tooltip.className = 'tooltip';
      tooltip.textContent = e.target.dataset.tooltip;
      tooltip.style.position = 'absolute';
      tooltip.style.background = 'var(--color-accent)';
      tooltip.style.color = 'white';
      tooltip.style.padding = '0.5rem 0.75rem';
      tooltip.style.borderRadius = '0.375rem';
      tooltip.style.fontSize = '0.875rem';
      tooltip.style.whiteSpace = 'nowrap';
      tooltip.style.zIndex = '1000';
      document.body.appendChild(tooltip);

      const rect = e.target.getBoundingClientRect();
      tooltip.style.top = (rect.top - tooltip.offsetHeight - 10) + 'px';
      tooltip.style.left = (rect.left + rect.width / 2 - tooltip.offsetWidth / 2) + 'px';

      e.target.addEventListener('mouseleave', () => {
        tooltip.remove();
      });
    });
  });
}

/**
 * Format date to readable string
 */
window.formatDate = (dateString) => {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
};

/**
 * Format time ago (e.g., "2 hours ago")
 */
window.timeAgo = (dateString) => {
  const date = new Date(dateString);
  const now = new Date();
  const seconds = Math.floor((now - date) / 1000);

  let interval = seconds / 31536000;
  if (interval > 1) return Math.floor(interval) + ' years ago';

  interval = seconds / 2592000;
  if (interval > 1) return Math.floor(interval) + ' months ago';

  interval = seconds / 86400;
  if (interval > 1) return Math.floor(interval) + ' days ago';

  interval = seconds / 3600;
  if (interval > 1) return Math.floor(interval) + ' hours ago';

  interval = seconds / 60;
  if (interval > 1) return Math.floor(interval) + ' minutes ago';

  return Math.floor(seconds) + ' seconds ago';
};

/**
 * Debounce function for performance
 */
window.debounce = (func, wait) => {
  let timeout;
  return (...args) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
};

/**
 * Throttle function
 */
window.throttle = (func, limit) => {
  let inThrottle;
  return (...args) => {
    if (!inThrottle) {
      func(...args);
      inThrottle = true;
      setTimeout(() => inThrottle = false, limit);
    }
  };
};

/**
 * Copy to clipboard
 */
window.copyToClipboard = async (text) => {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch (err) {
    console.error('Failed to copy:', err);
    return false;
  }
};

/**
 * Show notification
 */
window.showNotification = (message, type = 'info', duration = 3000) => {
  const notification = document.createElement('div');
  notification.className = `alert alert-${type}`;
  notification.textContent = message;
  notification.style.position = 'fixed';
  notification.style.top = '20px';
  notification.style.right = '20px';
  notification.style.zIndex = '2000';
  notification.style.maxWidth = '400px';
  notification.style.animation = 'slideInRight 0.3s ease-out';

  document.body.appendChild(notification);

  if (duration) {
    setTimeout(() => {
      notification.style.animation = 'slideInLeft 0.3s ease-out';
      setTimeout(() => notification.remove(), 300);
    }, duration);
  }

  return notification;
};

/**
 * Validate email
 */
window.validateEmail = (email) => {
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return re.test(email);
};

/**
 * Validate URL
 */
window.validateURL = (url) => {
  try {
    new URL(url);
    return true;
  } catch (error) {
    return false;
  }
};

/**
 * Get URL parameter
 */
window.getURLParameter = (param) => {
  const urlParams = new URLSearchParams(window.location.search);
  return urlParams.get(param);
};

/**
 * Smooth scroll to element
 */
window.smoothScroll = (element) => {
  element.scrollIntoView({ behavior: 'smooth' });
};

/**
 * Check if element is in viewport
 */
window.isInViewport = (element) => {
  const rect = element.getBoundingClientRect();
  return (
    rect.top >= 0 &&
    rect.left >= 0 &&
    rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
    rect.right <= (window.innerWidth || document.documentElement.clientWidth)
  );
};

/**
 * Initialize lazy loading for images
 */
function initLazyLoading() {
  const images = document.querySelectorAll('img[data-src]');
  
  if ('IntersectionObserver' in window) {
    const imageObserver = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const img = entry.target;
          img.src = img.dataset.src;
          img.removeAttribute('data-src');
          imageObserver.unobserve(img);
        }
      });
    });

    images.forEach(img => imageObserver.observe(img));
  } else {
    images.forEach(img => {
      img.src = img.dataset.src;
      img.removeAttribute('data-src');
    });
  }
}

/**
 * Add keyboard shortcuts
 */
function initKeyboardShortcuts() {
  document.addEventListener('keydown', (e) => {
    // Ctrl/Cmd + K for search/command palette (future use)
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
      e.preventDefault();
      // Trigger search
    }

    // Ctrl/Cmd + L for logout
    if ((e.ctrlKey || e.metaKey) && e.key === 'l') {
      e.preventDefault();
      if (window.authManager) {
        window.authManager.logout();
      }
    }
  });
}

/**
 * Initialize theme toggle (future dark mode support)
 */
function initThemeToggle() {
  const savedTheme = localStorage.getItem('theme') || 'light';
  document.documentElement.setAttribute('data-theme', savedTheme);

  const themeToggle = document.querySelector('[data-theme-toggle]');
  if (themeToggle) {
    themeToggle.addEventListener('click', () => {
      const currentTheme = document.documentElement.getAttribute('data-theme');
      const newTheme = currentTheme === 'light' ? 'dark' : 'light';
      document.documentElement.setAttribute('data-theme', newTheme);
      localStorage.setItem('theme', newTheme);
    });
  }
}

/**
 * Polyfill for older browsers
 */
if (!Object.hasOwn) {
  Object.hasOwn = function (obj, prop) {
    return Object.prototype.hasOwnProperty.call(obj, prop);
  };
}

/**
 * Initialize all features on page load
 */
document.addEventListener('DOMContentLoaded', () => {
  initTooltips();
  initLazyLoading();
  initKeyboardShortcuts();
  initThemeToggle();

  // Add smooth scrolling for anchor links
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
      e.preventDefault();
      const target = document.querySelector(this.getAttribute('href'));
      if (target) {
        window.smoothScroll(target);
      }
    });
  });

  // Prevent multiple form submissions
  document.querySelectorAll('form').forEach(form => {
    form.addEventListener('submit', function () {
      const button = this.querySelector('button[type="submit"]');
      if (button) {
        button.disabled = true;
        const originalText = button.textContent;
        button.textContent = 'Loading...';
        setTimeout(() => {
          if (document.contains(button)) {
            button.disabled = false;
            button.textContent = originalText;
          }
        }, 3000);
      }
    });
  });
});

/**
 * Handle online/offline status
 */
window.addEventListener('online', () => {
  window.showNotification('Back online', 'success');
});

window.addEventListener('offline', () => {
  window.showNotification('You are offline', 'warning');
});

/**
 * Unhandled error handler
 */
window.addEventListener('error', (event) => {
  console.error('Unhandled error:', event.error);
});

/**
 * Unhandled promise rejection handler
 */
window.addEventListener('unhandledrejection', (event) => {
  console.error('Unhandled promise rejection:', event.reason);
  // Prevent browser from crashing
  event.preventDefault();
});
