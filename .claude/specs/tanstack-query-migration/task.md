# TanStack Query Migration + Smart Polling — Tasks

**Taskyn Spec Node**: `1eebfb03fc584c8abfe1c6a3bc6d88ed`

---

## Foundation

- [x] Create query key factory (`src/api/queryKeys.ts`)
  - [x] Define keys for all domains: companies, projects, nodes, edges, milestones, dashboard, activity, timer, tags, search
  - [x] Export single `queryKeys` object with hierarchical key builders
  _US-13_

- [x] Update QueryClient configuration in App.tsx
  - [x] Set `refetchOnWindowFocus: true` explicitly
  - [x] Set `refetchOnReconnect: true`
  - [x] Keep existing `staleTime: 30_000` and `retry: 1`
  _US-11_

## Query Hooks

- [x] Create query hooks directory (`src/hooks/queries/`)
  _US-1_

- [x] Implement company query hooks (`useCompanies.ts`)
  - [x] `useCompanies(includeStats?)` — list with optional stats
  - [x] `useCompany(id)` — single company by ID
  _US-1_

- [x] Implement project query hooks (`useProjects.ts`)
  - [x] `useProjects(filters?)` — list with optional filters
  - [x] `useProject(id)` — single project by ID
  - [x] `useProjectMethodology(id)` — methodology info
  _US-1_

- [x] Implement node query hooks (`useNodes.ts`)
  - [x] `useNodes(filters?)` — list with optional filters
  - [x] `useNode(id)` — single node by ID
  - [x] `useNodeAncestors(id)` — ancestor nodes
  - [x] `useNodeDescendants(id)` — descendant nodes
  _US-1_

- [x] Implement edge query hooks (`useEdges.ts`)
  - [x] `useEdges(filters?)` — list with optional filters
  _US-1_

- [x] Implement dashboard query hook (`useDashboard.ts`)
  - [x] `useDashboard()` — dashboard summary
  _US-1_

- [x] Implement activity query hook (`useActivity.ts`)
  - [x] `useActivity(filters?)` — activity list
  _US-1_

- [x] Implement timer query hook (`useTimerQuery.ts`)
  - [x] `useTimerCurrent()` — active timer with `refetchInterval: 1000`
  _US-1, US-12_

- [x] Create query hooks barrel export (`src/hooks/queries/index.ts`)
  _US-1_

## Mutation Hooks

- [x] Create mutation hooks directory (`src/hooks/mutations/`)
  _US-2_

- [x] Implement company mutation hooks (`useCompanyMutations.ts`)
  - [x] `useCreateCompany` — invalidates `companies.all`
  - [x] `useUpdateCompany` — invalidates `companies.all`
  - [x] `useDeleteCompany` — invalidates `companies.all`, `projects.all`
  _US-2_

- [x] Implement project mutation hooks (`useProjectMutations.ts`)
  - [x] `useCreateProject` — invalidates `projects.all`, `companies.all`
  - [x] `useUpdateProject` — invalidates `projects.all`
  - [x] `useDeleteProject` — invalidates `projects.all`, `companies.all`
  _US-2_

- [x] Implement node mutation hooks (`useNodeMutations.ts`)
  - [x] `useCreateNode` — invalidates `nodes.all`, `dashboard.all`, `projects.all`
  - [x] `useUpdateNode` — invalidates `nodes.all`, `dashboard.all` (with optimistic update support)
  - [x] `useDeleteNode` — invalidates `nodes.all`, `dashboard.all`, `projects.all`
  - [x] `useStartNode` — invalidates `nodes.all`, `dashboard.all`
  - [x] `useCompleteNode` — invalidates `nodes.all`, `dashboard.all`, `projects.all`
  - [x] `useBlockNode` — invalidates `nodes.all`, `dashboard.all`
  _US-2_

- [x] Implement edge mutation hooks (`useEdgeMutations.ts`)
  - [x] `useCreateEdge` — invalidates `edges.all`, `nodes.all`
  - [x] `useDeleteEdge` — invalidates `edges.all`, `nodes.all`
  _US-2_

