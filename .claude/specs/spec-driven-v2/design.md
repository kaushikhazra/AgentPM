# Spec-Driven V2 — Design

## 1. Node Type Definitions

### 8 Node Types

| Node Type | Initial Status | Terminal Statuses | Time Tracked | Parents Under |
|-----------|---------------|-------------------|--------------|---------------|
| `spec` | `draft` | `done`, `cancelled` | No | (root) |
| `requirement` | `draft` | `done` | No | `spec` |
| `design` | `draft` | `approved` | No | `requirement` |
| `implementation` | `todo` | `done` | No | `design` |
| `task` | `todo` | `done` | **Yes** | `implementation` |
| `e2e_verification` | `pending` | `passed` | **Yes** | `requirement` |
| `functional_verification` | `pending` | `passed` | **Yes** | `design` |
| `unit_verification` | `pending` | `passed` | **Yes** | `implementation` |

### Status Workflows

**spec:**
```
draft → approved → in_progress → done
draft → cancelled
approved → draft (rethink)
approved → cancelled
in_progress → done
in_progress → cancelled
```

**requirement:**
```
draft → approved → in_progress → done
approved → draft (rethink)
in_progress → rework (on e2e failure)
rework → in_progress
in_progress → done
```

**design:**
```
draft → in_review → approved
in_review → rejected
rejected → draft (rework)
approved → rejected (on functional_verification failure — cascaded back to draft via rejected)
```

Note on cascade: when `functional_verification` fails, `design` goes `approved → rejected → draft` (two-step automatic cascade).

**implementation:**
```
todo → in_progress → in_review → done
in_review → rework (on unit failure or code review)
rework → in_progress
```

**task:**
```
todo → in_progress → done
```

**All verification types (e2e, functional, unit):**
```
pending → in_progress → passed
pending → in_progress → failed
failed → pending (retry — GATED: only when parent is back to terminal state)
```

## 2. Edge Type Definitions

### Parent Edges (strict hierarchy enforcement)

The `parent` edge enforces the hierarchy. Each node type can only parent under specific types:

```python
"parent": EdgeTypeDefinition(
    name="parent",
    source_types=[
        "requirement", "design", "implementation", "task",
        "e2e_verification", "functional_verification", "unit_verification",
    ],
    target_types=["spec", "requirement", "design", "implementation"],
    max_per_source=1,
    allows_cycles=False,
)
```

**But this alone isn't enough** — we need pair-level validation. The base `EdgeTypeDefinition` validates source and target types independently. We need a new mechanism to enforce that `task` can ONLY parent under `implementation`, not under `spec`.

#### Approach: `valid_parent_pairs` on the methodology

Add a new property to `BaseMethodology`:

```python
@property
def valid_parent_pairs(self) -> dict[str, list[str]]:
    """Map of child_type → allowed_parent_types."""
    return {}
```

In `SpecDrivenMethodology`:
```python
@property
def valid_parent_pairs(self) -> dict[str, list[str]]:
    return {
        "requirement": ["spec"],
        "design": ["requirement"],
        "implementation": ["design"],
        "task": ["implementation"],
        "e2e_verification": ["requirement"],
        "functional_verification": ["design"],
        "unit_verification": ["implementation"],
    }
```

The edge validation logic in `validate_edge()` will check this map for `parent` edges.

### Other Edge Types

```python
"depends_on": EdgeTypeDefinition(
    name="depends_on",
    source_types=ALL_TYPES,
    target_types=ALL_TYPES,
    allows_cycles=False,
)

"blocks": EdgeTypeDefinition(
    name="blocks",
    source_types=ALL_TYPES,
    target_types=ALL_TYPES,
    allows_cycles=False,
)
```

Remove `gates` and `validates` edge types (replaced by the hierarchy + verification pattern).

## 3. Verification Failure Cascade

### Mechanism

When a verification node transitions to `failed`, the system automatically cascades the parent back:

| Verification Type | Parent Node | Cascade Action |
|-------------------|-------------|----------------|
| `unit_verification` | `implementation` | `implementation` → `rework` |
| `functional_verification` | `design` | `design` → `rejected` (then auto → `draft`) |
| `e2e_verification` | `requirement` | `requirement` → `rework` |

