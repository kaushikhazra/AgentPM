# AgentPM: Personal AI-First Project Management System

*Like Agent M from MIB, but for your projects.*

## Claude Code Implementation Plan

---

## 1. Project Overview

### What We're Building
A personal apm project management system designed for a solo developer working with AI agents. The system is "AI-first" meaning it's designed to be operated primarily through AI assistants (Claude, Claude Code) via MCP, with a CLI as the secondary interface.

### Core Philosophy
- **AI as the primary interface**: Talk to your PM system, don't click through it
- **Agents as participants**: AI agents can log their own work and update status
- **Everything rolls up**: Time and effort tracked at task level, aggregated up the hierarchy
- **Continuous flow**: No fixed sprints, milestones instead
- **Local-first**: SQLite database, runs on your machine, you own your data

### User
Single user (Kaushik) managing multiple personal/professional projects with AI assistance.

---

## 2. Data Model

### Design Philosophy: Methodology-Agnostic Graph

AgentPM is designed to support multiple agentic PM methodologies (Spec/Kiro, BMAD, PIV Loop, custom workflows) through a **typed graph system** with a stable anchor hierarchy.

**Core Insight**: All methodologies share some common structure (you have projects, you track time), but differ in:
- What entities exist (Stories vs Specs vs Artifacts)
- How entities relate (tree vs DAG vs cyclical)
- What agents/actors operate on them
- How work flows through states

**Architecture**:
```
┌─────────────────────────────────────────────────────────────┐
│  ANCHOR LAYER (stable across all methodologies)            │
│  Company → Project                                          │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  GRAPH LAYER (methodology-defined)                          │
│  Nodes: typed work items (Story, Task, Spec, Artifact...)  │
│  Edges: typed relationships (parent, depends_on, validates) │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  TRACKING LAYER (universal)                                 │
│  TimeEntry, ActivityLog, Tags (attach to any node)         │
└─────────────────────────────────────────────────────────────┘
```

### Built-in Methodologies (added programmatically)

Each methodology is a **Python class** in `agentpm/methodologies/` that defines:
- Valid node types and their schemas
- Valid edge types and constraints  
- State machines for each node type
- Rollup/aggregation rules for metrics
- CLI commands and MCP tools specific to that methodology

**1. Classic Agile** (default)
```
Story ──[parent]──► Task
  │                   │
  └── states: backlog, ready, in_progress, done
                      └── states: todo, in_progress, blocked, in_review, done
```

**2. Spec-Driven** (Kiro-style)
```
Spec ──[gates]──► Design ──[gates]──► Implementation ──[validates]──► Validation
  │
  └── Each gate requires approval before next phase
  └── Validation can fail and loop back to Implementation
```

**3. BMAD** (Agent-centric)
```
Orchestrator
    ├──[delegates]──► SpecialistAgent ──[produces]──► Artifact
    ├──[delegates]──► SpecialistAgent ──[produces]──► Artifact
    └── Agents are first-class trackable entities
```

**4. PIV Loop** (Cyclical)
```
Plan ──► Implement ──► Validate ──┐
  ▲                               │
  └───────────[iterates]──────────┘
```

### Default Hierarchy (Classic Agile)
```
Company (context boundary)
└── Project (methodology: classic_agile)
    └── Milestone (optional grouping)
        └── Story
            └── Task
                └── TimeEntry
```

### Database Schema (SQLite)

