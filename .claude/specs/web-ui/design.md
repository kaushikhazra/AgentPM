# Web UI — Design

Architecture and design decisions for Taskyn's web interface.

---

## System Architecture

```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│  React UI   │ ───► │  FastAPI    │ ───► │ MCP Server  │ ───► │ Taskyn Core │
│  (Browser)  │ HTTP │  (REST)     │      │ (Tools)     │      │ (Python)    │
└─────────────┘      └─────────────┘      └─────────────┘      └─────────────┘
     frontend            backend              mcp/                 core/
```

**Core Invariant**: MCP is the single entry point to Taskyn core. FastAPI is a
thin REST-to-MCP bridge. It never imports from `taskyn.core`, `taskyn.graph`,
or `taskyn.db`. All data flows through `mcp.call_tool()`.

**Why**: Taskyn is AI-first. Humans via Web UI and AI agents via MCP must go
through the exact same code path — one set of validation, one set of business
logic, one set of activity logging.

---

## Package Layout

```
src/taskyn/
├── db/                       # existing
├── graph/                    # existing
├── core/                     # existing
├── methodologies/            # existing
├── cli/                      # existing
├── mcp/                      # existing (+ 3 changes, see MCP section)
│
└── web/                      # NEW
    ├── __init__.py
    │
    ├── backend/              # FastAPI REST API
    │   ├── __init__.py
    │   ├── main.py           # FastAPI app, CORS, router registration
    │   ├── deps.py           # get_mcp(), get_current_user(), call_mcp_tool()
    │   ├── schemas/          # Pydantic request/response models
    │   │   ├── __init__.py
    │   │   ├── common.py     # ErrorResponse
    │   │   ├── auth.py       # UserCreate, UserLogin, etc.
    │   │   ├── nodes.py      # NodeCreate, NodeUpdate, NodeResponse
    │   │   └── projects.py   # ProjectCreate, ProjectResponse
    │   ├── auth/             # JWT + password hashing
    │   │   ├── __init__.py
    │   │   ├── jwt.py        # create/decode tokens
    │   │   └── password.py   # bcrypt hash/verify
    │   └── routes/           # One module per resource
    │       ├── __init__.py
    │       ├── auth.py       # register, login, logout, refresh, me
    │       ├── companies.py
    │       ├── projects.py
    │       ├── nodes.py
    │       ├── edges.py
    │       ├── milestones.py
    │       ├── tags.py
    │       ├── timer.py
    │       ├── time_entries.py
    │       ├── activity.py
    │       ├── dashboard.py
    │       └── search.py
    │
    └── frontend/             # React application
        ├── package.json
        ├── vite.config.ts
        ├── tsconfig.json
        ├── index.html
        │
        └── src/
            ├── App.tsx
            ├── main.tsx
            ├── routes.tsx
            │
            ├── config/
            │   └── methodology-ui.ts
            │
            ├── api/
            │   ├── client.ts
            │   ├── companies.ts
            │   ├── projects.ts
            │   ├── nodes.ts
            │   ├── edges.ts
            │   ├── timer.ts
            │   ├── activity.ts
            │   ├── dashboard.ts
            │   └── search.ts
            │
            ├── types/
            │   └── index.ts
            │
            ├── providers/
            │   ├── AuthProvider.tsx
            │   ├── ThemeProvider.tsx
            │   ├── TimerProvider.tsx
            │   ├── ModalProvider.tsx
            │   └── ToastProvider.tsx
            │
            ├── hooks/
            │   ├── useAuth.ts
            │   ├── useTheme.ts
            │   ├── useTimer.ts
            │   ├── useModal.ts
            │   ├── useToast.ts
            │   └── useHotkeys.ts
            │
            ├── components/
            │   ├── atoms/
            │   ├── molecules/
            │   ├── organisms/
            │   └── templates/
            │
            ├── pages/
            │   ├── LoginPage.tsx
            │   ├── SignupPage.tsx
            │   ├── OnboardingPage.tsx
            │   ├── DashboardPage.tsx
            │   ├── CompaniesPage.tsx
            │   ├── ProjectsPage.tsx
            │   ├── ProjectDetailPage.tsx
            │   ├── NodeDetailPage.tsx
            │   ├── KanbanPage.tsx
            │   ├── PlannerPage.tsx
            │   ├── TrackerPage.tsx
            │   └── SettingsPage.tsx
            │
            └── styles/
                ├── themes.css
                └── base.css
```

