# Web UI — Requirements

User stories for Taskyn's web interface feature.

---

## Epic 1: Authentication

### US-1.1: Registration
As a new user, I want to create an account with my name, email, and password,
so that I can access the Taskyn web interface.

**Acceptance Criteria:**
- Form with name, email, password fields and validation
- Password is hashed with bcrypt before storage
- Duplicate email returns a clear error
- Successful registration redirects to onboarding

### US-1.2: Login
As a registered user, I want to log in with my email and password, so that
I can access my projects and tasks.

**Acceptance Criteria:**
- Form with email and password fields
- Server returns a short-lived JWT access token (15 min) in the response body
- Server sets a long-lived refresh token (7 days) as an HTTP-only cookie
- Access token is stored in memory (React state), never localStorage
- Invalid credentials show an error message
- Successful login redirects to the originally intended page (or dashboard)

### US-1.3: Session Persistence
As a logged-in user, I want my session to persist across page refreshes and
browser tabs, so I don't have to log in repeatedly.

**Acceptance Criteria:**
- On app load, attempt to refresh the access token using the HTTP-only cookie
- If refresh succeeds, restore the authenticated state silently
- If refresh fails (expired/missing cookie), redirect to login

### US-1.4: Automatic Token Refresh
As a logged-in user, I want expired API requests to be automatically retried
after refreshing my token, so I never see spurious auth errors.

**Acceptance Criteria:**
- When a 401 response is received, automatically call `/auth/refresh`
- Deduplicate concurrent refresh requests (only one in-flight at a time)
- Retry the original request with the new access token
- If refresh fails, redirect to login

### US-1.5: Logout
As a logged-in user, I want to log out so my session is terminated.

**Acceptance Criteria:**
- Calls `/auth/logout` to clear the refresh cookie server-side
- Clears the access token from React state
- Redirects to the login page

---

## Epic 2: Application Shell & Navigation

### US-2.1: Top Navigation Bar
As a user, I want a persistent navigation bar so I can move between sections
of the application.

**Acceptance Criteria:**
- Fixed top bar with Taskyn logo, nav links, search bar, user menu
- Nav links: Dashboard, Companies, Projects, Planner, Kanban, Tracker
- Active link is visually highlighted based on current route
- User avatar/menu on the right with Settings, Help, and Logout options

### US-2.2: Theme Support
As a user, I want to choose between dark/light modes and color themes
(amber, wine, ocean, forest), so the UI matches my preference.

**Acceptance Criteria:**
- Theme and mode selection in Settings page
- Preference persists in localStorage across sessions
- Applied via CSS custom properties on `<html>` element
- Default: dark mode, amber theme

### US-2.3: Protected Routes
As an unauthenticated user, I should be redirected to login when trying
to access any protected page.

**Acceptance Criteria:**
- All routes except `/login`, `/signup`, `/onboarding` are protected
- Redirect preserves the intended destination for post-login redirect
- Loading state shown while auth state is being determined

### US-2.4: Keyboard Shortcuts
As a power user, I want keyboard shortcuts for common actions so I can
navigate and operate the app quickly.

**Acceptance Criteria:**
- Shortcuts are context-sensitive (different per page)
- Shortcut hints displayed in a bottom bar
- Global shortcuts work from any page (e.g., search)

---

## Epic 3: Dashboard

### US-3.1: Dashboard Overview
As a user, I want to see a summary of my work when I open the app, so I
can quickly understand my current status.

**Acceptance Criteria:**
- Stats grid: tasks due today, in progress, completed this week, time tracked today
- Today's tasks list with checkboxes, priority indicators, and project context
- Active timer widget (if a timer is running)
- Recent activity feed
- Data fetched from `pm_get_dashboard` MCP tool

### US-3.2: Task Completion from Dashboard
As a user, I want to mark tasks as done directly from the dashboard, so I
don't have to navigate away.

**Acceptance Criteria:**
- Clicking a task checkbox calls `pm_complete_node`
- Task visually transitions to completed state
- Dashboard stats update (via TanStack Query cache invalidation)

### US-3.3: Dashboard "View All" Link
As a user, I want to see all my tasks when I click "View all" on the
dashboard task section.

**Acceptance Criteria:**
- "View all" navigates to the Planner page for the relevant project

---

## Epic 4: Companies

### US-4.1: Companies List
As a user, I want to see all my companies with summary stats, so I can
understand the overall status of each organization.

**Acceptance Criteria:**
- Grid of company cards showing name, description, and icon
- Each card displays: project count, task count, tracked time, completion %
- Stats fetched via `pm_list_companies(include_stats=true)`
- "New Company" button opens a creation modal

### US-4.2: Company Detail Modal
As a user, I want to view a company's details and its projects in a modal,
so I can quickly review without leaving the page.

**Acceptance Criteria:**
- Clicking a company card opens a "View Company" modal
- Modal shows: company info, stats, list of projects with progress bars
- "Edit" button opens edit modal
- "New Project" button opens project creation modal