```sql
-- ============================================================
-- ANCHOR LAYER: Stable across all methodologies
-- ============================================================

-- Companies act as top-level containers/contexts
CREATE TABLE companies (
    id TEXT PRIMARY KEY,  -- UUID
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Projects belong to a company and specify their methodology
CREATE TABLE projects (
    id TEXT PRIMARY KEY,
    company_id TEXT NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    methodology TEXT NOT NULL DEFAULT 'classic_agile',  -- 'classic_agile', 'spec_driven', 'bmad', 'piv_loop', etc.
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'on_hold', 'completed', 'archived')),
    config JSON,  -- Methodology-specific configuration
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Milestones remain universal (optional groupings within a project)
CREATE TABLE milestones (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    target_date DATE,
    status TEXT DEFAULT 'open' CHECK (status IN ('open', 'completed')),
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- GRAPH LAYER: Methodology-defined nodes and edges
-- ============================================================

-- Generic work items (nodes in the graph)
-- Type determines schema validation via methodology class
CREATE TABLE nodes (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    milestone_id TEXT REFERENCES milestones(id) ON DELETE SET NULL,
    
    -- Type system (validated by methodology)
    node_type TEXT NOT NULL,  -- 'story', 'task', 'spec', 'design', 'artifact', 'agent', etc.
    
    -- Common fields (all nodes have these)
    title TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL,  -- Valid statuses defined by methodology per node_type
    assignee TEXT,  -- Human or AI agent identifier
    
    -- Effort tracking (optional, depends on node_type)
    estimated_minutes INTEGER,
    story_points INTEGER,
    
    -- Metadata
    priority TEXT DEFAULT 'medium',
    blocked_reason TEXT,
    
    -- Extensible properties (methodology-specific fields)
    properties JSON,  -- e.g., {"acceptance_criteria": "...", "gate_approved": true}
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- Relationships between nodes (edges in the graph)
-- Edge types and constraints defined by methodology
CREATE TABLE edges (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    
    -- The relationship
    source_id TEXT NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
    target_id TEXT NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
    edge_type TEXT NOT NULL,  -- 'parent', 'depends_on', 'validates', 'produces', 'gates', 'iterates', etc.
    
    -- Edge metadata
    properties JSON,  -- e.g., {"approved": true, "approved_by": "kaushik", "approved_at": "..."}
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Prevent duplicate edges of same type between same nodes
    UNIQUE(source_id, target_id, edge_type)
);

-- ============================================================
-- TRACKING LAYER: Universal, attaches to any node
-- ============================================================

-- Time entries attach to any node
CREATE TABLE time_entries (
    id TEXT PRIMARY KEY,
    node_id TEXT NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
    started_at TIMESTAMP NOT NULL,
    ended_at TIMESTAMP,  -- NULL if currently running
    duration_minutes INTEGER,  -- Calculated or manual
    notes TEXT,
    source TEXT DEFAULT 'manual',  -- 'manual', 'cli', 'mcp', 'claude_code'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tags can attach to any node
CREATE TABLE tags (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    color TEXT  -- Hex color for UI later
);

CREATE TABLE node_tags (
    node_id TEXT REFERENCES nodes(id) ON DELETE CASCADE,
    tag_id TEXT REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (node_id, tag_id)
);

-- Activity log tracks all changes (already methodology-agnostic)
CREATE TABLE activity_log (
    id TEXT PRIMARY KEY,
    entity_type TEXT NOT NULL,  -- 'node', 'edge', 'project', 'milestone', etc.
    entity_id TEXT NOT NULL,
    node_type TEXT,  -- If entity_type='node', what kind? (for filtering)
    action TEXT NOT NULL,  -- 'created', 'status_changed', 'time_logged', 'edge_added', etc.
    old_value TEXT,
    new_value TEXT,
    actor TEXT,  -- 'kaushik', 'claude', 'claude_code', 'ai_scripter', 'system'
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- INDEXES
-- ============================================================

-- Anchor layer
CREATE INDEX idx_projects_company ON projects(company_id);
CREATE INDEX idx_projects_methodology ON projects(methodology);
CREATE INDEX idx_milestones_project ON milestones(project_id);

-- Graph layer
CREATE INDEX idx_nodes_project ON nodes(project_id);
CREATE INDEX idx_nodes_type ON nodes(node_type);
CREATE INDEX idx_nodes_status ON nodes(status);
CREATE INDEX idx_nodes_assignee ON nodes(assignee);
CREATE INDEX idx_nodes_milestone ON nodes(milestone_id);
CREATE INDEX idx_edges_source ON edges(source_id);
CREATE INDEX idx_edges_target ON edges(target_id);
CREATE INDEX idx_edges_type ON edges(edge_type);
CREATE INDEX idx_edges_project ON edges(project_id);

-- Tracking layer
CREATE INDEX idx_time_entries_node ON time_entries(node_id);
CREATE INDEX idx_activity_log_entity ON activity_log(entity_type, entity_id);
CREATE INDEX idx_activity_log_node_type ON activity_log(node_type);
CREATE INDEX idx_activity_log_created ON activity_log(created_at);
```

