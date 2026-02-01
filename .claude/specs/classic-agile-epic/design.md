# Epic Support - Design Document

## Current State

```
Hierarchy:
  Story
  └── Task

Edge "parent": task → story
```

## Target State

```
Hierarchy:
  Epic
  └── Story
      └── Task

Edge "parent":
  - task → story
  - story → epic
```

## Node Type: Epic

| Property | Value |
|----------|-------|
| name | `epic` |
| valid_statuses | `draft`, `ready`, `in_progress`, `done`, `cancelled` |
| initial_status | `draft` |
| terminal_statuses | `done`, `cancelled` |
| can_track_time | `False` (use rollup from children) |
| can_have_assignee | `True` |

### Status Workflow

```
draft ──→ ready ──→ in_progress ──→ done
  │         │           │
  └─────────┴───────────┴──────────→ cancelled
```

**Transitions:**
- `draft` → `ready`, `cancelled`
- `ready` → `in_progress`, `draft`, `cancelled`
- `in_progress` → `done`, `ready`, `cancelled`
- `done` → (terminal)
- `cancelled` → (terminal)

## Edge Type Updates

### Parent Edge

Current:
```python
"parent": EdgeTypeDefinition(
    name="parent",
    source_types=["task"],
    target_types=["story"],
    max_per_source=1,
    allows_cycles=False,
)
```

Updated:
```python
"parent": EdgeTypeDefinition(
    name="parent",
    source_types=["task", "story"],
    target_types=["story", "epic"],
    max_per_source=1,
    allows_cycles=False,
)
```

### Depends_on Edge

Add `epic` to both source and target types:
```python
"depends_on": EdgeTypeDefinition(
    name="depends_on",
    source_types=["task", "story", "epic"],
    target_types=["task", "story", "epic"],
    allows_cycles=False,
)
```

## Helper Methods

Add to `ClassicAgileMethodology`:

```python
def get_epic_type(self) -> str:
    return "epic"
```

## File Changes

| File | Change |
|------|--------|
| `src/agentpm/methodologies/classic_agile.py` | Add epic node type, update edges, add helper |
| `tests/test_methodology.py` | Add epic tests |

## Backwards Compatibility

- Existing projects using classic_agile will gain epic support automatically
- No migration needed - epic is additive
- Existing stories without epics continue to work (parent is optional)
