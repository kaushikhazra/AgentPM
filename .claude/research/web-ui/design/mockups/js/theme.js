// Taskyn Theme System
const STORAGE_KEY_MODE = 'taskyn-mode';
const STORAGE_KEY_THEME = 'taskyn-theme';

function setMode(mode) {
    document.documentElement.setAttribute('data-mode', mode);
    localStorage.setItem(STORAGE_KEY_MODE, mode);
    updateModeIcon(mode);

    // Update mode toggle buttons if they exist
    document.querySelectorAll('.mode-toggle button, [data-mode-btn]').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.mode === mode);
    });
}

function toggleMode() {
    const currentMode = document.documentElement.getAttribute('data-mode') || 'dark';
    const newMode = currentMode === 'dark' ? 'light' : 'dark';
    setMode(newMode);
}

function updateModeIcon(mode) {
    const sunIcon = document.querySelector('.icon-sun');
    const moonIcon = document.querySelector('.icon-moon');
    if (sunIcon && moonIcon) {
        if (mode === 'dark') {
            sunIcon.style.display = 'block';
            moonIcon.style.display = 'none';
        } else {
            sunIcon.style.display = 'none';
            moonIcon.style.display = 'block';
        }
    }
}

function setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem(STORAGE_KEY_THEME, theme);

    // Update active button in quick settings
    document.querySelectorAll('.quick-theme-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.theme === theme);
    });

    // Update radio buttons in settings page
    const radio = document.querySelector(`input[name="theme"][value="${theme}"]`);
    if (radio) radio.checked = true;
}

function loadSavedPreferences() {
    const savedMode = localStorage.getItem(STORAGE_KEY_MODE) || 'dark';
    const savedTheme = localStorage.getItem(STORAGE_KEY_THEME) || 'lavender';

    setMode(savedMode);
    setTheme(savedTheme);
}

// User dropdown toggle
function toggleUserDropdown() {
    const dropdown = document.querySelector('.user-dropdown');
    if (dropdown) {
        dropdown.classList.toggle('show');
    }
}

// Close dropdown when clicking outside
document.addEventListener('click', (e) => {
    const userMenu = document.querySelector('.user-menu');
    const dropdown = document.querySelector('.user-dropdown');
    if (dropdown && userMenu && !userMenu.contains(e.target)) {
        dropdown.classList.remove('show');
    }
});

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', loadSavedPreferences);

// Also run immediately in case DOM is already loaded
if (document.readyState !== 'loading') {
    loadSavedPreferences();
}
