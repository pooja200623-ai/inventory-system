/**
 * Main JavaScript for StockPulse - Inventory Management & Sales Analytics
 * Features:
 * - Responsive offcanvas/collapsible sidebar with backdrop & swipe-friendly handling
 * - Dark mode toggle with localStorage persistence
 * - Auto-dismissing alerts & toasts
 * - Global confirm delete modal
 * - Form button loading states on submit
 * - Dynamic table responsiveness & chart resize observer
 */

(function () {
    'use strict';

    // 1. Dark Mode Management
    const THEME_KEY = 'stockpulse-theme';

    function initTheme() {
        const savedTheme = localStorage.getItem(THEME_KEY);
        const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
        const currentTheme = savedTheme ? savedTheme : (prefersDark ? 'dark' : 'light');
        applyTheme(currentTheme);
    }

    function applyTheme(theme) {
        document.documentElement.setAttribute('data-bs-theme', theme);
        localStorage.setItem(THEME_KEY, theme);

        const themeToggles = document.querySelectorAll('.theme-toggle-btn');
        themeToggles.forEach(btn => {
            const icon = btn.querySelector('i');
            if (icon) {
                if (theme === 'dark') {
                    icon.className = 'bi bi-sun-fill text-warning';
                    btn.setAttribute('title', 'Switch to light mode');
                    btn.setAttribute('aria-label', 'Switch to light mode');
                } else {
                    icon.className = 'bi bi-moon-stars text-secondary';
                    btn.setAttribute('title', 'Switch to dark mode');
                    btn.setAttribute('aria-label', 'Switch to dark mode');
                }
            }
        });

        // Trigger Chart.js redraw if charts exist
        if (window.Chart && window.Chart.instances) {
            Object.values(window.Chart.instances).forEach(chart => {
                try {
                    const textColor = theme === 'dark' ? '#cbd5e1' : '#64748b';
                    const gridColor = theme === 'dark' ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.05)';

                    if (chart.options.scales) {
                        Object.values(chart.options.scales).forEach(scale => {
                            if (scale.ticks) scale.ticks.color = textColor;
                            if (scale.grid) scale.grid.color = gridColor;
                        });
                    }
                    chart.update();
                } catch (e) {
                    // Ignore chart redraw if not fully configured
                }
            });
        }
    }

    function toggleTheme() {
        const current = document.documentElement.getAttribute('data-bs-theme') || 'light';
        const next = current === 'dark' ? 'light' : 'dark';
        applyTheme(next);
    }

    // Apply theme immediately before rendering to avoid FOUC
    initTheme();

    document.addEventListener('DOMContentLoaded', function () {
        // Wire theme toggle buttons
        document.querySelectorAll('.theme-toggle-btn').forEach(btn => {
            btn.addEventListener('click', function (e) {
                e.preventDefault();
                toggleTheme();
            });
        });

        // 2. Responsive Sidebar Management
        const sidebar = document.getElementById('sidebar');
        const sidebarToggleBtn = document.getElementById('sidebarToggleBtn');
        const sidebarCloseBtn = document.getElementById('sidebarCloseBtn');
        const backdrop = document.getElementById('sidebarBackdrop');

        function openSidebar() {
            if (sidebar) {
                sidebar.classList.add('show');
                if (backdrop) backdrop.classList.add('show');
                document.body.style.overflow = window.innerWidth < 992 ? 'hidden' : '';
            }
        }

        function closeSidebar() {
            if (sidebar) {
                sidebar.classList.remove('show');
                if (backdrop) backdrop.classList.remove('show');
                document.body.style.overflow = '';
            }
        }

        if (sidebarToggleBtn) {
            sidebarToggleBtn.addEventListener('click', function (e) {
                e.preventDefault();
                if (sidebar && sidebar.classList.contains('show')) {
                    closeSidebar();
                } else {
                    openSidebar();
                }
            });
        }

        if (sidebarCloseBtn) {
            sidebarCloseBtn.addEventListener('click', function (e) {
                e.preventDefault();
                closeSidebar();
            });
        }

        if (backdrop) {
            backdrop.addEventListener('click', function () {
                closeSidebar();
            });
        }

        // Close sidebar on escape key
        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape' && sidebar && sidebar.classList.contains('show')) {
                closeSidebar();
            }
        });

        // Handle resize across 992px breakpoint
        window.addEventListener('resize', function () {
            if (window.innerWidth >= 992) {
                if (backdrop) backdrop.classList.remove('show');
                document.body.style.overflow = '';
            }
        });

        // 3. Auto-dismiss alerts after 5 seconds
        const alerts = document.querySelectorAll('.alert-dismissible');
        alerts.forEach(function (alert) {
            setTimeout(function () {
                try {
                    const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
                    if (bsAlert) bsAlert.close();
                } catch (e) {
                    // Ignore if already dismissed
                }
            }, 5000);
        });

        // 4. Form Loading States on Submit
        document.querySelectorAll('form').forEach(function (form) {
            // Skip search/filter GET forms from showing spinners
            if (form.method.toLowerCase() === 'get') return;
            // Skip forms with data-no-spinner attribute
            if (form.hasAttribute('data-no-spinner')) return;

            form.addEventListener('submit', function (e) {
                if (form.checkValidity && !form.checkValidity()) {
                    return; // let HTML5 validation handle invalid form
                }
                const submitBtn = form.querySelector('button[type="submit"]');
                if (submitBtn && !submitBtn.disabled) {
                    // Wrap existing button content if not already wrapped
                    if (!submitBtn.querySelector('.btn-text-content')) {
                        const originalHtml = submitBtn.innerHTML;
                        submitBtn.innerHTML = `<span class="btn-text-content">${originalHtml}</span>`;
                    }
                    submitBtn.classList.add('is-loading');
                    // Prevent repeated clicks
                    setTimeout(() => {
                        submitBtn.disabled = true;
                    }, 50);
                }
            });
        });

        // 5. Delete Confirmation Modal
        const deleteModalEl = document.getElementById('deleteConfirmModal');
        if (deleteModalEl) {
            const deleteModal = new bootstrap.Modal(deleteModalEl);
            const deleteForm = deleteModalEl.querySelector('#deleteConfirmForm');
            const deleteMessage = deleteModalEl.querySelector('#deleteConfirmMessage');
            const deleteItemName = deleteModalEl.querySelector('#deleteConfirmItemName');

            // Wire any element with data-confirm-delete
            document.querySelectorAll('[data-confirm-delete]').forEach(btn => {
                btn.addEventListener('click', function (e) {
                    e.preventDefault();
                    const actionUrl = this.getAttribute('data-delete-url') || this.getAttribute('href');
                    const itemName = this.getAttribute('data-item-name') || 'this item';
                    const message = this.getAttribute('data-item-message') || 'Are you sure you want to delete this record? This action cannot be undone.';

                    if (deleteForm && actionUrl) deleteForm.setAttribute('action', actionUrl);
                    if (deleteItemName) deleteItemName.textContent = itemName;
                    if (deleteMessage) deleteMessage.textContent = message;

                    deleteModal.show();
                });
            });
        }

        // 6. Ensure all tables in cards have responsive wrappers
        document.querySelectorAll('.card-body > table:not(.no-responsive)').forEach(table => {
            if (!table.parentElement.classList.contains('table-responsive')) {
                const wrapper = document.createElement('div');
                wrapper.className = 'table-responsive';
                table.parentNode.insertBefore(wrapper, table);
                wrapper.appendChild(table);
            }
        });

        // 7. Initialize Bootstrap Tooltips & Popovers
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"], [title]:not([data-bs-toggle])'));
        tooltipTriggerList.forEach(function (tooltipTriggerEl) {
            // Skip title on inputs, dropdowns or empty
            if (tooltipTriggerEl.tagName === 'INPUT' || tooltipTriggerEl.getAttribute('data-bs-toggle') === 'dropdown') return;
            const titleVal = tooltipTriggerEl.getAttribute('title');
            if (titleVal && titleVal.trim()) {
                new bootstrap.Tooltip(tooltipTriggerEl, {
                    delay: { show: 300, hide: 100 }
                });
            }
        });
    });
})();