### US-4.3: Company CRUD
As a user, I want to create, edit, and delete companies.

**Acceptance Criteria:**
- Create modal with name and description fields
- Edit modal pre-populated with current values
- Delete with confirmation dialog
- All operations go through MCP tools via FastAPI

---

## Epic 5: Projects

### US-5.1: Projects List
As a user, I want to see all my projects with per-project stats, so I can
assess progress at a glance.

**Acceptance Criteria:**
- Grid of project cards with name, company, description
- Each card shows: node counts by type, progress bar, completion %
- Stats fetched via `pm_list_projects(include_stats=true)`
- Filterable by company (dropdown) and status
- "New Project" button

### US-5.2: Project Detail Page
As a user, I want to view a project's details including its root-level
work items and stats.

**Acceptance Criteria:**
- Route: `/projects/:projectId`
- Breadcrumb: Companies > Company Name (if applicable)
- Stats grid: total nodes, completed, in progress, blocked, time tracked
- List of root-level nodes (methodology-specific: epics, specs, etc.)
- Create new root node button (label adapts to methodology)
- Data from 3 parallel calls: `pm_get_project`, `pm_list_nodes`, `pm_get_methodology_info`

### US-5.3: Project CRUD
As a user, I want to create, edit, and delete projects.

**Acceptance Criteria:**
- Create modal: name, company (dropdown), methodology (dropdown), description
- Edit modal: update name, description, status
- Delete with confirmation
- Empty state shown for new projects with no nodes

---

## Epic 6: Node Management (Methodology-Aware)

### US-6.1: Node Detail Page
As a user, I want to view any work item's details regardless of its type
or methodology, using a single generic page.

**Acceptance Criteria:**
- Route: `/nodes/:nodeId`
- Page adapts display based on methodology (icons, labels, colors from `methodology-ui.ts`)
- Shows: title, status badge, description, properties
- Breadcrumb built from `pm_get_ancestors`
- Children list (methodology-specific child types)
- Edges (outgoing/incoming), time entries, rollup stats from `pm_get_node`
- Data from 2 parallel calls: `pm_get_node`, `pm_get_ancestors`

### US-6.2: Node CRUD
As a user, I want to create, edit, and delete work items (nodes).

**Acceptance Criteria:**
- Create modal: type (methodology-valid types), title, description, parent, assignee, priority
- Edit modal: update title, description, assignee, priority
- Delete with confirmation
- Parent selection respects methodology edge rules

### US-6.3: Node Status Transitions
As a user, I want to start, complete, or block a work item so I can
track its lifecycle.

**Acceptance Criteria:**
- "Start" action calls `pm_start_node` (changes status + starts timer)
- "Complete" action calls `pm_complete_node` (stops timer + sets done)
- "Block" action calls `pm_block_node` with reason
- UI reflects the new status immediately (optimistic update)
- Invalid transitions are prevented based on methodology rules

---

## Epic 7: Kanban Board

### US-7.1: Kanban View
As a user, I want to see my project's work items in a kanban board, so I
can visualize workflow status.

**Acceptance Criteria:**
- Route: `/kanban/:projectId`
- Columns represent statuses (methodology-specific)
- Cards show node title, assignee, priority, type icon
- Project selector dropdown to switch between projects

### US-7.2: Kanban Drag-and-Drop
As a user, I want to drag cards between columns to change their status.

**Acceptance Criteria:**
- Drag a card from one column to another
- Calls `pm_update_node` with the new status
- Invalid transitions are prevented (card snaps back)
- Optimistic UI update

---

## Epic 8: Planner

### US-8.1: Planner View
As a user, I want to see my project's work items in an accordion tree
(hierarchical view) so I can plan and organize work.

**Acceptance Criteria:**
- Route: `/planner/:projectId`
- Accordion tree: root nodes > children > grandchildren
- Expand/collapse nodes to show children
- Each item shows: status, title, assignee, priority
- Project selector dropdown to switch projects

### US-8.2: Inline Planner Actions
As a user, I want to create, edit, and manage work items directly from
the planner without opening separate pages.

**Acceptance Criteria:**
- Inline "Add child" action on each node
- Quick status change (start, complete, block)
- Click node title to navigate to node detail page

---

## Epic 9: Time Tracking

### US-9.1: Timer Widget
As a user, I want to start, pause, and stop a timer on a task so I can
track my work time.

**Acceptance Criteria:**
- Timer widget visible on Dashboard and Tracker pages
- Shows: elapsed time (HH:MM:SS), task name, stop/pause controls
- Timer state persists across page navigation (TimerProvider)
- Starting a timer auto-stops any running timer
- Stop saves the time entry via `pm_stop_timer`

### US-9.2: Time Entry List
As a user, I want to see my time entries so I can review my work log.

**Acceptance Criteria:**
- Route: `/tracker`
- List of time entries with date, duration, task name, notes
- Active timer displayed at the top

### US-9.3: Manual Time Logging
As a user, I want to manually log time against a task for work I forgot
to track.

