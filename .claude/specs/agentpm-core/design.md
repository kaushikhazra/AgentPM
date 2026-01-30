# AgentPM Core Business Logic - Design

## Module Structure

```
src/agentpm/
└── core/
    ├── __init__.py         # Re-export main functions
    ├── work_items.py       # High-level work item API
    ├── workflow.py         # Status workflow shortcuts
    ├── rollup.py           # Aggregation calculations
    ├── reporting.py        # Dashboard, stats, search
    └── bulk.py             # Bulk operations
```

## Work Items API (core/work_items.py)

### Methodology-Aware Helpers

```python
def create_story(
    project_id: str,
    title: str,
    description: str | None = None,
    milestone_id: str | None = None,
    priority: str = "medium",
    story_points: int | None = None,
    acceptance_criteria: str | None = None,
    actor: str | None = None
) -> Node:
    """
    Create a story node (or equivalent in current methodology).
    For classic_agile: creates node_type="story"
    """
    methodology = get_project_methodology(project_id)
    # Find the "story-like" node type (top-level work item)
    node_type = methodology.get_story_type()  # Returns "story", "spec", etc.

    properties = {}
    if acceptance_criteria:
        properties["acceptance_criteria"] = acceptance_criteria

    return create_node(
        project_id=project_id,
        node_type=node_type,
        title=title,
        description=description,
        milestone_id=milestone_id,
        priority=priority,
        story_points=story_points,
        properties=properties,
        actor=actor
    )

def create_task(
    parent_id: str,  # Story ID
    title: str,
    description: str | None = None,
    assignee: str | None = None,
    estimated_minutes: int | None = None,
    actor: str | None = None
) -> Node:
    """
    Create a task under a story (or equivalent hierarchy).
    Automatically creates parent edge.
    """
    parent = get_node(parent_id)
    methodology = get_project_methodology(parent.project_id)

    # Find the "task-like" node type (child of story)
    node_type = methodology.get_task_type()

    task = create_node(
        project_id=parent.project_id,
        node_type=node_type,
        title=title,
        description=description,
        assignee=assignee,
        estimated_minutes=estimated_minutes,
        actor=actor
    )

    # Create parent edge
    create_edge(
        source_id=task.id,
        target_id=parent_id,
        edge_type="parent",
        actor=actor
    )

    return task
```

## Workflow Shortcuts (core/workflow.py)

```python
def start_node(node_id: str, actor: str | None = None) -> Node:
    """
    Start working on a node:
    1. Transition to in_progress (or methodology equivalent)
    2. Start timer
    """
    node = get_node(node_id)
    methodology = get_project_methodology(node.project_id)

    in_progress_status = methodology.get_in_progress_status(node.node_type)

    # Update status
    node = update_node(node_id, status=in_progress_status, actor=actor)

    # Start timer
    start_timer(node_id, actor=actor)

    return node

def complete_node(node_id: str, actor: str | None = None) -> Node:
    """
    Complete a node:
    1. Stop any active timer
    2. Transition to terminal status (done)
    """
    node = get_node(node_id)
    methodology = get_project_methodology(node.project_id)

    done_status = methodology.get_done_status(node.node_type)

    # Stop timer if running
    stop_timer(node_id, actor=actor)

    # Update status (this also sets completed_at)
    return update_node(node_id, status=done_status, actor=actor)

def block_node(node_id: str, reason: str, actor: str | None = None) -> Node:
    """Block a node with a reason"""
    return update_node(
        node_id,
        status="blocked",
        blocked_reason=reason,
        actor=actor
    )

def unblock_node(node_id: str, actor: str | None = None) -> Node:
    """Unblock a node, returning to in_progress"""
    return update_node(
        node_id,
        status="in_progress",
        blocked_reason=None,
        actor=actor
    )
```

## Rollup Calculations (core/rollup.py)

```python
@dataclass
class RollupStats:
    total_time_minutes: int
    estimated_time_minutes: int
    total_nodes: int
    completed_nodes: int
    blocked_nodes: int
    completion_percentage: float
    story_points: int | None

def get_node_rollup(node_id: str) -> RollupStats:
    """
    Calculate aggregated stats for a node and all descendants.

    1. Get all descendants via graph traversal
    2. Sum time entries across all
    3. Sum estimates
    4. Count by status
    5. Calculate percentages
    """
    descendants = get_descendants(node_id, edge_type="parent")
    all_nodes = [get_node(node_id)] + descendants

    total_time = sum(get_time_total(n.id) for n in all_nodes)
    estimated = sum(n.estimated_minutes or 0 for n in all_nodes)

    completed = sum(1 for n in all_nodes if n.status in terminal_statuses)
    blocked = sum(1 for n in all_nodes if n.status == "blocked")

    return RollupStats(
        total_time_minutes=total_time,
        estimated_time_minutes=estimated,
        total_nodes=len(all_nodes),
        completed_nodes=completed,
        blocked_nodes=blocked,
        completion_percentage=completed / len(all_nodes) * 100 if all_nodes else 0,
        story_points=sum(n.story_points or 0 for n in all_nodes) or None
    )

def get_milestone_rollup(milestone_id: str) -> RollupStats:
    """Rollup for all nodes in a milestone"""

def get_project_rollup(project_id: str) -> RollupStats:
    """Rollup for entire project"""
```

