# TanStack Query Migration + Smart Polling — Design

## Overview

This design migrates the Taskyn Web UI from manual `useState`/`useEffect` data fetching to TanStack Query v5, adding caching, deduplication, background refetch, and mutation-aware cache invalidation. A new `DataRefreshProvider` handles app-wide auto-update configuration.

**Taskyn Spec Node**: `1eebfb03fc584c8abfe1c6a3bc6d88ed`
**Research**: `.claude/research/web-ui/frontend/auto-update-approaches.md`

---

## Architecture

### Current State

```
Page Component
  ├── useState(data)
  ├── useState(loading)
  ├── useState(error)
  ├── useCallback(loadData) → apiModule.list()
  ├── useEffect → loadData()
  └── mutation → apiModule.create() → loadData()  (full refetch)
```

### Target State

```
Page Component
  ├── useCompanies() → { data, isLoading, error }     (cached, auto-refetch)
  ├── useCreateCompany() → { mutate, isPending }       (invalidates cache)
  └── UI-only useState (filters, tabs, modals)          (unchanged)
```

---

## File Structure

```
src/taskyn/web/frontend/src/
├── api/
│   ├── client.ts              # Existing — unchanged
│   ├── companies.ts           # Existing — unchanged
│   ├── projects.ts            # Existing — unchanged
│   ├── nodes.ts               # Existing — unchanged
│   ├── ... (other modules)    # Existing — unchanged
│   └── queryKeys.ts           # NEW — centralized key factory
├── hooks/
│   ├── queries/               # NEW — query hooks directory
│   │   ├── useCompanies.ts
│   │   ├── useProjects.ts
│   │   ├── useNodes.ts
│   │   ├── useDashboard.ts
│   │   ├── useActivity.ts
│   │   ├── useEdges.ts
│   │   ├── useMilestones.ts
│   │   ├── useTags.ts
│   │   ├── useSearch.ts
│   │   ├── useTimer.ts        # Query hook for timer API (used by TimerProvider)
│   │   └── index.ts           # Re-exports all query hooks
│   ├── mutations/             # NEW — mutation hooks directory
│   │   ├── useCompanyMutations.ts
│   │   ├── useProjectMutations.ts
│   │   ├── useNodeMutations.ts
│   │   ├── useEdgeMutations.ts
│   │   ├── useTimerMutations.ts
│   │   └── index.ts           # Re-exports all mutation hooks
│   ├── useAuth.ts             # Existing — unchanged
│   ├── useTheme.ts            # Existing — unchanged
│   ├── useToast.ts            # Existing — unchanged
│   ├── useModal.ts            # Existing — unchanged
│   └── useHotkeys.ts          # Existing — unchanged
├── providers/
│   ├── DataRefreshProvider.tsx # NEW — auto-update configuration
│   ├── AuthProvider.tsx        # Existing — unchanged
│   ├── ThemeProvider.tsx       # Existing — unchanged
│   ├── TimerProvider.tsx       # MODIFIED — uses query hook internally
│   ├── ModalProvider.tsx       # Existing — unchanged
│   └── ToastProvider.tsx       # Existing — unchanged
└── pages/                     # MODIFIED — all pages migrated
```

---

## Query Key Factory

Single source of truth for all cache keys. Enables consistent invalidation.

