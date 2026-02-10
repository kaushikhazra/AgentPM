# Fix list_nodes Default Limit Truncation

## User Stories

### US-1: Complete node listing for projects
**As a** Taskyn web UI user
**I want** to see all nodes (including epics) when viewing a project
**So that** I can manage my full project hierarchy without missing root-level items.

**Acceptance Criteria:**
- [ ] All nodes for a project are returned regardless of project size
- [ ] Projects with 100+ nodes display all node types correctly
- [ ] Epic/root-level nodes are always visible on the project detail page

### US-2: Accurate project statistics
**As a** Taskyn user
**I want** project statistics to reflect all nodes in the project
**So that** completion percentages and node type counts are accurate.

**Acceptance Criteria:**
- [ ] `get_project_stats()` counts all nodes, not just the first 100
- [ ] Node type breakdown includes every type present in the project
- [ ] Status breakdown accounts for every node

## Context

**Bug discovered in:** SAIDR project (104 nodes — 91 tasks, 9 stories, 4 epics)
**Symptom:** UI shows 0 epics; project stats omit epics entirely
**Root cause:** `graph/nodes.py:list_nodes()` defaults to `limit=100`, and callers don't override it. Epics (created first) fall outside the 100-row window due to `ORDER BY created_at DESC`.
