TASKYN PLANNING FEATURE — RESEARCH FINDINGS
============================================
Date: 2026-04-09
Purpose: Feed into Planning feature spec for Taskyn
Scope: Full codebase audit — data model, methodology system, MCP tools, frontend, gaps


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. DATA MODEL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SOURCE: src/taskyn/db/models.py, src/taskyn/db/schema.py, src/taskyn/db/enums.py

--- Entities & Fields ---

Company
  id, name, description?, type (EntityType), created_at, updated_at

Project
  id, company_id, name, description?, type (EntityType), methodology (Methodology),
  status (str), config (dict?), created_at, updated_at

Milestone
  id, project_id, name, description?, target_date (date?), status (str),
  completed_at?, created_at, updated_at
  -> The only entity with a native date field. target_date is optional, not enforced.

Node (work item — the primary unit of work)
  id, project_id, milestone_id?, node_type, title, description?,
  status, assignee (str?), estimated_minutes (int?), story_points (float?),
  actual_time (int, default 0), priority (str, default "medium"),
  blocked_reason (str?), properties (dict?), created_at, updated_at, completed_at?

  PLANNING RELEVANT:
  - priority: exists (low/medium/high/critical) — not time-aware
  - estimated_minutes: exists — closest proxy to "planned duration"
  - assignee: exists — single string, no role/actor distinction
  - NO: scheduled_for, planned_date, due_date, start_date, time_window

Edge (relationship between nodes)
  id, project_id, source_id, target_id, edge_type, properties (dict?), created_at
  Types: parent, depends_on, blocks, relates_to

TimeEntry (time tracking record)
  id, node_id, started_at, ended_at?, duration_minutes?, notes?,
  source (manual default), actor (str?), created_at

  PLANNING RELEVANT:
  - actor: exists — supports multi-actor time tracking (e.g., "KH", "V")
  - No "planned" flag — all entries are actual work, not planned intent

Tag
  id, name, color?

ActivityLog
  id, entity_type, entity_id, node_type?, action, old_value?, new_value?,
  actor?, notes?, created_at

--- Enums ---

EntityType: discovery, potential, matured, engaged, active, dormant
  (Used on Company and Project — not relevant to planning)

Methodology: classic_agile, spec_driven, learning

No enum exists for: priority levels, actor roles, plan statuses, time-slot types

--- Summary ---

The data model has the skeleton of planning concerns (priority, estimates, assignee,
actor on time entries) but NO temporal scheduling fields on nodes. There is no
"when to work on this" concept at the node level. Milestones have target_date
but that is a coarse deadline, not a schedule.


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
2. EXISTING PLANNER PAGE (FRONTEND)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SOURCE: src/taskyn/web/frontend/src/pages/PlannerPage.tsx, src/routes.tsx

--- Route ---
/planner and /planner/:projectId

--- What It Currently Shows ---
- Hierarchical tree view: Epic -> Story -> Task
- Project selector dropdown
- Status badges with visual indicators (done, progress, blocked, ready, backlog, review)
- Progress bars (% complete per parent node)
- Expand/collapse tree navigation
- Quick status toggle via checkbox on tasks
- Create node modal (Type, Parent, Title, Description)
- Click-through to node detail page

--- What It Can Do ---
- Browse work items in tree form
- Create new nodes
- Toggle task status
- Select project scope

--- What It CANNOT Do ---
- Show a calendar or timeline
- Schedule a node to a date
- Show a day/week plan
- Drag-and-drop to schedule
- Distinguish actors (KH vs V)
- Show planned vs actual comparison
- Filter by date, time window, or intention
- Show overdue items or upcoming deadlines

--- Verdict ---
The "Planner" page is currently a renamed tree view — it is a hierarchy browser,
not a planner. The name is aspirational. No planning functionality exists.

--- All Frontend Routes (for context) ---
/dashboard, /companies, /projects, /projects/:projectId,
/nodes/:nodeId, /kanban, /kanban/:projectId,
/planner, /planner/:projectId, /tracker, /settings


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
3. METHODOLOGY SYSTEM
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SOURCE: src/taskyn/methodologies/base.py + classic_agile.py + spec_driven.py + learning.py

--- NodeTypeDefinition (defined per type per methodology) ---
Fields:
  valid_statuses: list[str]
  initial_status: str
  terminal_statuses: list[str]
  allowed_transitions: dict[str, list[str]]
  can_track_time: bool
  can_have_assignee: bool

PLANNING RELEVANT: can_track_time controls timer eligibility.
MISSING: can_be_scheduled, can_have_due_date, can_be_planned

--- EdgeTypeDefinition ---
Fields:
  source_types, target_types, max_per_source, max_per_target, allows_cycles

