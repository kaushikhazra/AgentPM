/**
 * Taskyn - Context-Sensitive Keyboard Shortcuts
 * Renders shortcuts based on data-context attribute on .shortcut-bar
 */

const SHORTCUTS = {
    dashboard: [
        { key: 'C', label: 'New Company' },
        { key: 'P', label: 'New Project' },
        { key: 'T', label: 'Track Time' },
        { key: '/', label: 'Search' },
        { key: '?', label: 'Help' }
    ],
    company: [
        { key: 'C', label: 'New Company' },
        { key: 'B', label: 'Back' },
        { key: '/', label: 'Search' },
        { key: '?', label: 'Help' }
    ],
    projects: [
        { key: 'P', label: 'New Project' },
        { key: '/', label: 'Search' },
        { key: '?', label: 'Help' }
    ],
    project: [
        { key: 'E', label: 'New Epic' },
        { key: 'S', label: 'New Story' },
        { key: 'T', label: 'Track Time' },
        { key: 'B', label: 'Back' },
        { key: '/', label: 'Search' }
    ],
    epic: [
        { key: 'S', label: 'New Story' },
        { key: 'K', label: 'New Task' },
        { key: 'T', label: 'Track Time' },
        { key: 'B', label: 'Back' },
        { key: '/', label: 'Search' }
    ],
    story: [
        { key: 'K', label: 'New Task' },
        { key: 'T', label: 'Track Time' },
        { key: 'B', label: 'Back' },
        { key: '/', label: 'Search' }
    ],
    task: [
        { key: 'T', label: 'Track Time' },
        { key: 'D', label: 'Mark Done' },
        { key: 'B', label: 'Back' },
        { key: '/', label: 'Search' }
    ],
    kanban: [
        { key: 'F', label: 'Filter' },
        { key: 'T', label: 'Track Time' },
        { key: '/', label: 'Search' }
    ],
    timelog: [
        { key: 'N', label: 'New Entry' },
        { key: 'T', label: 'Start Timer' },
        { key: '/', label: 'Search' }
    ],
    tasks: [
        { key: 'K', label: 'New Task' },
        { key: 'F', label: 'Filter' },
        { key: 'T', label: 'Track Time' },
        { key: '/', label: 'Search' }
    ],
    settings: [
        { key: 'B', label: 'Back' },
        { key: '/', label: 'Search' },
        { key: '?', label: 'Help' }
    ],
    planner: [
        { key: 'A', label: 'Add Item' },
        { key: 'E', label: 'Expand All' },
        { key: 'C', label: 'Collapse All' },
        { key: '/', label: 'Search' }
    ],
    tracker: [
        { key: 'N', label: 'New Entry' },
        { key: 'T', label: 'Start Timer' },
        { key: '/', label: 'Search' }
    ]
};

function renderShortcuts() {
    const bar = document.querySelector('.shortcut-bar');
    if (!bar) return;

    const context = bar.dataset.context || 'dashboard';
    const shortcuts = SHORTCUTS[context] || SHORTCUTS.dashboard;

    bar.innerHTML = shortcuts.map(s => `
        <div class="shortcut-item">
            <kbd class="shortcut-key">${s.key}</kbd>
            <span class="shortcut-label">${s.label}</span>
        </div>
    `).join('');
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', renderShortcuts);
