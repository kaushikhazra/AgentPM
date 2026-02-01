# TUI Full CLI Feature Parity - Design

## Navigation Architecture

```
Dashboard (Key: 1) - Main screen
├── ProjectTree (sidebar) - Click to open detail screens
│   ├── Companies → CompanyDetailScreen
│   ├── Projects → ProjectDetailScreen
│   ├── Milestones → MilestoneDetailScreen
│   └── Tasks/Stories → TaskDetailScreen
├── TaskTable (main area)
└── Stats/Timer/Activity (bottom panels)

Kanban (Key: 2) - Existing
Settings (Key: 3) - Enhanced with Tags management
Search (Key: 4) - NEW full search screen
Activity (Key: 5) - NEW full activity history
Statistics (Key: 6) - NEW project stats dashboard
```

## Component Design

### Form Dialogs

All form dialogs follow the existing pattern:
- Inherit from `ModalScreen[bool]`
- Use `Vertical` container with centered alignment
- Include form fields with validation
- Post result via `dismiss(True/False)`
- Handle Escape for cancellation

**Form Field Pattern:**
```python
with Vertical(classes="form-row"):
    yield Label("Field Name")
    yield Input(id="field-name", placeholder="Enter value")
```

### Detail Screens

All detail screens follow this pattern:
- Inherit from `Screen`
- Show entity information in header
- List related entities (children)
- Provide context actions via keybindings
- Support Edit/Delete/New Child operations

**Layout:**
```
┌─────────────────────────────────────┐
│ Entity Name                    [Edit]│
├─────────────────────────────────────┤
│ Description text here...            │
│                                     │
│ ─── Children ───                    │
│ • Child 1                           │
│ • Child 2                           │
│                                     │
│ ─── Stats ───                       │
│ Created: 2024-01-01                 │
│ Items: 5                            │
└─────────────────────────────────────┘
```

### Widget Design

**EdgeList Widget:**
- Displays edges grouped by type (parent, blocks, depends_on)
- Shows node title with clickable navigation
- Supports add/remove operations

**TimeEntryTable Widget:**
- DataTable showing time entries
- Columns: Date, Duration, Notes
- Footer with total time

**TagList Widget:**
- Horizontal flow of tag chips
- Each tag has remove button (x)
- Add button at end

**ProgressChart Widget:**
- ASCII progress bars using Unicode blocks
- Shows percentage and counts
- Color-coded by status

## Keybinding System

### Global Bindings (app.py)
| Key | Action | Priority |
|-----|--------|----------|
| `1-6` | Screen navigation | High |
| `Ctrl+N` | New Task | High |
| `Ctrl+Shift+C` | New Company | Medium |
| `Ctrl+Shift+P` | New Project | Medium |
| `Ctrl+Shift+M` | New Milestone | Medium |
| `Ctrl+Shift+S` | New Story | Medium |
| `Ctrl+F` | Full Search | Medium |
| `/` | Command Palette | High |
| `?` | Help | High |
| `q` | Quit | High |

### Context Bindings (Detail Screens)
| Key | Action |
|-----|--------|
| `e` | Edit entity |
| `d` | Delete entity |
| `n` | New child |
| `s` | Change status |
| `t` | Toggle timer |
| `g` | Manage tags |
| `c` | Complete (milestones) |
| `Escape` | Back |

## Data Flow

### Create Entity Flow
```
User presses Ctrl+Shift+P (New Project)
  → TaskynTUI.action_new_project()
  → push_screen(ProjectFormDialog)
    → User fills form, submits
    → ProjectFormDialog creates project via core API
    → notify("Project created")
    → dismiss(True)
  → on_dismiss callback
    → _refresh_dashboard()
```

### Detail Screen Navigation
```
User clicks node in ProjectTree
  → ProjectTree posts NodeSelected message
  → TaskynTUI.on_project_tree_node_selected()
    → Determine node type
    → push_screen(appropriate DetailScreen)
```

## Command Palette Extensions

New commands to add in providers.py:

**Entity Commands:**
- "New Company" → `app.action_new_company()`
- "New Project" → `app.action_new_project()`
- "New Milestone" → `app.action_new_milestone()`
- "New Story" → `app.action_new_story()`

**Navigation Commands:**
- "Go to Search" → `app.action_view_search()`
- "Go to Activity" → `app.action_view_activity()`
- "Go to Statistics" → `app.action_view_statistics()`

**Data Commands:**
- "Create Backup" → `app.action_create_backup()`
- "Export JSON" → `app.action_export_data()`
- "Restore Backup" → `app.action_restore_backup()`

**Tag Commands:**
- "Create Tag" → `app.action_create_tag()`
- "Manage Tags" → navigates to Settings → Tags

## CSS Styling

Follow existing patterns in taskyn.tcss:
- Use CSS variables for colors
- Scope styles to widgets via class names
- Use `.form-row` for consistent form layouts
- Use `.detail-header`, `.detail-content` for screens

## Error Handling

- Show notifications via `self.notify()` for success/error
- Use `ConfirmDialog` for destructive operations
- Validate inputs before API calls
- Handle NotFoundError gracefully (show message, navigate back)

## File Organization

```
src/taskyn/tui/
├── dialogs/
│   ├── company_form.py
│   ├── project_form.py
│   ├── milestone_form.py
│   ├── story_form.py
│   ├── tag_form.py
│   ├── tag_picker.py
│   └── backup_restore.py
├── screens/
│   ├── company_detail.py
│   ├── project_detail.py
│   ├── milestone_detail.py
│   ├── search.py
│   ├── activity.py
│   └── statistics.py
└── widgets/
    ├── edge_list.py
    ├── time_entry_table.py
    ├── tag_list.py
    ├── search_input.py
    └── progress_chart.py
```