--- Classic Agile ---
Types: epic, story, task
  Epic: draft->ready->in_progress->done/cancelled (cannot track time)
  Story: backlog->ready->in_progress->done/cancelled (optional story_points)
  Task: todo->in_progress->blocked->in_review->done/cancelled (tracks time)
Edge types: parent (1-per-node), depends_on (no cycles)

--- Spec Driven ---
Types: spec, requirement, design, task (phase nodes, no time), todo (leaf, time-trackable)
  Phase nodes: draft->active->done/cancelled
  Todos: todo->in_progress->done/cancelled
  Strict gating: requirement activates when spec is active; design when all
  sibling requirements done; task when all sibling designs done
Edge types: parent (1-per-node), depends_on, blocks (no cycles)

--- Learning ---
Types: subject, topic, activity
  Subject: planned->active->completed/archived
  Topic: planned->researching->practicing->documenting->completed/archived (flexible)
  Activity: todo->in_progress->done/cancelled
Edge types: parent (1-per-node), depends_on, relates_to (cycles allowed)

--- What Methodologies Control vs Don't ---
CONTROL: node types, valid statuses, transitions, time tracking eligibility,
         assignee eligibility, edge cardinality, cycle rules
DON'T CONTROL: scheduling, priority tiers, date constraints, actor roles,
               planning intent, plan vs actual distinction

--- Implication for Planning ---
Planning rules (e.g., "can only schedule a todo if its parent task is active")
would need to be added to NodeTypeDefinition or a new PlanTypeDefinition.
Currently no hook exists for this.


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
4. CORE BUSINESS LOGIC
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SOURCE: src/taskyn/core/

work_items.py
  create_story(project_id, milestone_id?, priority, story_points, ...)
  create_task(story_id, assignee?, estimated_minutes?, priority, ...)
  get_story_with_tasks(story_id) -> hierarchical view
  -> No scheduling parameters

workflow.py
  start_node()        -> in_progress + start timer (if trackable)
  complete_node()     -> stop timer + done/cancelled
  block_node(reason)  -> blocked status
  unblock_node()      -> back to in_progress
  submit_for_review() -> in_review (if allowed by methodology)
  approve()           -> in_review -> done
  reject()            -> in_review -> in_progress
  -> All transitions are status-based. None are date/schedule triggered.

milestone.py
  create_milestone(project_id, name, description?, target_date?)
  update_milestone(... target_date?)
  list_milestones(project_id, status?) -> ordered by target_date
  complete_milestone() -> completed_at timestamp
  -> The only date-aware core module. Milestones are coarse containers, not schedules.

rollup.py
  RollupStats: total_time_minutes, estimated_time_minutes, total_nodes,
               completed_nodes, blocked_nodes, in_progress_nodes,
               completion_percentage, story_points
  get_node_rollup(node_id) -> descendant aggregate stats
  get_milestone_rollup(milestone_id)
  get_project_rollup(project_id)
  -> No concept of planned time vs estimated vs actual distinction

reporting.py
  Dashboard: active_timer, active_timer_node, in_progress_nodes, blocked_nodes,
             today_time_minutes, recent_activity
  ProjectStats: nodes_by_type, nodes_by_status, time_this_week,
                time_this_month, time_total, velocity_per_week, milestone_progress
  get_dashboard() -> actual current state; no "plan for today" concept
  -> velocity_per_week is computed from actual time_entries, not planned throughput

time_entry.py
  start_timer(node_id, notes?, source?, actor?)
  stop_timer(entry_id | actor) -> calculates duration_minutes
  get_active_timer(actor?) -> one timer per actor
  log_time(node_id, duration_minutes, notes?) -> manual entry
  -> actor field supports multi-actor already. This is the hook for KH vs V distinction.

--- No planning modules exist ---
There is no: planning.py, scheduling.py, intention.py, daily_plan.py


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
5. GRAPH LAYER
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SOURCE: src/taskyn/graph/nodes.py, edges.py, traversal.py

nodes.py — create_node() parameters:
  project_id, node_type, title, description?, assignee?, milestone_id?,
  estimated_minutes?, story_points?, priority?, properties?, actor?

nodes.py — list_nodes() filters:
  project_id, node_type, status, assignee, milestone_id, limit, offset
  -> NO: scheduled_for, due_date, date_range, actor_filter

nodes.py — update_node() fields:
  title, description, status, assignee, milestone_id, estimated_minutes,
  story_points, priority, blocked_reason, properties

edges.py:
  create_edge(source_id, target_id, edge_type) with cardinality + cycle validation
  list_edges(project_id, source_id?, target_id?, edge_type?)
  -> Edges encode dependency/hierarchy; no temporal edges possible