---

## Backend Design

### FastAPI as Thin Bridge

Every REST endpoint follows the same pattern:

```python
@router.get("/{id}")
async def get_resource(
    id: str,
    mcp = Depends(get_mcp),
    current_user: User = Depends(get_current_user),
):
    result = await call_mcp_tool(mcp, "pm_get_resource", {"id": id})
    return result
```

FastAPI responsibilities (and nothing else):
1. HTTP routing and method handling
2. Authentication (JWT validation)
3. Request body validation (Pydantic schemas)
4. MCP error → HTTP status code mapping
5. JSON serialization

### MCP Integration

In-process call via dependency injection:

```python
# deps.py
from taskyn.mcp.server import mcp as mcp_server

async def get_mcp():
    return mcp_server

async def call_mcp_tool(mcp, tool_name: str, args: dict):
    try:
        return await mcp.call_tool(tool_name, args)
    except ValueError as e:
        msg = str(e).lower()
        if "not found" in msg:
            raise HTTPException(404, detail=str(e))
        if "already exists" in msg or "cycle" in msg:
            raise HTTPException(409, detail=str(e))
        raise HTTPException(422, detail=str(e))
    except Exception:
        raise HTTPException(500, detail="Internal server error")
```

### Authentication

- JWT with HS256 signing
- Access token: 15 min, stored in React memory
- Refresh token: 7 days, HTTP-only secure cookie
- Password hashing: bcrypt via passlib
- User storage: SQLite `users` table

### Endpoint Map

All endpoints prefixed with `/api/v1`. Full table in `api-design.md`.

Key resource groups:
- `/auth/*` — register, login, logout, refresh, me
- `/companies/*` — CRUD + stats
- `/projects/*` — CRUD + stats + methodology
- `/nodes/*` — CRUD + transitions + ancestors/descendants + rollup + tags
- `/edges/*` — CRUD
- `/milestones/*` — CRUD + complete
- `/timer/*` — start, stop, current
- `/time-entries` — manual time logging
- `/dashboard` — aggregated dashboard data
- `/activity` — recent activity feed
- `/search` — full-text search

---

## Frontend Design

### Component Architecture — Atomic Design

| Level | Purpose | Examples |
|-------|---------|---------|
| Atoms | Smallest reusable elements | Button, Input, Badge, Avatar, Icon, StatusDot |
| Molecules | Atom combinations | NavLink, SearchBar, TaskItem, StatCard, Breadcrumb |
| Organisms | Complex sections | TopNav, KanbanBoard, TimerWidget, ActivityFeed, Modal |
| Templates | Page layouts | AuthLayout, AppShell, DetailLayout, FullWidthLayout |
| Pages | Route endpoints | DashboardPage, NodeDetailPage, KanbanPage |

### Methodology-Aware UI

Generic components adapt to any methodology via a frontend config:

```typescript
// config/methodology-ui.ts
METHODOLOGY_UI[project.methodology].nodeTypes[node.nodeType]
  → { displayName, plural, icon, color }
```

One `NodeDetailPage` renders "Epic" for classic_agile, "Spec" for spec_driven.
No methodology-specific page components.

### State Management

| State Type | Solution | Scope |
|------------|----------|-------|
| Server data | TanStack Query | Global cache |
| Auth | React Context | App-wide |
| Theme | React Context + localStorage | App-wide, persisted |
| Timer | React Context | App-wide, ticks every second |
| Modals | React Context | App-wide |
| Toasts | React Context | App-wide |
| Forms | useState / react-hook-form | Component-local |
| UI toggles | useState | Component-local |

