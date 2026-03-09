# Code Dry-Run Report #1

**Scope**: `src/taskyn/mcp/server.py` (lines 22-33, 765-804, 989-1027, 1072-1094), `tests/test_mcp_actor_override.py`
**Design**: `.claude/specs/caller-scoped-actor/design.md`
**Reviewed**: 2026-02-24

---

## Bugs (will cause incorrect behavior)

_None found._

---

## Gaps (missing implementation)

_None found. All 5 tools updated per design. `_resolve_actor` helper matches design spec exactly._

---

## Warnings (potential issues)

### [W1] Whitespace-only actor strings pass through as valid overrides
- **File**: `src/taskyn/mcp/server.py`:33
- **Pass**: Pass 4 (Input Validation)
- **What**: `_resolve_actor(" ")` returns `" "` (truthy) — a whitespace-only string becomes a valid actor identity. The core layer's `actor or None` guard (D9) normalizes empty string but not whitespace-only strings.
- **Risk**: An MCP caller accidentally passing `actor=" "` would create a timer under a whitespace actor, invisible in UI and hard to stop by name. Low probability — MCP tool callers are programmatic, not humans typing into a form.

### [W2] `pm_stop_timer` always resolves actor even when `entry_id` is provided
- **File**: `src/taskyn/mcp/server.py`:1026
- **Pass**: Pass 2 (Execution Path)
- **What**: When `entry_id` is provided, the core `stop_timer` ignores the actor parameter (D4 from MAT design). But `_resolve_actor(actor)` is still called, which reads `TASKYN_ACTOR` env var unnecessarily.
- **Risk**: No functional impact — the resolved actor is ignored by core when `entry_id` is set. Just a minor inefficiency. Not worth fixing.

---

## Style (code quality, conventions)

### [S1] Unused import in test file
- **File**: `tests/test_mcp_actor_override.py`:1
- **What**: `os` and `patch` from the original draft were removed, but the file header comment references "MCP tools" while tests call core functions directly. The docstring accurately explains this ("Tests validate _resolve_actor() logic and the end-to-end behavior when core functions receive actor values resolved by the MCP tool layer"). No issue — just noting the test approach.

---

## Summary

| Bugs | Gaps | Warnings | Style |
|------|------|----------|-------|
| 0 | 0 | 2 | 1 |

**Verdict**: PASS — No bugs or gaps. Two minor warnings (whitespace actor edge case, redundant resolution on entry_id stop) with negligible practical risk.
