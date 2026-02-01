# Taskyn TUI - Tasks

**Feature:** Terminal User Interface for Taskyn
**Date:** 2026-02-01

---

## Phase 1: Foundation & Core TUI

### Setup & Infrastructure

- [ ] Add Textual dependency to pyproject.toml
  - Add `textual>=0.50.0` to dependencies
  - Add `textual-dev>=1.0.0` to dev dependencies
  _US-001: Launch TUI Application_

- [ ] Create TUI module structure
  - Create `src/taskyn/tui/` directory
  - Create `__init__.py`, `app.py`
  - Create `screens/`, `widgets/`, `dialogs/`, `commands/` subdirectories
  _US-001: Launch TUI Application_

- [ ] Implement CLI integration
  - Create `src/taskyn/cli/tui.py` with launch command
  - Add `tui` subcommand to main CLI
  - Support `--dark`/`--light` flags
  _US-001: Launch TUI Application_

### Main Application

- [ ] Create base TaskynTUI app class
  - Implement `compose()` with Header and Footer
  - Define global key bindings (q, Ctrl+N, /, ?)
  - Setup theme switching
  _US-001: Launch TUI Application_

- [ ] Create global stylesheet (taskyn.tcss)
  - Define color variables for themes
  - Define status color classes
  - Define priority color classes
  - Setup responsive breakpoints
  _US-001: Launch TUI Application_

### Dashboard Screen

- [ ] Create DashboardScreen class
  - Implement grid layout (sidebar + main)
  - Add Header and Footer
  - Wire up navigation bindings
  _US-002: View Dashboard_

- [ ] Implement dashboard layout with CSS
  - Sidebar: 25 columns fixed
  - Main: flexible width
  - Stats/Timer panel: auto height
  - Activity log: remaining space
  _US-002: View Dashboard_

### Project Tree Widget

- [ ] Create ProjectTree widget
  - Extend Textual Tree widget
  - Load hierarchy from database
  - Custom node icons per type
  _US-003: Browse Project Hierarchy_

- [ ] Implement tree data loading
  - Fetch companies, projects, milestones, tasks
  - Build hierarchical structure
  - Handle empty states
  _US-003: Browse Project Hierarchy_

- [ ] Add tree node selection handling
  - Emit NodeSelected message
  - Update task list based on selection
  - Show breadcrumb navigation
  _US-003: Browse Project Hierarchy_

- [ ] Implement tree filtering
  - Add filter input at top
  - Filter nodes as user types
  - Show/hide matching branches
  _US-004: Filter Project Tree_

### Task Table Widget

- [ ] Create TaskTable widget
  - Extend DataTable
  - Define columns: Status, Title, Priority, Due
  - Enable row cursor mode
  _US-005: View Task List_

- [ ] Implement task data loading
  - Fetch tasks from database
  - Format status/priority icons
  - Format due dates (relative)
  _US-005: View Task List_

- [ ] Add table sorting
  - Click column header to sort
  - Toggle ascending/descending
  - Visual sort indicator
  _US-005: View Task List_

- [ ] Add row selection handling
  - Enter key opens task detail
  - Space key toggles status
  - Emit TaskSelected message
  _US-005: View Task List_

### Task Detail Screen

- [ ] Create TaskDetailScreen class
  - Accept task_id parameter
  - Load task data on mount
  - Display all task fields
  _US-006: View Task Details_

- [ ] Implement detail layout
  - Title and status header
  - Description with markdown
  - Metadata (priority, due, estimate)
  - Tags display
  _US-006: View Task Details_

- [ ] Add subtask display
  - List subtasks with checkboxes
  - Show completion count
  - Allow toggling completion
  _US-006: View Task Details_

- [ ] Add time entries display
  - List time entries
  - Show date, duration, notes
  - Total logged time
  _US-006: View Task Details_

---

## Phase 2: Task Management

### Task Form Widget

- [ ] Create TaskForm widget
  - Title input with validation
  - Project selector dropdown
  - Type selector (Task/Story)
  - Priority selector
  _US-007: Create New Task_

- [ ] Add remaining form fields
  - Status selector (per methodology)
  - Description textarea
  - Due date input with validation
  - Estimate input with validation
  _US-007: Create New Task_

- [ ] Implement form validation
  - Required field validation
  - Date format validation
  - Duration format validation
  - Inline error display
  _US-007: Create New Task_

- [ ] Implement form submission
  - Collect form data
  - Call core API to create task
  - Show success notification
  - Close modal and refresh list
  _US-007: Create New Task_

### Task Edit Modal

- [ ] Create EditTaskModal
  - Reuse TaskForm widget
  - Pre-populate with task data
  - Track changed fields
  _US-008: Edit Task_

- [ ] Implement update logic
  - Call core API to update task
  - Handle partial updates
  - Refresh UI after save
  _US-008: Edit Task_

### Status Picker Dialog

- [ ] Create StatusPickerDialog
  - Show valid transitions only
  - Respect methodology rules
  - Highlight current status
  _US-009: Change Task Status_

- [ ] Implement status change
  - Call workflow API
  - Update activity log
  - Refresh task display
  _US-009: Change Task Status_

