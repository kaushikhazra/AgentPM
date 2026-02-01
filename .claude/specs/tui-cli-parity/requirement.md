# TUI Full CLI Feature Parity - Requirements

## Overview
As a Taskyn user, I want all CLI capabilities available in the TUI so I never need to leave the terminal interface for any operation.

---

## User Stories

### Phase 1: Entity Management Foundation

**US-1.1: Company Management**
- As a user, I want to create companies from the TUI so I can organize my projects by client/organization.
- As a user, I want to view company details showing all associated projects.
- As a user, I want to edit company name and description.
- As a user, I want to delete companies (with confirmation).

**US-1.2: Project Management**
- As a user, I want to create projects under a company with methodology selection.
- As a user, I want to view project details showing milestones and quick stats.
- As a user, I want to edit project name, description, and status.
- As a user, I want to delete projects (with confirmation).

**US-1.3: Milestone Management**
- As a user, I want to create milestones under a project with target dates.
- As a user, I want to view milestone details with progress and tasks.
- As a user, I want to edit milestone name, description, and target date.
- As a user, I want to complete milestones.
- As a user, I want to delete milestones (with confirmation).

### Phase 2: Story & Node Enhancements

**US-2.1: Story Creation**
- As a user, I want to create stories with points and acceptance criteria.
- As a user, I want to associate stories with milestones.

**US-2.2: Enhanced Task Details**
- As a user, I want to see parent/child/dependency edges on task details.
- As a user, I want to see time entries with totals on task details.
- As a user, I want to see tags on task details.

### Phase 3: Tag Management

**US-3.1: Tag CRUD**
- As a user, I want to create tags with custom colors.
- As a user, I want to view all tags in settings.
- As a user, I want to delete tags.

**US-3.2: Tag Assignment**
- As a user, I want to add/remove tags from tasks and stories.
- As a user, I want to see tags displayed on task cards and details.

### Phase 4: Search & Activity Screens

**US-4.1: Full Search**
- As a user, I want a dedicated search screen with filters (type, status, project).
- As a user, I want to navigate to search results.

**US-4.2: Activity History**
- As a user, I want a full activity history screen with filters.
- As a user, I want pagination for large activity logs.

### Phase 5: Statistics Dashboard

**US-5.1: Project Statistics**
- As a user, I want to see comprehensive project statistics.
- As a user, I want to see node counts by type and status.
- As a user, I want to see time tracked (week/month/total).
- As a user, I want to see velocity metrics.
- As a user, I want to see milestone progress bars.
- As a user, I want to see blocker list.

### Phase 6: Backup & Export Enhancements

**US-6.1: Backup Management**
- As a user, I want to list existing backups.
- As a user, I want to restore from a backup with confirmation.

**US-6.2: Export Options**
- As a user, I want to choose export format (JSON).
- As a user, I want to choose export scope (all/project).

---

## Acceptance Criteria

### Global
- All keybindings work consistently across screens
- Command palette includes all new commands
- Navigation between screens is smooth
- All CRUD operations persist to database
- Activity is logged for all mutations
- Escape key returns to previous screen

### Performance
- Screen transitions should feel instant
- Form loading should not block UI
- Large data sets should use pagination/virtualization
