# TanStack Query Migration + Smart Polling — Requirements

## Overview

Migrate all frontend pages from manual `useState`/`useEffect` data fetching to TanStack Query v5 `useQuery`/`useMutation` hooks. Add a `DataRefreshProvider` for app-wide auto-update configuration. Zero backend changes required.

**Taskyn Spec Node**: `1eebfb03fc584c8abfe1c6a3bc6d88ed`
**Research**: `.claude/research/web-ui/frontend/auto-update-approaches.md`

---

## User Stories

### US-1: Query Hook Layer

As a developer, I need a set of custom query hooks that wrap TanStack Query so that pages don't call API functions directly, enabling caching, deduplication, and background refetch.

**Acceptance Criteria:**
- Custom hooks exist for each API domain: `useCompanies`, `useCompany`, `useProjects`, `useProject`, `useNodes`, `useNode`, `useNodeAncestors`, `useNodeDescendants`, `useDashboard`, `useActivity`, `useKanbanNodes`, `usePlannerData`, `useTrackerEntries`
- Each hook returns `{ data, isLoading, error, refetch }` (standard TanStack Query shape)
- Hooks accept filter parameters matching existing API signatures
- Query keys follow a consistent convention (e.g., `['companies']`, `['company', id]`, `['nodes', { project_id }]`)

### US-2: Mutation Hook Layer

As a developer, I need mutation hooks that wrap `useMutation` with proper cache invalidation so that creating, updating, or deleting an entity automatically refreshes all affected views.

**Acceptance Criteria:**
- Mutation hooks exist for each write operation: `useCreateCompany`, `useUpdateCompany`, `useDeleteCompany`, `useCreateProject`, `useUpdateProject`, `useDeleteProject`, `useCreateNode`, `useUpdateNode`, `useDeleteNode`, `useStartNode`, `useCompleteNode`, `useBlockNode`, `useCreateEdge`, `useDeleteEdge`, `useLogTime`, `useDeleteTimeEntry`
- Each mutation's `onSuccess` invalidates the correct query keys (e.g., `useCreateNode` invalidates `['nodes']`, `['dashboard']`, `['project', projectId]`)
- Mutations return `{ mutate, mutateAsync, isPending, error }` (standard TanStack shape)
- Toast notifications are triggered on success/error via `useToast` within the hooks

### US-3: Page Migration — DashboardPage

As a user, I want the dashboard to stay fresh automatically so that I see up-to-date stats without manually refreshing.

**Acceptance Criteria:**
- DashboardPage uses `useDashboard`, `useNodes({ status: 'in_progress' })`, `useActivity({ limit: 5 })`, `useProjects()` query hooks
- Dashboard data auto-refreshes every 60 seconds via `refetchInterval`
- Completing a task uses `useCompleteNode` mutation which invalidates dashboard + node queries
- All manual `useState`/`useCallback`/`useEffect` data-fetching code is removed
- Existing optimistic UI for task completion is preserved

### US-4: Page Migration — CompaniesPage

As a user, I want company data to update after I create, edit, or delete a company without a full page reload.

**Acceptance Criteria:**
- CompaniesPage uses `useCompanies({ includeStats: true })`, `useProjects({ include_stats: true })` query hooks
- CRUD operations use `useCreateCompany`, `useUpdateCompany`, `useDeleteCompany` mutation hooks
- After mutations, related queries are invalidated (not manually refetched)
- All manual `useState`/`useCallback`/`useEffect` data-fetching code is removed

### US-5: Page Migration — ProjectsPage

As a user, I want the projects list to update after creating a project without manual refresh.

**Acceptance Criteria:**
- ProjectsPage uses `useCompanies()`, `useProjects({ include_stats: true })` query hooks
- `useCreateProject` mutation invalidates `['projects']` and `['companies']` (stats change)
- Filter state (`selectedCompany`) remains local `useState` (UI-only state)
- All manual data-fetching code is removed

### US-6: Page Migration — ProjectDetailPage

As a user, I want the project detail view to refresh automatically when I add nodes or delete the project.

