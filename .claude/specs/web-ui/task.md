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

- [ ] Implement company routes (`routes/companies.py`)
  - [ ] GET `/companies`, GET `/companies/:id`, POST, DELETE
  - [ ] GET `/companies/:id/stats`
  _US-12.3_

- [ ] Implement project routes (`routes/projects.py`)
  - [ ] GET `/projects`, GET `/projects/:id`, POST, PATCH, DELETE
  - [ ] GET `/projects/:id/methodology`, GET `/projects/:id/stats`
  _US-12.3_

- [ ] Implement node routes (`routes/nodes.py`)
  - [ ] GET `/nodes`, GET `/nodes/:id`, POST, PATCH
  - [ ] POST `/nodes/:id/start`, `/nodes/:id/complete`, `/nodes/:id/block`
  - [ ] GET `/nodes/:id/ancestors`, `/nodes/:id/descendants`, `/nodes/:id/rollup`
  _US-12.3_

- [ ] Implement edge routes (`routes/edges.py`)
  - [ ] GET `/edges`, POST `/edges`, DELETE `/edges/:id`
  _US-12.3_

- [ ] Implement milestone routes (`routes/milestones.py`)
  - [ ] GET `/milestones`, POST `/milestones`, POST `/milestones/:id/complete`
  _US-12.3_

- [ ] Implement tag routes (`routes/tags.py`)
  - [ ] GET `/tags`, POST `/tags`
  - [ ] POST `/nodes/:id/tags`, DELETE `/nodes/:id/tags/:name`
  _US-12.3_

- [ ] Implement timer routes (`routes/timer.py`)
  - [ ] POST `/timer/start`, POST `/timer/stop`, GET `/timer/current`
  _US-12.3_

- [ ] Implement time entry routes (`routes/time_entries.py`)
  - [ ] POST `/time-entries`
  _US-12.3_

- [ ] Implement reporting routes
  - [ ] GET `/dashboard` (`routes/dashboard.py`)
  - [ ] GET `/activity` (`routes/activity.py`)
  - [ ] GET `/search` (`routes/search.py`)
  _US-12.3_

- [ ] Implement Pydantic schemas
  - [ ] `schemas/common.py` — ErrorResponse
  - [ ] `schemas/auth.py` — UserCreate, UserLogin
  - [ ] `schemas/nodes.py` — NodeCreate, NodeUpdate
  - [ ] `schemas/projects.py` — ProjectCreate, ProjectUpdate
  _US-12.3_

---

## Phase 4: React Frontend — Foundation

- [ ] Scaffold Vite + React + TypeScript project
  - [ ] Create `src/taskyn/web/frontend/` with package.json
  - [ ] Install dependencies: react-router-dom, @tanstack/react-query, react-hook-form, zod
  - [ ] Configure vite.config.ts with API proxy
  _US-13.1_

- [ ] Set up CSS from mockups
  - [ ] Copy themes.css and base.css from mockup CSS
  - [ ] Verify theme switching works (data-mode, data-theme attributes)
  _US-13.1_

- [ ] Implement API client layer
  - [ ] `api/client.ts` — base request function with auth headers
  - [ ] Token refresh on 401 with deduplication
  - [ ] ApiError class
  _US-13.3_

- [ ] Implement resource API modules
  - [ ] `api/companies.ts`, `api/projects.ts`, `api/nodes.ts`
  - [ ] `api/edges.ts`, `api/timer.ts`, `api/activity.ts`
  - [ ] `api/dashboard.ts`, `api/search.ts`
  _US-13.3_

- [ ] Implement TypeScript types
  - [ ] `types/index.ts` — Node, Project, Company, Edge, TimeEntry, etc.
  _US-13.1_

- [ ] Implement global providers
  - [ ] AuthProvider — user state, login/logout/register
  - [ ] ThemeProvider — mode + theme, localStorage persistence
  - [ ] TimerProvider — active timer, tick every second
  - [ ] ModalProvider — open/close, modal type registry
  - [ ] ToastProvider — notification queue, auto-dismiss
  _US-13.2_

- [ ] Implement routing
  - [ ] `routes.tsx` — all routes with React Router v6
  - [ ] ProtectedRoute component
  - [ ] Post-login redirect to intended destination
  _US-13.4_

- [ ] Implement methodology UI config
  - [ ] `config/methodology-ui.ts` — display names, icons, colors per methodology
  _US-6.1_

---

## Phase 5: React Frontend — Atoms & Molecules

- [ ] Implement atom components
  - [ ] Button (primary, secondary, ghost, danger variants)
  - [ ] Input (text input with label and error state)
  - [ ] Checkbox, Badge, Avatar, Icon, StatusDot, Kbd
  _US-2.1_

