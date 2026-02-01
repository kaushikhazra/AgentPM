# TUI Full CLI Feature Parity - Tasks

## Phase 1: Entity Management Foundation

### Company Management
- [x] Create `dialogs/company_form.py` with name/description fields
  _US-1.1: Company Management_
- [x] Create `screens/company_detail.py` showing projects list
  _US-1.1: Company Management_
- [x] Add `action_new_company` to app.py with Ctrl+Shift+C binding
  _US-1.1: Company Management_
- [x] Add company edit/delete actions to company detail screen
  _US-1.1: Company Management_

### Project Management
- [x] Create `dialogs/project_form.py` with company selector, methodology
  _US-1.2: Project Management_
- [x] Create `screens/project_detail.py` showing milestones and stats
  _US-1.2: Project Management_
- [x] Add `action_new_project` to app.py with Ctrl+Shift+P binding
  _US-1.2: Project Management_
- [x] Add project edit/delete actions to project detail screen
  _US-1.2: Project Management_

### Milestone Management
- [x] Create `dialogs/milestone_form.py` with project selector, target date
  _US-1.3: Milestone Management_
- [x] Create `screens/milestone_detail.py` showing progress and tasks
  _US-1.3: Milestone Management_
- [x] Add `action_new_milestone` to app.py with Ctrl+Shift+M binding
  _US-1.3: Milestone Management_
- [x] Add milestone edit/delete/complete actions to milestone detail screen
  _US-1.3: Milestone Management_

### Integration
- [x] Update `widgets/project_tree.py` to load companies/projects/milestones
  _US-1.1, US-1.2, US-1.3_
- [x] Add entity navigation in app.py (handle NodeSelected for all types)
  _US-1.1, US-1.2, US-1.3_
- [x] Add command palette commands for new entities in providers.py
  _US-1.1, US-1.2, US-1.3_

## Phase 2: Story & Node Enhancements

### Story Creation
- [x] Create `dialogs/story_form.py` with points, acceptance criteria
  _US-2.1: Story Creation_
- [x] Add `action_new_story` to app.py with Ctrl+Shift+S binding
  _US-2.1: Story Creation_
- [x] Update task_form.py to handle story-specific fields conditionally
  _US-2.1: Story Creation_

### Enhanced Task Details
- [x] Create `widgets/edge_list.py` displaying parent/child/dependency edges
  _US-2.2: Enhanced Task Details_
- [x] Create `widgets/time_entry_table.py` listing time entries with totals
  _US-2.2: Enhanced Task Details_
- [x] Update `screens/task_detail.py` to include edges, time entries, tags
  _US-2.2: Enhanced Task Details_

## Phase 3: Tag Management

### Tag CRUD
- [x] Create `dialogs/tag_form.py` for creating tags with color
  _US-3.1: Tag CRUD_
- [x] Update `screens/settings.py` to add Tags section with list and create
  _US-3.1: Tag CRUD_
- [x] Add tag delete functionality in settings
  _US-3.1: Tag CRUD_

### Tag Assignment
- [x] Create `dialogs/tag_picker.py` for multi-select tag assignment
  _US-3.2: Tag Assignment_
- [x] Create `widgets/tag_list.py` displaying tags with remove buttons
  _US-3.2: Tag Assignment_
- [x] Add tag management action (key: g) to task detail screen
  _US-3.2: Tag Assignment_

## Phase 4: Search & Activity Screens

### Full Search
- [x] Create `screens/search.py` with type/status/project filters
  _US-4.1: Full Search_
- [x] Add key 4 binding and Ctrl+F for search screen
  _US-4.1: Full Search_
- [x] Add search navigation commands to providers.py
  _US-4.1: Full Search_

### Activity History
- [x] Create `screens/activity.py` with filters and pagination
  _US-4.2: Activity History_
- [x] Add key 5 binding for activity screen
  _US-4.2: Activity History_

## Phase 5: Statistics Dashboard

### Project Statistics
- [x] Create `widgets/progress_chart.py` for ASCII progress bars
  _US-5.1: Project Statistics_
- [x] Create `screens/statistics.py` with project selector and full stats
  _US-5.1: Project Statistics_
- [x] Add key 6 binding for statistics screen
  _US-5.1: Project Statistics_

## Phase 6: Backup & Export Enhancements

### Backup Management
- [x] Create `dialogs/backup_restore.py` listing backups with restore
  _US-6.1: Backup Management_
- [x] Update `screens/settings.py` to use enhanced backup dialog
  _US-6.1: Backup Management_

### Export Options
- [x] Export JSON functionality already exists in settings.py
  _US-6.2: Export Options_
