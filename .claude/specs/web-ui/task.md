# Web UI — Tasks

---

## Phase 1: MCP Enhancements

- [x] Add `pm_get_company_stats` MCP tool to `server.py`
  - [x] Implement aggregation across company projects
  - [x] Add tests for company stats
  _US-11.1_

- [x] Add `include_stats` parameter to `pm_list_projects`
  - [x] Inline per-project stats when `include_stats=True`
  - [x] Verify backward compatibility (defaults to False)
  _US-11.2_

- [x] Add `include_stats` parameter to `pm_list_companies`
  - [x] Inline per-company stats when `include_stats=True`
  - [x] Verify backward compatibility (defaults to False)
  _US-11.3_

---

## Phase 2: FastAPI Backend — Foundation

- [x] Create `src/taskyn/web/` package structure
  - [x] Create `backend/`, `backend/routes/`, `backend/schemas/`, `backend/auth/`
  _US-12.1_

- [x] Implement FastAPI app (`main.py`)
  - [x] CORS middleware for localhost:5173
  - [x] Router registration with `/api/v1` prefix
  _US-12.1_

- [x] Implement MCP integration (`deps.py`)
  - [x] `get_mcp()` dependency
  - [x] `call_mcp_tool()` error-to-HTTP mapper
  _US-12.2_

- [x] Implement user authentication backend
  - [x] SQLite `users` table schema
  - [x] Password hashing with bcrypt (`auth/password.py`)
  - [x] JWT token creation and decoding (`auth/jwt.py`)
  - [x] `get_current_user()` dependency
  _US-12.4_

- [x] Implement auth routes (`routes/auth.py`)
  - [x] POST `/auth/register`
  - [x] POST `/auth/login` (returns access token, sets refresh cookie)
  - [x] POST `/auth/logout` (clears refresh cookie)
  - [x] POST `/auth/refresh` (validates cookie, returns new access token)
  - [x] GET `/auth/me`
  _US-12.4_

---

## Phase 3: FastAPI Backend — REST Endpoints

- [x] Implement company routes (`routes/companies.py`)
  - [x] GET `/companies`, GET `/companies/:id`, POST, DELETE
  - [x] GET `/companies/:id/stats`
  _US-12.3_

- [x] Implement project routes (`routes/projects.py`)
  - [x] GET `/projects`, GET `/projects/:id`, POST, PATCH, DELETE
  - [x] GET `/projects/:id/methodology`, GET `/projects/:id/stats`
  _US-12.3_

- [x] Implement node routes (`routes/nodes.py`)
  - [x] GET `/nodes`, GET `/nodes/:id`, POST, PATCH
  - [x] POST `/nodes/:id/start`, `/nodes/:id/complete`, `/nodes/:id/block`
  - [x] GET `/nodes/:id/ancestors`, `/nodes/:id/descendants`, `/nodes/:id/rollup`
  _US-12.3_

- [x] Implement edge routes (`routes/edges.py`)
  - [x] GET `/edges`, POST `/edges`, DELETE `/edges/:id`
  _US-12.3_

- [x] Implement milestone routes (`routes/milestones.py`)
  - [x] GET `/milestones`, POST `/milestones`, POST `/milestones/:id/complete`
  _US-12.3_

- [x] Implement tag routes (`routes/tags.py`)
  - [x] GET `/tags`, POST `/tags`
  - [x] POST `/nodes/:id/tags`, DELETE `/nodes/:id/tags/:name`
  _US-12.3_

- [x] Implement timer routes (`routes/timer.py`)
  - [x] POST `/timer/start`, POST `/timer/stop`, GET `/timer/current`
  _US-12.3_

- [x] Implement time entry routes (`routes/time_entries.py`)
  - [x] POST `/time-entries`
  _US-12.3_

- [x] Implement reporting routes
  - [x] GET `/dashboard` (`routes/dashboard.py`)
  - [x] GET `/activity` (`routes/activity.py`)
  - [x] GET `/search` (`routes/search.py`)
  _US-12.3_

