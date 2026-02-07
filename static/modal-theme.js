if (!document.getElementById('toast-container')) {
  const container = document.createElement('div');
  container.id = 'toast-container';
  container.className = 'toast-container';
  document.body.appendChild(container);
}

function showToast(message, type = 'info', duration = 4000) {
  const container = document.getElementById('toast-container');
  const icons = { success: '✓', error: '✗', warning: '⚠', info: 'ℹ' };
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `<div class="toast-icon" style="font-size:24px">${icons[type] || 'ℹ'}</div><div class="toast-message">${message}</div><button onclick="this.parentElement.remove()" style="background:none;border:none;color:#888;cursor:pointer;font-size:20px">×</button>`;
  container.appendChild(toast);
  setTimeout(() => toast.remove(), duration);
}

function showConfirm(title, message, onConfirm, onCancel) {
  const overlay = document.createElement('div');
  overlay.className = 'modal-overlay active';
  overlay.innerHTML = `<div class="modal-dialog"><div class="modal-header">⚠ ${title}</div><div class="modal-body">${message}</div><div class="modal-footer"><button class="modal-btn modal-btn-secondary" onclick="this.closest('.modal-overlay').remove()">Cancel</button><button class="modal-btn modal-btn-primary" id="confirmBtn">Confirm</button></div></div>`;
  document.body.appendChild(overlay);
  document.getElementById('confirmBtn').onclick = () => { overlay.remove(); if(onConfirm) onConfirm(); };
  overlay.addEventListener('click', (e) => { if (e.target === overlay) { overlay.remove(); if(onCancel) onCancel(); } });
}

function showAlert(title, message, type = 'info') {
  const icons = { success: '✓', error: '✗', warning: '⚠', info: 'ℹ' };
  const overlay = document.createElement('div');
  overlay.className = 'modal-overlay active';
  overlay.innerHTML = `<div class="modal-dialog"><div class="modal-header">${icons[type]} ${title}</div><div class="modal-body">${message}</div><div class="modal-footer"><button class="modal-btn modal-btn-primary" onclick="this.closest('.modal-overlay').remove()">OK</button></div></div>`;
  document.body.appendChild(overlay);
  overlay.addEventListener('click', (e) => { if (e.target === overlay) overlay.remove(); });
}