```typescript
// src/api/queryKeys.ts
export const queryKeys = {
  companies: {
    all: () => ['companies'] as const,
    lists: () => [...queryKeys.companies.all(), 'list'] as const,
    list: (filters?: { includeStats?: boolean }) =>
      [...queryKeys.companies.lists(), filters] as const,
    details: () => [...queryKeys.companies.all(), 'detail'] as const,
    detail: (id: string) => [...queryKeys.companies.details(), id] as const,
    stats: (id: string) => [...queryKeys.companies.all(), 'stats', id] as const,
  },
  projects: {
    all: () => ['projects'] as const,
    lists: () => [...queryKeys.projects.all(), 'list'] as const,
    list: (filters?: Record<string, unknown>) =>
      [...queryKeys.projects.lists(), filters] as const,
    details: () => [...queryKeys.projects.all(), 'detail'] as const,
    detail: (id: string) => [...queryKeys.projects.details(), id] as const,
    stats: (id: string) => [...queryKeys.projects.all(), 'stats', id] as const,
    methodology: (id: string) => [...queryKeys.projects.all(), 'methodology', id] as const,
  },
  nodes: {
    all: () => ['nodes'] as const,
    lists: () => [...queryKeys.nodes.all(), 'list'] as const,
    list: (filters?: Record<string, unknown>) =>
      [...queryKeys.nodes.lists(), filters] as const,
    details: () => [...queryKeys.nodes.all(), 'detail'] as const,
    detail: (id: string) => [...queryKeys.nodes.details(), id] as const,
    ancestors: (id: string) => [...queryKeys.nodes.all(), 'ancestors', id] as const,
    descendants: (id: string) => [...queryKeys.nodes.all(), 'descendants', id] as const,
    rollup: (id: string) => [...queryKeys.nodes.all(), 'rollup', id] as const,
  },
  edges: {
    all: () => ['edges'] as const,
    list: (filters?: Record<string, unknown>) =>
      [...queryKeys.edges.all(), 'list', filters] as const,
  },
  milestones: {
    all: () => ['milestones'] as const,
    list: (projectId: string, status?: string) =>
      [...queryKeys.milestones.all(), 'list', projectId, status] as const,
    detail: (id: string) => [...queryKeys.milestones.all(), 'detail', id] as const,
  },
  dashboard: {
    all: () => ['dashboard'] as const,
  },
  activity: {
    all: () => ['activity'] as const,
    list: (filters?: Record<string, unknown>) =>
      [...queryKeys.activity.all(), 'list', filters] as const,
  },
  timer: {
    all: () => ['timer'] as const,
    current: () => [...queryKeys.timer.all(), 'current'] as const,
  },
  tags: {
    all: () => ['tags'] as const,
    list: () => [...queryKeys.tags.all(), 'list'] as const,
    usage: (name: string) => [...queryKeys.tags.all(), 'usage', name] as const,
  },
  search: {
    all: () => ['search'] as const,
    results: (query: string, filters?: Record<string, unknown>) =>
      [...queryKeys.search.all(), query, filters] as const,
  },
};
```

**Invalidation pattern**: Invalidating `queryKeys.nodes.all()` (`['nodes']`) automatically invalidates all node lists, details, ancestors, descendants — because TanStack Query matches by prefix.

---

## Query Hook Pattern

Each domain gets a query hook file. Example for companies:

```typescript
// src/hooks/queries/useCompanies.ts
import { useQuery } from '@tanstack/react-query';
import { companiesApi } from '../../api/companies';
import { queryKeys } from '../../api/queryKeys';

export function useCompanies(includeStats?: boolean) {
  return useQuery({
    queryKey: queryKeys.companies.list({ includeStats }),
    queryFn: () => companiesApi.list(includeStats),
  });
}

export function useCompany(id: string) {
  return useQuery({
    queryKey: queryKeys.companies.detail(id),
    queryFn: () => companiesApi.get(id),
    enabled: !!id,
  });
}
```

**Conventions:**
- Hook names match the domain: `useCompanies` (list), `useCompany` (single)
- `enabled` guards prevent queries with missing IDs
- No `refetchInterval` by default — pages opt in via DataRefreshProvider or per-query override

---

## Mutation Hook Pattern

Grouped by domain. Each mutation declares its invalidation targets.

```typescript
// src/hooks/mutations/useCompanyMutations.ts
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { companiesApi } from '../../api/companies';
import { queryKeys } from '../../api/queryKeys';
import { useToast } from '../useToast';

export function useCreateCompany() {
  const queryClient = useQueryClient();
  const { addToast } = useToast();

  return useMutation({
    mutationFn: companiesApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.companies.all() });
      addToast('success', 'Company created');
    },
    onError: (err: Error) => {
      addToast('error', err.message);
    },
  });
}
```

**Conventions:**
- Mutation hooks call `useToast()` internally for success/error notifications
- `onSuccess` invalidates affected query keys — the cache handles the refetch
- Pages don't need to call `loadData()` or manage toast after mutations

---

## Invalidation Matrix

Which mutations invalidate which queries:

| Mutation | Invalidates |
|----------|-------------|
| `useCreateCompany` | `companies.all` |
| `useUpdateCompany` | `companies.all` |
| `useDeleteCompany` | `companies.all`, `projects.all` |
| `useCreateProject` | `projects.all`, `companies.all` (stats) |
| `useUpdateProject` | `projects.all` |
| `useDeleteProject` | `projects.all`, `companies.all` (stats) |
| `useCreateNode` | `nodes.all`, `dashboard.all`, `projects.all` (stats) |
| `useUpdateNode` | `nodes.all`, `dashboard.all` |
| `useDeleteNode` | `nodes.all`, `dashboard.all`, `projects.all` (stats) |
| `useStartNode` | `nodes.all`, `dashboard.all` |
| `useCompleteNode` | `nodes.all`, `dashboard.all`, `projects.all` (stats) |
| `useBlockNode` | `nodes.all`, `dashboard.all` |
| `useCreateEdge` | `edges.all`, `nodes.all` (ancestors/descendants) |
| `useDeleteEdge` | `edges.all`, `nodes.all` (ancestors/descendants) |
| `useLogTime` | `nodes.all`, `timer.all` |
| `useDeleteTimeEntry` | `nodes.all`, `timer.all` |
| `useStartTimer` | `timer.all` |
| `useStopTimer` | `timer.all`, `nodes.all` |

