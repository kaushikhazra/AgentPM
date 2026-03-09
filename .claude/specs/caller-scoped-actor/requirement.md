# Caller-Scoped Actor for Timer/Workflow — Requirements

## Overview

The multi-agent timer feature (MAT spec) scoped timers by actor, so different actors can run concurrent timers without interference. However, actor identity is determined at the **process level** via the `TASKYN_ACTOR` environment variable. All callers through the same MCP server instance share one actor identity.

This means sub-agents spawned by the same orchestrator (e.g., two Claude Code Task agents) cannot run independent timers — they all resolve to the same actor (e.g., `"web"`) and the second timer auto-stops the first.

The fix: allow MCP tool callers to pass an **explicit `actor` parameter** that overrides the transport-derived default. The core layer already supports arbitrary actor strings — only the MCP tool layer needs the override.

---

## User Stories

### CSA-1: Pass explicit actor to start_timer

**As an** MCP tool caller (sub-agent),
**I want to** pass an `actor` parameter to `pm_start_timer`,
**so that** my timer runs under my own identity rather than the shared transport actor.

**Acceptance Criteria:**
- `pm_start_timer(node_id, actor="agent-1")` creates a time entry with `actor="agent-1"`
- `pm_start_timer(node_id)` (no actor) falls back to `get_actor()` — backward compatible
- `pm_start_timer(node_id, actor="")` normalizes to `get_actor()` — empty string is not a valid override

### CSA-2: Pass explicit actor to stop_timer

**As an** MCP tool caller (sub-agent),
**I want to** pass an `actor` parameter to `pm_stop_timer`,
**so that** I stop only my own timer, not the transport actor's timer.

**Acceptance Criteria:**
- `pm_stop_timer(actor="agent-1")` stops only the timer where `actor="agent-1"`
- `pm_stop_timer()` (no actor) falls back to `get_actor()` — backward compatible
- `pm_stop_timer(entry_id="xyz")` still works regardless of actor (explicit entry override)

### CSA-3: Pass explicit actor to workflow actions

**As an** MCP tool caller (sub-agent),
**I want to** pass an `actor` parameter to `pm_start_node` and `pm_complete_node`,
**so that** workflow transitions use my identity for timer operations.

**Acceptance Criteria:**
- `pm_start_node(node_id, actor="agent-1")` starts a timer scoped to `"agent-1"`
- `pm_complete_node(node_id, actor="agent-1")` stops only `"agent-1"`'s timer on that node
- Both fall back to `get_actor()` when no actor is provided

### CSA-4: Pass explicit actor to get_active_timer

**As an** MCP tool caller (sub-agent),
**I want to** pass an `actor` parameter to `pm_get_active_timer`,
**so that** I can query my own timer status regardless of which transport I'm on.

**Acceptance Criteria:**
- `pm_get_active_timer(actor="agent-1")` returns only `"agent-1"`'s active timer
- `pm_get_active_timer()` (no actor) falls back to `get_actor()` — backward compatible
- `pm_get_active_timers()` (plural, all actors) is unchanged — no actor parameter needed

### CSA-5: Concurrent timers through the same MCP connection

**As a** system orchestrator spawning multiple sub-agents,
**I want** two sub-agents calling through the same MCP server to run independent timers by passing different actor values,
**so that** parallel work is tracked accurately without timer interference.

**Acceptance Criteria:**
- Agent calls `pm_start_timer(node_A, actor="sub-1")`, then `pm_start_timer(node_B, actor="sub-2")` — both timers remain active
- `pm_get_active_timers()` returns two entries with actors `"sub-1"` and `"sub-2"`
- `pm_stop_timer(actor="sub-1")` stops only sub-1's timer; sub-2 continues

---

## Infrastructure Dependencies

| Dependency | Status | Notes |
|-----------|--------|-------|
| `get_actor()` in `mcp/server.py` | Exists | Env var fallback — no changes needed |
| Core `start_timer()` | Exists | Already accepts `actor` param — no changes |
| Core `stop_timer()` | Exists | Already accepts `actor` param — no changes |
| Core `get_active_timer()` | Exists | Already accepts `actor` param — no changes |
| Core `start_node()` | Exists | Already accepts `actor` param — no changes |
| Core `complete_node()` | Exists | Already accepts `actor` param — no changes |
| MCP tool functions | Exists — needs `actor` param | 5 tools need optional `actor` parameter added |

---

## Configuration Summary

No new environment variables or config files. The existing `TASKYN_ACTOR` env var continues to serve as the default. The new `actor` parameter is purely opt-in at the tool call level.

---

## Out of Scope

- **Actor validation/registration** — actor strings are free-form. No validation that an actor is "real" or authorized.
- **Web UI changes** — the frontend continues to use the transport actor (`"web"`). No UI for selecting an actor.
- **CLI changes** — the CLI hardcodes `actor="cli"`. No override mechanism for CLI callers.
- **Rate limiting per actor** — no limit on how many distinct actors can exist. The one-timer-per-actor guardrail is sufficient.
- **Actor in tool descriptions** — updating MCP tool docstrings to document the new parameter is in scope; changing the MCP server instructions or system prompts is not.
