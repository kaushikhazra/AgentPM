# AgentPM Foundation - Design

## Architecture Overview

AgentPM uses a 3-layer architecture:

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

## Project Structure (Phase 1 Scope)

```
agentpm/
├── pyproject.toml
├── src/
│   └── agentpm/
│       ├── __init__.py
│       ├── config.py              # Configuration management
│       ├── db/
│       │   ├── __init__.py
│       │   ├── connection.py      # SQLite connection management
│       │   ├── schema.sql         # Full schema
│       │   └── models.py          # Pydantic models
│       ├── methodologies/
│       │   ├── __init__.py        # Registry
│       │   ├── base.py            # BaseMethodology ABC
│       │   └── classic_agile.py   # Default methodology
│       └── core/
│           ├── __init__.py
│           ├── company.py         # Company CRUD
│           └── project.py         # Project CRUD
└── tests/
    ├── conftest.py
    ├── test_db/
    ├── test_methodologies/
    └── test_core/
```

## Database Schema

### Anchor Layer Tables

```sql
CREATE TABLE companies (
    id TEXT PRIMARY KEY,  -- UUID
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE projects (
    id TEXT PRIMARY KEY,
    company_id TEXT NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    methodology TEXT NOT NULL DEFAULT 'classic_agile',
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'on_hold', 'completed', 'archived')),
    config JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

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
```

### Graph Layer Tables

```sql
CREATE TABLE nodes (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    milestone_id TEXT REFERENCES milestones(id) ON DELETE SET NULL,
    node_type TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL,
    assignee TEXT,
    estimated_minutes INTEGER,
    story_points INTEGER,
    priority TEXT DEFAULT 'medium',
    blocked_reason TEXT,
    properties JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE TABLE edges (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    source_id TEXT NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
    target_id TEXT NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
    edge_type TEXT NOT NULL,
    properties JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(source_id, target_id, edge_type)
);
```

### Tracking Layer Tables

```sql
CREATE TABLE time_entries (
    id TEXT PRIMARY KEY,
    node_id TEXT NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
    started_at TIMESTAMP NOT NULL,
    ended_at TIMESTAMP,
    duration_minutes INTEGER,
    notes TEXT,
    source TEXT DEFAULT 'manual',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE tags (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    color TEXT
);

CREATE TABLE node_tags (
    node_id TEXT REFERENCES nodes(id) ON DELETE CASCADE,
    tag_id TEXT REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (node_id, tag_id)
);

CREATE TABLE activity_log (
    id TEXT PRIMARY KEY,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    node_type TEXT,
    action TEXT NOT NULL,
    old_value TEXT,
    new_value TEXT,
    actor TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Methodology System Design

### Base Class

```python
class BaseMethodology(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def display_name(self) -> str: ...

    @property
    @abstractmethod
    def node_types(self) -> Dict[str, NodeTypeDefinition]: ...

    @property
    @abstractmethod
    def edge_types(self) -> Dict[str, EdgeTypeDefinition]: ...

    def validate_node(self, node: dict) -> List[str]: ...
    def validate_edge(self, edge: dict, source: dict, target: dict) -> List[str]: ...
    def validate_status_transition(self, node_type: str, old: str, new: str) -> bool: ...
```

### Classic Agile Methodology

**Node Types:**
- `story`: backlog → ready → in_progress → done/cancelled
- `task`: todo → in_progress → blocked → in_review → done/cancelled

**Edge Types:**
- `parent`: task → story (max 1 per task)
- `depends_on`: any → any (no cycles)

## Key Design Decisions

1. **UUIDs**: Use `uuid.uuid4().hex` for compact, offline-friendly IDs
2. **Timestamps**: Store as ISO8601 strings in UTC
3. **JSON properties**: Methodology-specific fields without schema migration
4. **Foreign keys enabled**: SQLite PRAGMA foreign_keys = ON
5. **Methodology as code**: Python classes, not YAML/JSON config

## Configuration

```python
# Default paths
DEFAULT_DB_PATH = "~/.agentpm/agentpm.db"

# Environment variables
AGENTPM_DB = os.getenv("AGENTPM_DB", DEFAULT_DB_PATH)
```
