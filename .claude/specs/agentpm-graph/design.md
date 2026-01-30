# AgentPM Graph Layer - Design

## Module Structure

```
src/agentpm/
├── graph/
│   ├── __init__.py
│   ├── nodes.py        # Node CRUD operations
│   ├── edges.py        # Edge CRUD operations
│   ├── traversal.py    # Graph traversal algorithms
│   └── validation.py   # Methodology validation helpers
├── core/
│   ├── milestone.py    # Milestone CRUD
│   ├── time_entry.py   # Time tracking
│   ├── tag.py          # Tag operations
│   └── activity.py     # Activity logging
```

## Graph Layer Design

### Node Operations (graph/nodes.py)

```python
def create_node(
    project_id: str,
    node_type: str,
    title: str,
    description: str | None = None,
    assignee: str | None = None,
    milestone_id: str | None = None,
    estimated_minutes: int | None = None,
    story_points: int | None = None,
    priority: str = "medium",
    properties: dict | None = None,
    actor: str | None = None
) -> Node:
    """
    1. Get project's methodology
    2. Validate node_type exists in methodology
    3. Validate properties against methodology
    4. Set initial status from methodology
    5. Generate UUID
    6. Insert into database
    7. Log activity
    8. Return Node
    """

def update_node(
    node_id: str,
    title: str | None = None,
    description: str | None = None,
    status: str | None = None,
    assignee: str | None = None,
    # ... other fields
    actor: str | None = None
) -> Node:
    """
    1. Get existing node
    2. Get project's methodology
    3. If status change, validate transition
    4. If entering blocked status, require blocked_reason
    5. If entering terminal status, set completed_at
    6. Update database
    7. Log activity for each changed field
    8. Return updated Node
    """

def get_node(node_id: str) -> Node | None
def list_nodes(
    project_id: str | None = None,
    node_type: str | None = None,
    status: str | None = None,
    assignee: str | None = None,
    milestone_id: str | None = None,
    limit: int = 100,
    offset: int = 0
) -> List[Node]
def delete_node(node_id: str, actor: str | None = None) -> bool
```

### Edge Operations (graph/edges.py)

```python
def create_edge(
    source_id: str,
    target_id: str,
    edge_type: str,
    properties: dict | None = None,
    actor: str | None = None
) -> Edge:
    """
    1. Get source and target nodes
    2. Verify same project
    3. Get methodology
    4. Validate edge_type exists
    5. Validate source node_type allowed for this edge_type
    6. Validate target node_type allowed for this edge_type
    7. Check cardinality constraints (max_per_source, max_per_target)
    8. If allows_cycles=False, detect cycles
    9. Insert into database
    10. Log activity
    11. Return Edge
    """

def delete_edge(edge_id: str, actor: str | None = None) -> bool
def list_edges(
    project_id: str | None = None,
    source_id: str | None = None,
    target_id: str | None = None,
    edge_type: str | None = None
) -> List[Edge]
```

### Graph Traversal (graph/traversal.py)

```python
def get_ancestors(
    node_id: str,
    edge_type: str | None = None,
    max_depth: int | None = None
) -> List[Node]:
    """
    Follow edges where node is the source, return targets.
    Uses BFS to find all ancestors up to max_depth.
    """

def get_descendants(
    node_id: str,
    edge_type: str | None = None,
    max_depth: int | None = None
) -> List[Node]:
    """
    Follow edges where node is the target, return sources.
    Uses BFS to find all descendants up to max_depth.
    """

def get_parents(node_id: str, edge_type: str = "parent") -> List[Node]:
    """Direct parents only (depth=1)"""

def get_children(node_id: str, edge_type: str = "parent") -> List[Node]:
    """Direct children only (depth=1)"""

def detect_cycle(source_id: str, target_id: str, edge_type: str) -> bool:
    """
    Returns True if adding edge would create a cycle.
    Uses DFS from target to see if source is reachable.
    """
```

### Validation (graph/validation.py)

```python
def validate_node_creation(project_id: str, node_type: str, properties: dict) -> List[str]
def validate_node_update(node: Node, updates: dict) -> List[str]
def validate_status_transition(node: Node, new_status: str) -> bool
def validate_edge_creation(source: Node, target: Node, edge_type: str) -> List[str]
```

## Time Tracking Design

### Timer State Machine

```
[No Timer] --start--> [Running] --stop--> [Completed]
                          |
                          +---(auto-stop on new start)
```

### Operations (core/time_entry.py)

```python
def start_timer(node_id: str, notes: str | None = None, actor: str | None = None) -> TimeEntry:
    """
    1. Check for active timer
    2. If active, stop it first (auto-stop)
    3. Create new TimeEntry with started_at=now, ended_at=None
    4. Log activity
    5. Return TimeEntry
    """

def stop_timer(entry_id: str | None = None, actor: str | None = None) -> TimeEntry | None:
    """
    1. If entry_id provided, stop that entry
    2. Otherwise, find active timer and stop it
    3. Set ended_at=now
    4. Calculate duration_minutes
    5. Log activity
    6. Return TimeEntry or None if no active timer
    """

def log_time(
    node_id: str,
    duration_minutes: int,
    notes: str | None = None,
    actor: str | None = None
) -> TimeEntry:
    """Manual time entry (no timer, just duration)"""

def get_active_timer() -> TimeEntry | None
def list_time_entries(node_id: str) -> List[TimeEntry]
def get_time_total(node_id: str) -> int  # Total minutes
```

## Activity Logging Design

### Automatic Logging

Activity is logged automatically by core operations. Each function accepts an `actor` parameter.

```python
def log_activity(
    entity_type: str,      # 'node', 'edge', 'time_entry', 'milestone', etc.
    entity_id: str,
    action: str,           # 'created', 'status_changed', 'assigned', etc.
    old_value: str | None = None,
    new_value: str | None = None,
    node_type: str | None = None,  # For filtering
    actor: str | None = None,
    notes: str | None = None
) -> ActivityLog
```

### Standard Actions
- `created` - Entity was created
- `updated` - Generic update
- `status_changed` - Status field changed
- `assigned` - Assignee changed
- `deleted` - Entity was deleted
- `time_started` - Timer started
- `time_stopped` - Timer stopped
- `time_logged` - Manual time entry
- `tagged` - Tag added
- `untagged` - Tag removed
- `milestone_assigned` - Node assigned to milestone
- `milestone_completed` - Milestone marked complete

## Tag System Design

```python
def create_tag(name: str, color: str | None = None) -> Tag
def list_tags() -> List[Tag]
def delete_tag(tag_id: str) -> bool

def tag_node(node_id: str, tag_name: str, actor: str | None = None) -> Node
def untag_node(node_id: str, tag_name: str, actor: str | None = None) -> Node
def list_nodes_by_tag(tag_name: str) -> List[Node]
def get_node_tags(node_id: str) -> List[Tag]
```

## Error Handling

Custom exceptions in `agentpm/exceptions.py`:

```python
class AgentPMError(Exception): ...
class NotFoundError(AgentPMError): ...
class ValidationError(AgentPMError): ...
class InvalidTransitionError(ValidationError): ...
class CycleDetectedError(ValidationError): ...
class CardinalityError(ValidationError): ...
```
