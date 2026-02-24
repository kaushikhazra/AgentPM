# Multi-Agent Concurrent Timers — Requirements

## Overview

Taskyn's time tracking currently enforces a single global active timer. When any caller starts a timer, the system auto-stops whichever timer was previously running — regardless of who started it. This makes multi-agent development impossible: if two Claude Code instances work in parallel on different tasks, they constantly kill each other's timers.

The fix is to **scope timers by actor**. Each actor (identified by the `TASKYN_ACTOR` env var or the `actor` parameter) gets its own independent timer slot. The existing "auto-stop previous timer" behavior is preserved but scoped per-actor, not globally. A guardrail of one active timer per actor prevents runaway timer accumulation.

---

## User Stories

### MAT-1: Start timer without killing other agents' timers

**As an** MCP client (agent),
**I want to** start a timer on a task without stopping timers started by other agents,
**so that** multiple agents can track time on their respective tasks simultaneously.

**Acceptance Criteria:**
- Starting a timer with `actor="agent-A"` does NOT stop an active timer owned by `actor="agent-B"`
- Starting a timer with `actor="agent-A"` DOES auto-stop any existing active timer owned by `actor="agent-A"`
- The `time_entries` table stores the `actor` value on each entry

### MAT-2: Stop only my own timer

**As an** MCP client (agent),
**I want** `stop_timer()` with no explicit entry/node ID to stop only my own active timer,
**so that** I don't accidentally stop another agent's work tracking.

**Acceptance Criteria:**
- `stop_timer(actor="agent-A")` with no `entry_id` or `node_id` stops only the timer where `actor="agent-A"` and `ended_at IS NULL`
- If `actor="agent-A"` has no active timer, returns `None` — does not fall back to stopping someone else's
- Stopping by explicit `entry_id` still works regardless of actor (for admin operations)

### MAT-3: Query my own active timer

**As an** MCP client (agent),
**I want to** query my active timer without seeing other agents' timers,
**so that** I can check my own time tracking status.

**Acceptance Criteria:**
- `get_active_timer(actor="agent-A")` returns only the timer owned by `agent-A`
- A new `get_active_timers()` function (no actor filter) returns ALL active timers across all actors
- The MCP tool `pm_get_active_timer` returns the calling agent's timer (scoped by `get_actor()`)

### MAT-4: One-timer-per-actor guardrail

**As the** system,
**I want to** enforce a maximum of one active timer per actor,
**so that** a malfunctioning agent cannot accumulate unlimited open timers.

**Acceptance Criteria:**
- If an actor already has an active timer and starts a new one, the old one is auto-stopped (same as current behavior, but per-actor)
- This limit is hardcoded to 1 for this iteration
- A `ValidationError` is NOT raised — the auto-stop is silent, matching current behavior

### MAT-5: Workflow actions scoped to actor

**As an** MCP client (agent),
**I want** `pm_start_node` and `pm_complete_node` to interact with my actor-scoped timer,
**so that** workflow actions in multi-agent scenarios don't interfere with each other.

**Acceptance Criteria:**
- `start_node(node_id, actor="agent-A")` starts a timer scoped to `agent-A` (does not stop `agent-B`'s timer)
- `complete_node(node_id, actor="agent-A")` only stops the timer if it belongs to `agent-A` and is on that node
- If `agent-A` completes a node but `agent-B` has the active timer on that node, `agent-B`'s timer is NOT stopped

### MAT-6: Cross-agent timer visibility (API)

**As a** project manager viewing the dashboard,
**I want to** see all active timers across all agents,
**so that** I can monitor who is working on what.

**Acceptance Criteria:**
- A new MCP tool `pm_get_active_timers` returns a list of all active timers with their actor, node, and duration
- The existing `pm_get_active_timer` (singular) continues to work, scoped to the calling actor
- Each active timer entry includes the `actor` field in its response
- A new backend API endpoint `GET /timer/active` returns all active timers (used by the web UI)

### MAT-7: Dashboard shows all active timers

**As a** user viewing the Dashboard page,
**I want to** see all currently running timers (not just one),
**so that** I can see what every agent is working on at a glance.

**Acceptance Criteria:**
- The TimerWidget displays a list of all active timers, each showing: actor name, task title, and elapsed time
- Each timer has its own stop button
- The "Time Tracked Today" stat card aggregates time from all actors
- When no timers are running, the widget shows "No Active Timers" (same as today)

### MAT-8: Tracker page shows multi-agent entries

**As a** user viewing the Tracker page,
**I want to** see which actor created each time entry,
**so that** I can understand how work was distributed across agents.

**Acceptance Criteria:**
- Each time entry row displays the `actor` label (e.g., a badge or subtitle)
- Active entries from multiple agents can show the pulsing dot simultaneously
- The TimerWidget at the top shows all active timers (same as Dashboard)
- Filtering by actor is NOT required for this iteration (out of scope)

### MAT-9: Kanban cards show multi-agent tracking

**As a** user viewing the Kanban board,
**I want to** see tracking indicators on all cards that have active timers (not just one),
**so that** I can see which tasks are being worked on by which agents.

**Acceptance Criteria:**
- Multiple kanban cards can show the tracking indicator simultaneously (one per active timer)
- Each tracking indicator shows the actor name alongside the elapsed time (e.g., "mcp · 00:15:30")
- The left-border highlight applies to all cards with active timers
- If two agents track the same node (edge case), both are shown

### MAT-10: Frontend types and state support multiple timers

**As a** frontend developer,
**I want** the `ActiveTimer` type and `TimerProvider` to support multiple concurrent timers,
**so that** all UI components can render multi-agent state correctly.

**Acceptance Criteria:**
- `ActiveTimer` type includes an `actor: string` field
- `TimerProvider` exposes `activeTimers: ActiveTimer[]` (list) in addition to or replacing the current singular `activeTimer`
- Each timer's elapsed time is calculated independently
- The 1-second polling interval fetches all active timers in a single API call
- `start()` and `stop()` continue to operate on the web UI user's timer (actor = "web")

---

## Infrastructure Dependencies

| Dependency | Status | Notes |
|-----------|--------|-------|
| `time_entries` table | Exists — needs `actor` column | Additive schema migration (nullable TEXT column) |
| `TimeEntry` model | Exists — needs `actor` field | New optional field on Pydantic model |
| `ActiveTimer` TS type | Exists — needs `actor` field | New field on frontend type |
| `TimerProvider` | Exists — single timer | Refactor to manage `activeTimers[]` |
| `TimerWidget` | Exists — single timer | Refactor to render list of timers |
| `GET /timer/current` | Exists — returns one | New `GET /timer/active` returns all |
| `TASKYN_ACTOR` env var | Exists | Already read by `get_actor()` in MCP server |
| Activity log | Exists | Already receives `actor` param — no changes needed |

---

## Out of Scope

- **Configurable max timers per actor** — hardcoded to 1 for now. A future spec will make this configurable (per-actor or per-project settings).
- **Actor registration/authentication** — actors are identified by string only. No validation that an actor string is "real."
- **Filter tracker by actor** — the tracker shows all entries; per-actor filtering is deferred.
- **CLI timer changes** — the CLI uses `actor="cli"`. The `stop` and `status` commands must be updated to pass `actor="cli"` to `get_active_timer()` so they find the CLI-scoped timer. This is a minor fix, not a new feature.