### Key Design Decisions
1. **UUIDs for IDs**: Enables offline creation, sync-friendly
2. **Generic `nodes` table**: Any work item type lives here, validated by methodology
3. **Generic `edges` table**: Any relationship type, methodology defines what's valid
4. **JSON `properties` field**: Methodology-specific fields without schema migration
5. **Methodology as code**: Python classes define valid types, states, transitions
6. **Time entries on nodes**: Track time on any node type, not just "tasks"
7. **Activity log is universal**: Works across all methodologies

### Methodology System (Programmatic, Not Config)

Each methodology is a Python class that inherits from `BaseMethodology`. **No YAML/JSON config** — methodologies are code so they can have validation logic, computed properties, and custom behaviors.

```python
# agentpm/methodologies/base.py
from abc import ABC, abstractmethod
from typing import Dict, List, Set
from pydantic import BaseModel

class NodeTypeDefinition(BaseModel):
    """Defines a valid node type for this methodology"""
    name: str  # e.g., 'story', 'task', 'spec'
    valid_statuses: List[str]
    initial_status: str
    terminal_statuses: Set[str]  # Statuses that mean "done"
    allowed_transitions: Dict[str, List[str]]  # state -> [valid next states]
    required_properties: List[str] = []
    optional_properties: List[str] = []
    can_track_time: bool = True
    can_have_assignee: bool = True

class EdgeTypeDefinition(BaseModel):
    """Defines a valid edge type for this methodology"""
    name: str  # e.g., 'parent', 'depends_on', 'validates'
    source_types: List[str]  # Which node types can be source
    target_types: List[str]  # Which node types can be target
    max_per_source: int | None = None  # e.g., 1 for 'parent' (tree structure)
    max_per_target: int | None = None
    allows_cycles: bool = False

class BaseMethodology(ABC):
    """Base class for all methodologies"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier: 'classic_agile', 'spec_driven', etc."""
        pass
    
    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable name"""
        pass
    
    @property
    @abstractmethod
    def node_types(self) -> Dict[str, NodeTypeDefinition]:
        """All valid node types for this methodology"""
        pass
    
    @property
    @abstractmethod
    def edge_types(self) -> Dict[str, EdgeTypeDefinition]:
        """All valid edge types for this methodology"""
        pass
    
    def validate_node(self, node: dict) -> List[str]:
        """Return list of validation errors, empty if valid"""
        pass
    
    def validate_edge(self, edge: dict, source: dict, target: dict) -> List[str]:
        """Return list of validation errors, empty if valid"""
        pass
    
    def on_status_change(self, node: dict, old_status: str, new_status: str):
        """Hook for side effects when status changes (e.g., cascade updates)"""
        pass
    
    def compute_rollup(self, project_id: str) -> dict:
        """Compute aggregated metrics for the project"""
        pass
```

**Example: Classic Agile Methodology**
```python
# agentpm/methodologies/classic_agile.py

class ClassicAgileMethodology(BaseMethodology):
    name = "classic_agile"
    display_name = "Classic Agile"
    
    @property
    def node_types(self):
        return {
            "story": NodeTypeDefinition(
                name="story",
                valid_statuses=["backlog", "ready", "in_progress", "done", "cancelled"],
                initial_status="backlog",
                terminal_statuses={"done", "cancelled"},
                allowed_transitions={
                    "backlog": ["ready", "cancelled"],
                    "ready": ["in_progress", "backlog", "cancelled"],
                    "in_progress": ["done", "ready", "cancelled"],
                    "done": [],
                    "cancelled": [],
                },
                optional_properties=["acceptance_criteria", "story_points"],
            ),
            "task": NodeTypeDefinition(
                name="task",
                valid_statuses=["todo", "in_progress", "blocked", "in_review", "done", "cancelled"],
                initial_status="todo",
                terminal_statuses={"done", "cancelled"},
                allowed_transitions={
                    "todo": ["in_progress", "cancelled"],
                    "in_progress": ["blocked", "in_review", "done", "todo", "cancelled"],
                    "blocked": ["in_progress", "cancelled"],
                    "in_review": ["done", "in_progress", "cancelled"],
                    "done": [],
                    "cancelled": [],
                },
            ),
        }
    
    @property
    def edge_types(self):
        return {
            "parent": EdgeTypeDefinition(
                name="parent",
                source_types=["task"],
                target_types=["story"],
                max_per_source=1,  # A task has exactly one parent story
                allows_cycles=False,
            ),
            "depends_on": EdgeTypeDefinition(
                name="depends_on",
                source_types=["task", "story"],
                target_types=["task", "story"],
                allows_cycles=False,
            ),
        }
```