traversal.py:
  detect_cycle(node_id, target_id, edge_type)
  get_ancestors(node_id, edge_type?, max_depth?)
  get_descendants(node_id, edge_type?, max_depth?) -> returns {id, parent_id}
  get_parents(node_id, edge_type?)
  get_children(node_id, edge_type?)
  -> All structural traversal. No date/time-aware queries.

--- Query gaps for planning ---
MISSING query capabilities:
  - list_nodes(scheduled_date=date)
  - list_nodes(due_before=date)
  - list_nodes(planned_for_actor="KH", on_date=date)
  - list_nodes(overdue=True)
  - list_nodes(has_plan=True)


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
6. MCP TOOLS — FULL INVENTORY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SOURCE: src/taskyn/mcp/server.py

COMPANY (6): pm_list_companies, pm_create_company, pm_get_company,
             pm_update_company, pm_delete_company, pm_get_company_stats

PROJECT (6): pm_list_projects, pm_create_project, pm_get_project,
             pm_update_project, pm_delete_project, pm_get_methodology_info

MILESTONE (6): pm_list_milestones, pm_create_milestone, pm_get_milestone,
               pm_update_milestone, pm_delete_milestone, pm_complete_milestone

NODE (10): pm_list_nodes, pm_create_node, pm_get_node, pm_update_node,
           pm_start_node, pm_complete_node, pm_block_node, pm_delete_node,
           pm_get_ancestors, pm_get_descendants

EDGE (3): pm_list_edges, pm_create_edge, pm_delete_edge

TIME TRACKING (8): pm_start_timer, pm_stop_timer, pm_log_time,
                   pm_list_time_entries, pm_get_time_entry, pm_delete_time_entry,
                   pm_get_active_timer, pm_get_active_timers

REPORTING (4): pm_get_dashboard, pm_get_project_stats,
               pm_get_rollup, pm_get_recent_activity

SEARCH (1): pm_search

TAG (6): pm_list_tags, pm_create_tag, pm_tag_node, pm_untag_node,
         pm_delete_tag, pm_get_tag_usage

TOTAL: ~50 tools

--- Planning-Adjacent Tools (can be repurposed or extended) ---
pm_update_node:           set priority, assignee — useful for planning assignments
pm_list_nodes:            filter by assignee — query KH or V workload
pm_get_dashboard:         shows today_time_minutes (actual, not planned)
pm_list_milestones:       ordered by target_date — only date-aware query today
pm_get_active_timer:      actor-scoped — foundation for multi-actor tracking
pm_get_active_timers:     all-actor view — who is working on what right now

--- No Planning Tools Exist ---
MISSING:
  pm_schedule_node(node_id, scheduled_date, actor?)
  pm_get_daily_plan(date, actor?)
  pm_get_weekly_plan(week_start, actor?)
  pm_create_plan(date, actor, node_ids) -> daily intention
  pm_reschedule_node(node_id, new_date)
  pm_list_planned_nodes(date_range, actor?)
  pm_list_overdue_nodes(project_id?)
  pm_compare_plan_vs_actual(date, actor?)


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
7. GAPS FOR PLANNING — STRUCTURED ANALYSIS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

A. TEMPORAL SCHEDULING — MISSING ENTIRELY
  - No scheduled_for, planned_date, start_date, due_date on nodes
  - No time_window (e.g., "block 9am-11am on Monday for this task")
  - No deadline enforcement (no validation that done before due_date)
  - Only temporal field on any work item: milestone.target_date (coarse, optional)
  - Impact: Cannot express "work on X on 2026-04-10" in any data-model-supported way

B. MULTI-ACTOR ASSIGNMENT — PARTIAL (foundation exists, semantics missing)
  - actor field EXISTS on TimeEntry — proof of multi-actor awareness
  - actor field EXISTS on ActivityLog — who did what
  - assignee on Node is a raw string — no validation, no actor registry
  - actor on pm_create_node is for activity logging, not assignment
  - MISSING: role distinction (planner vs executor vs reviewer)
  - MISSING: "assigned by KH to V for execution" pattern
  - Impact: Can track who did work (via time_entry.actor) but cannot plan WHO
    will do work, or distinguish the planner from the executor

C. PLAN vs EXECUTION TRACKING — MISSING
  - No Plan entity (no table, no model, no API)
  - estimated_minutes approximates plan estimate (static field, not a versioned plan)
  - actual_time approximates execution result (computed from time_entries)
  - No "daily intention" record ("I plan to do A, B, C today")
  - No versioning if plan changes mid-day
  - Impact: Cannot answer "what did I plan vs what actually happened on 2026-04-08"

D. DAILY/WEEKLY/MONTHLY PLANNING — MISSING
  - No day planner query ("show me my plan for today")
  - No weekly view with slotted items
  - No intention system (distinct from status — "I intend to work on X" != "X is in_progress")
  - Dashboard shows today_time_minutes (actual work done) only
  - Impact: No planning horizon concept at any granularity

