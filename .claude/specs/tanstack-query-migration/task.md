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

- [ ] Create mutation hooks directory (`src/hooks/mutations/`)
  _US-2_

- [ ] Implement company mutation hooks (`useCompanyMutations.ts`)
  - [ ] `useCreateCompany` — invalidates `companies.all`
  - [ ] `useUpdateCompany` — invalidates `companies.all`
  - [ ] `useDeleteCompany` — invalidates `companies.all`, `projects.all`
  _US-2_

- [ ] Implement project mutation hooks (`useProjectMutations.ts`)
  - [ ] `useCreateProject` — invalidates `projects.all`, `companies.all`
  - [ ] `useUpdateProject` — invalidates `projects.all`
  - [ ] `useDeleteProject` — invalidates `projects.all`, `companies.all`
  _US-2_

- [ ] Implement node mutation hooks (`useNodeMutations.ts`)
  - [ ] `useCreateNode` — invalidates `nodes.all`, `dashboard.all`, `projects.all`
  - [ ] `useUpdateNode` — invalidates `nodes.all`, `dashboard.all` (with optimistic update support)
  - [ ] `useDeleteNode` — invalidates `nodes.all`, `dashboard.all`, `projects.all`
  - [ ] `useStartNode` — invalidates `nodes.all`, `dashboard.all`
  - [ ] `useCompleteNode` — invalidates `nodes.all`, `dashboard.all`, `projects.all`
  - [ ] `useBlockNode` — invalidates `nodes.all`, `dashboard.all`
  _US-2_

- [ ] Implement edge mutation hooks (`useEdgeMutations.ts`)
  - [ ] `useCreateEdge` — invalidates `edges.all`, `nodes.all`
  - [ ] `useDeleteEdge` — invalidates `edges.all`, `nodes.all`
  _US-2_

- [ ] Implement timer mutation hooks (`useTimerMutations.ts`)
  - [ ] `useStartTimer` — invalidates `timer.all`
  - [ ] `useStopTimer` — invalidates `timer.all`, `nodes.all`
  - [ ] `useLogTime` — invalidates `nodes.all`, `timer.all`
  - [ ] `useDeleteTimeEntry` — invalidates `nodes.all`, `timer.all`
  _US-2_

- [ ] Create mutation hooks barrel export (`src/hooks/mutations/index.ts`)
  _US-2_

## DataRefreshProvider

- [ ] Create DataRefreshProvider (`src/providers/DataRefreshProvider.tsx`)
  - [ ] Expose `refreshAll()` — invalidates all queries
  - [ ] Expose `isRefreshing` — true while queries are refetching
  - [ ] Create `useDataRefresh()` hook
  _US-11_

- [ ] Wire DataRefreshProvider into App.tsx provider hierarchy
  - [ ] Place between QueryClientProvider and ThemeProvider
  _US-11_

## TimerProvider Migration

- [ ] Migrate TimerProvider to use query hook internally
  - [ ] Replace manual `timerApi.getCurrent()` with `useTimerCurrent()` query hook
  - [ ] Replace manual `timerApi.start()` / `timerApi.stop()` with mutation hooks
  - [ ] Keep `setInterval` for smooth elapsed counter
  - [ ] Verify public interface (`useTimer()`) is unchanged
  _US-12_

## Page Migrations

- [ ] Migrate DashboardPage
  - [ ] Replace useState/useEffect with `useDashboard`, `useNodes`, `useActivity`, `useProjects`
  - [ ] Add `refetchInterval: 60_000` to dashboard query
  - [ ] Replace task completion with `useCompleteNode` mutation
  - [ ] Preserve optimistic completion UI
  - [ ] Remove manual `loadData` callback
  _US-3_

- [ ] Migrate CompaniesPage
  - [ ] Replace useState/useEffect with `useCompanies`, `useProjects`
  - [ ] Replace CRUD with `useCreateCompany`, `useUpdateCompany`, `useDeleteCompany`
  - [ ] Remove manual `loadData` callback and toast calls after mutations
  _US-4_

- [ ] Migrate ProjectsPage
  - [ ] Replace useState/useEffect with `useCompanies`, `useProjects`
  - [ ] Replace create with `useCreateProject`
  - [ ] Keep filter `useState` as local UI state
  - [ ] Remove manual `loadData` callback
  _US-5_

- [ ] Migrate ProjectDetailPage
  - [ ] Replace useState/useEffect with `useProject`, `useNodes`, `useCompany`
  - [ ] Replace mutations with `useCreateNode`, `useDeleteProject`
  - [ ] Keep tab `useState` as local UI state
  - [ ] Remove manual `loadData` callback
  _US-6_

- [ ] Migrate NodeDetailPage
  - [ ] Replace useState/useEffect with `useNode`, `useProject`, `useCompany`, `useNodeAncestors`, `useNodeDescendants`
  - [ ] Replace mutations with `useStartNode`, `useCompleteNode`, `useCreateNode`, `useDeleteNode`
  - [ ] Remove manual `loadData` callback
  _US-7_

- [ ] Migrate KanbanPage
  - [ ] Replace useState/useEffect with `useProjects`, `useNodes`
  - [ ] Implement optimistic drag-and-drop with `useUpdateNode` (`onMutate`/`onError`/`onSettled`)
  - [ ] Remove manual state management for drag/drop
  _US-8_

- [ ] Migrate PlannerPage
  - [ ] Replace useState/useEffect with `useProjects`, `useNodes`, `useEdges`
  - [ ] Replace mutations with `useCreateNode`, `useStartNode`, `useCompleteNode`
  - [ ] Keep `buildTree` as derived computation from query data
  - [ ] Remove manual `loadData` callback
  _US-9_

- [ ] Migrate TrackerPage
  - [ ] Replace useState/useEffect with `useNodes`
  - [ ] Replace mutations with `useLogTime`, `useDeleteTimeEntry`
  - [ ] Keep date filtering as derived state
  - [ ] Remove manual `loadData` callback
  _US-10_