**Adding a New Methodology**

To add Spec-Driven (Kiro-style):
1. Create `agentpm/methodologies/spec_driven.py`
2. Define node types: `spec`, `design`, `implementation`, `validation`
3. Define edge types: `gates` (with approval logic), `validates`
4. Implement custom hooks for gate approval workflow
5. Register in `agentpm/methodologies/__init__.py`

The CLI and MCP tools automatically adapt — they read from the methodology to know what commands/tools are valid for that project.

---

## 3. MCP Server Design

### Overview
The MCP server exposes the PM system to AI assistants. This is the PRIMARY interface.

### Technology
- **Language**: Python (aligns with Kaushik's Pydantic AI work)
- **MCP SDK**: Use the official `mcp` Python package
- **Transport**: stdio (for Claude Code) and SSE (for Claude.ai if needed later)

### Tools to Expose

#### Company Management
```
pm_list_companies() -> List[Company]
pm_create_company(name, description?) -> Company
pm_get_company(id) -> Company with projects summary
```

#### Project Management
```
pm_list_projects(company_id?, status?) -> List[Project]
pm_create_project(company_id, name, methodology?, description?) -> Project
pm_get_project(id) -> Project with methodology info and stats
pm_update_project(id, status?, name?, description?) -> Project
pm_get_methodology_info(project_id) -> MethodologyInfo (valid node types, edge types, statuses)
```

#### Milestone Management
```
pm_list_milestones(project_id, status?) -> List[Milestone]
pm_create_milestone(project_id, name, target_date?, description?) -> Milestone
pm_complete_milestone(id) -> Milestone
```

#### Node Management (Generic, Methodology-Aware)
```
pm_list_nodes(project_id, node_type?, status?, assignee?) -> List[Node]
pm_create_node(project_id, node_type, title, description?, properties?) -> Node
pm_get_node(id) -> Node with edges and time entries
pm_update_node(id, status?, assignee?, properties?) -> Node
pm_start_node(id) -> Node (sets to in_progress status, starts time entry)
pm_complete_node(id) -> Node (sets to terminal status, ends active time entry)
pm_block_node(id, reason) -> Node
```

#### Edge/Relationship Management
```
pm_list_edges(project_id?, source_id?, target_id?, edge_type?) -> List[Edge]
pm_create_edge(source_id, target_id, edge_type, properties?) -> Edge
pm_delete_edge(id) -> void
pm_get_ancestors(node_id, edge_type?) -> List[Node]
pm_get_descendants(node_id, edge_type?) -> List[Node]
```

#### Time Tracking (Works on Any Node)
```
pm_start_timer(node_id, notes?) -> TimeEntry
pm_stop_timer(node_id?, entry_id?) -> TimeEntry (stops active timer)
pm_log_time(node_id, duration_minutes, notes?) -> TimeEntry (manual entry)
pm_get_active_timer() -> TimeEntry | None
```

#### Reporting / Queries
```
pm_get_dashboard() -> Dashboard summary (active nodes, time today, blockers)
pm_get_project_stats(project_id) -> Stats (velocity, completion rate, time spent)
pm_search(query) -> List of matching entities across types
pm_get_recent_activity(limit?, entity_type?, entity_id?) -> List[ActivityLog]
pm_get_rollup(node_id) -> RollupStats (aggregated time, effort from descendants)
```

#### Tags
```
pm_list_tags() -> List[Tag]
pm_create_tag(name, color?) -> Tag
pm_tag_node(node_id, tag_name) -> Node
pm_untag_node(node_id, tag_name) -> Node
```

### MCP Resources (Read-only context)
```
pm://dashboard - Current state summary
pm://project/{id} - Project details with methodology
pm://project/{id}/methodology - Valid types, statuses, transitions for this project
pm://node/{id} - Node details with edges
pm://activity/recent - Recent activity feed
```

### Example Interactions

**User to Claude**: "What am I working on right now?"
```
Claude calls: pm_get_dashboard()
Returns: Active task "Implement MCP server" on Mythline, timer running 47 min
```

**User to Claude**: "Create a task under the scripter story to add error handling"
```
Claude calls: pm_create_task(story_id="...", title="Add error handling to scripter", assignee="claude_code")
```

**Claude Code working**: "I'm starting work on the parser task"
```
Claude Code calls: pm_start_task(id="...")
```

**Claude Code done**: "Finished the parser implementation"
```
Claude Code calls: pm_complete_task(id="...")
```

---

## 4. CLI Design

### Overview
The CLI is the secondary interface for quick interactions and scripting.

### Technology
- **Language**: Python
- **Framework**: `typer` (modern, type-hinted CLI framework)
- **Output**: Rich formatting with `rich` library

### Command Structure

```bash
# Top-level command
apm [OPTIONS] COMMAND [ARGS]

# Global options
--db PATH        # Database path (default: ~/.agentpm/agentpm.db)
--json           # Output as JSON instead of formatted
--verbose        # Verbose output
```

### Commands

#### Company
```bash
apm company list
apm company create "Personal Projects" --description "My personal stuff"
apm company show <id>
```

#### Project
```bash
apm project list [--company <id>] [--status active|on_hold|completed|archived]
apm project create <company_id> "Mythline" --description "AI video production"
apm project show <id>
apm project update <id> --status on_hold
```

#### Milestone
```bash
apm milestone list <project_id>
apm milestone create <project_id> "MVP Release" --target 2025-03-01
apm milestone complete <id>
```

#### Story
```bash
apm story list [--project <id>] [--milestone <id>] [--status <status>]
apm story create <project_id> "Automated script generation" --priority high
apm story show <id>
apm story update <id> --status in_progress --milestone <mid>
```

#### Task
```bash
apm task list [--story <id>] [--status <status>] [--assignee <name>]
apm task create <story_id> "Implement output parser" --estimate 120 --assignee claude_code
apm task show <id>
apm task update <id> --status in_progress
apm task start <id>           # Sets in_progress + starts timer
apm task done <id>            # Sets done + stops timer
apm task block <id> "Waiting for API access"
```

#### Time Tracking
```bash
apm timer start <task_id> [--notes "Working on..."]
apm timer stop
apm timer status              # Show active timer
apm time log <task_id> 90 --notes "Debugging session"
```

#### Dashboard & Reporting
```bash
apm dashboard                 # Overview: active tasks, today's time, blockers
apm stats <project_id>        # Project statistics
apm activity [--limit 20]     # Recent activity
```

#### Search
```bash
apm search "scripter"         # Search across all entities
```

#### Tags
```bash
apm tag list
apm tag create "bug" --color "#ff0000"
apm tag add <task_id> bug
apm tag remove <task_id> bug
```

### Example CLI Session

```bash
$ apm dashboard
╭─ AgentPM Dashboard ─────────────────────────────────────╮
│                                                           │
│  🔥 Active Task: Implement MCP server                     │
│     Project: Mythline → Story: Agent Integration          │
│     Timer: 1h 23m running                                 │
│                                                           │
│  📊 Today: 3h 45m tracked across 4 tasks                 │
│                                                           │
│  🚧 Blockers: 1                                           │
│     - "API rate limiting" on Data fetcher task            │
│                                                           │
╰───────────────────────────────────────────────────────────╯

$ apm task start abc123
✓ Started task: "Add error handling"
  Timer running...

$ apm task done abc123
✓ Completed task: "Add error handling"
  Time logged: 45 minutes
```

---

## 5. Project Structure

```
agentpm/
├── README.md
├── pyproject.toml              # Poetry or pip package config
├── .env.example
│
├── src/
│   └── agentpm/
│       ├── __init__.py
│       ├── config.py           # Configuration management
│       │
│       ├── db/
│       │   ├── __init__.py
│       │   ├── connection.py   # SQLite connection management
│       │   ├── schema.sql      # Schema file (graph-based)
│       │   ├── migrations/     # Future migrations
│       │   └── models.py       # Pydantic models (Node, Edge, etc.)
│       │
│       ├── methodologies/      # 🆕 Methodology definitions (code, not config)
│       │   ├── __init__.py     # Registry of all methodologies
│       │   ├── base.py         # BaseMethodology ABC
│       │   ├── classic_agile.py    # Story → Task (default)
│       │   ├── spec_driven.py      # Spec → Design → Impl → Validation
│       │   ├── bmad.py             # Agent → Task → Artifact
│       │   └── piv_loop.py         # Plan → Implement → Validate (cyclic)
│       │
│       ├── graph/              # 🆕 Graph operations layer
│       │   ├── __init__.py
│       │   ├── nodes.py        # Node CRUD (generic, type-validated)
│       │   ├── edges.py        # Edge CRUD (generic, type-validated)
│       │   ├── traversal.py    # Graph queries (ancestors, descendants, paths)
│       │   └── validation.py   # Validates against methodology rules
│       │
│       ├── core/               # Business logic (uses graph layer)
│       │   ├── __init__.py
│       │   ├── company.py      # Company CRUD operations
│       │   ├── project.py      # Project CRUD (includes methodology selection)
│       │   ├── milestone.py    # Milestone CRUD operations
│       │   ├── work_items.py   # High-level API for nodes (creates via methodology)
│       │   ├── time_entry.py   # Time tracking operations
│       │   ├── tag.py          # Tag operations
│       │   ├── activity.py     # Activity logging
│       │   └── reporting.py    # Dashboard, stats, rollups
│       │
│       ├── mcp/
│       │   ├── __init__.py
│       │   ├── server.py       # MCP server setup
│       │   ├── tools.py        # Tool definitions (methodology-aware)
│       │   └── resources.py    # Resource definitions
│       │
│       └── cli/
│           ├── __init__.py
│           ├── main.py         # Typer app entry point
│           ├── company.py      # Company commands
│           ├── project.py      # Project commands (--methodology flag)
│           ├── milestone.py    # Milestone commands
│           ├── node.py         # 🆕 Generic node commands (methodology-aware)
│           ├── edge.py         # 🆕 Relationship commands
│           ├── timer.py        # Time tracking commands
│           ├── dashboard.py    # Dashboard & reporting
│           └── formatting.py   # Rich output helpers
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py             # Pytest fixtures
│   ├── test_db/
│   ├── test_methodologies/     # 🆕 Test each methodology
│   ├── test_graph/             # 🆕 Test graph operations
│   ├── test_core/
│   ├── test_mcp/
│   └── test_cli/
│
└── scripts/
    ├── init_db.py              # Initialize database
    └── seed_data.py            # Optional: seed sample data
```

---

## 6. Implementation Phases

### Phase 1: Foundation + Methodology System (Day 1-2)
**Goal**: Working database, base methodology system, anchor layer

1. Set up project structure with pyproject.toml
2. Create SQLite connection management
3. Implement graph-based schema creation/initialization
4. Create Pydantic models: `Node`, `Edge`, `Company`, `Project`, `Milestone`
5. Implement `BaseMethodology` ABC
6. Implement `ClassicAgileMethodology` (default)
7. Implement CRUD for Company, Project (with methodology selection)
8. Write tests for database and methodology validation

**Deliverable**: Can create projects with classic_agile methodology via Python code

### Phase 2: Graph Layer + Tracking (Day 2-3)
**Goal**: Full graph operations working

1. Implement `graph/nodes.py` — Node CRUD with type validation
2. Implement `graph/edges.py` — Edge CRUD with relationship validation
3. Implement `graph/traversal.py` — ancestors, descendants, paths
4. Implement `graph/validation.py` — validates against methodology rules
5. Implement Milestone CRUD
6. Implement TimeEntry (attaches to any node)
7. Implement Tag system (attaches to any node)
8. Implement Activity logging (auto-log on changes)
9. Write tests for graph operations

**Deliverable**: Can create nodes, edges, track time via Python code

### Phase 3: Core Business Logic (Day 3-4)
**Goal**: High-level API that wraps graph operations

1. Implement `core/work_items.py` — creates nodes/edges via methodology
2. Implement status transitions with validation
3. Implement rollup calculations (time, effort up the graph)
4. Implement `core/reporting.py` — dashboard, stats, search
5. Write tests for business logic

**Deliverable**: Clean API for all operations, methodology-aware

### Phase 4: CLI (Day 4-5)
**Goal**: Usable command-line interface

1. Set up Typer app structure
2. Implement company, project commands (--methodology flag)
3. Implement milestone commands
4. Implement generic node commands (aware of methodology types)
5. Implement edge/relationship commands
6. Implement timer commands
7. Implement dashboard and stats
8. Add rich formatting for output
9. Test CLI end-to-end

**Deliverable**: Fully functional CLI that adapts to project methodology

### Phase 5: MCP Server (Day 5-6)
**Goal**: AI-accessible interface

1. Set up MCP server with Python SDK
2. Implement all tools (wrapping core functions)
3. Make tools methodology-aware (return valid types/transitions)
4. Implement resources for read-only access
5. Add proper error handling and validation
6. Test with Claude Code
7. Document MCP setup for claude_desktop_config.json

**Deliverable**: Claude and Claude Code can manage projects

### Phase 6: Polish & Additional Methodologies (Day 6-7)
**Goal**: Production-ready, multiple methodologies

1. Add comprehensive error messages
2. Improve CLI help text
3. Write README with setup instructions
4. Create example workflows per methodology
5. Implement `SpecDrivenMethodology` (Kiro-style) as second methodology
6. Add database backup utility
7. Performance testing with realistic data

**Deliverable**: Ready for daily use, extensible for new methodologies

---

## 7. Technical Decisions & Notes

### Why SQLite?
- Single file, easy backup (just copy the file)
- No server to manage
- Fast enough for personal use (thousands of tasks is fine)
- Full SQL for complex queries
- Works offline

### Why Python?
- Aligns with Kaushik's Pydantic AI work
- Excellent MCP SDK support
- Typer makes great CLIs
- Easy to extend later

### Why UUIDs?
- Can create entities offline
- No coordination needed
- Merge-friendly if you ever want sync
- Use `uuid.uuid4().hex` for compact strings

### Timestamp Handling
- Store as ISO8601 strings in SQLite
- Use UTC everywhere
- Convert to local time only for display

### MCP Configuration
After building, add to `~/.claude/claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "agentpm": {
      "command": "python",
      "args": ["-m", "agentpm.mcp.server"],
      "env": {
        "AGENTPM_DB": "/path/to/agentpm.db"
      }
    }
  }
}
```

### Future Considerations (Not in MVP)
- Web UI (React? SvelteKit?)
- Sync across machines (CRDTs? Simple git-based?)
- Integrations (GitHub issues, calendar)
- AI insights ("you're spending a lot of time on blocked tasks")
- Pomodoro mode for timer
- Recurring tasks

---

## 8. Validation Checklist

Before considering each phase complete:

### Database Layer
- [ ] Can create/read/update/delete all entities
- [ ] Foreign key constraints enforced
- [ ] Activity automatically logged on changes
- [ ] No orphaned records possible

### CLI
- [ ] All commands have --help
- [ ] JSON output works for all commands
- [ ] Error messages are helpful
- [ ] Dashboard shows meaningful data
- [ ] Timer start/stop works correctly

### MCP Server
- [ ] All tools accessible from Claude
- [ ] Errors return useful messages
- [ ] Resources load correctly
- [ ] Works with Claude Code

### Overall
- [ ] Can complete a full workflow: create company → project → story → task → log time → complete
- [ ] Search finds entities across types
- [ ] Stats calculate correctly
- [ ] Activity log captures all changes

---

## 9. Sample Data for Testing

```python
# Use this to verify the system works end-to-end

# Company
personal = create_company("Personal", "Personal projects and learning")

# Project
mythline = create_project(personal.id, "Mythline", "AI-powered WoW video production")

# Milestone
mvp = create_milestone(mythline.id, "MVP", target_date="2025-03-01")

# User Story
story = create_story(
    mythline.id,
    "Automated Script Generation",
    description="As a content creator, I want AI to generate video scripts from quest data",
    priority="high",
    milestone_id=mvp.id
)

# Tasks
task1 = create_task(story.id, "Design script output format", estimated_minutes=60, assignee="kaushik")
task2 = create_task(story.id, "Implement scripter agent", estimated_minutes=180, assignee="claude_code")
task3 = create_task(story.id, "Add error handling", estimated_minutes=90, assignee="claude_code")

# Time tracking
start_task(task1.id)
# ... work ...
complete_task(task1.id)
```

---

## 10. Commands for Claude Code

When starting work, tell Claude Code:

> I'm building AgentPM, a personal project management system. Here's the full plan: [this document]
> 
> Start with Phase 1. Create the project structure and implement the database layer with SQLite.
> 
> Key requirements:
> - Use Python with Pydantic for models
> - SQLite for storage
> - Follow the schema exactly as specified
> - Write tests as you go
> - Use the project structure outlined in section 5

For subsequent phases:

> Continue with Phase [N] of the AgentPM plan. [Any specific notes or changes]

---

*Plan created: January 2025*
*Author: Claude (with Kaushik)*
*Version: 1.0*
