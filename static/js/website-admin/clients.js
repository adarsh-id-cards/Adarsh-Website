/**
 * Website Admin - Clients Module
 * Manages local website client logos (Decoupled from legacy bridge)
 */
(function () {
    const BASE = '/dashboard/api';

    /* ===== UI HELPERS ===== */

    function setLogoPreview(logoUrl) {
        const preview = document.getElementById('cl_logo_preview');
        if (!preview) return;
        if (logoUrl) {
            preview.innerHTML = `<img src="${logoUrl}" alt="Current client logo">`;
        } else {
            preview.innerHTML = '<span>No logo uploaded</span>';
        }
    }

    function setVisibilitySelectTheme(selectEl, value) {
        if (!selectEl) return;
        selectEl.classList.remove('status-visible', 'status-hidden');
        selectEl.classList.add(value === 'visible' ? 'status-visible' : 'status-hidden');
    }

    /* ===== MODAL ACTIONS ===== */

    window.openAddClientModal = function () {
        document.getElementById('clientModalTitle').textContent = 'Add Client Logo';
        document.getElementById('clientForm').reset();
        document.getElementById('clientId').value = '';
        setLogoPreview('');
        
        if (window.ModalManager) {
            window.ModalManager.register('clientModal', { overlayClass: 'show' });
            window.ModalManager.open('clientModal');
        } else {
            document.getElementById('clientModal').classList.add('show');
        }
    };

    window.openUploadClientLogo = function (id) {
        if (!id) {
            showToast('Client ID required.', 'error');
            return;
        }

        document.getElementById('clientModalTitle').textContent = 'Update Client Logo';
        document.getElementById('clientForm').reset();
        document.getElementById('clientId').value = String(id);
        setLogoPreview('');

        ApiClient.get(`${BASE}/clients/${id}/`)
            .then(d => {
                if (!d.success || !d.client) {
                    showToast(d.message || 'Failed to load client.', 'error');
                    return;
                }
                const c = d.client;
                document.getElementById('cl_name').value = c.name || '';
                setLogoPreview(c.logo || '');
            })
            .catch(() => {
                showToast('Network error', 'error');
            });

        if (window.ModalManager) {
            window.ModalManager.register('clientModal', { overlayClass: 'show' });
            window.ModalManager.open('clientModal');
        } else {
            document.getElementById('clientModal').classList.add('show');
        }
    };

    window.closeClientModal = function () {
        if (window.ModalManager) {
            window.ModalManager.close('clientModal');
        } else {
            document.getElementById('clientModal').classList.remove('show');
        }
    };

    /* ===== CRUD ACTIONS ===== */

    window.removeClientLogo = async function (id, clientName) {
        if (!id) return;

        let ok = false;
        if (typeof waConfirm === 'function') {
            ok = await waConfirm({
                title: 'Delete Client Logo?',
                text: `Are you sure you want to delete ${clientName || 'this client'}? This action cannot be undone.`,
                icon: 'fa-solid fa-trash',
                confirmLabel: 'Delete',
                btnClass: 'btn-danger',
            });
        } else {
            ok = window.confirm(`Delete logo for ${clientName}?`);
        }
        if (!ok) return;

        ApiClient.post(`${BASE}/clients/${id}/delete/`, {})
            .then(d => {
                if (d.success) {
                    showToast('Client logo deleted', 'success');
                    window.location.reload();
                } else {
                    showToast(d.message || 'Could not delete logo', 'error');
                }
            })
            .catch(() => showToast('Network error', 'error'));
    };

    window.setClientWebsiteVisibility = function (id, visibility, selectEl) {
        if (!id || !selectEl) return;
        const newValue = visibility === 'visible' ? 'visible' : 'hidden';
        const previous = selectEl.dataset.current || (newValue === 'visible' ? 'hidden' : 'visible');
        setVisibilitySelectTheme(selectEl, newValue);

        const fd = new FormData();
        fd.set('website_is_visible', newValue === 'visible' ? 'true' : 'false');

        ApiClient.upload(`${BASE}/clients/${id}/update/`, fd)
            .then(d => {
                if (d.success) {
                    selectEl.dataset.current = newValue;
                    showToast(`Visibility updated to ${newValue}.`, 'success');
                } else {
                    selectEl.value = previous;
                    setVisibilitySelectTheme(selectEl, previous);
                    showToast(d.message || 'Could not update visibility', 'error');
                }
            })
            .catch(() => {
                selectEl.value = previous;
                setVisibilitySelectTheme(selectEl, previous);
                showToast('Network error', 'error');
            });
    };

    window.setClientWebsiteOrder = function (id, inputEl) {
        if (!id || !inputEl) return;

        const previousRaw = inputEl.dataset.currentOrder || '0';
        const previous = Number.parseInt(previousRaw, 10);
        const parsed = Number.parseInt(String(inputEl.value || '').trim(), 10);

        if (!Number.isInteger(parsed) || parsed < 0 || parsed > 9999) {
            inputEl.value = Number.isInteger(previous) ? String(previous) : '0';
            showToast('Order must be between 0 and 9999.', 'error');
            return;
        }

        inputEl.value = String(parsed);
        inputEl.disabled = true;

        const fd = new FormData();
        fd.set('website_display_order', String(parsed));

        ApiClient.upload(`${BASE}/clients/${id}/update/`, fd)
            .then(d => {
                if (d.success) {
                    inputEl.dataset.currentOrder = String(parsed);
                    showToast('Display order updated.', 'success');
                } else {
                    inputEl.value = Number.isInteger(previous) ? String(previous) : '0';
                    showToast(d.message || 'Could not update order', 'error');
                }
            })
            .catch(() => {
                inputEl.value = Number.isInteger(previous) ? String(previous) : '0';
                showToast('Network error', 'error');
            })
            .finally(() => {
                inputEl.disabled = false;
            });
    };

    /* ===== FORM SUBMIT (ADD / UPDATE) ===== */
    document.getElementById('clientForm').addEventListener('submit', function (e) {
        e.preventDefault();
        const id = document.getElementById('clientId').value;
        const name = document.getElementById('cl_name').value.trim();
        const logoInput = document.getElementById('cl_logo');
        
        if (!name) {
            showToast('Client name is required.', 'error');
            return;
        }

        const fd = new FormData();
        fd.set('name', name);
        if (logoInput.files.length > 0) {
            fd.set('logo', logoInput.files[0]);
        } else if (!id) {
            showToast('Please select a logo image.', 'error');
            return;
        }

        const url = id ? `${BASE}/clients/${id}/update/` : `${BASE}/clients/create/`;
        
        const submitBtn = this.querySelector('button[type="submit"]');
        const originalHtml = submitBtn.innerHTML;
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Saving...';

        ApiClient.upload(url, fd)
            .then(d => {
                if (d.success) {
                    showToast(d.message, 'success');
                    window.location.reload();
                } else {
                    showToast(d.message || 'Error saving client', 'error');
                }
            })
            .catch(() => showToast('Network error', 'error'))
            .finally(() => {
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalHtml;
            });
    });

    /* ===== INIT ===== */
    document.querySelectorAll('.client-visibility-select').forEach(function (selectEl) {
        const current = selectEl.value === 'visible' ? 'visible' : 'hidden';
        selectEl.dataset.current = current;
        setVisibilitySelectTheme(selectEl, current);
    });

    // Make sure old function names used in templates work
    window.editClient = function (id) { openUploadClientLogo(id); };
})();