- [ ] Implement molecule components
  - [ ] NavLink, SearchBar, UserMenu
  - [ ] TaskItem, StatCard, ActivityItem
  - [ ] Breadcrumb, FilterBadge
  _US-2.1_

---

## Phase 6: React Frontend — Organisms & Templates

- [ ] Implement organism components
  - [ ] TopNav (logo, nav links, search, user menu)
  - [ ] Section (header + content slot)
  - [ ] TaskList, ActivityFeed
  - [ ] TimerWidget (display, controls)
  - [ ] Modal (overlay, content, actions via portal)
  - [ ] Toast (notification component)
  _US-2.1, US-9.1_

- [ ] Implement template components
  - [ ] AuthLayout (centered card)
  - [ ] AppShell (TopNav + main content area + shortcut bar)
  - [ ] DashboardLayout (stats grid + 2-column content)
  - [ ] DetailLayout (breadcrumb + header + content)
  - [ ] FullWidthLayout (edge-to-edge for kanban)
  _US-2.1_

---

## Phase 7: React Frontend — Pages (Auth)

- [ ] Implement LoginPage
  - [ ] Email/password form with validation
  - [ ] Error display for invalid credentials
  - [ ] Post-login redirect
  _US-1.2_

- [ ] Implement SignupPage
  - [ ] Name/email/password form with validation
  - [ ] Redirect to onboarding on success
  _US-1.1_

- [ ] Implement OnboardingPage
  - [ ] Welcome flow (create first company/project)
  _US-1.1_

---

## Phase 8: React Frontend — Pages (Core)

- [ ] Implement DashboardPage
  - [ ] Stats grid (tasks due, in progress, completed, time)
  - [ ] Today's tasks list with completion checkboxes
  - [ ] Timer widget
  - [ ] Activity feed
  - [ ] "View all" links to planner
  _US-3.1, US-3.2, US-3.3_

- [ ] Implement CompaniesPage
  - [ ] Company cards with stats
  - [ ] Company detail modal (view, edit)
  - [ ] Create/delete company modals
  _US-4.1, US-4.2, US-4.3_

- [ ] Implement ProjectsPage
  - [ ] Project cards with stats and progress bars
  - [ ] Filter by company and status
  - [ ] Create project modal
  _US-5.1, US-5.3_

- [ ] Implement ProjectDetailPage
  - [ ] Breadcrumb, stats grid
  - [ ] Root node list (adapts to methodology)
  - [ ] Create node modal
  - [ ] Empty state for new projects
  _US-5.2, US-5.3_

- [ ] Implement NodeDetailPage
  - [ ] Generic, methodology-aware layout
  - [ ] Breadcrumb from ancestors
  - [ ] Node info, status badge, description
  - [ ] Children list, edges, time entries, rollup
  - [ ] Status transition actions (start, complete, block)
  - [ ] Edit/delete modals
  _US-6.1, US-6.2, US-6.3_

---

## Phase 9: React Frontend — Pages (Views)

- [ ] Implement KanbanPage
  - [ ] Kanban board with status columns
  - [ ] Cards with node title, assignee, priority, type icon
  - [ ] Project selector dropdown
  - [ ] Drag-and-drop for status transitions
  _US-7.1, US-7.2_

- [ ] Implement PlannerPage
  - [ ] Accordion tree (root > children > grandchildren)
  - [ ] Expand/collapse nodes
  - [ ] Inline actions (add child, status change)
  - [ ] Project selector dropdown
  _US-8.1, US-8.2_

- [ ] Implement TrackerPage
  - [ ] Time entry list with date, duration, task, notes
  - [ ] Active timer widget at top
  - [ ] "Log Time" modal
  _US-9.1, US-9.2, US-9.3_

- [ ] Implement SettingsPage
  - [ ] Theme selector (amber, wine, ocean, forest)
  - [ ] Mode toggle (dark/light)
  - [ ] Profile display
  _US-10.1_

---

## Phase 10: Integration & Polish

- [ ] Wire up keyboard shortcuts
  - [ ] Global shortcuts (search)
  - [ ] Page-specific shortcuts
  - [ ] Shortcut bar at bottom
  _US-2.4_

- [ ] End-to-end testing
  - [ ] Auth flow (register, login, refresh, logout)
  - [ ] CRUD operations (company, project, node)
  - [ ] Timer flow (start, stop, view entries)
  - [ ] Kanban drag-and-drop
  _All US_

- [ ] Dev server configuration
  - [ ] Vite proxy to FastAPI backend
  - [ ] Concurrent dev start (uvicorn + vite)
  _US-13.1_