No Redux. TanStack Query handles server state (caching, invalidation,
optimistic updates). React Context handles the 5 global UI concerns.

### Routing

React Router v6 with nested routes:

```
/                           → Redirect to /dashboard or /login
/login                      → LoginPage
/signup                     → SignupPage
/onboarding                 → OnboardingPage
/dashboard                  → DashboardPage (protected)
/companies                  → CompaniesPage (protected)
/projects                   → ProjectsPage (protected)
/projects/:projectId        → ProjectDetailPage (protected)
/nodes/:nodeId              → NodeDetailPage (protected, generic)
/kanban/:projectId          → KanbanPage (protected)
/planner/:projectId         → PlannerPage (protected)
/tracker                    → TrackerPage (protected)
/settings                   → SettingsPage (protected)
```

Protected routes wrap children in `ProtectedRoute` → `AppShell`.

### Data Fetching Patterns

**Page load — parallel queries:**
```
NodeDetailPage:
  useQuery(['nodes', nodeId])        → pm_get_node (composite: edges + time + rollup)
  useQuery(['ancestors', nodeId])    → pm_get_ancestors (breadcrumbs)

ProjectDetailPage:
  useQuery(['projects', projectId])  → pm_get_project (includes stats)
  useQuery(['nodes', projectId])     → pm_list_nodes
  useQuery(['methodology', id])      → pm_get_methodology_info
```

**Mutations:**
```
useMutation → api call → on success:
  1. Invalidate related queries
  2. Show toast notification
  3. Close modal (if open)
```

### CSS Strategy

- CSS custom properties for theming (from mockup CSS)
- Two base files: `themes.css` (color tokens) + `base.css` (component styles)
- Theme applied via `data-mode` and `data-theme` attributes on `<html>`
- No CSS-in-JS library (keep CSS files from mockups)

---

## MCP Changes

3 backward-compatible changes to `src/taskyn/mcp/server.py`:

| Change | Type | Details |
|--------|------|---------|
| `pm_get_company_stats(company_id)` | New tool | Aggregated stats across all company projects |
| `pm_list_projects(include_stats)` | Enhancement | Optional per-project stats inline |
| `pm_list_companies(include_stats)` | Enhancement | Optional per-company stats inline |

Full implementation details in `.claude/research/web-ui/core/mcp-changes.md`.

---

## Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| MCP as single entry point | FastAPI → MCP → Core | AI-first: humans and agents use same code path |
| Thin bridge pattern | No business logic in FastAPI | DRY, single validation layer |
| Generic node pages | One NodeDetailPage for all types | Methodology-agnostic, scales to future methodologies |
| Frontend owns UI metadata | methodology-ui.ts config | Backend stays pure data/validation |
| TanStack Query for server state | No Redux | Caching, invalidation, optimistic updates built-in |
| JWT auth | Access (memory) + Refresh (cookie) | Stateless, XSS-protected refresh |
| Atomic Design components | atoms/molecules/organisms/templates | Reusable, consistent UI |
| CSS custom properties | Not CSS-in-JS | Mockup CSS reuse, theme system already designed |
| No composite FastAPI endpoints | Parallel TanStack Query calls | Keeps FastAPI as pure thin bridge |
| Planner route with projectId | `/planner/:projectId` | Consistent with kanban pattern |

---

## Dependencies

### Backend (Python)
- fastapi
- uvicorn
- python-jose (JWT)
- passlib[bcrypt] (password hashing)
- pydantic (already used by Taskyn)

### Frontend (Node.js)
- react, react-dom
- react-router-dom v6
- @tanstack/react-query
- react-hook-form
- zod
- vite (build tool)
- typescript

---

## References

### Research Documents

