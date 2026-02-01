# Taskyn TUI - Design Document

**Feature:** Terminal User Interface for Taskyn
**Date:** 2026-02-01

---

## Architecture Overview

```
src/taskyn/
├── tui/                          # NEW: TUI module
│   ├── __init__.py
│   ├── app.py                    # Main TaskynTUI application class
│   ├── taskyn.tcss               # Global stylesheet
│   │
│   ├── screens/                  # Full-screen views
│   │   ├── __init__.py
│   │   ├── dashboard.py          # Main dashboard screen
│   │   ├── project.py            # Project detail with tabs
│   │   ├── task_detail.py        # Task detail view
│   │   └── settings.py           # Settings screen
│   │
│   ├── widgets/                  # Reusable UI components
│   │   ├── __init__.py
│   │   ├── project_tree.py       # Hierarchical project tree
│   │   ├── task_table.py         # Task list table
│   │   ├── task_card.py          # Task card (for kanban)
│   │   ├── task_form.py          # Create/edit task form
│   │   ├── timer_display.py      # Time tracking widget
│   │   ├── stats_panel.py        # Statistics display
│   │   ├── activity_log.py       # Activity feed
│   │   └── status_bar.py         # Custom status bar
│   │
│   ├── dialogs/                  # Modal dialogs
│   │   ├── __init__.py
│   │   ├── confirm.py            # Confirmation dialog
│   │   ├── quick_task.py         # Quick task creation
│   │   └── status_picker.py      # Status change picker
│   │
│   └── commands/                 # Command palette
│       ├── __init__.py
│       └── providers.py          # Search providers
│
├── cli/
│   ├── main.py                   # MODIFY: Add tui command
│   └── tui.py                    # NEW: TUI launch commands
│
└── core/                         # Existing - no changes
    └── ...
```

---

## Component Design

### 1. Main Application (app.py)

```python
class TaskynTUI(App):
    """Main Taskyn TUI application."""

    TITLE = "Taskyn"
    CSS_PATH = "taskyn.tcss"

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("ctrl+n", "new_task", "New Task"),
        ("ctrl+p", "command_palette", "Commands"),
        ("/", "search", "Search"),
        ("?", "help", "Help"),
        ("1", "view_dashboard", "Dashboard"),
        ("2", "view_projects", "Projects"),
        ("3", "view_settings", "Settings"),
    ]

    SCREENS = {
        "dashboard": DashboardScreen,
        "project": ProjectScreen,
        "task": TaskDetailScreen,
        "settings": SettingsScreen,
    }

    COMMANDS = App.COMMANDS | {TaskSearchProvider}
```

**State Management:**
- Active project context stored in `app.current_project`
- Active timer stored in `app.active_timer`
- Use reactive attributes for automatic UI updates

---

### 2. Dashboard Screen (screens/dashboard.py)

```
Layout:
┌─────────────────────────────────────────────────────────┐
│ Header                                                   │
├──────────────┬──────────────────────────────────────────┤
│              │                                          │
│ ProjectTree  │  TaskTable                               │
│ (sidebar)    │  (main content)                          │
│              │                                          │
│              ├──────────────────┬───────────────────────┤
│              │ StatsPanel       │ TimerDisplay          │
│              ├──────────────────┴───────────────────────┤
│              │ ActivityLog                              │
├──────────────┴──────────────────────────────────────────┤
│ Footer                                                   │
└─────────────────────────────────────────────────────────┘
```

**CSS Grid Layout:**
```css
DashboardScreen {
    layout: grid;
    grid-size: 2 3;
    grid-columns: 25 1fr;
    grid-rows: 1fr auto auto;
}

#sidebar {
    row-span: 3;
}
```

---

### 3. Project Tree (widgets/project_tree.py)

**Hierarchy Model:**
```
Company (icon: 🏢)
└── Project (icon: 📁)
    └── Milestone (icon: 🎯)
        └── Story (icon: 📖)
            └── Task (icon: ✓)
```

**Data Binding:**
- Tree nodes store `{id, type, name}` in `node.data`
- On selection, emit `ProjectTree.NodeSelected` message
- Parent screen handles navigation based on node type

**Custom Rendering:**
```python
def render_label(self, node, base_style, style):
    data = node.data
    icon = NODE_ICONS.get(data.get("type", ""), "")
    status = data.get("status", "")
    status_style = STATUS_STYLES.get(status, "")
    return Text(f"{icon} {node.label}", style=status_style)
```

---

### 4. Task Table (widgets/task_table.py)

**Columns:**
| Column   | Width | Sortable | Description |
|----------|-------|----------|-------------|
| Status   | 8     | Yes      | Status icon + abbreviated text |
| Title    | 1fr   | Yes      | Task title, truncated |
| Priority | 10    | Yes      | Priority icon + text |
| Due      | 12    | Yes      | Due date, relative format |

**Features:**
- Zebra stripes for readability
- Row cursor (full row selection)
- Keyboard sorting with column key (s+column letter)
- Status change via Space key
- Detail view via Enter key

---

### 5. Task Form (widgets/task_form.py)

**Form Fields:**
```python
FIELDS = [
    ("title", Input, {"validators": [Length(1, 200)]}),
    ("project", Select, {"options": project_options}),
    ("type", Select, {"options": [("Task", "task"), ("Story", "story")]}),
    ("priority", Select, {"options": PRIORITY_OPTIONS}),
    ("status", Select, {"options": status_options}),  # Dynamic per methodology
    ("description", TextArea, {}),
    ("due_date", Input, {"validators": [DateValidator()]}),
    ("estimate", Input, {"validators": [DurationValidator()]}),
]
```

**Validation:**
- Real-time validation with visual feedback
- Submit disabled until valid
- Clear error messages below each field

