// DOM Elements
const form = document.getElementById('form');
const repoUrlInput = document.getElementById('repo_url');
const prNumberInput = document.getElementById('pr_number');
const githubTokenInput = document.getElementById('github_token');
const submitButton = form.querySelector('button');
const statusDiv = document.getElementById('status');

// State
let currentTaskId = null;
let pollAttempt = 0;
const MAX_POLL_ATTEMPTS = 300; // 10 minutes with 2-second intervals
const POLL_INTERVAL = 2000; // 2 seconds

// Form submission
form.addEventListener('submit', async (e) => {
  e.preventDefault();

  const repo_url = repoUrlInput.value.trim();
  const pr_number = prNumberInput.value.trim();
  const github_token = githubTokenInput.value.trim();

  // Validation
  if (!repo_url) {
    showError('Repository URL is required');
    return;
  }

  if (!pr_number) {
    showError('PR Number is required');
    return;
  }

  // Disable form during submission
  submitButton.disabled = true;
  statusDiv.innerHTML = '<div class="status-header">Initializing...</div>';

  try {
    // Start task
    const response = await fetch('/start-task', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        repo_url,
        pr_number,
        github_token: github_token || null,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      showError(errorData.detail || 'Failed to start task');
      submitButton.disabled = false;
      return;
    }

    const data = await response.json();
    currentTaskId = data.task_id;
    pollAttempt = 0;

    // Start polling for status
    pollStatus();
  } catch (error) {
    showError(`Error: ${error.message}`);
    submitButton.disabled = false;
  }
});

// Poll for task status
async function pollStatus() {
  if (pollAttempt >= MAX_POLL_ATTEMPTS) {
    showError('Task timed out after 10 minutes');
    submitButton.disabled = false;
    return;
  }

  pollAttempt++;

  try {
    const response = await fetch(`/task-status/${currentTaskId}/`);

    if (!response.ok) {
      if (response.status === 404) {
        showError('Task not found');
        submitButton.disabled = false;
        return;
      }
      throw new Error(`HTTP ${response.status}`);
    }

    const data = await response.json();

    // Display status
    displayStatus(data);

    // Check if task is completed or failed
    if (data.status === 'completed') {
      submitButton.disabled = false;
      displayResult(data);
      return;
    }

    if (data.status === 'failed') {
      submitButton.disabled = false;
      displayError(data);
      return;
    }

    // Continue polling if still pending
    setTimeout(pollStatus, POLL_INTERVAL);
  } catch (error) {
    showError(`Polling error: ${error.message}`);
    submitButton.disabled = false;
  }
}

// Display status
function displayStatus(data) {
  const statusBadgeClass = {
    pending: 'status-pending',
    processing: 'status-pending',
    completed: 'status-success',
    failed: 'status-error',
  }[data.status] || 'status-pending';

  const statusText = data.status.charAt(0).toUpperCase() + data.status.slice(1);

  statusDiv.innerHTML = `
    <div class="status-header">
      <span class="spinner"></span>Analysis Status
    </div>
    <div class="task-id">Task ID: ${data.task_id}</div>
    <span class="status-badge ${statusBadgeClass}">
      ${statusText}
    </span>
    <div style="color: var(--text-tertiary); margin-top: 16px; font-size: 0.85rem;">
      Progress: ${data.progress || '0'}% complete
      <div style="margin-top: 12px; width: 100%; height: 6px; background: var(--border); border-radius: 3px; overflow: hidden;">
        <div style="height: 100%; width: ${data.progress || 0}%; background: linear-gradient(90deg, var(--primary), var(--accent)); transition: width 0.3s ease; border-radius: 3px;"></div>
      </div>
    </div>
  `;
}

// Display result
function displayResult(data) {
  const html = `
    <div class="status-header">
      Analysis Complete
    </div>
    <div class="task-id">Task ID: ${data.task_id}</div>
    <span class="status-badge status-success">
      COMPLETED
    </span>
    <div class="result-content">
      ${data.result || 'No result available'}
    </div>
  `;
  statusDiv.innerHTML = html;
}

// Display error
function displayError(data) {
  const html = `
    <div class="status-header">
      Analysis Failed
    </div>
    <div class="task-id">Task ID: ${data.task_id}</div>
    <span class="status-badge status-error">
      ERROR
    </span>
    <div class="result-content">
      <span class="error-text">${data.error || 'Unknown error occurred'}</span>
    </div>
  `;
  statusDiv.innerHTML = html;
}

// Show error message
function showError(message) {
  statusDiv.innerHTML = `
    <div class="status-header">
      Error
    </div>
    <div class="result-content">
      <span class="error-text">${message}</span>
    </div>
  `;
}