- [x] Implement Pydantic schemas
  - [x] `schemas/common.py` — ErrorResponse
  - [x] `schemas/auth.py` — UserCreate, UserLogin
  - [x] `schemas/nodes.py` — NodeCreate, NodeUpdate
  - [x] `schemas/projects.py` — ProjectCreate, ProjectUpdate
  _US-12.3_

---

## Phase 4: React Frontend — Foundation

- [x] Scaffold Vite + React + TypeScript project
  - [x] Create `src/taskyn/web/frontend/` with package.json
  - [x] Install dependencies: react-router-dom, @tanstack/react-query, react-hook-form, zod
  - [x] Configure vite.config.ts with API proxy
  _US-13.1_

- [x] Set up CSS from mockups
  - [x] Copy themes.css and base.css from mockup CSS
  - [x] Verify theme switching works (data-mode, data-theme attributes)
  _US-13.1_

- [x] Implement API client layer
  - [x] `api/client.ts` — base request function with auth headers
  - [x] Token refresh on 401 with deduplication
  - [x] ApiError class
  _US-13.3_

- [x] Implement resource API modules
  - [x] `api/companies.ts`, `api/projects.ts`, `api/nodes.ts`
  - [x] `api/edges.ts`, `api/timer.ts`, `api/activity.ts`
  - [x] `api/dashboard.ts`, `api/search.ts`
  _US-13.3_

- [x] Implement TypeScript types
  - [x] `types/index.ts` — Node, Project, Company, Edge, TimeEntry, etc.
  _US-13.1_

- [x] Implement global providers
  - [x] AuthProvider — user state, login/logout/register
  - [x] ThemeProvider — mode + theme, localStorage persistence
  - [x] TimerProvider — active timer, tick every second
  - [x] ModalProvider — open/close, modal type registry
  - [x] ToastProvider — notification queue, auto-dismiss
  _US-13.2_

- [x] Implement routing
  - [x] `routes.tsx` — all routes with React Router v6
  - [x] ProtectedRoute component
  - [x] Post-login redirect to intended destination
  _US-13.4_

- [x] Implement methodology UI config
  - [x] `config/methodology-ui.ts` — display names, icons, colors per methodology
  _US-6.1_

---

## Phase 5: React Frontend — Atoms & Molecules

- [x] Implement atom components
  - [x] Button (primary, secondary, ghost, danger variants)
  - [x] Input (text input with label and error state)
  - [x] Checkbox, Badge, Avatar, Icon, StatusDot, Kbd
  _US-2.1_

- [x] Implement molecule components
  - [x] NavLink, SearchBar, UserMenu
  - [x] TaskItem, StatCard, ActivityItem
  - [x] Breadcrumb, FilterBadge
  _US-2.1_

---

## Phase 6: React Frontend — Organisms & Templates

- [x] Implement organism components
  - [x] TopNav (logo, nav links, search, user menu)
  - [x] Section (header + content slot)
  - [x] TaskList, ActivityFeed
  - [x] TimerWidget (display, controls)
  - [x] Modal (overlay, content, actions via portal)
  - [x] Toast (notification component)
  _US-2.1, US-9.1_

- [x] Implement template components
  - [x] AuthLayout (centered card)
  - [x] AppShell (TopNav + main content area + shortcut bar)
  - [x] DashboardLayout (stats grid + 2-column content)
  - [x] DetailLayout (breadcrumb + header + content)
  - [x] FullWidthLayout (edge-to-edge for kanban)
  _US-2.1_

---

## Phase 7: React Frontend — Pages (Auth)

- [x] Implement LoginPage
  - [x] Email/password form with validation
  - [x] Error display for invalid credentials
  - [x] Post-login redirect
  _US-1.2_

- [x] Implement SignupPage
  - [x] Name/email/password form with validation
  - [x] Redirect to onboarding on success
  _US-1.1_

- [x] Implement OnboardingPage
  - [x] Welcome flow (create first company/project)
  _US-1.1_