---

## DataRefreshProvider

Sits between `QueryClientProvider` and the rest of the app. Provides app-wide refresh controls.

```typescript
// src/providers/DataRefreshProvider.tsx
interface DataRefreshContextValue {
  refreshAll: () => void;
  isRefreshing: boolean;
}
```

**Responsibilities:**
- Exposes `refreshAll()` — invalidates all queries (useful for manual refresh button, reconnect events)
- Exposes `isRefreshing` — true while any query is fetching after invalidation
- Does NOT own `refetchInterval` — individual pages/hooks set that per their needs

**Provider hierarchy update:**

```
QueryClientProvider
  DataRefreshProvider       ← NEW
    ThemeProvider
      AuthProvider
        TimerProvider       ← MODIFIED (uses query hook internally)
          ModalProvider
            ToastProvider
              RouterProvider
```

---

## QueryClient Configuration Update

```typescript
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,           // 30s — existing
      retry: 1,                     // existing
      refetchOnWindowFocus: true,   // catch external changes (default, explicit)
      refetchOnReconnect: true,     // refetch after network recovery
    },
  },
});
```

No aggressive global `refetchInterval`. Pages opt in:
- **DashboardPage**: `refetchInterval: 60_000` (60s)
- **TimerProvider**: `refetchInterval: 1_000` (1s) for active timer query
- **All others**: No interval — rely on stale time + window focus + mutation invalidation

---

## TimerProvider Migration

The most nuanced migration. TimerProvider currently manages its own API calls and a `setInterval` for elapsed time.

**Strategy:** Use a query hook for the API state, keep the `setInterval` for smooth elapsed counter.

```
TimerProvider
  ├── useQuery(timer.current, refetchInterval: 1000)  ← replaces manual API polling
  ├── setInterval(updateElapsed, 1000)                  ← stays for smooth UI
  ├── useStartTimer mutation                             ← replaces direct API call
  └── useStopTimer mutation                              ← replaces direct API call
```

**Public interface unchanged** — `useTimer()` consumers see no difference.

---

## Optimistic Updates (KanbanPage)

KanbanPage drag-and-drop needs instant visual feedback. Uses TanStack Query's built-in optimistic update pattern:

```typescript
const updateNode = useMutation({
  mutationFn: ({ id, data }) => nodesApi.update(id, data),
  onMutate: async ({ id, data }) => {
    await queryClient.cancelQueries({ queryKey: queryKeys.nodes.list({ project_id }) });
    const previous = queryClient.getQueryData(queryKeys.nodes.list({ project_id }));
    queryClient.setQueryData(queryKeys.nodes.list({ project_id }), (old) =>
      old?.map(n => n.id === id ? { ...n, ...data } : n)
    );
    return { previous };
  },
  onError: (_err, _vars, context) => {
    queryClient.setQueryData(queryKeys.nodes.list({ project_id }), context?.previous);
    addToast('error', 'Failed to update status');
  },
  onSettled: () => {
    queryClient.invalidateQueries({ queryKey: queryKeys.nodes.all() });
  },
});
```

---

## Page Migration Pattern

Each page migration follows the same steps:

1. **Replace data `useState`** with `useQuery` hooks (loading, error, data come from the hook)
2. **Replace mutation callbacks** with `useMutation` hooks (no manual `loadData()` call)
3. **Keep UI-only `useState`** — filters, tabs, modals, form fields stay as local state
4. **Remove `useCallback(loadData)`** and the `useEffect` that calls it
5. **Remove manual toast calls** after mutations (moved into mutation hooks)
6. **Test** that caching, invalidation, and refetch work correctly

---

## What Does NOT Change

- **API modules** (`src/api/*.ts`) — raw functions stay as-is, query hooks wrap them
- **API client** (`src/api/client.ts`) — token management, error handling unchanged
- **AuthProvider** — keeps its own auth flow (not query-based, handles tokens)
- **ThemeProvider, ModalProvider, ToastProvider** — no API calls, unchanged
- **Component structure** — pages keep their JSX, only data-fetching layer changes
- **Backend** — zero changes to FastAPI or MCP server
