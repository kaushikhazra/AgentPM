# Spec-Driven Methodology v3 — Tasks

## 1. Backend: Methodology Implementation

- [x] Update `src/taskyn/methodologies/spec_driven.py` with 5 node types (spec, requirement, design, task, todo)
  - [x] Phase nodes (spec, requirement, design, task): statuses `draft → active → done, cancelled`
  - [x] Todo nodes: statuses `todo → in_progress → done, cancelled`
  - [x] `can_track_time = True` only on todo
  - [x] `valid_parent_pairs`: requirement→spec, design→spec, task→spec, todo→requirement/design/task
  - [x] Edge types: parent, depends_on, blocks
  - [x] Helper methods: `get_story_type()` → spec, `get_task_type()` → todo, `get_in_progress_status()`, `get_done_status()`
  _Design: hierarchy section, statuses section_

## 2. Backend: Strict Gating Logic

- [x] Implement phase gating in workflow/validation layer
  - [x] Requirement can go `active` only when parent Spec is `active` or `done`
  - [x] Design can go `active` only when ALL sibling Requirements under same Spec are `done`
  - [x] Task can go `active` only when ALL sibling Designs under same Spec are `done`
  - [x] Todo can start (`in_progress`) only when parent phase is `active` or `done`
  - [x] Return clear validation error messages when gating blocks a transition
  _Design: strict gating section_

## 3. Backend: Update Cascade Logic

- [x] Update `src/taskyn/core/cascade.py` for v3 (remove v2 verification cascade, simplify)
  - [x] Remove verification-failure cascade logic (no more verification nodes)
  - [x] Remove re-verification gating logic
  _Design: comparison v2 → v3_

## 4. Backend: Register Methodology

- [x] Register `spec_driven` name to point to v3 class (replaces v2)
  - [x] Check methodology registry/factory for how methodologies are resolved
  - [x] Ensure existing `spec_driven` projects use v3 going forward
  _Design: methodology name stays `spec_driven`_

## 5. Backend: Database Migration

- [ ] Write migration for existing spec_driven projects
  - [ ] Map v2 node types to v3: implementation → task, task(v2) → todo, verification nodes → todo
  - [ ] Map v2 statuses to v3 universal statuses
  - [ ] Handle edge/parent relationships that change due to hierarchy flattening
  _Requirement: key requirement #1, #2_

## 6. Backend: Unit Tests

- [x] Updated `tests/test_spec_driven.py` (32 tests)
  - [x] Test all 5 node type definitions and status workflows
  - [x] Test all valid parent-child pairs (positive and negative)
  - [x] Test strict gating: requirement→design→task phase gates
  - [x] Test gating error messages are clear
  - [x] Test time tracking only on todo nodes
  - [x] Test helper methods (get_story_type, get_task_type, etc.)
  - [x] Run tests and verify all pass (32/32 pass, 0 regressions)
  _Design: all sections_

## 7. Frontend: Update Methodology UI Config

- [x] Update `web/src/config/methodology-ui.ts`
  - [x] Add v3 node type definitions (spec, requirement, design, task, todo) with icons, colors, display names
  - [x] Update hierarchy mapping for v3 (spec→[requirement,design,task], all→todo)
  - [x] Update status labels for universal statuses (draft, active, done, cancelled, todo, in_progress)
  - [x] Remove v2 verification node type UI config
  - [x] Add `getChildTypes()` for multi-child parent support
  _Design: hierarchy section, statuses section_

## 8. Frontend: Update All Pages

- [x] Update `NodeDetailPage.tsx`
  - [x] Multi-child type support (type selector in create modal for spec nodes)
  - [x] Action buttons for universal statuses (draft/todo→start, active/in_progress→complete)
  - [x] Remove `approved` status references
  - [x] Add `active`, `todo`, `cancelled` status handling
- [x] Update `ProjectDetailPage.tsx`
  - [x] Remove `approved` status references
  - [x] Add v3 status class handling
- [x] Update `PlannerPage.tsx`
  - [x] Remove `approved` status references
  - [x] Add v3 status class handling
- [x] Update `KanbanPage.tsx`
  - [x] Add `active`, `todo`, `cancelled` status colors
- [x] Update `ProjectsPage.tsx`
  - [x] Replace hardcoded `['epic', 'story', 'task']` with methodology-aware node types
  _Design: gating section, UI implications_

## 9. Integration: API Validation Tests

- [x] Test methodology via REST API (Docker deployment)
  - [x] Create a company and project with spec_driven methodology
  - [x] Create spec → requirement → design → task hierarchy
  - [x] Create todos under requirement, design, and task
  - [x] Verify gating: attempt to activate design before requirement is done → BLOCKED
  - [x] Verify gating: attempt to activate task before design is done → BLOCKED
  - [x] Verify gating: complete requirement → design can now activate → SUCCESS
  - [x] Track time on todos: start timer, complete node → timer auto-stops
  - [x] Verify time rolls up through hierarchy (2m 41s visible on parent)
  - [x] Verify phase nodes reject timer start → BLOCKED
  _Design: full design doc, strict gating section_

## 10. E2E: Docker Deploy + Puppeteer Test

- [x] Deploy to Docker and run Puppeteer E2E tests
  - [x] `docker compose up --build -d` — both containers healthy
  - [x] Create company → create spec_driven project → create full hierarchy
  - [x] Walk through the gated workflow: draft→active→done on phases in order
  - [x] Verify gating feedback (API returns clear error messages)
  - [x] Verify time tracking on todos (timer starts/stops correctly)
  - [x] ProjectsPage: methodology-aware stats (specs/requirements/designs vs epics/stories/tasks)
  - [x] ProjectDetailPage: stats, status badges, child type labels all correct
  - [x] NodeDetailPage: multi-child type selector for specs, single-child "New Todo" for phases
  - [x] PlannerPage: 3-level hierarchy renders correctly, status badges, expand/collapse
  - [x] KanbanPage: all v3 status columns display correctly with proper colors
  - [x] Classic Agile regression: Learning project renders correctly (no regressions)
  _User verification scenario_

## 11. Backend: Workflow Fix (discovered during E2E)

- [x] Fix `start_node` in `workflow.py` to skip timer on phase nodes
  - [x] `start_node` was unconditionally calling `start_timer` — fails on `can_track_time=False` nodes
  - [x] Now checks `node_type_def.can_track_time` before starting timer
  - [x] All 45 tests pass (32 spec_driven + 13 workflow)
