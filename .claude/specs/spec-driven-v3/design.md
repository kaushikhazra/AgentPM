# Spec-Driven Methodology v3 — Design

**Date**: 2026-02-17
**Status**: Draft
**Research**: `.claude/research/spec-driven-development-industry-research.md`

---

## Philosophy

- **Requirement** = WHAT to implement (drives acceptance criteria)
- **Design** = HOW to implement (drives architecture decisions)
- **Task** = implementation grouping (e.g., "Frontend Development", "Backend API")
- **Todo** = universal work unit (tracks time, leaf node)

Spec-anchored rigor: specs evolve alongside code, tests enforce alignment. Not spec-first-then-forget, not spec-as-source.

---

## Hierarchy

3 levels, 5 node types:

```
Spec (Level 1 — container)
├── Requirement (Level 2 — what) → todos
├── Design (Level 2 — how) → todos
└── Task (Level 2 — implementation grouping) → todos
```

### Parent-Child Rules

| Child | Valid Parents |
|-------|-------------|
| Requirement | Spec |
| Design | Spec |
| Task | Spec |
| Todo | Requirement, Design, Task |

### Examples

**Feature work:**
```
Spec: "User Authentication"
├── Requirement: "OAuth2 Login" → todos (write user stories, validate criteria)
├── Design: "Auth Architecture" → todos (diagram, prototype, review)
├── Task: "Frontend Auth Flow" → todos (login form, callback handler, tests)
├── Task: "Backend OAuth API" → todos (endpoints, token refresh, tests)
└── Task: "Database Schema" → todos (migration, seed data)
```

**Bug fix (no new spec needed):**
```
Existing Spec: "User Authentication"
└── Task: "Frontend Auth Flow"
    └── Todo: "Fix session timeout on token refresh"  ← just add a todo
```

---

## Statuses

### Phase Nodes (Spec, Requirement, Design, Task)

Universal simple statuses:

| Status | Meaning |
|--------|---------|
| `draft` | Not started / being written |
| `active` | In progress |
| `done` | Complete |
| `cancelled` | Dropped |

Transitions:
```
draft → active → done
draft → cancelled
active → cancelled
```

### Todo Nodes

Aligned with classic_agile task pattern for start/stop timer support:

| Status | Meaning |
|--------|---------|
| `todo` | Not started |
| `in_progress` | Being worked on (timer running) |
| `done` | Complete |
| `cancelled` | Dropped |

Transitions:
```
todo → in_progress → done
todo → cancelled
in_progress → cancelled
```

---

## Strict Gating

Sequential phase gates enforce discipline for AI coders:

| Gate | Rule |
|------|------|
| Spec → Requirement | Requirement can go `active` when Spec is `active` |
| Requirement → Design | Design can go `active` when **all** Requirements are `done` |
| Design → Task | Task can go `active` when **all** Designs are `done` |
| Phase → Todo | Todos can start when their parent phase is `active` |

This prevents AI agents from jumping ahead and breaking the flow.

---

## Time Tracking

- **Only on Todos** — todos are the sole node type with `can_track_time = True`
- Uses `pm_start_node` (sets `in_progress` + starts timer) and `pm_complete_node` (sets `done` + stops timer)
- Time rolls up through the hierarchy: Todo → parent (Task/Design/Requirement) → Spec

---

## Edge Types

| Edge | Source Types | Target Types | Purpose |
|------|------------|-------------|---------|
| `parent` | Requirement, Design, Task, Todo | Spec, Requirement, Design, Task | Hierarchy |
| `depends_on` | All | All | Sequential dependencies |
| `blocks` | All | All | Blocking relationships |

---

## Comparison: v2 → v3

| Aspect | v2 | v3 |
|--------|----|----|
| Node types | 8 (spec, requirement, design, implementation, task, 3x verification) | 5 (spec, requirement, design, task, todo) |
| Hierarchy depth | 5 levels mandatory | 3 levels |
| Verification | 3 separate verification node types | Tests are todos under tasks |
| Statuses | Complex per-type (12+ unique) | Universal simple set (4 per level) |
| Time tracking | Task + verification nodes | Todos only |
| Scale-adaptive | No (same ceremony for all) | Yes (bugs = add a todo, features = full hierarchy) |
| Context cost | High (many nodes, deep traversal) | Low (flat, fewer nodes) |

---

## Design Decisions

1. **Why "todo" not "subtask"?** — "Subtask" implies hierarchy depth. "Todo" is a universal, flat work unit. It's what you *do*, regardless of which phase it belongs to.

2. **Why strict gating?** — AI coding agents need guardrails. Without gates, agents will skip requirement gathering and jump straight to coding. Strict gates enforce the discipline that produces better outcomes.

3. **Why universal statuses?** — v2 had 12+ unique statuses across node types (draft, approved, in_review, rejected, rework, pending, passed, failed...). This created cognitive overhead and complex transition logic. Simple universal statuses reduce code complexity and are easier for both humans and AI to reason about.

4. **Why tests as todos?** — Separate verification node types in v2 were overhead. A test is just work you do — write it, run it, track the time. It belongs as a todo under the relevant task.

5. **Why Task as an implementation grouping?** — Without it, all implementation todos would be flat under the spec. Task provides natural grouping by concern (frontend, backend, DB) without adding hierarchy depth.
