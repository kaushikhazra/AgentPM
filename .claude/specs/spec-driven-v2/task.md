# Spec-Driven V2 — Tasks

## 1. Methodology Definition
- [x] Rewrite `spec_driven.py` with all 8 node types and their status workflows
  - [x] `spec`: draft → approved → in_progress → done | cancelled
  - [x] `requirement`: draft → approved → in_progress → done, with rework loop
  - [x] `design`: draft → in_review → approved, with rejected → draft loop
  - [x] `implementation`: todo → in_progress → in_review → done, with rework loop
  - [x] `task`: todo → in_progress → done
  - [x] `e2e_verification`: pending → in_progress → passed | failed, with retry
  - [x] `functional_verification`: same as e2e
  - [x] `unit_verification`: same as e2e
  - [x] Set `can_track_time=False` for spec, requirement, design, implementation
  - [x] Set `can_track_time=True` for task, e2e/functional/unit verification
  _US-01, US-02, US-05_

- [x] Update edge types: parent (with strict pairs), depends_on, blocks; remove gates/validates
  _US-01, US-02_

- [x] Update helper methods: `get_story_type`, `get_task_type`, `get_in_progress_status`, `get_done_status`
  _US-01_

## 2. Parent Pair Validation
- [x] Add `valid_parent_pairs` property to `BaseMethodology` (default empty dict)
  _US-01, US-02_

- [x] Implement pair validation in `spec_driven.py`: child_type → [allowed_parent_types]
  _US-01, US-02_

- [x] Update `validate_edge()` in `base.py` to check `valid_parent_pairs` for parent edges
  _US-01, US-02_

- [x] Update `validate_edge_creation()` in `validation.py` if needed (no change needed — delegates to validate_edge)
  _US-01, US-02_

## 3. Verification Cascade
- [x] Create `src/taskyn/core/cascade.py` with cascade logic
  - [x] `on_status_changed(node_id)` — find parent, cascade status back
  - [x] `validate_reverification(node_id)` — check parent is in terminal state
  _US-03_

- [x] Add post-transition hook in `update_node()` (nodes.py) to call cascade on verification failure
  _US-03_

- [x] Add pre-transition check in `validate_node_update()` (validation.py) to gate re-verification
  _US-03_

## 4. Time Tracking Enforcement
- [x] Add `can_track_time` check in `start_timer()` — reject if node type disallows it
  _US-05_

- [x] Add `can_track_time` check in `log_time()` — reject if node type disallows it
  _US-05_

- [x] Verify `propagate_actual_time()` works with 5-level hierarchy (no code change needed)
  _US-05_

## 5. MCP Server Updates
- [x] Update `pm_get_methodology_info` to expose `valid_parent_pairs` and `can_track_time` per node type
  _US-01_

## 6. Tests
- [x] Test all 8 node type status workflows (valid transitions and rejections)
  _US-01, US-02_

- [x] Test parent pair validation (valid and invalid parent combinations)
  _US-01, US-02_

- [x] Test verification cascade (unit/functional/e2e failure → parent rework)
  _US-03_

- [x] Test re-verification gating (cannot retry until parent is terminal)
  _US-03_

- [x] Test time tracking enforcement (rejected on non-trackable nodes, allowed on trackable)
  _US-05_

- [x] Test actual_time rollup through 5-level hierarchy (covered by existing propagate_actual_time tests)
  _US-05_

## 7. Migration
- [x] Handle existing projects: update in place, no old nodes exist (project has 0 nodes)
  _US-06_
