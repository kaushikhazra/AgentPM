# Node Actual Time - Requirements

## Overview
Taskyn tracks time via time_entries but nodes have no denormalized `actual_time` field. This means node lists show no time data, and rollup calculations are expensive (N+1 queries on every read). Add an `actual_time` field to nodes with write-time propagation up the parent chain, making time visible everywhere nodes appear.

## User Stories

### US-1: See time spent on individual tasks
**As a** project manager,
**I want** to see how much time was spent on each task in node lists,
**So that** I can identify which tasks consumed the most effort without opening each one.

### US-2: See aggregated time on parent nodes
**As a** project manager,
**I want** parent nodes (specs, stories) to show the total time spent across all their children,
**So that** I can understand effort at the feature/spec level, not just individual tasks.

### US-3: Real-time time propagation
**As a** user tracking time,
**I want** `actual_time` to update automatically when I start/stop timers or log time,
**So that** the data is always current without needing to refresh or wait for a batch job.

### US-4: Second-level granularity
**As a** user working with AI agents,
**I want** time tracked in seconds (not minutes),
**So that** short tasks completed by AI agents are accurately captured.

## Acceptance Criteria
- Every node has an `actual_time` field (integer, seconds, default 0)
- Leaf nodes: `actual_time` = sum of own time entries (in seconds)
- Parent nodes: `actual_time` = sum of direct children's `actual_time`
- `actual_time` propagates up the parent chain on every time entry change (create/stop/delete)
- Propagation does not block the caller (background thread or async)
- Node lists display `actual_time` formatted as human-readable (e.g., "2h 15m", "45s")
- Node detail page displays `actual_time`
- Existing data is backfilled via a migration script
- `actual_time` is stored in seconds for sub-minute granularity