| Document | Path | Covers |
|----------|------|--------|
| Design Research | `.claude/research/web-ui/design/web-ui-design-research.md` | 22 UI inspirations, color palettes, typography, layout principles, design tokens, theme system |
| Component Architecture | `.claude/research/web-ui/frontend/component-architecture.md` | React component tree, Atomic Design, methodology-aware UI, folder structure |
| State Management | `.claude/research/web-ui/frontend/state-management.md` | TanStack Query, React Context providers, no-Redux rationale |
| Routing | `.claude/research/web-ui/frontend/routing.md` | React Router v6, route table, ProtectedRoute, breadcrumbs, code splitting |
| API Design | `.claude/research/web-ui/backend/api-design.md` | REST endpoints, MCP integration, thin bridge pattern, error handling |
| Auth Flow | `.claude/research/web-ui/backend/auth-flow.md` | JWT tokens, refresh flow, bcrypt passwords, SQLite user storage |
| MCP Changes | `.claude/research/web-ui/core/mcp-changes.md` | New/enhanced MCP tools, corrected audit assessments |

### UI Mockups

All mockups in `.claude/research/web-ui/design/mockups/`:

| Mockup | Page | Key UI Elements |
|--------|------|-----------------|
| `login.html` | LoginPage | Email/password form, centered card layout |
| `signup.html` | SignupPage | Name/email/password form |
| `onboarding.html` | OnboardingPage | Welcome wizard |
| `dashboard.html` | DashboardPage | Stats grid, tasks list, timer widget, activity feed |
| `company.html` | CompaniesPage | Company cards with stats, view/edit modal |
| `projects.html` | ProjectsPage | Project cards with progress bars, company filter |
| `project.html` | ProjectDetailPage | Breadcrumb, stats grid, root nodes list |
| `project-empty.html` | ProjectDetailPage | Empty state for new projects |
| `epic.html` | NodeDetailPage | Classic Agile epic rendering |
| `story.html` | NodeDetailPage | Classic Agile story rendering |
| `kanban.html` | KanbanPage | Status columns, cards, project selector |
| `planner.html` | PlannerPage | Accordion tree, project selector |
| `tracker.html` | TrackerPage | Time entry list, active timer, log time modal |
| `settings.html` | SettingsPage | Theme/mode selectors, profile |

### Mockup Assets

All in `.claude/research/web-ui/design/mockups/`:

| File | Purpose |
|------|---------|
| `css/themes.css` | Color tokens, theme definitions (amber, wine, ocean, forest), dark/light modes |
| `css/base.css` | Component styles, layout, typography |
| `js/theme.js` | Theme/mode switching logic (reference for ThemeProvider) |
| `js/shortcuts.js` | Keyboard shortcut handling (reference for useHotkeys) |

### Audit

| Document | Path | Purpose |
|----------|------|---------|
| Route & Data Audit | `.claude/temp/web-ui-route-audit.md` | 7 issues found auditing mockups against routes/API |
| Code Review | `.claude/specs/web-ui/review-code.md` | 47 issues across 4 severity levels, missing test coverage |

---

## Phase 11: Hardening & Quality

Phase 11 addresses all findings from the code review (`review-code.md`). Organized
into four sub-phases by domain: security, backend correctness, frontend quality, and
test coverage.

### 11A — Security Hardening

Fixes CRITICAL #1-3 and auth-related HIGH/MEDIUM issues.

**JWT Secret (CR-1)**
- Refuse to start if `TASKYN_JWT_SECRET` is unset or < 32 characters
- Raise `RuntimeError` at module import time, not silently fallback
- Add `jti` (JWT ID) and `iat` claims for future revocation support

**Rate Limiting (CR-2)**
- Add `slowapi` middleware on `/auth/login`, `/auth/register`, `/auth/refresh`
- Default: 5 attempts/minute per IP with exponential backoff on login
- 10 attempts/minute on register

**Authorization / Tenant Isolation (CR-3)**
- Pass `current_user.id` into every MCP tool call
- For now: log the user ID for audit trail (ownership enforcement deferred until
  multi-user is a real requirement, since Taskyn is a personal PM tool)
