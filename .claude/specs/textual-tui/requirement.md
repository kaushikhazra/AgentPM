# Taskyn TUI - Requirements

**Feature:** Terminal User Interface for Taskyn
**Date:** 2026-02-01
**Methodology:** Spec-Driven Development

---

## User Stories

### Epic: TUI Foundation

**US-001: Launch TUI Application**
As a user, I want to launch the Taskyn TUI from the command line so that I can manage my projects in a rich terminal interface.

Acceptance Criteria:
- `taskyn ui` or `taskyn tui launch` starts the TUI
- Application displays a header with title and time
- Application displays a footer with available keyboard shortcuts
- Application can be quit with `q` key
- Supports `--dark` / `--light` theme flags

---

**US-002: View Dashboard**
As a user, I want to see a dashboard overview when I launch the TUI so that I can quickly understand my project status.

Acceptance Criteria:
- Dashboard shows project tree in left sidebar
- Dashboard shows task list in main area
- Dashboard shows progress statistics
- Dashboard shows active timer (if running)
- Dashboard shows recent activity feed

---

### Epic: Project Navigation

**US-003: Browse Project Hierarchy**
As a user, I want to navigate through my companies, projects, milestones, and tasks in a tree view so that I can find items quickly.

Acceptance Criteria:
- Tree shows hierarchical structure: Company > Project > Milestone > Story/Task
- Nodes can be expanded/collapsed with arrow keys or Enter
- Selected node highlights
- Tree updates when items are added/removed
- Icons differentiate node types

---

**US-004: Filter Project Tree**
As a user, I want to filter the project tree so that I can focus on specific projects or items.

Acceptance Criteria:
- Filter input at top of tree sidebar
- Tree filters as user types
- Clear filter with Escape or clear button
- Empty state shown when no matches

---

### Epic: Task Management

**US-005: View Task List**
As a user, I want to see my tasks in a sortable, filterable table so that I can manage my work efficiently.

Acceptance Criteria:
- Table shows: Status, Title, Priority, Due Date
- Rows are selectable with keyboard/mouse
- Columns are sortable by clicking header
- Zebra stripes for readability
- Status shown with icons/colors

---

**US-006: View Task Details**
As a user, I want to see full task details in a detail view so that I can understand the complete context.

Acceptance Criteria:
- Shows title, status, priority, due date
- Shows description with markdown rendering
- Shows subtasks with completion status
- Shows tags
- Shows time entries
- Shows parent story/project breadcrumb

---

**US-007: Create New Task**
As a user, I want to create new tasks via a modal form so that I can add work items quickly.

Acceptance Criteria:
- Modal opens with `Ctrl+N` or `n` key
- Form fields: Title, Project, Type, Priority, Status, Description, Due Date, Estimate
- Tab navigates between fields
- Enter submits (when on button), Escape cancels
- Validation feedback shown inline
- Form pre-selects current project context

---

**US-008: Edit Task**
As a user, I want to edit existing tasks so that I can update information as work progresses.

Acceptance Criteria:
- Edit with `e` key from task detail/list
- Same form as create, pre-populated
- Shows what changed before saving
- Cancel returns to previous view

---

**US-009: Change Task Status**
As a user, I want to quickly change task status so that I can update progress efficiently.

Acceptance Criteria:
- `s` key opens status picker
- Shows valid status transitions only
- Updates immediately on selection
- Activity log records change

---

**US-010: Delete Task**
As a user, I want to delete tasks I no longer need so that I can keep my workspace clean.

Acceptance Criteria:
- `d` key initiates delete
- Confirmation dialog shown
- `y` confirms, `n`/Escape cancels
- Soft delete (can be recovered via CLI)

---

### Epic: Time Tracking

**US-011: Start/Stop Timer**
As a user, I want to start and stop time tracking from the TUI so that I can log my work time.

Acceptance Criteria:
- `t` key toggles timer on selected task
- Active timer shown in dashboard panel
- Timer shows elapsed time (HH:MM:SS)
- Pause/Resume with Space in focus mode
- Stop saves time entry

---

**US-012: Focus Timer Mode**
As a user, I want a distraction-free timer view so that I can focus on my current task.

Acceptance Criteria:
- Large digit display for elapsed time
- Shows current task name
- Shows today's total logged time
- Minimal UI, maximum focus
- Escape returns to dashboard

---

### Epic: Search & Navigation

**US-013: Command Palette Search**
As a user, I want to search tasks and commands from a command palette so that I can navigate quickly.

Acceptance Criteria:
- `/` or `Ctrl+P` opens command palette
- Search tasks by title
- Search commands by name
- Results show type (task/command) and context
- Arrow keys navigate, Enter selects
- Recent searches remembered

---

**US-014: Global Keyboard Navigation**
As a user, I want comprehensive keyboard shortcuts so that I can work efficiently without a mouse.

Acceptance Criteria:
- `?` shows help with all shortcuts
- Vim-style navigation (h/j/k/l) supported
- Number keys (1-4) switch tabs
- All actions accessible via keyboard
- Shortcuts shown in footer

---

### Epic: Views & Screens

**US-015: Kanban Board View**
As a user, I want to see my sprint tasks in a kanban board so that I can visualize workflow.

Acceptance Criteria:
- Columns: Backlog, Todo, In Progress, Done
- Tasks shown as cards in columns
- Arrow keys move between columns
- Cards show title, priority, due date
- Progress bar at bottom

---

**US-016: Settings Screen**
As a user, I want to configure TUI settings so that I can customize my experience.

Acceptance Criteria:
- Theme selection (Dark/Light/System)
- Default methodology
- Default view
- Database info display
- Backup/Export actions

---

### Epic: Polish & UX

**US-017: Responsive Layout**
As a user, I want the TUI to adapt to my terminal size so that it works on different displays.

Acceptance Criteria:
- Minimum 80x24 supported
- Sidebar hides on narrow terminals
- Panels resize proportionally
- Text truncates gracefully

---

**US-018: Loading States**
As a user, I want visual feedback during loading so that I know the app is working.

Acceptance Criteria:
- Spinner shown during data loads
- Skeleton placeholders for lists
- Loading text in status bar
- No frozen/unresponsive states

---

**US-019: Error Handling**
As a user, I want clear error messages so that I can understand and resolve issues.

Acceptance Criteria:
- Errors shown in notification area
- Validation errors shown inline
- Database errors handled gracefully
- Option to retry failed operations

---

## Non-Functional Requirements

**NFR-001: Performance**
- TUI should start in under 1 second
- Navigation should feel instant (<100ms)
- No blocking operations on main thread

**NFR-002: Compatibility**
- Support Windows Terminal, iTerm2, standard Linux terminals
- Support 256-color and true-color terminals
- Graceful degradation for limited terminals

**NFR-003: Accessibility**
- Keyboard-only navigation
- Screen reader compatible where possible
- High contrast theme option

**NFR-004: Testing**
- Unit tests for all widgets
- Integration tests for screens
- Snapshot tests for visual regression
