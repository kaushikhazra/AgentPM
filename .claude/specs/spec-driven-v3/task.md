# Spec-Driven Methodology v3 — Tasks

## 1. Backend: Methodology Implementation

- [ ] Create `src/taskyn/methodologies/spec_driven_v3.py` with 5 node types (spec, requirement, design, task, todo)
  - [ ] Phase nodes (spec, requirement, design, task): statuses `draft → active → done, cancelled`
  - [ ] Todo nodes: statuses `todo → in_progress → done, cancelled`
  - [ ] `can_track_time = True` only on todo
  - [ ] `valid_parent_pairs`: requirement→spec, design→spec, task→spec, todo→requirement/design/task
  - [ ] Edge types: parent, depends_on, blocks
  - [ ] Helper methods: `get_story_type()` → spec, `get_task_type()` → todo, `get_in_progress_status()`, `get_done_status()`
  _Design: hierarchy section, statuses section_

## 2. Backend: Strict Gating Logic

- [ ] Implement phase gating in workflow/validation layer
  - [ ] Requirement can go `active` only when parent Spec is `active` or `done`
  - [ ] Design can go `active` only when ALL sibling Requirements under same Spec are `done`
  - [ ] Task can go `active` only when ALL sibling Designs under same Spec are `done`
  - [ ] Todo can start (`in_progress`) only when parent phase is `active` or `done`
  - [ ] Return clear validation error messages when gating blocks a transition
  _Design: strict gating section_

## 3. Backend: Update Cascade Logic

- [ ] Update `src/taskyn/core/cascade.py` for v3 (remove v2 verification cascade, simplify)
  - [ ] Remove verification-failure cascade logic (no more verification nodes)
  - [ ] Remove re-verification gating logic
  _Design: comparison v2 → v3_

## 4. Backend: Register Methodology

- [ ] Register `spec_driven` name to point to v3 class (replaces v2)
  - [ ] Check methodology registry/factory for how methodologies are resolved
  - [ ] Ensure existing `spec_driven` projects use v3 going forward
  _Design: methodology name stays `spec_driven`_

## 5. Backend: Database Migration

- [ ] Write migration for existing spec_driven projects
  - [ ] Map v2 node types to v3: implementation → task, task(v2) → todo, verification nodes → todo
  - [ ] Map v2 statuses to v3 universal statuses
  - [ ] Handle edge/parent relationships that change due to hierarchy flattening
  _Requirement: key requirement #1, #2_

## 6. Backend: Unit Tests

- [ ] Create `tests/test_spec_driven_v3.py`
  - [ ] Test all 5 node type definitions and status workflows
  - [ ] Test all valid parent-child pairs (positive and negative)
  - [ ] Test strict gating: requirement→design→task phase gates
  - [ ] Test gating error messages are clear
  - [ ] Test time tracking only on todo nodes
  - [ ] Test helper methods (get_story_type, get_task_type, etc.)
  - [ ] Run tests and verify all pass
  _Design: all sections_

## 7. Frontend: Update Methodology UI Config

- [ ] Update `web/src/config/methodology-ui.ts`
  - [ ] Add v3 node type definitions (spec, requirement, design, task, todo) with icons, colors, display names
  - [ ] Update hierarchy mapping for v3 (spec→requirement/design/task, all→todo)
  - [ ] Update status labels for universal statuses (draft, active, done, cancelled, todo, in_progress)
  - [ ] Remove v2 verification node type UI config
  _Design: hierarchy section, statuses section_

## 8. Frontend: Update Node Detail Page

- [ ] Update `web/src/pages/NodeDetailPage.tsx` and related components
  - [ ] Action buttons for universal statuses (draft→active→done)
  - [ ] Todo start/stop timer actions
  - [ ] "New Todo" button on requirement, design, and task nodes
  - [ ] Gating feedback: show why a phase can't be activated (e.g., "Requirements not complete")
  _Design: gating section, UI implications_

## 9. Integration: MCP Validation Tests

- [ ] Test methodology via MCP tools (autonomous verification)
  - [ ] Create a company and project with spec_driven methodology
  - [ ] Create spec → requirement → design → task hierarchy
  - [ ] Create todos under requirement, design, and task
  - [ ] Verify gating: attempt to activate design before requirement is done → expect rejection
  - [ ] Verify gating: attempt to activate task before design is done → expect rejection
  - [ ] Verify gating: complete requirement → design can now activate
  - [ ] Track time on todos: start timer, stop timer, verify actual_time
  - [ ] Verify time rolls up through hierarchy
  - [ ] Verify invalid node types are rejected
  - [ ] Verify invalid parent-child pairs are rejected
  _Design: full design doc, strict gating section_

## 10. E2E: Docker Deploy + Puppeteer Test

- [ ] Deploy to Docker and run Puppeteer E2E tests
  - [ ] `docker compose up --build -d`
  - [ ] Create company → create spec_driven project
  - [ ] Create full hierarchy: spec with requirements, designs, tasks, todos
  - [ ] Walk through the gated workflow: draft→active on each phase in order
  - [ ] Attempt out-of-order activation → verify UI shows gating feedback
  - [ ] Track time on todos → verify timer and rollup display
  - [ ] Verify all node types render correctly with proper icons/colors/statuses
  _User verification scenario_