- [x] Fix trailing-slash redirect bug (redirect_slashes=False, route paths)
  _US-12.2_

---

## Phase 8: React Frontend — Pages (Core)

- [x] Implement DashboardPage
  - [x] Stats grid (tasks due, in progress, completed, time)
  - [x] Today's tasks list with completion checkboxes
  - [x] Timer widget
  - [x] Activity feed
  - [x] "View all" links to planner
  _US-3.1, US-3.2, US-3.3_

- [x] Implement CompaniesPage
  - [x] Company cards with stats
  - [x] Company detail modal (view, edit)
  - [x] Create/delete company modals
  _US-4.1, US-4.2, US-4.3_

- [x] Implement ProjectsPage
  - [x] Project cards with stats and progress bars
  - [x] Filter by company and status
  - [x] Create project modal
  _US-5.1, US-5.3_

- [x] Implement ProjectDetailPage
  - [x] Breadcrumb, stats grid
  - [x] Root node list (adapts to methodology)
  - [x] Create node modal
  - [x] Empty state for new projects
  _US-5.2, US-5.3_

- [x] Implement NodeDetailPage
  - [x] Generic, methodology-aware layout
  - [x] Breadcrumb from ancestors
  - [x] Node info, status badge, description
  - [x] Children list, edges, time entries, rollup
  - [x] Status transition actions (start, complete, block)
  - [x] Edit/delete modals
  _US-6.1, US-6.2, US-6.3_

- [x] Fix trailing-slash URLs in all API modules
  _US-12.2_

---

## Phase 9: React Frontend — Pages (Views)

- [x] Implement KanbanPage
  - [x] Kanban board with status columns
  - [x] Cards with node title, assignee, priority, type icon
  - [x] Project selector dropdown
  - [-] Drag-and-drop for status transitions (deferred to Phase 10)
  _US-7.1, US-7.2_

- [x] Implement PlannerPage
  - [x] Accordion tree (root > children > grandchildren)
  - [x] Expand/collapse nodes
  - [x] Inline actions (add child, status change)
  - [x] Project selector dropdown
  _US-8.1, US-8.2_

- [x] Implement TrackerPage
  - [x] Time entry list with date, duration, task, notes
  - [x] Active timer widget at top
  - [x] "Log Time" modal
  _US-9.1, US-9.2, US-9.3_

- [x] Implement SettingsPage
  - [x] Theme selector (amber, wine, ocean, forest)
  - [x] Mode toggle (dark/light)
  - [x] Profile display
  _US-10.1_

---

## Phase 10: Integration & Polish

- [x] Wire up keyboard shortcuts
  - [x] Global shortcuts (Ctrl+K search, / search, B back, ? help)
  - [x] Page-specific shortcuts (context-sensitive per route)
  - [x] Shortcut bar at bottom (ShortcutBar organism)
  - [x] useHotkeys hook (global keyboard event handler)
  - [x] SearchModal organism (command-palette search overlay)
  _US-2.4_

- [x] End-to-end testing
  - [x] Auth flow (register, login, refresh, logout)
  - [x] CRUD operations (company, project, node)
  - [x] Timer flow (start, stop, view entries)
  - [x] Kanban drag-and-drop (HTML5 native, optimistic updates)
  _All US_

- [x] Dev server configuration
  - [x] Vite proxy to FastAPI backend (already configured)
  - [x] Concurrent dev start (scripts/dev_server.py — uvicorn + vite)
  _US-13.1_

---

## Phase 11: Hardening & Quality

### 11A — Security Hardening

- [x] Fix JWT secret handling (CR-1)
  - [x] Remove hardcoded fallback; raise `RuntimeError` if `TASKYN_JWT_SECRET` unset or < 32 chars
  - [x] Add `jti` and `iat` claims to JWT tokens
  _US-14.1_