### Delete Confirmation

- [ ] Create ConfirmDialog widget
  - Generic confirmation dialog
  - Warning icon for destructive
  - Yes/No buttons
  - Keyboard shortcuts (y/n)
  _US-010: Delete Task_

- [ ] Implement delete flow
  - Show confirmation
  - Call core API on confirm
  - Remove from list
  - Show undo option (timed)
  _US-010: Delete Task_

---

## Phase 3: Time Tracking

### Timer Display Widget

- [ ] Create TimerDisplay widget
  - Large digit display (Digits)
  - Elapsed time counter
  - Task name label
  - Control buttons
  _US-011: Start/Stop Timer_

- [ ] Implement timer state machine
  - Idle → Running → Paused → Stopped
  - Persist state across screens
  - Auto-save on app quit
  _US-011: Start/Stop Timer_

- [ ] Integrate with core timer API
  - Start timer with task_id
  - Stop and save time entry
  - Handle existing running timer
  _US-011: Start/Stop Timer_

### Focus Timer Screen

- [ ] Create FocusTimerScreen
  - Full screen timer display
  - Minimal distractions
  - Today's total time
  _US-012: Focus Timer Mode_

- [ ] Add focus mode controls
  - Space to pause/resume
  - S to stop and save
  - Escape to return to dashboard
  _US-012: Focus Timer Mode_

---

## Phase 4: Search & Navigation

### Command Palette

- [ ] Create TaskSearchProvider
  - Search tasks by title
  - Show project context in results
  - Navigate to task on select
  _US-013: Command Palette Search_

- [ ] Create CommandProvider
  - Register system commands
  - Show keyboard shortcuts
  - Execute actions on select
  _US-013: Command Palette Search_

- [ ] Integrate command palette
  - Open with / or Ctrl+P
  - Close with Escape
  - Navigate with arrows
  _US-013: Command Palette Search_

### Keyboard Navigation

- [ ] Implement vim-style navigation
  - h/j/k/l for movement
  - Enter to select/open
  - Escape to go back
  _US-014: Global Keyboard Navigation_

- [ ] Create help screen/overlay
  - Show all key bindings
  - Group by context
  - Open with ? key
  _US-014: Global Keyboard Navigation_

---

## Phase 5: Additional Views

### Kanban Board View

- [ ] Create KanbanBoard widget
  - Columns per status
  - Task cards in columns
  - Horizontal scrolling
  _US-015: Kanban Board View_

- [ ] Implement drag-and-drop (keyboard)
  - Arrow keys move between columns
  - Enter to "drop" in column
  - Update status on move
  _US-015: Kanban Board View_

### Settings Screen

- [ ] Create SettingsScreen
  - Theme selector
  - Default methodology
  - Default view
  _US-016: Settings Screen_

- [ ] Add database info panel
  - Show database path
  - Show database size
  - Backup/Export buttons
  _US-016: Settings Screen_

---

## Phase 6: Polish & UX

### Responsive Layout

- [ ] Implement responsive breakpoints
  - <100 cols: hide sidebar
  - <120 cols: compact stats
  - Full layout at 120+ cols
  _US-017: Responsive Layout_

- [ ] Add graceful text truncation
  - Ellipsis for long titles
  - Tooltip on hover (if supported)
  _US-017: Responsive Layout_

### Loading States

- [ ] Add loading indicators
  - Spinner for data loads
  - Skeleton placeholders
  - Loading text in footer
  _US-018: Loading States_

- [ ] Implement worker-based loading
  - Background data fetching
  - Non-blocking UI updates
  _US-018: Loading States_

### Error Handling

- [ ] Create notification system
  - Success/error/warning types
  - Auto-dismiss timer
  - Stack multiple notifications
  _US-019: Error Handling_

- [ ] Implement error boundaries
  - Catch widget errors
  - Show error message
  - Offer retry option
  _US-019: Error Handling_

---

## Phase 7: Testing

### Unit Tests

- [ ] Test ProjectTree widget
  - Node rendering
  - Selection handling
  - Filtering
  _NFR-004: Testing_

- [ ] Test TaskTable widget
  - Data loading
  - Sorting
  - Selection
  _NFR-004: Testing_

- [ ] Test TaskForm widget
  - Validation
  - Submission
  - Error display
  _NFR-004: Testing_

- [ ] Test TimerDisplay widget
  - State transitions
  - Time formatting
  - Integration with core
  _NFR-004: Testing_

### Integration Tests

- [ ] Test full task creation flow
  - Open form → fill → submit → verify in list
  _NFR-004: Testing_

- [ ] Test task editing flow
  - Select → edit → save → verify changes
  _NFR-004: Testing_

- [ ] Test timer flow
  - Start → pause → resume → stop → verify time entry
  _NFR-004: Testing_

### Snapshot Tests

- [ ] Create dashboard snapshot tests
  - Empty state
  - With data
  - Different themes
  _NFR-004: Testing_

- [ ] Create form snapshot tests
  - Empty form
  - Filled form
  - Validation errors
  _NFR-004: Testing_

---

## Completed Tasks

_(Move completed tasks here with [x] marker)_