### Implementation: Status Transition Hook

In `workflow.py` (or a new `cascade.py`), add a post-transition hook:

```python
def on_status_change(node_id: str, node_type: str, old_status: str, new_status: str):
    """Called after every status transition. Handles cascades."""
    if new_status == "failed" and node_type in VERIFICATION_TYPES:
        cascade_verification_failure(node_id, node_type)
```

The cascade logic:
1. Find the parent node (via parent edge)
2. Transition parent to rework/rejected state
3. For `design`: auto-transition `rejected → draft` (two-step)

### Re-verification Gating

When a verification node attempts `failed → pending`:
1. Find the parent node
2. Check if parent is in terminal state (`done`, `approved`, `passed`)
3. If not, reject the transition with error: "Parent must be in terminal state before re-verification"

This requires a **pre-transition hook** in the workflow:

```python
def pre_status_change(node_id: str, node_type: str, old_status: str, new_status: str) -> list[str]:
    """Called before status transition. Returns list of errors (empty = OK)."""
    if node_type in VERIFICATION_TYPES and old_status == "failed" and new_status == "pending":
        return validate_reverification_allowed(node_id)
    return []
```

## 4. Time Tracking Enforcement

### `can_track_time` Flag

The `NodeTypeDefinition` already has a `can_track_time` field. Set it:

| Node Type | `can_track_time` |
|-----------|-----------------|
| `spec` | `False` |
| `requirement` | `False` |
| `design` | `False` |
| `implementation` | `False` |
| `task` | `True` |
| `e2e_verification` | `True` |
| `functional_verification` | `True` |
| `unit_verification` | `True` |

### Enforcement Point

In `time_entry.py`, `start_timer()` and `log_time()` must check:
```python
methodology = get_methodology_for_node(node_id)
node_type_def = methodology.get_node_type(node.node_type)
if not node_type_def.can_track_time:
    raise ValidationError(f"Time tracking not allowed on '{node.node_type}' nodes")
```

### Rollup

Existing `propagate_actual_time()` already walks up parent edges. No change needed — it sums own time entries + children's `actual_time` recursively.

## 5. Helper Method Updates

```python
def get_story_type(self) -> str:
    return "spec"

def get_task_type(self) -> str:
    return "task"

def get_in_progress_status(self, node_type: str) -> str:
    status_map = {
        "spec": "in_progress",
        "requirement": "in_progress",
        "design": "in_review",
        "implementation": "in_progress",
        "task": "in_progress",
        "e2e_verification": "in_progress",
        "functional_verification": "in_progress",
        "unit_verification": "in_progress",
    }
    return status_map.get(node_type, "in_progress")

def get_done_status(self, node_type: str) -> str:
    status_map = {
        "spec": "done",
        "requirement": "done",
        "design": "approved",
        "implementation": "done",
        "task": "done",
        "e2e_verification": "passed",
        "functional_verification": "passed",
        "unit_verification": "passed",
    }
    return status_map.get(node_type, "done")
```

## 6. Migration Strategy

### Approach: Version the methodology

- Rename current methodology to `spec_driven_v1` (or keep as `spec_driven_legacy`)
- New methodology is `spec_driven` (takes over the name)
- Existing projects keep their methodology tag — if `spec_driven` and has old-style nodes, the system detects v1 vs v2 by checking existing node types
- OR: simpler — just update in place and accept that old projects may need manual node type adjustments

### Recommendation

Given this is a personal project with few existing nodes (most completed/cleaned), update `spec_driven` in place. Document the breaking change. Old completed nodes won't be affected since they're terminal.

## 7. Files to Modify

1. **`src/taskyn/methodologies/spec_driven.py`** — Complete rewrite of node types, edge types, helpers
2. **`src/taskyn/methodologies/base.py`** — Add `valid_parent_pairs` property, update `validate_edge()`
3. **`src/taskyn/core/workflow.py`** — Add pre/post transition hooks for cascade
4. **`src/taskyn/core/time_entry.py`** — Add `can_track_time` enforcement
5. **`src/taskyn/mcp/server.py`** — Update `pm_get_methodology_info` to expose new fields
6. **`tests/`** — New tests for hierarchy validation, cascade, gating