## Reporting (core/reporting.py)

### Dashboard

```python
@dataclass
class Dashboard:
    active_timer: TimeEntry | None
    active_timer_node: Node | None
    in_progress_nodes: List[Node]
    blocked_nodes: List[Node]
    today_time_minutes: int
    recent_activity: List[ActivityLog]

def get_dashboard() -> Dashboard:
    """
    Get current state summary across all projects.
    """
    active_timer = get_active_timer()
    active_node = get_node(active_timer.node_id) if active_timer else None

    # Get all in-progress nodes
    in_progress = list_nodes(status="in_progress")

    # Get all blocked nodes
    blocked = list_nodes(status="blocked")

    # Calculate today's time
    today_start = datetime.now().replace(hour=0, minute=0, second=0)
    today_entries = list_time_entries_since(today_start)
    today_time = sum(e.duration_minutes or 0 for e in today_entries)

    # Recent activity
    recent = list_activity(limit=10)

    return Dashboard(
        active_timer=active_timer,
        active_timer_node=active_node,
        in_progress_nodes=in_progress,
        blocked_nodes=blocked,
        today_time_minutes=today_time,
        recent_activity=recent
    )
```

### Project Statistics

```python
@dataclass
class ProjectStats:
    total_nodes: Dict[str, int]  # by node_type
    nodes_by_status: Dict[str, int]
    time_this_week: int
    time_this_month: int
    time_total: int
    velocity_per_week: float  # avg completions per week
    blockers: List[Node]
    milestone_progress: List[MilestoneProgress]

def get_project_stats(project_id: str) -> ProjectStats:
    ...
```

### Search

```python
@dataclass
class SearchResult:
    entity_type: str  # 'node', 'milestone', 'project'
    entity: Node | Milestone | Project
    match_context: str  # snippet showing where match occurred
    relevance: float

def search(
    query: str,
    entity_types: List[str] | None = None,
    project_id: str | None = None,
    limit: int = 20
) -> List[SearchResult]:
    """
    Full-text search across entities.

    Uses SQLite LIKE for MVP, can upgrade to FTS5 later.
    """
    results = []

    # Search nodes
    if not entity_types or 'node' in entity_types:
        nodes = search_nodes(query, project_id)
        results.extend([
            SearchResult('node', n, extract_context(n, query), 1.0)
            for n in nodes
        ])

    # Search milestones
    if not entity_types or 'milestone' in entity_types:
        milestones = search_milestones(query, project_id)
        results.extend([
            SearchResult('milestone', m, extract_context(m, query), 0.9)
            for m in milestones
        ])

    # Sort by relevance
    return sorted(results, key=lambda r: r.relevance, reverse=True)[:limit]
```

## Bulk Operations (core/bulk.py)

```python
def bulk_move_to_milestone(
    node_ids: List[str],
    milestone_id: str,
    actor: str | None = None
) -> List[Node]:
    """Move multiple nodes to a milestone"""
    return [
        update_node(nid, milestone_id=milestone_id, actor=actor)
        for nid in node_ids
    ]

def bulk_update_status(
    node_ids: List[str],
    status: str,
    actor: str | None = None
) -> List[Node]:
    """Change status of multiple nodes (validates each transition)"""

def bulk_reassign(
    node_ids: List[str],
    assignee: str,
    actor: str | None = None
) -> List[Node]:
    """Reassign multiple nodes"""

def bulk_tag(
    node_ids: List[str],
    tag_name: str,
    actor: str | None = None
) -> List[Node]:
    """Add tag to multiple nodes"""

def bulk_delete(
    node_ids: List[str],
    actor: str | None = None
) -> int:
    """Delete multiple nodes, returns count deleted"""
```

## Methodology Extensions

Add helper methods to BaseMethodology:

```python
class BaseMethodology(ABC):
    # ... existing ...

    def get_story_type(self) -> str:
        """Return the top-level work item type"""
        # Default: first node type, override in subclasses

    def get_task_type(self) -> str:
        """Return the child work item type"""

    def get_in_progress_status(self, node_type: str) -> str:
        """Return the 'working on it' status for this node type"""

    def get_done_status(self, node_type: str) -> str:
        """Return the terminal 'completed' status"""

    def get_blocked_status(self, node_type: str) -> str | None:
        """Return blocked status if supported, else None"""
```