**Acceptance Criteria:**
- "Log Time" button opens a modal
- Fields: node (searchable dropdown), duration, notes
- Calls `pm_log_time`

---

## Epic 10: Settings

### US-10.1: Settings Page
As a user, I want to configure my preferences.

**Acceptance Criteria:**
- Route: `/settings`
- Theme selection: amber, wine, ocean, forest
- Mode toggle: dark / light
- Profile section: name, email (display only for v1)

---

## Epic 11: MCP Enhancements (Core Changes)

### US-11.1: Company Stats Tool
As a web UI consumer, I need aggregated company statistics from a single
MCP call, so the companies page doesn't require N+1 requests.

**Acceptance Criteria:**
- New `pm_get_company_stats(company_id)` MCP tool
- Returns: project count, total nodes, completed nodes, completion %, total time
- Uses existing `get_project_stats` core function (no new core logic)

### US-11.2: Projects List with Stats
As a web UI consumer, I need per-project stats inline in the projects list,
so the projects page doesn't require N+1 requests.

**Acceptance Criteria:**
- `pm_list_projects` gains optional `include_stats: bool = False` parameter
- When true, each project includes: total nodes, completed, completion %, time, nodes by type
- Backward compatible (defaults to False)

### US-11.3: Companies List with Stats
As a web UI consumer, I need per-company stats inline in the companies list,
so the companies page doesn't require N+1 requests.

**Acceptance Criteria:**
- `pm_list_companies` gains optional `include_stats: bool = False` parameter
- When true, each company includes: project count, total nodes, completed, completion %, time
- Backward compatible (defaults to False)

---

## Epic 12: FastAPI Backend

### US-12.1: FastAPI App Setup
As a developer, I need a FastAPI application that serves as a thin REST
bridge to MCP tools.

**Acceptance Criteria:**
- FastAPI app with CORS configured for Vite dev server (localhost:5173)
- API versioning at `/api/v1`
- Router modules for each resource domain
- Swagger docs at `/api/docs`

### US-12.2: MCP Integration Layer
As a developer, I need FastAPI to call MCP tools in-process without
importing Taskyn core directly.

**Acceptance Criteria:**
- `get_mcp()` dependency provides MCP server instance
- `call_mcp_tool()` helper maps MCP errors to HTTP status codes
- FastAPI never imports from `taskyn.core`, `taskyn.graph`, or `taskyn.db`

### US-12.3: REST Endpoints
As a frontend developer, I need RESTful endpoints that map 1:1 to MCP tools.

**Acceptance Criteria:**
- CRUD endpoints for: companies, projects, nodes, edges, milestones, tags
- Action endpoints: node start/complete/block, timer start/stop
- Query endpoints: dashboard, activity, search
- All endpoints require authentication (except `/auth/*`)
- Standard error response format: `{ error, detail, code }`

### US-12.4: User Authentication Backend
As a developer, I need auth endpoints for registration, login, logout,
and token refresh.

**Acceptance Criteria:**
- `POST /auth/register` - create user with bcrypt-hashed password
- `POST /auth/login` - validate credentials, return access token, set refresh cookie
- `POST /auth/logout` - clear refresh cookie
- `POST /auth/refresh` - validate refresh cookie, return new access token
- `GET /auth/me` - return current user info
- Users stored in SQLite `users` table

---

## Epic 13: React Frontend Foundation

### US-13.1: Project Scaffolding
As a developer, I need a React project with Vite, TypeScript, and the
required dependencies.

**Acceptance Criteria:**
- Vite + React + TypeScript project in `src/taskyn/web/frontend/`
- Dependencies: react-router-dom, @tanstack/react-query, react-hook-form, zod
- CSS based on existing mockup stylesheets (themes.css, base.css)
- Folder structure follows Atomic Design pattern

### US-13.2: Global Providers
As a developer, I need React context providers for app-wide state.

**Acceptance Criteria:**
- AuthProvider: user state, login/logout/register actions
- ThemeProvider: mode + theme, persisted to localStorage
- TimerProvider: active timer state, tick every second
- ModalProvider: central modal management (open/close)
- ToastProvider: notification queue with auto-dismiss

### US-13.3: API Client Layer
As a developer, I need a typed API client that handles auth headers,
token refresh, and error mapping.

**Acceptance Criteria:**
- Base `request()` function with auth header injection
- Automatic 401 retry with token refresh
- Resource-specific API modules (nodesApi, projectsApi, companiesApi, etc.)
- `ApiError` class for structured error handling

### US-13.4: Routing Setup
As a developer, I need React Router v6 configured with all application routes.

**Acceptance Criteria:**
- Public routes: `/login`, `/signup`, `/onboarding`
- Protected routes wrapped in `ProtectedRoute` + `AppShell`
- Routes: `/dashboard`, `/companies`, `/projects`, `/projects/:projectId`,
  `/nodes/:nodeId`, `/kanban/:projectId`, `/planner/:projectId`, `/tracker`, `/settings`
- Catch-all redirects to `/`
