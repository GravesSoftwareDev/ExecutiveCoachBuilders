(function () {
    const KEY = 'ecb-theme';

    function getPreferred() {
        return localStorage.getItem(KEY) ||
            (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
    }

    function applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        const btn = document.getElementById('theme-toggle');
        if (!btn) return;
        const icon = btn.querySelector('i');
        if (theme === 'dark') {
            icon.className = 'bi bi-sun';
            btn.setAttribute('aria-label', 'Switch to light mode');
        } else {
            icon.className = 'bi bi-moon';
            btn.setAttribute('aria-label', 'Switch to dark mode');
        }
    }

    // Apply immediately (before DOMContentLoaded) to avoid flash
    applyTheme(getPreferred());

    document.addEventListener('DOMContentLoaded', function () {
        applyTheme(getPreferred());
        const btn = document.getElementById('theme-toggle');
        if (btn) {
            btn.addEventListener('click', function () {
                const next = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
                localStorage.setItem(KEY, next);
                applyTheme(next);
            });
        }
    });
})();