**Acceptance Criteria:**
- ProjectDetailPage uses `useProject(projectId)`, `useNodes({ project_id: projectId })`, `useCompany(companyId)` query hooks
- `useCreateNode` and `useDeleteProject` mutations invalidate the correct keys
- Tab state remains local `useState`
- All manual data-fetching code is removed

### US-7: Page Migration — NodeDetailPage

As a user, I want the node detail view to stay current when I start, complete, or add child nodes.

**Acceptance Criteria:**
- NodeDetailPage uses `useNode(nodeId)`, `useProject(projectId)`, `useCompany(companyId)`, `useNodeAncestors(nodeId)`, `useNodeDescendants(nodeId)` query hooks
- Workflow mutations (`useStartNode`, `useCompleteNode`) and CRUD mutations invalidate correct keys
- All manual data-fetching code is removed

### US-8: Page Migration — KanbanPage

As a user, I want the Kanban board to reflect drag-and-drop status changes with optimistic updates.

**Acceptance Criteria:**
- KanbanPage uses `useProjects()`, `useNodes({ project_id })` query hooks
- Drag-and-drop uses `useUpdateNode` with `onMutate` for optimistic cache update and `onError` rollback
- Dropping a card updates the cache immediately without waiting for server response
- All manual data-fetching code is removed

### US-9: Page Migration — PlannerPage

As a user, I want the planner tree view to update when I create nodes or change their status.

**Acceptance Criteria:**
- PlannerPage uses `useNodes({ project_id })`, `useEdges({ project_id })`, `useProjects()` query hooks
- `useCreateNode`, `useStartNode`, `useCompleteNode` mutations invalidate `['nodes']` and `['edges']`
- Tree building logic (`buildTree`) remains as a derived computation from query data
- All manual data-fetching code is removed

### US-10: Page Migration — TrackerPage

As a user, I want the time tracker to show new entries after I log or delete time.

**Acceptance Criteria:**
- TrackerPage uses `useNodes()` (for time entries) query hooks
- `useLogTime`, `useDeleteTimeEntry` mutations invalidate `['nodes']` and `['timer']`
- Date filtering/grouping remains as derived state
- All manual data-fetching code is removed

### US-11: DataRefreshProvider

As a developer, I need an app-wide provider that configures auto-refresh behavior so that all pages benefit from consistent polling and window-focus refetch.

**Acceptance Criteria:**
- `DataRefreshProvider` wraps the app (inside `QueryClientProvider`)
- Configures `refetchOnWindowFocus: true` globally (catch external changes when user returns)
- Provides context for pages to opt into selective `refetchInterval` (e.g., dashboard 60s, timer 1s)
- Exposes a `refreshAll()` function that invalidates all queries on demand
- Provider does NOT duplicate QueryClient defaults — it extends them with app-specific refresh logic

### US-12: TimerProvider Migration

As a user, I want the active timer to stay in sync automatically, using TanStack Query for the timer's API state while preserving the 1-second elapsed tick.

**Acceptance Criteria:**
- TimerProvider uses a `useQuery` internally for `timerApi.getCurrent()` with `refetchInterval: 1000` (1s)
- The `elapsed` counter continues to use `setInterval` for smooth UI updates between refetches
- `start()` and `stop()` use mutations that invalidate `['timer']`
- The provider's public interface (`activeTimer`, `elapsed`, `start`, `stop`, `refresh`) remains unchanged
- No breaking changes to existing `useTimer()` consumers

### US-13: Query Key Convention

As a developer, I need a centralized query key factory so that invalidation is consistent and typo-proof.

**Acceptance Criteria:**
- A `queryKeys` object is defined in a single file (e.g., `src/api/queryKeys.ts`)
- Keys follow the pattern: `queryKeys.companies.all()`, `queryKeys.companies.detail(id)`, `queryKeys.nodes.list(filters)`, etc.
- All query and mutation hooks use this factory — no raw string keys
- Invalidation uses key prefixes (e.g., invalidating `['companies']` invalidates both list and detail)