- [x] Add auth rate limiting (CR-2)
  - [x] Install `slowapi`; add limiter to `/auth/login` (5/min), `/auth/register` (10/min), `/auth/refresh` (30/min)
  - [x] Return HTTP 429 with `Retry-After` header (via slowapi default handler)
  - [x] Configurable via `TASKYN_RATE_LIMIT` env var (default `true`)
  _US-14.2_

- [ ] Add tenant audit trail (CR-3) — deferred to 11B
  - [ ] Pass `current_user.id` into every MCP tool call
  - [ ] Add `user_id` to activity log entries
  _US-14.3_

- [x] Harden auth cookies (CR-8, CR-9)
  - [x] Make `secure` flag configurable via `TASKYN_COOKIE_SECURE` env var (default `false` for dev)
  - [x] Mirror `set_cookie` attributes on `delete_cookie` (shared `_COOKIE_ATTRS`)
  _US-14.4_

- [x] Add input validation (CR-6, CR-7, CR-22, CR-23)
  - [x] `password: Field(min_length=8, max_length=128)`, `name: Field(min_length=1, max_length=255)`
  - [x] Add `max_length` to all string fields across all schemas
  - [x] `MilestoneCreate.target_date`: change to `datetime.date`
  - [x] `TimeEntryCreate.duration_minutes`: `Field(gt=0, le=1440)`
  _US-14.5_

- [x] Fix user enumeration (CR-18)
  - [x] `/auth/register` returns generic error on duplicate email
  _US-14.5_

- [x] Configure CORS via env var (CR-36, CR-37)
  - [x] `TASKYN_CORS_ORIGINS` env var; narrow `allow_methods`/`allow_headers`
  _US-15.5_

- [x] Add `email-validator` to pyproject.toml `[web]` extras (CR-33)
  _US-15.4_

- [x] Add error logging (CR-11)
  - [x] Add `logger.exception()` in `call_mcp_tool` catch-all before re-raise
  _US-15.2_

### 11B — Backend Correctness

- [x] Fix PATCH semantics (CR-10)
  - [x] Change `exclude_none=True` to `exclude_unset=True` in all PATCH routes
  _US-15.1_

- [x] Add error logging (CR-11) — done in 11A
  - [x] Add `logger.exception()` in `call_mcp_tool` catch-all before re-raise
  _US-15.2_

- [x] Fix thread-safe SQLite (CR-19)
  - [x] Replace module-level `_db()` in `auth/users.py` with per-call context manager
  _US-15.5_

- [ ] Add pagination (CR-20) — deferred
  - [ ] Add `limit`/`offset` parameters to all list endpoints (default 50/0)
  - [ ] Return `X-Total-Count` header
  _US-15.3_

- [x] Add missing CRUD endpoints (CR-21)
  - [x] DELETE `/nodes/:id` + `pm_delete_node` MCP tool
  - [x] GET/PATCH `/milestones/:id` + `pm_get_milestone`/`pm_update_milestone` MCP tools
  - [x] PATCH `/companies/:id` + `pm_update_company` MCP tool
  _US-15.4_

- [x] Add `email-validator` to pyproject.toml `[web]` extras (CR-33) — done in 11A
  _US-15.4_

- [x] Configure CORS via env var (CR-36, CR-37) — done in 11A
  - [x] `TASKYN_CORS_ORIGINS` env var; narrow `allow_methods`/`allow_headers`
  _US-15.5_

### 11C — Frontend Quality

- [ ] Fix AuthProvider refresh race (CR-4)
  - [ ] Use raw `fetch` for initial refresh, or skip auto-refresh for `/auth/refresh`
  _US-16.1_

- [ ] Fix PlannerPage infinite loop (CR-5)
  - [ ] Decouple expanded-initialization from `loadData` callback
  _US-16.1_

- [ ] Fix TrackerPage N+1 loading (CR-12)
  - [ ] Add `GET /api/v1/time-entries` endpoint; use in TrackerPage
  _US-16.1_

- [ ] Fix SearchModal stale results race (CR-31)
  - [ ] Use `AbortController` to cancel stale search requests
  _US-16.1_

