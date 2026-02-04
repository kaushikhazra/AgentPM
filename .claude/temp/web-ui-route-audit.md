# Web UI Route & Data Audit

Findings from reviewing all HTML mockups against the routing and API design.

---

## Issue 1: Company Detail is Modal-Only (No Route Needed)

**Mockup**: `company.html`

The company detail view is rendered as a **modal**, not a separate page. Clicking a
company card opens a "View Company" modal showing:
- Company name, description, icon
- Stats: projects count, tasks count, tracked time, % done
- List of projects with progress bars
- Edit and "New Project" actions

**Conclusion**: No `/companies/:companyId` route needed. The `/companies` route is
sufficient. CRUD is handled via modals (New, View, Edit).

---

## Issue 2: Missing Company-Level Aggregation

**Mockup**: `company.html`

Each company card and the view modal display aggregated stats:
- Number of projects
- Total tasks across all projects
- Total time tracked
- Overall completion percentage

**Problem**: There is no `pm_get_company_stats` MCP tool. The existing
`pm_get_company` tool only returns basic company info (id, name, description).

**Options**:
1. Add a new `pm_get_company_stats` MCP tool that returns aggregated data
2. Compute stats on the FastAPI side by calling multiple MCP tools (violates thin bridge)
3. Compute stats on the frontend by fetching projects per company (N+1)

**Recommendation**: Option 1 - add `pm_get_company_stats` MCP tool. Keeps the
single entry point clean and avoids N+1 on the frontend.

---

## Issue 3: Projects List N+1 Problem

**Mockup**: `projects.html`

Each project card displays:
- Project name, company, description
- Node counts by type (e.g., "3 epics, 12 stories, 47 tasks")
- Progress bar with completion percentage

**Problem**: `pm_list_projects` returns basic project data. Getting per-project
stats requires calling `pm_get_project_stats` for each project individually.

For a user with 8 projects, that's 9 API calls (1 list + 8 stats).

**Options**:
1. Add `pm_list_projects_with_stats` composite MCP tool
2. Enrich `pm_list_projects` to include stats inline
3. Accept N+1 and let TanStack Query parallelize the calls

**Recommendation**: Option 2 - enrich `pm_list_projects` with an optional
`include_stats=true` parameter. The MCP tool already has access to the data.

---

## Issue 4: Planner Route Missing Project Context

**Mockup**: `planner.html`

The planner shows an accordion tree (Epic > Story > Task) that is clearly
project-scoped. It also has a project selector dropdown (same pattern as kanban).

**Current route**: `/planner` (no project parameter)
**Kanban route**: `/kanban/:projectId` (has project parameter)

These should be consistent.

**Recommendation**: Change to `/planner/:projectId` to match the kanban pattern.
The project selector in the UI navigates between `/planner/:projectA` and
`/planner/:projectB`.

---

## Issue 5: Node Detail Page Requires 4 Separate Calls

**Mockups**: `epic.html`, `story.html`

The node detail page needs:
1. `pm_get_node` - node data
2. `pm_get_ancestors` - breadcrumb chain
3. `pm_get_descendants` or `pm_list_nodes` with parent filter - children
4. `pm_get_rollup` - aggregated stats

**Problem**: 4 round-trips for a single page load.

**Options**:
1. Add a composite `pm_get_node_detail` MCP tool that returns everything
2. Accept the 4 calls and let TanStack Query parallelize them
3. FastAPI composes the response from multiple MCP calls (composite endpoint)

**Recommendation**: Option 3 - FastAPI serves a composite `/nodes/:id/detail`
endpoint that calls multiple MCP tools and assembles the response. This keeps MCP
tools atomic (good for AI agents) while giving the frontend a single efficient call.
This is an acceptable responsibility for the "thin bridge" - it's not adding business
logic, just aggregating data.

---

## Issue 6: Dashboard "View All" Tasks Links to Non-Existent Route

**Mockup**: `dashboard.html`

The "Today's Tasks" section has a "View all" link pointing to `tasks.html`.
There is no `/tasks` route in the route table.

**Options**:
1. Map "View all" to the Planner page (`/planner/:projectId`)
2. Add a dedicated `/tasks` route for a flat task list view
3. Remove the "View all" link

**Recommendation**: Option 1 is sufficient for now. The planner already shows all
tasks in a tree. If a flat task view becomes needed later, it can be added.

---

## Issue 7: Project Detail Page Also Needs Multiple Calls

**Mockup**: `project.html`

The project detail page needs:
1. `pm_get_project` - project info
2. `pm_get_project_stats` - stats (epics, stories, tasks, progress)
3. `pm_list_nodes` with project_id - root nodes list
4. `pm_get_methodology_info` - methodology config for UI rendering

**Problem**: 4 round-trips for a single page load.

**Recommendation**: Same as Issue 5 - FastAPI can serve a composite
`/projects/:id/detail` endpoint that aggregates these MCP calls.

---

## Summary of Required Changes

### Routing Changes

| Change | From | To |
|--------|------|-----|
| Planner route | `/planner` | `/planner/:projectId` |
| Dashboard "View all" | links to `/tasks` | links to `/planner/:projectId` |

### New MCP Tools Needed

| Tool | Purpose |
|------|---------|
| `pm_get_company_stats` | Aggregated stats per company (project count, task count, time, completion %) |

### MCP Tool Enhancements

| Tool | Enhancement |
|------|-------------|
| `pm_list_projects` | Add optional `include_stats` parameter to inline per-project stats |

### New Composite FastAPI Endpoints

These are NOT new MCP tools. They are FastAPI-level aggregations that call multiple
atomic MCP tools and return a combined response. This keeps MCP tools atomic for AI
agents while giving the frontend efficient single-call page loads.

| Endpoint | MCP Tools Called | Purpose |
|----------|-----------------|---------|
| `GET /nodes/:id/detail` | `pm_get_node` + `pm_get_ancestors` + `pm_get_descendants` + `pm_get_rollup` | Full node page data |
| `GET /projects/:id/detail` | `pm_get_project` + `pm_get_project_stats` + `pm_list_nodes` + `pm_get_methodology_info` | Full project page data |

### Updated Route Table

```
/                           → Redirect to /dashboard (if auth) or /login
/login                      → LoginPage
/signup                     → SignupPage
/onboarding                 → OnboardingPage

/dashboard                  → DashboardPage (protected)
/companies                  → CompaniesPage (protected) [detail via modal]
/projects                   → ProjectsPage (protected)
/projects/:projectId        → ProjectDetailPage (protected)
/nodes/:nodeId              → NodeDetailPage (protected, generic)
/kanban/:projectId          → KanbanPage (protected)
/planner/:projectId         → PlannerPage (protected)
/tracker                    → TrackerPage (protected)
/settings                   → SettingsPage (protected)
```
