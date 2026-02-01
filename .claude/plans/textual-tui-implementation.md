# Taskyn TUI Implementation Plan

**Feature:** Terminal User Interface using Textual
**Created:** 2026-02-01

---

## Overview

Build a rich Terminal User Interface for Taskyn using the Textual library. This will provide a full-featured, keyboard-driven interface for managing projects, tasks, and time tracking directly in the terminal.

---

## Phase Summary

| Phase | Focus | Key Deliverables |
|-------|-------|------------------|
| 1 | Foundation | App skeleton, Dashboard, Tree, Table |
| 2 | Task Management | Create/Edit/Delete tasks, Status changes |
| 3 | Time Tracking | Timer widget, Focus mode |
| 4 | Search | Command palette, Keyboard navigation |
| 5 | Views | Kanban board, Settings screen |
| 6 | Polish | Responsive layout, Loading states, Errors |
| 7 | Testing | Unit, Integration, Snapshot tests |

---

## Implementation Order

### Phase 1: Foundation (Start Here)

**Goal:** Working dashboard with project tree and task list

1. **Setup (First)**
   - Add Textual to pyproject.toml
   - Create directory structure
   - Add `taskyn ui` CLI command

2. **Main App**
   - Create `TaskynTUI` class
   - Create `taskyn.tcss` stylesheet
   - Header/Footer with bindings

3. **Dashboard Screen**
   - Grid layout (sidebar + main)
   - Placeholder widgets

4. **Project Tree**
   - Load hierarchy from DB
   - Node selection → update task list
   - Custom icons per node type

5. **Task Table**
   - Load tasks from DB
   - Column sorting
   - Row selection → detail view

6. **Task Detail Screen**
   - Display all task fields
   - Description rendering
   - Back navigation

**Milestone:** User can launch TUI, browse projects, view task details

---

### Phase 2: Task Management

**Goal:** Full CRUD for tasks

1. **Task Form Widget**
   - All input fields
   - Validation
   - Project/Type/Priority/Status selectors

2. **Create Task Modal**
   - Open with Ctrl+N
   - Submit creates task
   - Refresh list on success

3. **Edit Task Modal**
   - Pre-populate form
   - Update on save

4. **Status Picker**
   - Show valid transitions
   - Quick status change

5. **Delete with Confirmation**
   - Confirmation dialog
   - Delete on confirm

**Milestone:** User can create, edit, change status, and delete tasks

---

### Phase 3: Time Tracking

**Goal:** Timer integration in TUI

1. **Timer Display Widget**
   - Digits display
   - Task name
   - Control buttons

2. **Timer State Management**
   - Start/Pause/Stop states
   - Persist across screens

3. **Core Integration**
   - Call time_entry APIs
   - Handle existing timers

4. **Focus Timer Screen**
   - Full screen timer
   - Minimal distractions

**Milestone:** User can start/stop timers from TUI

---

### Phase 4: Search & Navigation

**Goal:** Fast navigation via command palette

1. **Task Search Provider**
   - Search by title
   - Show results with context

2. **Command Provider**
   - System commands
   - Show shortcuts

3. **Keyboard Navigation**
   - Vim bindings
   - Help overlay

**Milestone:** User can search and navigate entirely via keyboard

---

### Phase 5: Additional Views

**Goal:** Enhanced visualization options

1. **Kanban Board**
   - Column per status
   - Keyboard "drag-drop"

2. **Settings Screen**
   - Theme selection
   - Database info

**Milestone:** User has multiple ways to visualize work

---

### Phase 6: Polish

**Goal:** Production-ready UX

1. **Responsive Layout**
   - Handle small terminals
   - Graceful degradation

2. **Loading States**
   - Spinners
   - Skeletons

3. **Error Handling**
   - Notifications
   - Retry options

**Milestone:** Polished, production-ready TUI

---

### Phase 7: Testing

**Goal:** Comprehensive test coverage

1. **Unit Tests**
   - Widget tests
   - Mock database

2. **Integration Tests**
   - Full user flows

3. **Snapshot Tests**
   - Visual regression

**Milestone:** High confidence in code quality

---

## Git Flow

```
develop
└── feature/textual-tui          # Main feature branch
    ├── feature/tui-foundation   # Phase 1
    ├── feature/tui-crud         # Phase 2
    ├── feature/tui-timer        # Phase 3
    ├── feature/tui-search       # Phase 4
    ├── feature/tui-views        # Phase 5
    ├── feature/tui-polish       # Phase 6
    └── feature/tui-tests        # Phase 7
```

---

## Technical Decisions

1. **Async vs Sync:** Use Textual's workers for database operations to keep UI responsive

2. **State Management:** Store app-level state (current project, active timer) as reactive attributes on `TaskynTUI` class

3. **Data Loading:** Each widget loads its own data via core APIs; no centralized store

4. **CSS Strategy:** Single `taskyn.tcss` file with component-specific selectors; dynamic classes for states

5. **Testing:** Use `app.run_test()` with Pilot for all tests; snapshot tests for visual regression

---

## Dependencies

```toml
# pyproject.toml additions
[project.optional-dependencies]
tui = [
    "textual>=0.50.0",
]

[project.optional-dependencies]
dev = [
    # ... existing
    "textual-dev>=1.0.0",
]
```

---

## Success Criteria

1. **Functional:** All user stories implemented and working
2. **Performance:** TUI starts in <1s, navigation feels instant
3. **Usability:** Keyboard-only navigation is smooth
4. **Quality:** Tests pass, no visual regressions
5. **Documentation:** Key bindings documented, help accessible

---

## Related Documents

- Research: `.claude/research/textual-tui-research.md`
- Mockups: `.claude/research/textual-tui-mockups.md`
- Requirements: `.claude/specs/textual-tui/requirement.md`
- Design: `.claude/specs/textual-tui/design.md`
- Tasks: `.claude/specs/textual-tui/task.md`
