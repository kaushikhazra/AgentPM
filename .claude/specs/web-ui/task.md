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
