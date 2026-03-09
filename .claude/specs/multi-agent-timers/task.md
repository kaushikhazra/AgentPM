# Multi-Agent Concurrent Timers — Tasks

## 1. Schema, Model, and Core Layer

- [x] Velasari adds `actor TEXT` column to `time_entries` in `src/taskyn/db/schema.sql` — _MAT-1_
- [x] Velasari adds `idx_time_entries_actor_active` index to `schema.sql` — _MAT-1_
- [x] Velasari adds actor column migration in `src/taskyn/db/connection.py` `_run_migrations()` — _MAT-1_
- [x] Velasari adds `actor: str | None = None` field to `TimeEntry` in `src/taskyn/db/models.py` — _MAT-1_
- [x] Velasari updates `_row_to_time_entry()` in `src/taskyn/core/time_entry.py` to read `row["actor"]` — _MAT-1_
- [x] Velasari scopes `start_timer()` to actor with `actor = actor or None` guard, actor-scoped auto-stop, and actor in INSERT/return — _MAT-1, MAT-4_
- [x] Velasari scopes `stop_timer()` default lookup to actor, includes `actor=entry.actor` in return — _MAT-2_
- [x] Velasari scopes `get_active_timer()` to accept `actor` param with `WHERE actor IS ?` — _MAT-3_
- [x] Velasari adds `get_active_timers()` function returning all active timers — _MAT-6_
- [x] Velasari scopes `_get_active_timer_for_node()` to accept `actor` param — _MAT-2_
- [x] Velasari updates `log_time()` with `actor = actor or None` guard, actor in INSERT/return — _MAT-1_
- [x] Velasari exports `get_active_timers` from `src/taskyn/core/__init__.py` — _MAT-6_
- [x] Velasari adds `actor` param to `get_dashboard()` in `src/taskyn/core/reporting.py` — _MAT-3_
- [x] Velasari writes 8 multi-actor test cases in `tests/test_time_entry.py` — _MAT-1, MAT-2, MAT-3, MAT-4, MAT-6_

## 2. Workflow and CLI Actor Scoping

- [x] Velasari scopes `complete_node()` in `src/taskyn/core/workflow.py` to `get_active_timer(actor=actor)` — _MAT-5_
- [x] Velasari scopes `submit_for_review()` in `src/taskyn/core/workflow.py` to `get_active_timer(actor=actor)` — _MAT-5_
- [x] Velasari scopes CLI `stop_timer()` in `src/taskyn/cli/timer.py` to `get_active_timer(actor="cli")` — _MAT-2_
- [x] Velasari scopes CLI `timer_status()` in `src/taskyn/cli/timer.py` to `get_active_timer(actor="cli")` — _MAT-3_
- [x] Velasari scopes CLI `dashboard()` in `src/taskyn/cli/dashboard.py` to `get_dashboard(actor="cli")` — _MAT-3_
- [x] Velasari writes `test_complete_node_actor_scoping` test — _MAT-5_
- [x] Velasari writes `test_submit_for_review_actor_scoping` test — _MAT-5_
- [x] Velasari fixes existing workflow tests to use actor-scoped `get_active_timer()` — _MAT-3_
- [x] `test_cli_actor_round_trip` covered in todo 1 — _MAT-2, MAT-3_

## 3. MCP Server, Web API, and Docker Config

- [x] Velasari scopes `pm_get_active_timer()` in `src/taskyn/mcp/server.py` to `get_active_timer(actor=get_actor())` — _MAT-3_
- [x] Velasari adds `pm_get_active_timers()` tool to `src/taskyn/mcp/server.py` — _MAT-6_
- [x] Velasari scopes `pm_get_dashboard()` in `src/taskyn/mcp/server.py` to `get_dashboard(actor=get_actor())` — _MAT-3_
- [x] Velasari scopes dashboard resource in `src/taskyn/mcp/server.py` to `get_dashboard(actor=get_actor())` — _MAT-3_
- [x] Velasari adds `GET /timer/active` endpoint in `src/taskyn/web/backend/routes/timer.py` — _MAT-6_
- [x] Velasari changes `TASKYN_ACTOR=mcp` to `TASKYN_ACTOR=web` on `taskyn-core` service in `docker-compose.yml` — _MAT-10_
- [x] Velasari changes `TASKYN_ACTOR=mcp` to `TASKYN_ACTOR=web` on `taskyn-core` service in `docker-compose.dev.yml` — _MAT-10_

## 4. Frontend Multi-Timer Support

- [x] Velasari adds `actor` field to `ActiveTimer` and `TimeEntry` in `src/taskyn/web/frontend/src/types/index.ts` — _MAT-10_
- [x] Velasari adds `getActive()` method to `src/taskyn/web/frontend/src/api/timer.ts` — _MAT-10_
- [x] Velasari adds `active()` query key to `src/taskyn/web/frontend/src/api/queryKeys.ts` — _MAT-10_
- [x] Velasari adds `useActiveTimers` hook to `src/taskyn/web/frontend/src/hooks/queries/useTimerQuery.ts` — _MAT-10_
- [x] Velasari refactors `TimerProvider` to `activeTimers[]` + `elapsedMap` in `src/taskyn/web/frontend/src/providers/TimerProvider.tsx` — _MAT-10_
- [x] `useTimer` hook type re-export unchanged (context type auto-propagates) — _MAT-10_
- [x] Velasari refactors `TimerWidget` to render multi-timer list in `src/taskyn/web/frontend/src/components/organisms/TimerWidget.tsx` — _MAT-7_
- [x] Velasari updates `DashboardPage` to sum elapsed from `elapsedMap` in `src/taskyn/web/frontend/src/pages/DashboardPage.tsx` — _MAT-7_
- [x] Velasari adds actor badge to entries in `src/taskyn/web/frontend/src/pages/TrackerPage.tsx` — _MAT-8_
- [x] Velasari adds multi-card tracking indicators with actor in `src/taskyn/web/frontend/src/pages/KanbanPage.tsx` — _MAT-9_
- [x] Velasari adds `.timer-entry`, `.timer-actor`, `.time-entry-actor` CSS classes in `src/taskyn/web/frontend/src/styles/base.css` — _MAT-7, MAT-8_
- [x] Velasari verifies TypeScript build + Vite production build compile cleanly — _MAT-10_

## 5. Code Dry-Run #1 Fixes

- [x] Velasari fixes `_row_to_time_entry()` in `src/taskyn/core/reporting.py` to include `actor=row["actor"]` — _MAT-1_ (B1)
- [x] Velasari removes `useTimerCurrent` double-polling from `TimerProvider`, single `useActiveTimers` poll — _MAT-10_ (G2, W2)
- [x] Velasari adds `entryId?` parameter to `stop()` in `TimerProvider` — _MAT-7_ (G1)
- [x] Velasari adds per-timer stop buttons to `TimerWidget` multi-timer layout — _MAT-7_ (W1)
- [x] Velasari verifies TypeScript + Vite build + all tests pass — _MAT-10_

## 6. Schema Migration & Docker Build Fixes

- [x] Velasari moves `idx_time_entries_actor_active` index from `schema.sql` to `connection.py` migration — _MAT-1_
- [x] Velasari adds `rm -rf dist` before `npm run build` in `Dockerfile.web` to prevent stale local artifacts — _MAT-10_
- [x] Velasari adds `**/dist/` to `.dockerignore` to exclude nested frontend dist from Docker context — _MAT-10_
- [x] Velasari verifies Docker build + browser test: Dashboard (2 Active Timers), Tracker (actor badges + stop), Kanban (timer indicators with actor) — _MAT-7, MAT-8, MAT-9, MAT-10_
