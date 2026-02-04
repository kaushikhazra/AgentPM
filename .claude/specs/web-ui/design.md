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