- [ ] Fix useHotkeys listener churn (CR-32)
  - [ ] Memoize shortcuts or use `useRef` for stable reference
  _US-16.1_

- [ ] Extract `statusClass` to shared util (CR-15)
  - [ ] Create `utils/status.ts`; import in PlannerPage, NodeDetailPage, ProjectDetailPage
  _US-16.2_

- [ ] Refactor to use FilterBadge molecule (CR-16)
  - [ ] Replace manual dropdown in KanbanPage and PlannerPage with FilterBadge
  _US-16.2_

- [ ] Decide on React Query (CR-24)
  - [ ] Wire TanStack Query into data fetching, or remove from dependencies
  _US-16.2_

- [ ] Add lazy loading (CR-13)
  - [ ] Convert page imports in `routes.tsx` to `React.lazy()` with `Suspense`
  _US-16.3_

- [ ] Add ErrorBoundary (CR-25)
  - [ ] Create ErrorBoundary component; wrap AppShell children
  _US-16.4_

- [ ] Add Kanban keyboard accessibility (CR-14)
  - [ ] Keyboard alternative for drag-and-drop (Enter/arrow keys)
  _US-16.4_

- [ ] Add modal accessibility (CR-27)
  - [ ] `role="dialog"`, `aria-modal="true"`, focus trapping on Modal and SearchModal
  _US-16.4_

- [ ] Add loading states (CR-28)
  - [ ] Skeleton/spinner on KanbanPage, PlannerPage, TrackerPage, CompaniesPage
  _US-16.4_

- [ ] Wrap modal forms in `<form>` (CR-29)
  - [ ] Enter key submits in CompaniesPage, PlannerPage, ProjectDetailPage, NodeDetailPage
  _US-16.4_

- [ ] Add delete confirmation dialog (CR-30)
  - [ ] Confirmation before delete on CompaniesPage
  _US-16.4_

- [ ] Fix TimerProvider mount guard (CR-26)
  - [ ] Skip timer API call until auth is confirmed
  _US-16.4_

- [ ] Add guest guard on auth pages (CR-45)
  - [ ] Redirect logged-in users away from `/login` and `/signup`
  _US-16.4_

- [ ] Add 404 page (CR-44)
  - [ ] Show proper 404 page instead of silent redirect to dashboard
  _US-16.4_

- [ ] Add Icon `aria-hidden` (CR-47)
  - [ ] Decorative SVG icons get `aria-hidden="true"`
  _US-16.4_

- [ ] Fix Toast cleanup (CR-46)
  - [ ] Clear `setTimeout` on unmount in ToastProvider
  _US-16.4_

- [ ] Fix dev_server.py Windows SIGTERM (CR-17)
  - [ ] Wrap `signal.signal(signal.SIGTERM, ...)` in `try/except ValueError`
  _US-16.4_

### 11D — Test Coverage

- [ ] Add security tests (CR-34, CR-35)
  - [ ] Expired JWT access token rejected by `/auth/me`
  - [ ] Access token used as refresh token rejected
  - [ ] Expired refresh token rejected
  - [ ] Unauthenticated POST/PATCH/DELETE return 401
  _US-17.1_

- [ ] Add functional tests
  - [ ] `pm_create_node` with `parent_id` (auto-edge creation)
  - [ ] 404 responses for non-existent resource IDs
  - [ ] `pm_update_project`, `pm_delete_company`, `pm_delete_project` via MCP
  - [ ] MCP resources (`pm://dashboard`, `pm://activity/recent`)
  - [ ] `pm_create_node` with invalid `node_type`
  _US-17.2_

- [ ] Add robustness tests
  - [ ] `pm_create_edge` with invalid edge_type
  - [ ] `pm_list_nodes` with filter combinations
  - [ ] `GET /projects?include_stats=true`
  - [ ] `PATCH /nodes/{id}` with empty body
  - [ ] Search result content verification
  - [ ] Timer: start second auto-stops first
  - [ ] `pm_block_node` via MCP
  _US-17.3_
