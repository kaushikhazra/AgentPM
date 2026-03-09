# Learning Methodology — Design

## Decisions Log

| # | Decision | Rationale |
|---|----------|-----------|
| D1 | Topic transitions are fully flexible (non-gated) | LM-3, LM-6: Learners skip, revisit, and jump between phases. Unlike spec_driven's strict gating. |
| D2 | `get_in_progress_status` varies by node type | LM-9: subject→`active`, topic→`researching`, activity→`in_progress`. Required for `pm_start_node` to pick the right status. |
| D3 | `relates_to` allows cycles; `depends_on` is acyclic | LM-7: Cross-referencing is bidirectional. Learning paths are directional (no circular deps). |
| D4 | Project creation dropdown needs manual update | LM-8: `ProjectsPage.tsx` hardcodes methodology options — add "Learning" option. |
| D5 | UI colors follow tier convention | LM-8: lavender=top (subject), sky=mid (topic), mint=leaf (activity) — matches epic/story/task and spec/requirement/todo patterns. |
| D6 | No activation gating on hierarchy | LM-6: Unlike spec_driven, topics don't require parent subject to be `active`. Activities don't require parent topic to be in any phase. |

---

## 1. LearningMethodology Class

_Traces to: LM-1, LM-2, LM-3, LM-4, LM-5, LM-6, LM-7, LM-9_

### 1.1 Node Type Definitions

```python
# src/taskyn/methodologies/learning.py

"""Learning methodology (Subject → Topic → Activity).

Hierarchy (3 levels, 3 node types):
    subject (Level 1 — domain container)
    └── topic (Level 2 — learning item with phase-based statuses)
        └── activity (Level 3 — leaf work unit, tracks time)

Subject statuses: planned → active → completed | archived
Topic statuses: planned → researching → practicing → documenting → completed | archived
Activity statuses: todo → in_progress → done | cancelled

Phases (researching/practicing/documenting) are advisory, not gated.
Learners can skip, revisit, or jump between phases freely.
"""

from taskyn.methodologies.base import (
    BaseMethodology,
    NodeTypeDefinition,
    EdgeTypeDefinition,
)

_ALL_TYPES = ["subject", "topic", "activity"]


class LearningMethodology(BaseMethodology):
    """Learning methodology with flexible phase-based workflow."""

    @property
    def name(self) -> str:
        return "learning"

    @property
    def display_name(self) -> str:
        return "Learning"

    @property
    def node_types(self) -> dict[str, NodeTypeDefinition]:
        return {
            "subject": NodeTypeDefinition(
                name="subject",
                valid_statuses=["planned", "active", "completed", "archived"],
                initial_status="planned",
                terminal_statuses={"completed", "archived"},
                allowed_transitions={
                    "planned": ["active", "archived"],
                    "active": ["completed", "archived"],
                    "completed": ["archived"],
                    "archived": [],
                },
                can_track_time=False,
                can_have_assignee=True,
            ),
            "topic": NodeTypeDefinition(
                name="topic",
                valid_statuses=[
                    "planned",
                    "researching",
                    "practicing",
                    "documenting",
                    "completed",
                    "archived",
                ],
                initial_status="planned",
                terminal_statuses={"completed", "archived"},
                allowed_transitions={
                    "planned": ["researching", "practicing", "documenting", "completed", "archived"],
                    "researching": ["practicing", "documenting", "completed", "archived"],
                    "practicing": ["researching", "documenting", "completed", "archived"],
                    "documenting": ["researching", "practicing", "completed", "archived"],
                    "completed": ["archived"],
                    "archived": [],
                },
                can_track_time=False,
                can_have_assignee=True,
            ),
            "activity": NodeTypeDefinition(
                name="activity",
                valid_statuses=["todo", "in_progress", "done", "cancelled"],
                initial_status="todo",
                terminal_statuses={"done", "cancelled"},
                allowed_transitions={
                    "todo": ["in_progress", "cancelled"],
                    "in_progress": ["done", "cancelled"],
                    "done": [],
                    "cancelled": [],
                },
                can_track_time=True,
                can_have_assignee=True,
            ),
        }

    @property
    def edge_types(self) -> dict[str, EdgeTypeDefinition]:
        return {
            "parent": EdgeTypeDefinition(
                name="parent",
                source_types=["topic", "activity"],
                target_types=["subject", "topic"],
                max_per_source=1,
                allows_cycles=False,
            ),
            "depends_on": EdgeTypeDefinition(
                name="depends_on",
                source_types=_ALL_TYPES,
                target_types=_ALL_TYPES,
                allows_cycles=False,
            ),
            "relates_to": EdgeTypeDefinition(
                name="relates_to",
                source_types=_ALL_TYPES,
                target_types=_ALL_TYPES,
                allows_cycles=True,
            ),
        }

    @property
    def valid_parent_pairs(self) -> dict[str, list[str]]:
        return {
            "topic": ["subject"],
            "activity": ["topic"],
        }

    def get_story_type(self) -> str:
        return "topic"

    def get_task_type(self) -> str:
        return "activity"

    def get_in_progress_status(self, node_type: str) -> str:
        if node_type == "activity":
            return "in_progress"
        if node_type == "topic":
            return "researching"
        return "active"

    def get_done_status(self, node_type: str) -> str:
        if node_type == "activity":
            return "done"
        return "completed"

    def get_blocked_status(self, node_type: str) -> str | None:
        return None  # Learning has no blocked status
```

