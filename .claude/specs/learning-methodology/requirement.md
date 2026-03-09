# Learning Methodology — Requirements

## Overview

Taskyn's methodology system currently supports `classic_agile` (delivery-focused: epic → story → task) and `spec_driven` (gated workflow: spec → requirement/design/task → todo). Neither fits learning-oriented projects where the goal is skill/knowledge acquisition rather than software delivery.

The "Learning" project (5 epics, 34 stories, 70 tasks) currently shoehorns learning into `classic_agile`, losing the natural Research → Hands-on → Document lifecycle that characterizes learning work. Epics map to broad domains, stories to focused topics, tasks to activities — but the phase progression is implicit and untracked.

The `learning` methodology formalizes this with three node types (**subject**, **topic**, **activity**) and phase-based statuses on topics. Phases are advisory, not gated — a learner can skip from researching straight to documenting, or revisit an earlier phase. This distinguishes it from `spec_driven` which enforces strict phase gating.

---

## User Stories

### LM-1: Register the learning methodology

**As a** Taskyn developer,
**I want to** register a new `learning` methodology in the system,
**so that** projects can use it as their workflow.

**Acceptance Criteria:**
- `Methodology` enum in `enums.py` includes `LEARNING = "learning"`
- A `LearningMethodology` class exists in `methodologies/learning.py`, subclassing `BaseMethodology`
- The methodology is registered in `methodologies/__init__.py` at module load
- `methodology_exists("learning")` returns `True`
- `pm_get_methodology_info` returns the full definition when queried for a learning project

### LM-2: Subject node type (domain container)

**As a** learner,
**I want to** create subjects that represent broad learning domains,
**so that** I can organize my learning into high-level areas.

**Acceptance Criteria:**
- `subject` is a valid node type in the learning methodology
- Statuses: `planned` (initial) → `active` → `completed` → `archived`
- Allowed transitions: planned→active, active→completed, active→archived, completed→archived
- `can_track_time = False` (subjects are containers, not work items)
- `can_have_assignee = True`
- No required properties; optional properties: none for v1
- Subjects cannot have a parent (they are top-level)

### LM-3: Topic node type with phase-based statuses

**As a** learner,
**I want to** create topics that progress through research, practice, and documentation phases,
**so that** my learning follows a structured but flexible lifecycle.

**Acceptance Criteria:**
- `topic` is a valid node type in the learning methodology
- Statuses: `planned` (initial) → `researching` → `practicing` → `documenting` → `completed` → `archived`
- Transitions are non-gated — any forward or backward movement is allowed:
  - planned → researching, practicing, documenting, completed (can skip phases)
  - researching → practicing, documenting, completed (can skip ahead)
  - practicing → researching, documenting, completed (can go back)
  - documenting → researching, practicing, completed (can revisit)
  - completed → archived
  - Any active phase → archived (abandon)
- `can_track_time = False` (topics are containers; activities track time)
- `can_have_assignee = True`
- Terminal statuses: `completed`, `archived`
- Topics must have a subject as parent

### LM-4: Activity node type with time tracking

**As a** learner,
**I want to** create activities under topics that track my actual learning time,
**so that** I know how much effort each learning task takes.

**Acceptance Criteria:**
- `activity` is a valid node type in the learning methodology
- Statuses: `todo` (initial) → `in_progress` → `done` → `cancelled`
- Allowed transitions: todo→in_progress, in_progress→done, in_progress→cancelled
- `can_track_time = True` (this is the leaf work unit)
- `can_have_assignee = True`
- Terminal statuses: `done`, `cancelled`
- Activities must have a topic as parent
- `pm_start_node` on an activity starts a timer and sets status to `in_progress`
- `pm_complete_node` on an activity stops the timer and sets status to `done`

### LM-5: Hierarchy enforcement

**As the** system,
**I want to** enforce a strict three-level hierarchy (subject → topic → activity),
**so that** the learning structure remains consistent and navigable.

**Acceptance Criteria:**
- `valid_parent_pairs` enforces: topic parent must be subject, activity parent must be topic
- Creating a topic without a subject parent raises a validation error
- Creating an activity without a topic parent raises a validation error
- Creating a subject with a parent raises a validation error (subjects are root nodes)
- Edge type `parent` connects: topic→subject, activity→topic

### LM-6: Flexible phase navigation (non-gated)

**As a** learner,
**I want to** move between phases freely without being blocked by gating rules,
**so that** my learning workflow adapts to how I actually learn.