- Add `user_id` column to activity log

**Auth Cookie Hardening (CR-8, CR-9, CR-40)**
- Make `secure` flag configurable: `TASKYN_COOKIE_SECURE` env var, defaults to `true`
- Mirror `set_cookie` attributes on `delete_cookie` (samesite, httponly, path)
- Add refresh token hash storage in `users` table; on logout, invalidate server-side

**Password & Schema Validation (CR-6, CR-7, CR-22, CR-23)**
- `password: Field(min_length=8, max_length=128)`
- `name: Field(min_length=1, max_length=255)`
- All string fields: `max_length` constraints (names: 255, descriptions: 5000, reasons: 1000)
- `MilestoneCreate.target_date`: use `datetime.date` type instead of `str`
- `TimeEntryCreate.duration_minutes`: `Field(gt=0, le=1440)`

**User Enumeration (CR-18)**
- `/auth/register` returns generic error on duplicate email (same message as validation failure)

### 11B — Backend Correctness

Fixes functional bugs, missing endpoints, and infrastructure issues.

**PATCH Semantics (CR-10)**
- Change `exclude_none=True` to `exclude_unset=True` on all PATCH endpoints
- Allows clients to explicitly set fields to `null` (e.g., un-assign a node)

**Error Logging (CR-11)**
- Add `logging.getLogger(__name__).exception(...)` in `call_mcp_tool` catch-all
- Never swallow stack traces in production

**Thread-Safe SQLite (CR-19)**
- Module-level `_db()` in `auth/users.py` is not safe for async FastAPI
- Use `contextvar` or per-request connection pattern

**Pagination (CR-20)**
- Add `limit` and `offset` query parameters to all list endpoints
- Default: `limit=50`, `offset=0`
- Return `X-Total-Count` header for client-side pagination

**Missing CRUD (CR-21)**
- DELETE `/nodes/:id`
- GET/PATCH `/milestones/:id`
- PATCH `/companies/:id`

**email-validator Dependency (CR-33)**
- Add `email-validator` to `pyproject.toml` `[web]` extras

**CORS Configuration (CR-36, CR-37)**
- Make `allow_origins` configurable via `TASKYN_CORS_ORIGINS` env var
- Narrow `allow_methods` and `allow_headers` to actually used values

### 11C — Frontend Quality

Fixes loops, DRY violations, performance, and accessibility.

**Auth Refresh Race (CR-4)**
- `AuthProvider` initial refresh should use raw `fetch` (bypass the 401 retry path)
- Or: skip auto-refresh for the `/auth/refresh` endpoint in `request()`

**PlannerPage Infinite Loop (CR-5)**
- Decouple expanded-initialization from `loadData` callback
- Separate `useEffect` for setting initial expanded state after data loads

**TrackerPage N+1 (CR-12)**
- Add `GET /api/v1/time-entries` endpoint with date range and node filters
- Replace `nodesApi.list()` with `timeEntriesApi.list()` in TrackerPage

**Lazy Loading (CR-13)**
- Convert all page imports in `routes.tsx` to `React.lazy()` with `Suspense`
- Code-split each page into its own chunk

**Kanban Accessibility (CR-14)**
- Add keyboard alternative: Enter to pick up card, arrow keys to move, Enter to drop
- Or: integrate `@hello-pangea/dnd` for built-in keyboard support

**DRY: statusClass (CR-15)**
- Extract to `src/taskyn/web/frontend/src/utils/status.ts`
- Import in PlannerPage, NodeDetailPage, ProjectDetailPage

**DRY: FilterBadge (CR-16)**
- Refactor KanbanPage and PlannerPage to use existing `FilterBadge` molecule

**dev_server.py Windows Fix (CR-17)**
- Wrap `signal.signal(signal.SIGTERM, ...)` in `try/except ValueError`

**ErrorBoundary (CR-25)**
- Add `ErrorBoundary` component wrapping `AppShell` children
- Show recovery UI instead of white screen on unhandled render errors