E. PRIORITY ORDERING WITHIN TIME WINDOWS — PARTIAL
  - priority field EXISTS (low/medium/high/critical) but is global, not time-scoped
  - No "position" or "order" field for sequencing within a day/week
  - No "do X before Y within the same day" constraint
  - Impact: Cannot create an ordered daily agenda ("first this, then that")

F. NODE QUERY CAPABILITIES — INCOMPLETE FOR PLANNING
  Current list_nodes filters: project_id, node_type, status, assignee, milestone_id
  MISSING:
    - scheduled_date (exact date match)
    - due_before / due_after (date range)
    - planned_for_actor + on_date
    - overdue (due_date < today AND status != done)
    - has_active_plan (linked to a plan entry)

G. FRONTEND PLANNER — ENTIRELY UNBUILT
  Current /planner page: tree browser (hierarchy view, not a planner)
  MISSING:
    - Calendar view (month/week/day)
    - Drag-and-drop scheduling
    - Time slot grid (e.g., 8am-6pm with blocks)
    - "Today Plan" widget
    - Weekly planner (Monday-Sunday grid)
    - Planned vs Actual comparison panel
    - Actor filter (show KH plan vs V plan)
    - Overdue / upcoming deadlines sidebar

H. METHODOLOGY HOOKS — NOT EXTENDED FOR PLANNING
  NodeTypeDefinition has: can_track_time, can_have_assignee
  MISSING hooks:
    - can_be_scheduled
    - can_have_due_date
    - planning_allowed_statuses (e.g., only schedule tasks in todo/ready state)
  Without this, planning rules cannot be methodology-aware


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
8. WHAT EXISTS THAT PLANNING CAN BUILD ON
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

These are real assets — not gaps — that a Planning feature can leverage:

  [+] priority field on Node — global ranking already exists
  [+] estimated_minutes on Node — planning duration already tracked
  [+] actual_time on Node — execution reality already tracked
  [+] actor on TimeEntry — multi-actor work already modeled
  [+] actor on ActivityLog — who-did-what already recorded
  [+] milestone.target_date — coarse deadline concept exists
  [+] get_active_timer/get_active_timers — actor-scoped current work known
  [+] today_time_minutes in Dashboard — daily actual time already computed
  [+] velocity_per_week in ProjectStats — throughput already measured
  [+] assignee on Node — assignment string field exists (needs enrichment)
  [+] list_nodes(assignee=X) — can already query by assignee
  [+] can_track_time in NodeTypeDefinition — methodology governs time; same hook
      can govern scheduling eligibility
  [+] Edge type "blocks" + depends_on — sequencing constraints already modeled
  [+] MCP tool pattern — all pm_* tools follow a consistent pattern; new planning
      tools can slot in cleanly


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
9. CANDIDATE ADDITIONS (not decisions — inputs for spec/design)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Data model:

  OPTION A — fields on Node:
    scheduled_date (DATE) — "work on this on 2026-04-10"
    due_date (DATE) — hard deadline
    planned_duration_minutes (INT) — distinct from estimated (intent vs estimate)
    Pros: simple; no new table; works with existing list_nodes filter pattern
    Cons: no versioning; no "daily plan as entity"; cannot reorder within a day

  OPTION B — new PlanEntry table:
    plan_id, date, actor, node_id, planned_minutes, display_order, created_at
    Pros: plans are entities; supports daily plan versioning; ordered agendas;
          multi-actor plans separate from node fields; plan vs actual is clear
    Cons: more complex; new query surface; UI must manage plan entities

Core modules (new):
  core/planning.py — create_daily_plan, get_daily_plan, compare_plan_vs_actual
  core/scheduling.py — schedule_node, reschedule, detect_conflicts, list_overdue

Query extensions:
  list_nodes: add scheduled_date, due_before, due_after, overdue=bool filters

Methodology extensions:
  NodeTypeDefinition: add can_be_scheduled, can_have_due_date flags

MCP tools (new):
  pm_schedule_node, pm_reschedule_node
  pm_get_daily_plan(date, actor?), pm_get_weekly_plan(week_start, actor?)
  pm_create_plan(date, actor, [{node_id, planned_minutes, order}])
  pm_compare_plan_vs_actual(date, actor?)
  pm_list_planned_nodes(date?, date_range?, actor?)
  pm_list_overdue_nodes(project_id?)

Frontend (rebuild /planner):
  Weekly grid view — 7-day columns, node cards draggable into time slots
  Today Plan widget — on Dashboard or dedicated Today page
  Planned vs Actual panel — side-by-side for a selected date
  Overdue / upcoming section — items past due, items due soon
  Actor filter — toggle between KH plan and V plan


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
END OF RESEARCH
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