**Acceptance Criteria:**
- A topic in `researching` can jump directly to `documenting` (skip practice)
- A topic in `documenting` can go back to `researching` (revisit earlier phase)
- A topic in `planned` can jump directly to `completed` (already knew this)
- No activation gating — a topic does NOT require its parent subject to be `active`
- Activities under a topic can be started regardless of the topic's current phase status

### LM-7: Edge types for learning relationships

**As a** learner,
**I want to** link related topics and define learning paths,
**so that** I can see connections and recommended sequencing between learning areas.

**Acceptance Criteria:**
- Edge type `parent` exists for hierarchy (topic→subject, activity→topic)
- Edge type `relates_to` exists for cross-referencing (any→any, allows cycles)
- Edge type `depends_on` exists for advisory sequencing (any→any, acyclic)
- `depends_on` is **advisory only** — the system does NOT prevent starting work on a node whose dependency is incomplete. It documents the intended learning path.
- No `blocks` edge type (learning is non-blocking)
- `max_per_source = 1` for parent edges (tree structure)
- `relates_to` has no cardinality constraints
- `depends_on` has no cardinality constraints

### LM-8: Frontend methodology UI configuration

**As a** user viewing learning projects in the web UI,
**I want to** see appropriate labels, icons, and colors for learning node types and statuses,
**so that** the UI reflects the learning context, not delivery context.

**Acceptance Criteria:**
- `METHODOLOGY_UI.learning` exists in `methodology-ui.ts` with:
  - `displayName: "Learning"`
  - Node types: subject (with icon, color, plural), topic, activity
  - Status labels: planned, researching, practicing, documenting, completed, archived, todo, in_progress, done, cancelled
- `METHODOLOGY_HIERARCHY.learning` defines: subject→topic, topic→activity
- Kanban board groups topics by phase status (researching, practicing, documenting columns)
- Project creation modal offers "Learning" as a methodology option
- `getChildTypes("learning", "subject")` returns `["topic"]`
- `getChildTypes("learning", "topic")` returns `["activity"]`

### LM-9: Helper method overrides

**As a** developer using the methodology API,
**I want** the learning methodology to return correct helpers,
**so that** workflow functions operate correctly.

**Acceptance Criteria:**
- `get_story_type()` returns `"topic"` (maps to the primary work container)
- `get_task_type()` returns `"activity"` (maps to the time-tracking leaf)
- `get_in_progress_status()` returns `"in_progress"` (for activities)
- `get_done_status()` returns `"done"` (for activities) / `"completed"` (for subjects/topics)
- `get_blocked_status()` returns `None` (no blocked status in learning)
- `is_terminal_status("completed")` returns `True`
- `is_terminal_status("archived")` returns `True`
- `is_terminal_status("done")` returns `True`

---

## Infrastructure Dependencies

| Dependency | Status | Notes |
|-----------|--------|-------|
| `BaseMethodology` ABC | Exists | No changes needed — new class subclasses it |
| `Methodology` enum | Exists — needs new value | Add `LEARNING = "learning"` |
| Methodology registry | Exists | Register `LearningMethodology` instance |
| `workflow.py` | Exists | Already methodology-agnostic — no changes |
| MCP server | Exists | Already methodology-agnostic — no changes |
| Web backend routes | Exists | Already methodology-agnostic — no changes |
| `methodology-ui.ts` | Exists — needs new entry | Add learning methodology UI config |
| `METHODOLOGY_HIERARCHY` | Exists — needs new entry | Add learning hierarchy rules |
| Frontend query hooks | Exists | No changes needed |

---

## Configuration Summary

### New Files

```
src/taskyn/methodologies/learning.py    # LearningMethodology class
tests/test_learning_methodology.py      # Unit tests
```

### Modified Files

```
src/taskyn/db/enums.py                                          # Add LEARNING enum value
src/taskyn/methodologies/__init__.py                            # Register LearningMethodology
src/taskyn/web/frontend/src/config/methodology-ui.ts            # Add learning UI config
CLAUDE.md                                                        # Document learning methodology
```

---

## Out of Scope

- **Migration of the existing Learning project** from `classic_agile` to `learning` — this is a separate data migration task, not part of the methodology definition
- **Phase analytics** — completion rates per phase, average time in research vs. practice, etc.
- **Phase prerequisites/gating** — explicitly out of scope; phases are advisory
- **Topic templates** — pre-defined topic structures with suggested activities
- **External integrations** — linking to learning platforms, courses, or resources
- **Custom properties** — no required or optional properties on any node type for v1
- **Enforced dependency blocking** — `depends_on` is advisory; the system never prevents starting work based on incomplete dependencies
- **Blocked status** — learning work is not blockable; learners skip or revisit phases instead