- [x] Implement timer mutation hooks (`useTimerMutations.ts`)
  - [x] `useStartTimer` — invalidates `timer.all`
  - [x] `useStopTimer` — invalidates `timer.all`, `nodes.all`
  - [x] `useLogTime` — invalidates `nodes.all`, `timer.all`
  - [x] `useDeleteTimeEntry` — invalidates `nodes.all`, `timer.all`
  _US-2_

- [x] Create mutation hooks barrel export (`src/hooks/mutations/index.ts`)
  _US-2_

## DataRefreshProvider

- [x] Create DataRefreshProvider (`src/providers/DataRefreshProvider.tsx`)
  - [x] Expose `refreshAll()` — invalidates all queries
  - [x] Expose `isRefreshing` — true while queries are refetching
  - [x] Create `useDataRefresh()` hook
  _US-11_

- [x] Wire DataRefreshProvider into App.tsx provider hierarchy
  - [x] Place between QueryClientProvider and ThemeProvider
  _US-11_

## TimerProvider Migration

- [x] Migrate TimerProvider to use query hook internally
  - [x] Replace manual `timerApi.getCurrent()` with `useTimerCurrent()` query hook
  - [x] Replace manual `timerApi.start()` / `timerApi.stop()` with query invalidation
  - [x] Keep `setInterval` for smooth elapsed counter
  - [x] Verify public interface (`useTimer()`) is unchanged
  _US-12_

## Page Migrations

- [x] Migrate DashboardPage
  - [x] Replace useState/useEffect with `useDashboard`, `useNodes`, `useActivity`, `useProjects`
  - [x] Add `refetchInterval: 60_000` to dashboard query
  - [x] Replace task completion with `useCompleteNode` mutation
  - [x] Preserve optimistic completion UI
  - [x] Remove manual `loadData` callback
  _US-3_

- [x] Migrate CompaniesPage
  - [x] Replace useState/useEffect with `useCompanies`, `useProjects`
  - [x] Replace CRUD with `useCreateCompany`, `useUpdateCompany`, `useDeleteCompany`
  - [x] Remove manual `loadData` callback and toast calls after mutations
  _US-4_

- [x] Migrate ProjectsPage
  - [x] Replace useState/useEffect with `useCompanies`, `useProjects`
  - [x] Replace create with `useCreateProject`
  - [x] Keep filter `useState` as local UI state
  - [x] Remove manual `loadData` callback
  _US-5_

- [x] Migrate ProjectDetailPage
  - [x] Replace useState/useEffect with `useProject`, `useNodes`, `useCompany`
  - [x] Replace mutations with `useCreateNode`, `useDeleteProject`
  - [x] Keep tab `useState` as local UI state
  - [x] Remove manual `loadData` callback
  _US-6_

- [x] Migrate NodeDetailPage
  - [x] Replace useState/useEffect with `useNode`, `useProject`, `useCompany`, `useNodeAncestors`, `useNodeDescendants`
  - [x] Replace mutations with `useStartNode`, `useCompleteNode`, `useCreateNode`, `useDeleteNode`
  - [x] Remove manual `loadData` callback
  _US-7_

- [x] Migrate KanbanPage
  - [x] Replace useState/useEffect with `useProjects`, `useNodes`
  - [x] Implement optimistic drag-and-drop with `useOptimisticUpdateNode` (`onMutate`/`onError`/`onSettled`)
  - [x] Remove manual state management for drag/drop
  _US-8_

- [x] Migrate PlannerPage
  - [x] Replace useState/useEffect with `useProjects`, `useNodes`, `useEdges`
  - [x] Replace mutations with `useCreateNode`, `useStartNode`, `useCompleteNode`
  - [x] Keep `buildTree` as derived computation from query data
  - [x] Remove manual `loadData` callback
  _US-9_

- [x] Migrate TrackerPage
  - [x] Replace useState/useEffect with `useNodes`
  - [x] Replace mutations with `useLogTime`, `useDeleteTimeEntry`
  - [x] Keep date filtering as derived state
  - [x] Remove manual `loadData` callback
  _US-10_
