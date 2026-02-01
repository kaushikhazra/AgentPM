# Textual TUI Library Research

**Date:** 2026-02-01
**Purpose:** Research for building a Terminal User Interface for Taskyn project management app

## Overview

[Textual](https://textual.textualize.io/) is a Python framework for building sophisticated Terminal User Interfaces (TUIs). Built by Textualize.io on top of the Rich library, it provides a modern, web-inspired approach to terminal application development.

**Key Characteristics:**
- Cross-platform (Windows, Linux, macOS)
- Async-first with optional async support
- CSS-like styling system
- Component-based architecture
- Built-in testing framework
- Can serve apps as web applications via `textual serve`

**Installation:**
```bash
pip install textual textual-dev
```

---

## 1. Core Concepts

### 1.1 App Class

The `App` class is the foundation for all Textual applications:

```python
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static

class TaskynApp(App):
    """Main Taskyn application."""

    TITLE = "Taskyn"
    SUB_TITLE = "AI-First Project Management"
    CSS_PATH = "taskyn.tcss"  # External CSS file

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("d", "toggle_dark", "Toggle Dark Mode"),
        ("?", "help", "Help"),
    ]

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Header()
        yield Static("Main content here")
        yield Footer()

    def on_mount(self) -> None:
        """Called when app enters application mode."""
        self.title = "Taskyn"

    def action_toggle_dark(self) -> None:
        """Toggle dark mode."""
        self.theme = "textual-dark" if self.theme == "textual-light" else "textual-light"

if __name__ == "__main__":
    app = TaskynApp()
    app.run()
```

### 1.2 Compose Method

The `compose()` method is a generator that yields widgets:

```python
from textual.containers import Horizontal, Vertical, Container

def compose(self) -> ComposeResult:
    # Use context managers for nested layouts
    with Horizontal():
        with Vertical(id="sidebar"):
            yield ProjectTree()
        with Vertical(id="main"):
            yield TaskList()
    yield Footer()
```

### 1.3 Widget Lifecycle

1. **`__init__`** - Widget construction
2. **`compose()`** - Define child widgets
3. **`on_mount()`** - Post-mount initialization
4. **`render()`** - Return renderable content (for simple widgets)

### 1.4 Key Bindings

```python
from textual.binding import Binding

class MyApp(App):
    BINDINGS = [
        Binding("ctrl+n", "new_task", "New Task", show=True),
        Binding("ctrl+s", "save", "Save", key_display="Ctrl+S"),
        Binding("escape", "cancel", "Cancel", show=False),  # Hidden from footer
    ]
```

---

## 2. Layout System

### 2.1 Vertical Layout (Default)

Arranges widgets top-to-bottom:

```css
Screen {
    layout: vertical;
}

.task-item {
    height: auto;  /* Content-based height */
}
```

### 2.2 Horizontal Layout

Arranges widgets left-to-right:

```css
#toolbar {
    layout: horizontal;
    height: 3;
}

#toolbar Button {
    width: 1fr;  /* Equal distribution */
}
```

### 2.3 Grid Layout

For complex dashboard layouts:

```css
Screen {
    layout: grid;
    grid-size: 3 2;  /* 3 columns, 2 rows */
    grid-columns: 1fr 2fr 1fr;
    grid-rows: auto 1fr;
    grid-gutter: 1;
}

#stats {
    column-span: 2;
}
```

### 2.4 Docking

Fix widgets to edges:

```css
#sidebar {
    dock: left;
    width: 30;
}

Header {
    dock: top;
}

Footer {
    dock: bottom;
}
```

### 2.5 Container Widgets

```python
from textual.containers import (
    Horizontal,      # Horizontal layout
    Vertical,        # Vertical layout
    Container,       # Generic container
    ScrollableContainer,  # With scrolling
    VerticalScroll,  # Vertical scrollable
    HorizontalScroll,  # Horizontal scrollable
)
```

---

## 3. CSS Styling

### 3.1 CSS File Structure

```css
/* taskyn.tcss */

/* Variables */
$primary: #3b82f6;
$success: #22c55e;
$warning: #f59e0b;
$error: #ef4444;

/* Type selectors */
Button {
    margin: 1;
}

/* ID selectors */
#sidebar {
    width: 30;
    background: $surface;
}

/* Class selectors */
.task-done {
    text-style: strike;
    color: $text-muted;
}

/* Pseudo-classes */
Button:hover {
    background: $primary;
}

Button:focus {
    border: thick $accent;
}

/* Combinators */
#sidebar > Tree {
    margin: 1 2;
}
```

### 3.2 Common CSS Properties

```css
Widget {
    /* Sizing */
    width: 100%;
    height: auto;
    min-width: 20;
    max-height: 50%;

    /* Spacing */
    margin: 1 2;           /* vertical horizontal */
    padding: 1 2 1 2;      /* top right bottom left */

    /* Display */
    display: block;        /* block | none */
    visibility: visible;   /* visible | hidden */

    /* Colors */
    background: $surface;
    color: $text;
    border: solid $primary;

    /* Text */
    text-align: center;    /* left | center | right */
    text-style: bold italic underline;

    /* Layout */
    layout: vertical;
    overflow: auto;        /* auto | hidden | scroll */
}
```

### 3.3 Dynamic CSS Classes

```python
# In widget or app code
def update_task_status(self, task_id: str, done: bool) -> None:
    task_widget = self.query_one(f"#task-{task_id}")
    if done:
        task_widget.add_class("task-done")
    else:
        task_widget.remove_class("task-done")

# Toggle class
widget.toggle_class("expanded")

# Check class
if widget.has_class("selected"):
    ...
```

---

## 4. Key Widgets for Taskyn

### 4.1 DataTable (Task Lists)

```python
from textual.widgets import DataTable

class TaskTable(DataTable):
    """Display tasks in a table format."""

    def on_mount(self) -> None:
        self.cursor_type = "row"
        self.zebra_stripes = True

        # Add columns
        self.add_columns("Status", "Title", "Priority", "Due Date")

        # Add rows with keys for later reference
        self.add_row("[ ]", "Implement TUI", "High", "2026-02-05", key="task-1")
        self.add_row("[x]", "Research Textual", "High", "2026-02-01", key="task-2")

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle row selection."""
        row_key = event.row_key
        self.post_message(TaskSelected(row_key.value))

    def update_task(self, task_id: str, column: str, value: str) -> None:
        """Update a cell value."""
        self.update_cell(task_id, column, value)

    def sort_by_priority(self) -> None:
        """Sort tasks by priority."""
        self.sort("Priority", key=lambda x: {"High": 0, "Medium": 1, "Low": 2}.get(x, 3))
```

### 4.2 Tree (Project Hierarchy)

```python
from textual.widgets import Tree
from textual.widgets.tree import TreeNode

class ProjectTree(Tree):
    """Display project/task hierarchy."""

    def __init__(self) -> None:
        super().__init__("Projects", id="project-tree")

    def on_mount(self) -> None:
        self.root.expand()
        self.load_projects()

    def load_projects(self) -> None:
        """Load project hierarchy from database."""
        # Example structure
        project1 = self.root.add("Taskyn Development", expand=True, data={"id": "proj-1"})
        project1.add_leaf("Setup repository", data={"id": "task-1", "type": "task"})

        milestone = project1.add("v1.0 Release", data={"id": "ms-1", "type": "milestone"})
        milestone.add_leaf("Core features", data={"id": "task-2", "type": "task"})
        milestone.add_leaf("Testing", data={"id": "task-3", "type": "task"})

    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        """Handle node selection."""
        node_data = event.node.data
        if node_data:
            self.post_message(NodeSelected(node_data))

    def render_label(self, node: TreeNode, base_style, style) -> Text:
        """Customize node rendering."""
        label = node.label
        if node.data and node.data.get("type") == "milestone":
            return Text(f"[M] {label}", style="bold cyan")
        return Text(str(label))
```

### 4.3 TabbedContent (Dashboard Views)

```python
from textual.widgets import TabbedContent, TabPane, Markdown

class DashboardTabs(TabbedContent):
    """Main dashboard with multiple views."""

    def compose(self) -> ComposeResult:
        with TabPane("Overview", id="overview"):
            yield DashboardOverview()
        with TabPane("Tasks", id="tasks"):
            yield TaskListView()
        with TabPane("Timeline", id="timeline"):
            yield TimelineView()
        with TabPane("Activity", id="activity"):
            yield ActivityLog()

    def switch_to_tasks(self) -> None:
        """Programmatically switch to tasks tab."""
        self.active = "tasks"
```

### 4.4 Input and Forms

```python
from textual.widgets import Input, Button, Select, TextArea
from textual.containers import Vertical, Horizontal
from textual.validation import Length, Regex

class TaskForm(Vertical):
    """Form for creating/editing tasks."""

    def compose(self) -> ComposeResult:
        yield Input(
            placeholder="Task title",
            id="title",
            validators=[Length(minimum=1, maximum=200)]
        )
        yield TextArea(id="description", language=None)
        yield Select(
            options=[
                ("High", "high"),
                ("Medium", "medium"),
                ("Low", "low"),
            ],
            prompt="Priority",
            id="priority"
        )
        yield Input(
            placeholder="Due date (YYYY-MM-DD)",
            id="due_date",
            validators=[Regex(r"\d{4}-\d{2}-\d{2}")]
        )
        with Horizontal():
            yield Button("Save", variant="primary", id="save")
            yield Button("Cancel", variant="default", id="cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save":
            self.save_task()
        elif event.button.id == "cancel":
            self.dismiss()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter key in inputs."""
        if event.validation_result and event.validation_result.is_valid:
            # Move to next field or save
            pass

    def save_task(self) -> None:
        title = self.query_one("#title", Input).value
        description = self.query_one("#description", TextArea).text
        priority = self.query_one("#priority", Select).value
        # ... create task
```

### 4.5 ProgressBar (Task Progress)

```python
from textual.widgets import ProgressBar, Static
from textual.containers import Horizontal

class TaskProgress(Horizontal):
    """Display task completion progress."""

    def compose(self) -> ComposeResult:
        yield Static("Progress:", classes="label")
        yield ProgressBar(total=100, show_eta=False, id="progress")
        yield Static("0%", id="percent")

    def update_progress(self, completed: int, total: int) -> None:
        percent = (completed / total * 100) if total > 0 else 0
        self.query_one("#progress", ProgressBar).update(total=total, progress=completed)
        self.query_one("#percent", Static).update(f"{percent:.0f}%")
```

### 4.6 Digits (Timer Display)

```python
from textual.widgets import Digits
from textual.reactive import reactive

class TimerDisplay(Digits):
    """Display active timer in large digits."""

    elapsed_seconds = reactive(0)

    def on_mount(self) -> None:
        self.set_interval(1, self.tick)

    def tick(self) -> None:
        if self.running:
            self.elapsed_seconds += 1

    def watch_elapsed_seconds(self, seconds: int) -> None:
        hours, remainder = divmod(seconds, 3600)
        minutes, secs = divmod(remainder, 60)
        self.update(f"{hours:02d}:{minutes:02d}:{secs:02d}")
```

### 4.7 RichLog (Activity Feed)

```python
from textual.widgets import RichLog
from rich.text import Text

class ActivityLog(RichLog):
    """Display activity feed with rich formatting."""

    def on_mount(self) -> None:
        self.auto_scroll = True
        self.max_lines = 1000

    def log_activity(self, action: str, item: str, user: str = "You") -> None:
        timestamp = datetime.now().strftime("%H:%M")
        text = Text()
        text.append(f"[{timestamp}] ", style="dim")
        text.append(user, style="bold")
        text.append(f" {action} ", style="")
        text.append(item, style="cyan")
        self.write(text)
```

---

## 5. Screens and Navigation

### 5.1 Creating Screens

```python
from textual.screen import Screen, ModalScreen

class TaskDetailScreen(Screen):
    """Full-screen task detail view."""

    BINDINGS = [
        ("escape", "pop_screen", "Back"),
        ("e", "edit", "Edit"),
        ("d", "delete", "Delete"),
    ]

    def __init__(self, task_id: str) -> None:
        super().__init__()
        self.task_id = task_id

    def compose(self) -> ComposeResult:
        yield Header()
        yield TaskDetailView(self.task_id)
        yield Footer()

    def action_edit(self) -> None:
        self.app.push_screen(TaskEditScreen(self.task_id))
```

### 5.2 Modal Dialogs

```python
from textual.screen import ModalScreen
from textual.widgets import Button, Static
from textual.containers import Vertical, Horizontal

class ConfirmDialog(ModalScreen[bool]):
    """Confirmation dialog."""

    CSS = """
    ConfirmDialog {
        align: center middle;
    }

    #dialog {
        width: 60;
        height: auto;
        border: thick $primary;
        background: $surface;
        padding: 1 2;
    }
    """

    def __init__(self, message: str) -> None:
        super().__init__()
        self.message = message

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Static(self.message)
            with Horizontal():
                yield Button("Yes", variant="primary", id="yes")
                yield Button("No", variant="default", id="no")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "yes")
```

### 5.3 Screen Navigation

```python
# Push screen onto stack (can go back)
self.app.push_screen(TaskDetailScreen(task_id))

# Push with callback for return value
def handle_confirm(confirmed: bool) -> None:
    if confirmed:
        self.delete_task(task_id)

self.app.push_screen(ConfirmDialog("Delete task?"), handle_confirm)

# Pop current screen
self.app.pop_screen()

# Switch screen (replaces top of stack)
self.app.switch_screen(DashboardScreen())
```

### 5.4 App Modes

```python
class TaskynApp(App):
    """Multi-mode application."""

    MODES = {
        "dashboard": DashboardScreen,
        "projects": ProjectsScreen,
        "settings": SettingsScreen,
    }
    DEFAULT_MODE = "dashboard"

    BINDINGS = [
        ("1", "switch_mode('dashboard')", "Dashboard"),
        ("2", "switch_mode('projects')", "Projects"),
        ("3", "switch_mode('settings')", "Settings"),
    ]
```

---

## 6. Events and Messages

### 6.1 Handling Events

```python
from textual.message import Message

class TaskWidget(Static):
    """Custom task widget with events."""

    class Selected(Message):
        """Posted when task is selected."""
        def __init__(self, task_id: str) -> None:
            super().__init__()
            self.task_id = task_id

    class StatusChanged(Message):
        """Posted when task status changes."""
        def __init__(self, task_id: str, new_status: str) -> None:
            super().__init__()
            self.task_id = task_id
            self.new_status = new_status

    def on_click(self) -> None:
        self.post_message(self.Selected(self.task_id))

# In parent widget or app
def on_task_widget_selected(self, event: TaskWidget.Selected) -> None:
    """Handle task selection."""
    self.show_task_detail(event.task_id)

def on_task_widget_status_changed(self, event: TaskWidget.StatusChanged) -> None:
    """Handle status change."""
    self.update_database(event.task_id, event.new_status)
```

### 6.2 Using @on Decorator

```python
from textual.on import on

class TaskList(Widget):

    @on(Button.Pressed, "#new-task")
    def handle_new_task(self, event: Button.Pressed) -> None:
        """Handle new task button specifically."""
        self.create_new_task()

    @on(Button.Pressed, "#delete-task")
    def handle_delete(self, event: Button.Pressed) -> None:
        """Handle delete button specifically."""
        self.delete_selected_task()
```

---

## 7. Reactive Attributes

### 7.1 Basic Reactivity

```python
from textual.reactive import reactive

class TaskCard(Widget):
    """Task card with reactive properties."""

    title = reactive("Untitled")
    status = reactive("pending")
    priority = reactive("medium")

    def watch_status(self, old_status: str, new_status: str) -> None:
        """Called when status changes."""
        self.remove_class(f"status-{old_status}")
        self.add_class(f"status-{new_status}")

    def validate_priority(self, priority: str) -> str:
        """Validate priority value."""
        valid = ["low", "medium", "high"]
        return priority if priority in valid else "medium"

    def render(self) -> str:
        return f"[{self.status}] {self.title} ({self.priority})"
```

### 7.2 Computed Properties

```python
class ProjectStats(Widget):

    total_tasks = reactive(0)
    completed_tasks = reactive(0)

    def compute_progress_percent(self) -> float:
        """Computed from other reactives."""
        if self.total_tasks == 0:
            return 0.0
        return (self.completed_tasks / self.total_tasks) * 100
```

### 7.3 Data Binding

```python
# Parent can bind reactives to child widgets
class TaskView(Widget):
    task_title = reactive("")

    def compose(self) -> ComposeResult:
        yield TaskHeader().data_bind(title=TaskView.task_title)
```

---

## 8. Workers (Background Tasks)

### 8.1 Async Workers

```python
from textual.worker import Worker, work

class TaskList(Widget):

    @work(exclusive=True)
    async def load_tasks(self, project_id: str) -> None:
        """Load tasks in background."""
        self.loading = True
        try:
            tasks = await self.fetch_tasks(project_id)
            self.display_tasks(tasks)
        finally:
            self.loading = False

    async def fetch_tasks(self, project_id: str) -> list:
        """Async database call."""
        # Simulated async operation
        await asyncio.sleep(0.1)
        return db.get_tasks(project_id)
```

### 8.2 Thread Workers

```python
from textual.worker import work, get_current_worker

class DataImporter(Widget):

    @work(thread=True, exclusive=True)
    def import_data(self, file_path: str) -> None:
        """Run in thread (for sync APIs)."""
        worker = get_current_worker()

        with open(file_path) as f:
            for i, line in enumerate(f):
                if worker.is_cancelled:
                    return
                # Process line
                self.call_from_thread(self.update_progress, i)
```

---

## 9. Command Palette

### 9.1 System Commands

```python
from textual.command import SystemCommand

class TaskynApp(App):

    def get_system_commands(self, screen):
        yield from super().get_system_commands(screen)
        yield SystemCommand("New Task", "Create a new task", self.action_new_task)
        yield SystemCommand("New Project", "Create a new project", self.action_new_project)
        yield SystemCommand("Search", "Search tasks and projects", self.action_search)
```

### 9.2 Custom Command Provider

```python
from textual.command import Provider, Hit
from textual.types import IgnoreReturnCallbackType

class TaskSearchProvider(Provider):
    """Search tasks from command palette."""

    async def search(self, query: str) -> Hits:
        """Search tasks matching query."""
        matcher = self.matcher(query)

        tasks = await self.app.search_tasks(query)
        for task in tasks:
            score = matcher.match(task.title)
            if score > 0:
                yield Hit(
                    score,
                    matcher.highlight(task.title),
                    partial(self.app.open_task, task.id),
                    help=f"Open task: {task.title}"
                )

class TaskynApp(App):
    COMMANDS = App.COMMANDS | {TaskSearchProvider}
```

---

## 10. Integration with Typer CLI

### 10.1 Basic Integration

```python
# src/taskyn/cli/tui.py
import typer
from textual.app import App

from taskyn.tui.app import TaskynTUI

tui_app = typer.Typer()

@tui_app.command()
def launch(
    project: str = typer.Option(None, "--project", "-p", help="Open specific project"),
    dark: bool = typer.Option(True, "--dark/--light", help="Color mode"),
):
    """Launch the Taskyn TUI."""
    app = TaskynTUI(initial_project=project, dark_mode=dark)
    app.run()

@tui_app.command()
def dashboard():
    """Open the dashboard view."""
    app = TaskynTUI(initial_screen="dashboard")
    app.run()
```

### 10.2 Main CLI Integration

```python
# src/taskyn/cli/main.py
import typer
from taskyn.cli.tui import tui_app
from taskyn.cli.tasks import tasks_app

app = typer.Typer()
app.add_typer(tui_app, name="tui", help="Terminal UI commands")
app.add_typer(tasks_app, name="tasks", help="Task management")

@app.command()
def ui():
    """Quick shortcut to launch TUI."""
    from taskyn.tui.app import TaskynTUI
    TaskynTUI().run()
```

---

## 11. Testing Textual Apps

### 11.1 Basic Tests

```python
# tests/test_tui.py
import pytest
from taskyn.tui.app import TaskynTUI

@pytest.mark.asyncio
async def test_app_starts():
    """Test app can start and exit."""
    app = TaskynTUI()
    async with app.run_test() as pilot:
        assert app.title == "Taskyn"
        await pilot.press("q")

@pytest.mark.asyncio
async def test_new_task_form():
    """Test new task creation."""
    app = TaskynTUI()
    async with app.run_test() as pilot:
        await pilot.press("ctrl+n")  # Open new task form
        await pilot.press("T", "e", "s", "t")  # Type title
        await pilot.press("tab")  # Move to next field
        await pilot.press("enter")  # Submit
```

### 11.2 Snapshot Testing

```python
# tests/test_tui_snapshots.py
def test_dashboard_snapshot(snap_compare):
    """Visual regression test for dashboard."""
    assert snap_compare("src/taskyn/tui/app.py", terminal_size=(120, 40))

def test_task_form_snapshot(snap_compare):
    """Visual regression test for task form."""
    assert snap_compare(
        "src/taskyn/tui/app.py",
        press=["ctrl+n"],  # Open form first
        terminal_size=(80, 30)
    )
```

---

## 12. Recommended Project Structure

```
src/taskyn/
├── tui/
│   ├── __init__.py
│   ├── app.py              # Main TaskynTUI app class
│   ├── taskyn.tcss         # Main stylesheet
│   │
│   ├── screens/
│   │   ├── __init__.py
│   │   ├── dashboard.py    # Dashboard screen
│   │   ├── projects.py     # Projects list screen
│   │   ├── task_detail.py  # Task detail screen
│   │   └── settings.py     # Settings screen
│   │
│   ├── widgets/
│   │   ├── __init__.py
│   │   ├── task_tree.py    # Project/task hierarchy tree
│   │   ├── task_table.py   # Task list table
│   │   ├── task_card.py    # Task card widget
│   │   ├── task_form.py    # Task create/edit form
│   │   ├── timer.py        # Time tracking widget
│   │   ├── stats.py        # Statistics widgets
│   │   └── activity.py     # Activity log widget
│   │
│   ├── dialogs/
│   │   ├── __init__.py
│   │   ├── confirm.py      # Confirmation dialog
│   │   ├── task_quick.py   # Quick task creation
│   │   └── search.py       # Search dialog
│   │
│   └── commands/
│       ├── __init__.py
│       └── providers.py    # Command palette providers
│
├── cli/
│   ├── __init__.py
│   ├── main.py             # Main Typer app
│   └── tui.py              # TUI launch commands
│
└── core/
    └── ...                 # Existing business logic
```

---

## 13. Best Practices

### 13.1 Widget Design

1. **Keep widgets focused**: One widget, one responsibility
2. **Use composition**: Build complex UIs from simple widgets
3. **Prefer CSS over Python**: Use CSS for layout and styling
4. **Use reactive attributes**: For data-driven updates
5. **Define custom messages**: For widget-to-parent communication

### 13.2 Performance

1. **Use workers**: For I/O and heavy computation
2. **Batch updates**: Avoid rapid successive refreshes
3. **Lazy loading**: Load data as needed, not all at once
4. **Use `refresh(layout=False)`**: When only content changes

### 13.3 Code Organization

1. **Separate screens**: Each major view in its own file
2. **Reusable widgets**: Extract common patterns
3. **CSS files**: Keep styles in `.tcss` files
4. **Type hints**: Use throughout for better IDE support

### 13.4 User Experience

1. **Keyboard first**: Comprehensive key bindings
2. **Visual feedback**: Loading indicators, status messages
3. **Consistent navigation**: Standard keys work everywhere
4. **Help accessibility**: Footer shows available actions
5. **Command palette**: Quick access to all features

---

## 14. Taskyn-Specific Recommendations

### 14.1 Dashboard View

```
+----------------------------------+
| Taskyn - Dashboard    [12:30 PM] |
+----------------------------------+
| Projects  | Active Tasks         |
| +--------+| [ ] Design TUI       |
| | Taskyn || [ ] Implement Tree   |
| |  v1.0  || [x] Research Textual |
| | Sprint || -------------------- |
| +--------+| Stats: 15/20 (75%)   |
|           | [================  ] |
+-----------+----------------------+
| Activity Log                     |
| 12:25 Created task "Design TUI"  |
| 12:20 Completed "Research"       |
+----------------------------------+
| q Quit | n New Task | / Search   |
+----------------------------------+
```

### 14.2 Recommended Widgets by Feature

| Feature | Widget(s) |
|---------|-----------|
| Project hierarchy | Tree |
| Task lists | DataTable or ListView |
| Task details | Custom widget with Static, Label |
| Forms | Input, TextArea, Select, Button |
| Progress | ProgressBar, Sparkline |
| Timer | Digits (custom TimerDisplay) |
| Activity | RichLog |
| Navigation | TabbedContent, Screens |
| Modals | ModalScreen |
| Search | Command Palette + custom provider |

### 14.3 Key Features to Implement

1. **Dashboard Screen**: Overview with stats, recent activity
2. **Project Tree**: Hierarchical view with companies/projects/milestones/tasks
3. **Task Table**: Sortable, filterable task list
4. **Task Form**: Create/edit with validation
5. **Timer Widget**: Start/stop/pause time tracking
6. **Activity Feed**: Real-time updates
7. **Search**: Command palette integration
8. **Quick Actions**: Keyboard-driven workflow

---

## Sources

- [Textual Official Documentation](https://textual.textualize.io/)
- [Textual Tutorial](https://textual.textualize.io/tutorial/)
- [Textual GitHub Repository](https://github.com/Textualize/textual)
- [Real Python - Python Textual: Build Beautiful UIs in the Terminal](https://realpython.com/python-textual/)
- [ArjanCodes - Guide to Building Interactive Terminal Apps with Textual](https://arjancodes.com/blog/textual-python-library-for-creating-interactive-terminal-applications/)