---

### 6. Timer Display (widgets/timer_display.py)

**States:**
- **Idle:** Shows "00:00:00" dimmed, "No active timer" text
- **Running:** Animated digits, task name, pulsing record indicator
- **Paused:** Static digits, "PAUSED" indicator

**Implementation:**
```python
class TimerDisplay(Widget):
    elapsed = reactive(0)
    running = reactive(False)
    task_name = reactive("")

    def on_mount(self):
        self.timer_handle = self.set_interval(1, self.tick, pause=True)

    def tick(self):
        if self.running:
            self.elapsed += 1

    def watch_elapsed(self, elapsed):
        self.query_one(Digits).update(format_duration(elapsed))
```

---

### 7. Activity Log (widgets/activity_log.py)

**Entry Types:**
- Task created/updated/deleted
- Status changed
- Timer started/stopped
- Time entry logged

**Format:**
```
[12:30] You created task "Implement TUI"
[12:25] You changed "Research" status to DONE
[12:20] You started timer on "Design mockups"
```

**Implementation:**
- Use `RichLog` widget
- Auto-scroll to latest
- Limit to 100 entries (configurable)
- Lazy load older entries on scroll up

---

### 8. Confirm Dialog (dialogs/confirm.py)

**Design:**
- Modal overlay with semi-transparent background
- Centered dialog box
- Warning icon for destructive actions
- Keyboard shortcuts: `y` = Yes, `n`/`Esc` = No
- Returns boolean to callback

---

### 9. Command Palette Providers (commands/providers.py)

**TaskSearchProvider:**
- Searches tasks by title
- Shows task context (project, status)
- Opens task detail on selection

**CommandProvider:**
- System commands (new task, toggle theme, etc.)
- Shows keyboard shortcut in results
- Executes action on selection

---

## CSS Theming (taskyn.tcss)

**Color Palette: Vibrant Modern**

```css
/* Primary Colors */
$primary: #8B5CF6;      /* Purple - main brand color */
$accent: #06B6D4;       /* Cyan - focus, highlights */
$success: #10B981;      /* Emerald - done, success */
$warning: #F59E0B;      /* Amber - in progress, medium */
$error: #F43F5E;        /* Rose - blocked, high priority */

/* Status Colors */
$status-backlog: #94A3B8;    /* Slate - waiting */
$status-todo: #8B5CF6;       /* Purple - ready */
$status-progress: #F59E0B;   /* Amber - active */
$status-done: #10B981;       /* Emerald - completed */
$status-blocked: #F43F5E;    /* Rose - blocked */

/* Priority Colors */
$priority-high: #F43F5E;     /* Rose - urgent */
$priority-medium: #F59E0B;   /* Amber - normal */
$priority-low: #94A3B8;      /* Slate - can wait */

/* UI Colors */
$header-bg: #8B5CF6;         /* Purple header */
$focus-border: #06B6D4;      /* Cyan focus ring */
$timer-active: #06B6D4;      /* Cyan timer display */
$rec-indicator: #F43F5E;     /* Rose recording dot */
```

**Dynamic Classes:**
```css
.status-backlog { color: $status-backlog; }
.status-todo { color: $status-todo; }
.status-in_progress { color: $status-progress; }
.status-done { color: $status-done; text-style: strike; }
.status-blocked { color: $status-blocked; }

.priority-high { color: $priority-high; }
.priority-medium { color: $priority-medium; }
.priority-low { color: $priority-low; }

*:focus { border: tall $focus-border; }
```

---

## Data Flow

### Reading Data

```
TUI Widget → Core API → Database
    ↑           ↓
    └── Pydantic Models ←┘
```

Widgets call existing core functions:
- `taskyn.core.project.get_projects()`
- `taskyn.core.work_items.get_tasks()`
- `taskyn.core.time_entry.get_active_timer()`

### Writing Data

```
Form Input → Validation → Core API → Database
                ↓
            Activity Log (auto-logged by core)
```

### Reactive Updates

```python
# In widget
def on_mount(self):
    self.load_data()

def load_data(self):
    with get_db() as db:
        self.tasks = get_tasks(db, project_id=self.project_id)

# When data changes
def on_task_created(self, event):
    self.load_data()  # Refresh from database
```

---

## Error Handling Strategy

1. **Database Errors:** Show notification, allow retry
2. **Validation Errors:** Inline feedback, prevent submission
3. **Network Errors:** N/A (local SQLite)
4. **Unexpected Errors:** Log to debug, show generic message

---

## Testing Strategy

### Unit Tests
- Each widget tested in isolation
- Mock database calls
- Test reactive behavior
- Test event handling

### Integration Tests
```python
async def test_create_task_flow():
    app = TaskynTUI()
    async with app.run_test() as pilot:
        await pilot.press("ctrl+n")          # Open form
        await pilot.press(*"Test task")      # Type title
        await pilot.press("tab", "tab")      # Navigate
        await pilot.click("#save")           # Save
        # Assert task appears in list
```

### Snapshot Tests
- Dashboard initial state
- Task detail view
- Form states (empty, filled, errors)
- Dialog states

---

## Dependencies

**New:**
```toml
[project.optional-dependencies]
tui = [
    "textual>=0.50.0",
    "textual-dev>=1.0.0",  # Development tools
]
```

**pyproject.toml entry point:**
```toml
[project.scripts]
taskyn = "taskyn.cli.main:app"
```

---

## Migration Path

Phase 1: Core TUI (MVP)
- Dashboard with tree, task list, basic navigation
- Task detail view
- New task form

Phase 2: Enhanced Features
- Timer integration
- Activity log
- Command palette search

Phase 3: Polish
- Kanban board view
- Settings screen
- Responsive layout improvements
- Theme customization