**React Query Removal or Use (CR-24)**
- Either wire TanStack Query into data fetching or remove it from dependencies

**TimerProvider Mount Guard (CR-26)**
- Skip timer API call until auth is confirmed (check `user` before fetching)

**Modal Accessibility (CR-27)**
- Add `role="dialog"`, `aria-modal="true"`, focus trapping to Modal and SearchModal

**Loading States (CR-28)**
- Add skeleton/spinner loading states to KanbanPage, PlannerPage, TrackerPage, CompaniesPage

**Form Submission (CR-29)**
- Wrap modal form contents in `<form>` elements so Enter key submits

**Delete Confirmation (CR-30)**
- Add confirmation dialog before delete operations (CompaniesPage)

**SearchModal Race (CR-31)**
- Use `AbortController` to cancel stale search requests

**useHotkeys Churn (CR-32)**
- Memoize shortcuts array or use `useRef` to avoid listener add/remove on every render

**Guest Guard (CR-45)**
- Redirect logged-in users away from `/login` and `/signup`

**404 Page (CR-44)**
- Show a proper 404 page instead of silently redirecting to dashboard

**Icon Accessibility (CR-47)**
- Add `aria-hidden="true"` to decorative Icon SVGs

**Toast Cleanup (CR-46)**
- Clear `setTimeout` on unmount in ToastProvider

### 11D — Test Coverage

Fills gaps identified in the review's "Missing Test Coverage" section.

**Security Tests (Critical)**
- Expired JWT access token rejected by `/auth/me`
- Access token used as refresh token rejected by `/auth/refresh`
- Expired refresh token rejected by `/auth/refresh`
- Unauthenticated POST/PATCH/DELETE return 401 (not just GET)

**Functional Tests (High)**
- `pm_create_node` with `parent_id` parameter (auto-edge creation)
- 404 responses for non-existent resource IDs
- `pm_update_project`, `pm_delete_company`, `pm_delete_project` via MCP
- MCP resources (`pm://dashboard`, `pm://activity/recent`)
- `pm_create_node` with invalid `node_type`

**Robustness Tests (Medium)**
- `pm_create_edge` with invalid edge_type
- `pm_list_nodes` with filter combinations
- Web route `GET /projects?include_stats=true`
- Web route `PATCH /nodes/{id}` with empty body
- Search result content verification
- Timer: start second timer auto-stops first
- `pm_block_node` via MCP

---

## Phase 12: UI/UX Alignment

Phase 12 addresses all discrepancies identified in the Look & Feel Review (`review-ui-lnf.md`).
These ensure the React implementation matches the HTML mockups in `.claude/research/web-ui/design/mockups/`.

### 12A — Navigation

**TopNav Missing Links (LF-1, LF-2)**
- Add Planner nav link between Projects and Tracker
- Add Kanban nav link between Planner and Tracker
- Both routes exist (`/planner`, `/kanban`) but were inaccessible from nav

### 12B — Login Page

**Text Alignment (LF-11 through LF-15)**
- Subtitle: "Sign in to your account to continue" → "Sign in to continue to your workspace"
- Email label: "Email" → "Email address"
- Social button order: GitHub, Google → Google, GitHub
- Signup link: "Sign up" → "Create one"
- Add theme toggle button in top-right corner

### 12C — Dashboard Page

**Stat Cards & Section (LF-3, LF-4, LF-5)**
- Stat card labels: "Total Tasks" → "Tasks Due Today", "Completed" → "Completed This Week", "Projects" → "Time Tracked Today"
- Section title: "In Progress" → "Today's Tasks"
- Task meta format: Show "Due today" format matching mockup
- Enable task checkboxes for completion (TaskItem component already supports this)

### 12D — Kanban Board

**Card Enhancements (LF-7, LF-8, LF-9)**
- Add timer indicator on cards with active timer ("⏱ 01:45:32 tracking")
- Add priority dots to card meta (using existing `task-priority` class)
- Show due dates ("Today", "Tomorrow", "Next week") instead of node type + ID
- Apply `border-left: 3px solid var(--accent-primary)` to card with active timer