### 1.2 Transition Diagram

```
Subject:    planned ──→ active ──→ completed ──→ archived
                  └──────────────→ archived ←─────┘

Topic:      planned ──→ researching ←──→ practicing
                  │         │                │
                  │         └──→ documenting ←┘
                  │              │
                  └──→ completed ←┘ ──→ archived
                  └──────────────────→ archived

Activity:   todo ──→ in_progress ──→ done
                          └──→ cancelled
              └──→ cancelled
```

---

## 2. Enum Registration

_Traces to: LM-1_

```python
# src/taskyn/db/enums.py

class Methodology(str, Enum):
    CLASSIC_AGILE = "classic_agile"
    SPEC_DRIVEN = "spec_driven"
    LEARNING = "learning"              # ← new
```

```python
# src/taskyn/methodologies/__init__.py

from taskyn.methodologies.learning import LearningMethodology  # ← new import

# At module load, after existing registrations:
_register_methodology(LearningMethodology())  # ← new registration
```

---

## 3. Frontend UI Configuration

_Traces to: LM-8_

### 3.1 Hierarchy

```typescript
// src/taskyn/web/frontend/src/config/methodology-ui.ts

export const METHODOLOGY_HIERARCHY: Record<string, Record<string, string | string[]>> = {
  // ... existing entries ...
  learning: {
    subject: 'topic',
    topic: 'activity',
  },
};
```

### 3.2 UI Metadata

```typescript
export const METHODOLOGY_UI: Record<string, MethodologyUI> = {
  // ... existing entries ...
  learning: {
    displayName: 'Learning',
    nodeTypes: {
      subject: {
        displayName: 'Subject',
        plural: 'Subjects',
        icon: 'SB',
        color: 'var(--accent-lavender)',
      },
      topic: {
        displayName: 'Topic',
        plural: 'Topics',
        icon: 'TP',
        color: 'var(--accent-sky)',
      },
      activity: {
        displayName: 'Activity',
        plural: 'Activities',
        icon: 'A',
        color: 'var(--accent-mint)',
      },
    },
    statusLabels: {
      planned: 'Planned',
      active: 'Active',
      researching: 'Researching',
      practicing: 'Practicing',
      documenting: 'Documenting',
      completed: 'Completed',
      archived: 'Archived',
      todo: 'To Do',
      in_progress: 'In Progress',
      done: 'Done',
      cancelled: 'Cancelled',
    },
  },
};
```

### 3.3 Project Creation Dropdown

```tsx
// src/taskyn/web/frontend/src/pages/ProjectsPage.tsx

<select ...>
  <option value="classic_agile">Classic Agile</option>
  <option value="spec_driven">Spec Driven</option>
  <option value="learning">Learning</option>           {/* ← new */}
</select>
```

---

## 4. CLAUDE.md Update

_Traces to: LM-1_

Add to the Methodologies section:

```markdown
## Methodologies

- `classic_agile`: story → task, statuses: backlog/ready/in_progress/done
- `spec_driven`: spec → design → implementation → validation (gated workflow)
- `learning`: subject → topic → activity, topic phases: planned/researching/practicing/documenting/completed (non-gated)
```

---

## 5. Files Changed

| File | Change |
|------|--------|
| `src/taskyn/methodologies/learning.py` | **New** — `LearningMethodology` class with 3 node types, 3 edge types, strict hierarchy |
| `src/taskyn/db/enums.py` | Add `LEARNING = "learning"` to `Methodology` enum |
| `src/taskyn/methodologies/__init__.py` | Import + register `LearningMethodology` |
| `src/taskyn/web/frontend/src/config/methodology-ui.ts` | Add `learning` to `METHODOLOGY_HIERARCHY` and `METHODOLOGY_UI` |
| `src/taskyn/web/frontend/src/pages/ProjectsPage.tsx` | Add "Learning" option to methodology `<select>` |
| `CLAUDE.md` | Document `learning` methodology in Methodologies section |
| `tests/test_learning_methodology.py` | **New** — Unit tests for node types, transitions, hierarchy, edge validation, helpers |

---

## Future Work (Out of Scope)

- **Migration tool** — Convert existing Learning project from classic_agile to learning methodology (separate task)
- **Phase analytics** — Time-per-phase aggregation, completion rates
- **Topic templates** — Pre-defined activity sets for common learning patterns
- **Kanban phase columns** — Custom column grouping by topic phase (currently groups by status, which works but could be more semantic)
