// Themed Modal & Toast System - Include in all pages

// Create toast container on page load
if (!document.getElementById('toast-container')) {
  const container = document.createElement('div');
  container.id = 'toast-container';
  container.className = 'toast-container';
  document.body.appendChild(container);
}

// Show Toast Notification
function showToast(message, type = 'info', duration = 4000) {
  const container = document.getElementById('toast-container');
  
  const icons = {
    success: '✓',
    error: '✗',
    warning: '⚠',
    info: 'ℹ'
  };
  
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `
    <div class="toast-icon">${icons[type] || 'ℹ'}</div>
    <div class="toast-message">${message}</div>
    <button class="toast-close" onclick="this.parentElement.remove()">×</button>
  `;
  
  container.appendChild(toast);
  
  // Auto-remove after duration
  setTimeout(() => {
    toast.style.animation = 'toastSlideIn 0.3s ease reverse';
    setTimeout(() => toast.remove(), 300);
  }, duration);
}

// Show Themed Confirm Dialog
function showConfirm(title, message, onConfirm, onCancel) {
  const overlay = document.createElement('div');
  overlay.className = 'modal-overlay active';
  
  overlay.innerHTML = `
    <div class="modal-dialog">
      <div class="modal-header">
        ⚠ ${title}
      </div>
      <div class="modal-body">
        ${message}
      </div>
      <div class="modal-footer">
        <button class="modal-btn modal-btn-secondary" onclick="this.closest('.modal-overlay').remove(); ${onCancel ? `(${onCancel})()` : ''}">
          Cancel
        </button>
        <button class="modal-btn modal-btn-primary" onclick="this.closest('.modal-overlay').remove(); (${onConfirm})()">
          Confirm
        </button>
      </div>
    </div>
  `;
  
  document.body.appendChild(overlay);
  
  // Close on overlay click
  overlay.addEventListener('click', (e) => {
    if (e.target === overlay) {
      overlay.remove();
      if (onCancel) onCancel();
    }
  });
}

// Show Themed Alert Dialog
function showAlert(title, message, type = 'info') {
  const icons = {
    success: '✓',
    error: '✗',
    warning: '⚠',
    info: 'ℹ'
  };
  
  const overlay = document.createElement('div');
  overlay.className = 'modal-overlay active';
  
  overlay.innerHTML = `
    <div class="modal-dialog">
      <div class="modal-header">
        ${icons[type]} ${title}
      </div>
      <div class="modal-body">
        ${message}
      </div>
      <div class="modal-footer">
        <button class="modal-btn modal-btn-primary" onclick="this.closest('.modal-overlay').remove()">
          OK
        </button>
      </div>
    </div>
  `;
  
  document.body.appendChild(overlay);
  
  // Close on overlay click
  overlay.addEventListener('click', (e) => {
    if (e.target === overlay) {
      overlay.remove();
    }
  });
  
  // Close on Escape
  const escHandler = (e) => {
    if (e.key === 'Escape') {
      overlay.remove();
      document.removeEventListener('keydown', escHandler);
    }
  };
  document.addEventListener('keydown', escHandler);
}

// Show Themed Prompt Dialog
function showPrompt(title, message, defaultValue, onConfirm) {
  const overlay = document.createElement('div');
  overlay.className = 'modal-overlay active';
  
  overlay.innerHTML = `
    <div class="modal-dialog">
      <div class="modal-header">
        ${title}
      </div>
      <div class="modal-body">
        <p style="margin-bottom: 15px;">${message}</p>
        <input type="text" id="promptInput" 
               value="${defaultValue || ''}"
               style="width: 100%; padding: 10px; background: #0a0a0a; border: 1px solid #444; 
                      border-radius: 6px; color: #c5a000; font-size: 14px;">
      </div>
      <div class="modal-footer">
        <button class="modal-btn modal-btn-secondary" onclick="this.closest('.modal-overlay').remove()">
          Cancel
        </button>
        <button class="modal-btn modal-btn-primary" id="promptConfirm">
          OK
        </button>
      </div>
    </div>
  `;
  
  document.body.appendChild(overlay);
  
  const input = overlay.querySelector('#promptInput');
  const confirmBtn = overlay.querySelector('#promptConfirm');
  
  confirmBtn.onclick = () => {
    const value = input.value;
    overlay.remove();
    if (onConfirm) onConfirm(value);
  };
  
  input.focus();
  input.select();
  
  input.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
      confirmBtn.click();
    }
  });
  
  overlay.addEventListener('click', (e) => {
    if (e.target === overlay) {
      overlay.remove();
    }
  });
}

// Replace native dialogs
window.themedAlert = showAlert;
window.themedConfirm = showConfirm;
window.themedPrompt = showPrompt;
window.showToast = showToast;

// Example usage:
// showToast('Settings saved successfully!', 'success');
// showToast('Failed to connect to camera', 'error');
// showConfirm('Reset All', 'Are you sure you want to reset all cameras?', () => { /* do reset */ });
// showAlert('Camera Info', 'Camera 0: 1920x1080 @ 30fps', 'info');