### 12E — Projects Page

**Color Picker (LF-6)**
- Add 6-color picker to "New Project" modal
- Colors: primary gradient, secondary gradient, mint-sage, sky-primary, peach-blush, butter-mint
- Store selected color in project properties or use project color field
- Display selected color on project card icons

---

## Phase 13: Delete Functionality

Phase 13 completes CRUD coverage by adding delete operations to all entities that are
missing them. Based on the delete functionality audit:

| Entity | Backend | Frontend API | Frontend UI |
|--------|---------|--------------|-------------|
| Company | ✓ | ✓ | ✓ |
| Project | ✓ | ✓ | ❌ |
| Node | ✓ | ❌ | ❌ |
| Edge | ✓ | ✓ | ❌ |
| Milestone | ❌ | ❌ | ❌ |
| Tag | ❌ | ❌ | ❌ |
| Node Tag | ✓ | ✓ | ❌ |
| Time Entry | ❌ | ❌ | ❌ |

### 13A — Backend Additions

**Milestone Delete (US-18.4)**
- Add `pm_delete_milestone(milestone_id)` MCP tool to `server.py`
- Add `DELETE /milestones/:id` route to `routes/milestones.py`
- Validate milestone exists before delete

**Tag Delete (US-18.5)**
- Add `pm_delete_tag(tag_name)` MCP tool to `server.py`
- Add `DELETE /tags/:name` route to `routes/tags.py`
- Return warning if tag is currently applied to nodes

**Time Entry Delete (US-18.7)**
- Add `pm_delete_time_entry(entry_id)` MCP tool to `server.py`
- Add `DELETE /time-entries/:id` route to `routes/time_entries.py`
- Validate entry exists and belongs to current user

### 13B — Frontend API Additions

**Node API (US-18.2)**
```typescript
// api/nodes.ts
delete: (id: string) => api.delete(`/nodes/${id}`)
```

**Milestone API (US-18.4)**
```typescript
// api/milestones.ts (new file or add to existing)
delete: (id: string) => api.delete(`/milestones/${id}`)
```

**Tag API (US-18.5)**
```typescript
// api/tags.ts (new file or add to existing)
delete: (name: string) => api.delete(`/tags/${encodeURIComponent(name)}`)
```

**Time Entry API (US-18.7)**
```typescript
// api/timeEntries.ts (new file or add to existing)
delete: (id: string) => api.delete(`/time-entries/${id}`)
```

### 13C — Frontend UI Additions

**ProjectsPage / ProjectDetailPage (US-18.1)**
- Add delete button to project actions (card menu or detail page header)
- Confirmation modal: "Delete project? This will also delete all nodes and time entries."
- On success: redirect to `/projects`, show success toast
- On failure: show error toast

**NodeDetailPage (US-18.2)**
- Add delete button to page header actions
- Confirmation modal: "Delete {nodeType}? This will also delete all children and time entries."
- On success: redirect to parent node or project
- On failure: show error toast

**NodeDetailPage - Edges (US-18.3)**
- Add delete/remove icon button on each edge row
- Confirmation modal: "Remove relationship to {targetNode}?"
- On success: refresh node detail
- On failure: show error toast

**NodeDetailPage - Tags (US-18.6)**
- Add X button on each tag badge
- No confirmation needed (quick action)
- On success: refresh node detail
- On failure: show error toast

**TrackerPage (US-18.7)**
- Add delete button on each time entry row
- Confirmation modal: "Delete time entry for {taskName}?"
- On success: refresh time entries list
- On failure: show error toast

**Settings or Tags Page (US-18.5)**
- Add tags management section or dedicated page
- List all tags with delete button
- Confirmation modal with warning if tag is in use: "Delete tag '{name}'? It is currently applied to N nodes."
- On success: refresh tags list
- On failure: show error toast
