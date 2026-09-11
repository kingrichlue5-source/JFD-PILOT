const Utils = {
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    formatDate(dateStr) {
        if (!dateStr) return '-';
        const d = new Date(dateStr);
        return d.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
    },

    formatDateTime(dateStr) {
        if (!dateStr) return '-';
        const d = new Date(dateStr);
        return d.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
    },

    formatTime(dateStr) {
        if (!dateStr) return '-';
        const d = new Date(dateStr);
        return d.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
    },

    timeAgo(dateStr) {
        if (!dateStr) return '-';
        const now = new Date();
        const d = new Date(dateStr);
        const diffMs = now - d;
        const diffMin = Math.floor(diffMs / 60000);
        if (diffMin < 1) return 'Just now';
        if (diffMin < 60) return `${diffMin}m ago`;
        const diffHr = Math.floor(diffMin / 60);
        if (diffHr < 24) return `${diffHr}h ago`;
        const diffDay = Math.floor(diffHr / 24);
        return `${diffDay}d ago`;
    },

    waitMinutes(checkInTime) {
        if (!checkInTime) return 0;
        const now = new Date();
        const d = new Date(checkInTime);
        return Math.floor((now - d) / 60000);
    },

    toast(message, type = 'info') {
        const container = document.getElementById('toast-container');
        if (!container) return;
        const toast = document.createElement('div');
        const colors = {
            success: 'bg-[#10b981]',
            error:   'bg-[#f43f5e]',
            warning: 'bg-[#f59e0b]',
            info:    'bg-[#3b82f6]'
        };
        toast.className = `toast ${colors[type] || colors.info} text-white px-5 py-3 rounded-xl shadow-lg text-sm font-medium flex items-center gap-2 min-w-[280px] animate-slide-in`;
        const icons = {
            success: '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>',
            error:   '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>',
            warning: '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>',
            info:    '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>'
        };
        toast.innerHTML = `${icons[type] || icons.info}<span class="text-sm">${message}</span>`;
        container.appendChild(toast);
        setTimeout(() => { toast.style.opacity = '0'; toast.style.transform = 'translateX(40px)'; setTimeout(() => toast.remove(), 300); }, 3500);
    },

    acuityLabel(level) {
        const labels = { 1: 'E1 - Resuscitation', 2: 'E2 - Emergent', 3: 'E3 - Urgent', 4: 'E4 - Less Urgent', 5: 'E5 - Non-Urgent' };
        return labels[level] || 'Unknown';
    },

    acuityColor(level) {
        const colors = { 1: 'acuity-badge-1', 2: 'acuity-badge-2', 3: 'acuity-badge-3', 4: 'acuity-badge-4', 5: 'acuity-badge-5' };
        return colors[level] || 'bg-gray-200';
    },

    genderLabel(g) {
        return { M: 'Male', F: 'Female', O: 'Other', U: 'Unknown' }[g] || g;
    },

    statusBadge(status) {
        const colors = {
            checked_in:    'bg-blue-100 text-blue-700',
            in_triage:     'bg-amber-100 text-amber-700',
            in_progress:   'bg-violet-100 text-violet-700',
            completed:     'bg-emerald-100 text-emerald-700',
            cancelled:     'bg-slate-100 text-slate-600',
            no_show:       'bg-rose-100 text-rose-700',
            scheduled:     'bg-indigo-100 text-indigo-700',
            awaiting_disposition: 'bg-orange-100 text-orange-700',
        };
        const label = status.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
        return `<span class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[0.6875rem] font-semibold ${colors[status] || 'bg-slate-100 text-slate-600'}">${label}</span>`;
    },

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },

    skeleton(rows = 3) {
        let html = '';
        for (let i = 0; i < rows; i++) {
            html += `<div class="skeleton h-4 rounded mb-2" style="width:${70 + Math.random() * 30}%"></div>`;
        }
        return html;
    },

    animateCounter(el, target, duration = 900) {
        if (!el || target === 0) return;
        const start = performance.now();
        const initial = 0;
        const step = (now) => {
            const progress = Math.min((now - start) / duration, 1);
            const eased = 1 - Math.pow(1 - progress, 3);
            el.textContent = Math.floor(initial + (target - initial) * eased).toLocaleString();
            if (progress < 1) requestAnimationFrame(step);
        };
        requestAnimationFrame(step);
    }
};

const Modal = {
    show(title, bodyHTML, options = {}) {
        const existing = document.getElementById('app-modal');
        if (existing) existing.remove();

        const size = options.size === 'lg' ? 'max-w-3xl' : options.size === 'sm' ? 'max-w-md' : 'max-w-xl';
        const onSave = options.onSave || null;
        const saveText = options.saveText || 'Save';
        const hideSave = options.hideSave === true;

        const overlay = document.createElement('div');
        overlay.id = 'app-modal';
        overlay.className = 'modal-overlay';
        overlay.onclick = (e) => { if (e.target === overlay) Modal.hide(); };

        let footerHTML = '';
        if (!hideSave) {
            footerHTML = `
                <div class="modal-footer">
                    <button onclick="Modal.hide()" class="btn-outline text-xs">Cancel</button>
                    <button id="modal-save-btn" onclick="Modal._save()" class="btn-primary text-xs">${saveText}</button>
                </div>`;
        }

        overlay.innerHTML = `
            <div class="modal-container ${size}">
                <div class="modal-header">
                    <h3>${title}</h3>
                    <button onclick="Modal.hide()" class="modal-close">
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
                    </button>
                </div>
                <div class="modal-body">
                    ${bodyHTML}
                </div>
                ${footerHTML}
            </div>`;

        document.body.appendChild(overlay);
        Modal._onSave = onSave;

        const firstInput = overlay.querySelector('input, select, textarea');
        if (firstInput) setTimeout(() => firstInput.focus(), 100);
    },

    hide() {
        const modal = document.getElementById('app-modal');
        if (modal) modal.remove();
        Modal._onSave = null;
    },

    async _save() {
        if (Modal._onSave) {
            const btn = document.getElementById('modal-save-btn');
            if (btn) {
                btn.disabled = true;
                btn.textContent = 'Saving...';
            }
            try {
                await Modal._onSave();
                Modal.hide();
            } catch (err) {
                if (btn) {
                    btn.disabled = false;
                    btn.textContent = 'Save';
                }
                Utils.toast(err.message || 'An error occurred', 'error');
            }
        }
    },

    confirm(title, message, onConfirm) {
        Modal.show(title, `<p class="text-sm text-slate-600">${message}</p>`, {
            size: 'sm',
            saveText: 'Confirm',
            hideSave: false,
            onSave: async () => {
                await onConfirm();
            }
        });
    }
};
