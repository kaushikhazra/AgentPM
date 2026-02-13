# Spec-Driven V2 — Requirements

## User Stories

### US-01: Hierarchical Node Structure
**As a** project manager (AI or human),
**I want** a 5-level mandatory hierarchy (spec → requirement → design → implementation → task),
**So that** work is naturally grouped from feature-level thinking down to individual work items.

**Acceptance Criteria:**
- All 5 levels are distinct node types with their own status workflows
- Every level is mandatory — no skipping levels
- Parent enforcement: each node type can only parent under its designated level
- Time tracking only on `task` nodes; `actual_time` rolls up through the hierarchy

### US-02: Scoped Verification Nodes
**As a** project manager,
**I want** three distinct verification node types scoped to specific hierarchy levels,
**So that** verification has clear semantic meaning and cannot be misplaced.

**Acceptance Criteria:**
- `e2e_verification` can only parent under `requirement` (validates the requirement)
- `functional_verification` can only parent under `design` (validates the design)
- `unit_verification` can only parent under `implementation` (validates the implementation)
- All three share the same status workflow: `pending → in_progress → passed → failed`
- All three track time (timers allowed)

### US-03: Cascading Verification Failure
**As a** project manager,
**I want** verification failure to automatically cascade the parent node back to a rework/draft state,
**So that** the system enforces that failures are addressed before re-verification.

**Acceptance Criteria:**
- `unit_verification → failed` cascades `implementation → rework`
- `functional_verification → failed` cascades `design → rejected → draft`
- `e2e_verification → failed` cascades `requirement → rework`
- Verification cannot retry (`failed → pending`) until parent is back to its done/terminal state
- Cascade is system-enforced (automatic on status transition)

### US-04: Fix Work Creation on Failure
**As an** AI agent or human,
**I want** to create fix work at the appropriate level when verification fails,
**So that** there is a traceable history of original work and fix work.

**Acceptance Criteria:**
- Unit failure → new `task` under the same `implementation`
- Functional failure → update `design` notes → new `implementation` + `task` nodes
- E2E failure → update `requirement` if needed → new `design` → new `implementation` → new `task`
- Original work nodes remain intact (history preserved)
- Fix work is tracked separately (its own time entries)

### US-05: Time Tracking Rollup
**As a** project manager,
**I want** `actual_time` to roll up from time-tracked nodes through the full hierarchy,
**So that** I can see aggregate time at any level.

**Acceptance Criteria:**
- Time tracking (timers) allowed on: `task`, `e2e_verification`, `functional_verification`, `unit_verification`
- Time tracking NOT allowed on: `spec`, `requirement`, `design`, `implementation`
- `actual_time` on non-leaf nodes = own time entries + sum of children's `actual_time`
- Rollup propagates up the full parent chain to `spec`

### US-06: Backward-Compatible Migration
**As a** system maintainer,
**I want** existing projects using spec_driven methodology to be handled gracefully,
**So that** the upgrade doesn't break existing data.

**Acceptance Criteria:**
- Existing `spec_driven` projects with old node types continue to function or are migrated
- New projects created with `spec_driven` use the v2 hierarchy
- Migration path is documented
