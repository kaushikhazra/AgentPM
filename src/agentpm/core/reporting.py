"""Dashboard, statistics, and search functionality."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from agentpm.db.connection import fetchall
from agentpm.db.models import Node, Milestone, Project, TimeEntry, ActivityLog
from agentpm.core.project import get_project, list_projects
from agentpm.core.time_entry import get_active_timer, list_time_entries
from agentpm.core.activity import list_activity
from agentpm.core.milestone import list_milestones
from agentpm.core.rollup import get_milestone_rollup, RollupStats
from agentpm.exceptions import NotFoundError


@dataclass
class Dashboard:
    """Current state summary across all projects."""

    active_timer: TimeEntry | None
    active_timer_node: Node | None
    in_progress_nodes: list[Node]
    blocked_nodes: list[Node]
    today_time_minutes: int
    recent_activity: list[ActivityLog]


@dataclass
class MilestoneProgress:
    """Progress information for a milestone."""

    milestone: Milestone
    stats: RollupStats


@dataclass
class ProjectStats:
    """Project statistics."""

    total_nodes: dict[str, int]  # by node_type
    nodes_by_status: dict[str, int]
    time_this_week: int
    time_this_month: int
    time_total: int
    velocity_per_week: float  # avg completions per week
    blockers: list[Node]
    milestone_progress: list[MilestoneProgress]


@dataclass
class SearchResult:
    """Search result with context."""

    entity_type: str  # 'node', 'milestone', 'project'
    entity: Node | Milestone | Project
    match_context: str  # snippet showing where match occurred
    relevance: float


def list_time_entries_since(since: datetime) -> list[TimeEntry]:
    """List time entries since a given datetime."""
    rows = fetchall(
        """
        SELECT * FROM time_entries
        WHERE started_at >= ? OR (ended_at IS NOT NULL AND ended_at >= ?)
        ORDER BY started_at DESC
        """,
        (since, since),
    )
    return [_row_to_time_entry(row) for row in rows]


def _row_to_time_entry(row) -> TimeEntry:
    """Convert a database row to a TimeEntry model."""
    return TimeEntry(
        id=row["id"],
        node_id=row["node_id"],
        started_at=_parse_datetime(row["started_at"]),
        ended_at=_parse_datetime(row["ended_at"]) if row["ended_at"] else None,
        duration_minutes=row["duration_minutes"],
        notes=row["notes"],
        source=row["source"] or "manual",
        created_at=_parse_datetime(row["created_at"]),
    )


def _parse_datetime(value) -> datetime:
    """Parse a datetime from SQLite."""
    if isinstance(value, datetime):
        # Ensure it's timezone-aware
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value
    if isinstance(value, str):
        for fmt in [
            "%Y-%m-%d %H:%M:%S.%f",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%dT%H:%M:%S",
        ]:
            try:
                dt = datetime.strptime(value, fmt)
                return dt.replace(tzinfo=timezone.utc)
            except ValueError:
                continue
    return datetime.now(timezone.utc)


def get_dashboard() -> Dashboard:
    """
    Get current state summary across all projects.
    """
    from agentpm.graph import get_node, list_nodes

    active_timer = get_active_timer()
    active_node = get_node(active_timer.node_id) if active_timer else None

    # Get all in-progress nodes
    in_progress = list_nodes(status="in_progress")

    # Get all blocked nodes
    blocked = list_nodes(status="blocked")

    # Calculate today's time
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_entries = list_time_entries_since(today_start)
    today_time = sum(e.duration_minutes or 0 for e in today_entries)

    # Add active timer time if it started today
    if active_timer:
        timer_start = active_timer.started_at
        if timer_start.tzinfo is None:
            timer_start = timer_start.replace(tzinfo=timezone.utc)
        if timer_start >= today_start:
            elapsed = (now - timer_start).total_seconds() / 60
            today_time += int(elapsed)

    # Recent activity
    recent = list_activity(limit=10)

    return Dashboard(
        active_timer=active_timer,
        active_timer_node=active_node,
        in_progress_nodes=in_progress,
        blocked_nodes=blocked,
        today_time_minutes=today_time,
        recent_activity=recent,
    )


def get_project_stats(project_id: str) -> ProjectStats:
    """Get comprehensive project statistics."""
    from agentpm.graph import list_nodes

    project = get_project(project_id)
    if project is None:
        raise NotFoundError("Project", project_id)

    nodes = list_nodes(project_id=project_id)

    # Count by node_type
    total_nodes: dict[str, int] = {}
    for node in nodes:
        total_nodes[node.node_type] = total_nodes.get(node.node_type, 0) + 1

    # Count by status
    nodes_by_status: dict[str, int] = {}
    for node in nodes:
        nodes_by_status[node.status] = nodes_by_status.get(node.status, 0) + 1

    # Time calculations
    now = datetime.now(timezone.utc)
    week_start = now - timedelta(days=now.weekday())
    week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    time_total = 0
    time_this_week = 0
    time_this_month = 0

    for node in nodes:
        entries = list_time_entries(node.id)
        for entry in entries:
            duration = entry.duration_minutes or 0
            time_total += duration
            entry_start = entry.started_at
            if entry_start.tzinfo is None:
                entry_start = entry_start.replace(tzinfo=timezone.utc)
            if entry_start >= week_start:
                time_this_week += duration
            if entry_start >= month_start:
                time_this_month += duration

    # Velocity calculation (completions per week)
    completed_nodes = [n for n in nodes if n.completed_at is not None]
    if completed_nodes:
        # Find date range
        completion_dates = [n.completed_at for n in completed_nodes if n.completed_at]
        if completion_dates:
            earliest = min(completion_dates)
            weeks = max(1, (now - earliest).days / 7)
            velocity_per_week = round(len(completed_nodes) / weeks, 1)
        else:
            velocity_per_week = 0.0
    else:
        velocity_per_week = 0.0

    # Blockers
    blockers = [n for n in nodes if n.status == "blocked"]

    # Milestone progress
    milestones = list_milestones(project_id)
    milestone_progress = []
    for milestone in milestones:
        stats = get_milestone_rollup(milestone.id)
        milestone_progress.append(MilestoneProgress(milestone=milestone, stats=stats))

    return ProjectStats(
        total_nodes=total_nodes,
        nodes_by_status=nodes_by_status,
        time_this_week=time_this_week,
        time_this_month=time_this_month,
        time_total=time_total,
        velocity_per_week=velocity_per_week,
        blockers=blockers,
        milestone_progress=milestone_progress,
    )


def _extract_context(text: str | None, query: str, max_length: int = 100) -> str:
    """Extract a context snippet around the query match."""
    if not text:
        return ""

    query_lower = query.lower()
    text_lower = text.lower()

    pos = text_lower.find(query_lower)
    if pos == -1:
        return text[:max_length] + "..." if len(text) > max_length else text

    # Get context around match
    start = max(0, pos - 30)
    end = min(len(text), pos + len(query) + 30)

    context = text[start:end]
    if start > 0:
        context = "..." + context
    if end < len(text):
        context = context + "..."

    return context


def search_nodes(
    query: str, project_id: str | None = None, limit: int = 20
) -> list[Node]:
    """Search nodes by title and description."""
    sql = """
        SELECT * FROM nodes
        WHERE (title LIKE ? OR description LIKE ?)
    """
    params = [f"%{query}%", f"%{query}%"]

    if project_id:
        sql += " AND project_id = ?"
        params.append(project_id)

    sql += " ORDER BY updated_at DESC LIMIT ?"
    params.append(limit)

    rows = fetchall(sql, tuple(params))
    return [_row_to_node(row) for row in rows]


def search_milestones(
    query: str, project_id: str | None = None, limit: int = 20
) -> list[Milestone]:
    """Search milestones by name and description."""
    sql = """
        SELECT * FROM milestones
        WHERE (name LIKE ? OR description LIKE ?)
    """
    params = [f"%{query}%", f"%{query}%"]

    if project_id:
        sql += " AND project_id = ?"
        params.append(project_id)

    sql += " ORDER BY target_date ASC NULLS LAST LIMIT ?"
    params.append(limit)

    rows = fetchall(sql, tuple(params))
    return [_row_to_milestone(row) for row in rows]


def search_projects(query: str, limit: int = 20) -> list[Project]:
    """Search projects by name and description."""
    sql = """
        SELECT * FROM projects
        WHERE (name LIKE ? OR description LIKE ?)
        ORDER BY updated_at DESC LIMIT ?
    """
    rows = fetchall(sql, (f"%{query}%", f"%{query}%", limit))
    return [_row_to_project(row) for row in rows]


def search(
    query: str,
    entity_types: list[str] | None = None,
    project_id: str | None = None,
    limit: int = 20,
) -> list[SearchResult]:
    """
    Full-text search across entities.

    Uses SQLite LIKE for MVP, can upgrade to FTS5 later.
    """
    results: list[SearchResult] = []

    # Search nodes
    if not entity_types or "node" in entity_types:
        nodes = search_nodes(query, project_id, limit)
        results.extend(
            [
                SearchResult(
                    entity_type="node",
                    entity=n,
                    match_context=_extract_context(
                        n.title if query.lower() in (n.title or "").lower() else n.description,
                        query,
                    ),
                    relevance=1.0 if query.lower() in (n.title or "").lower() else 0.8,
                )
                for n in nodes
            ]
        )

    # Search milestones
    if not entity_types or "milestone" in entity_types:
        milestones = search_milestones(query, project_id, limit)
        results.extend(
            [
                SearchResult(
                    entity_type="milestone",
                    entity=m,
                    match_context=_extract_context(
                        m.name if query.lower() in (m.name or "").lower() else m.description,
                        query,
                    ),
                    relevance=0.9 if query.lower() in (m.name or "").lower() else 0.7,
                )
                for m in milestones
            ]
        )

    # Search projects (only if no project_id filter)
    if (not entity_types or "project" in entity_types) and not project_id:
        projects = search_projects(query, limit)
        results.extend(
            [
                SearchResult(
                    entity_type="project",
                    entity=p,
                    match_context=_extract_context(
                        p.name if query.lower() in (p.name or "").lower() else p.description,
                        query,
                    ),
                    relevance=0.85 if query.lower() in (p.name or "").lower() else 0.65,
                )
                for p in projects
            ]
        )

    # Sort by relevance and limit
    return sorted(results, key=lambda r: r.relevance, reverse=True)[:limit]


def _row_to_node(row) -> Node:
    """Convert a database row to a Node model."""
    import json

    properties = None
    if row["properties"]:
        try:
            properties = json.loads(row["properties"])
        except json.JSONDecodeError:
            pass

    return Node(
        id=row["id"],
        project_id=row["project_id"],
        milestone_id=row["milestone_id"],
        node_type=row["node_type"],
        title=row["title"],
        description=row["description"],
        status=row["status"],
        assignee=row["assignee"],
        estimated_minutes=row["estimated_minutes"],
        story_points=row["story_points"],
        priority=row["priority"] or "medium",
        blocked_reason=row["blocked_reason"],
        properties=properties,
        created_at=_parse_datetime(row["created_at"]),
        updated_at=_parse_datetime(row["updated_at"]),
        completed_at=_parse_datetime(row["completed_at"]) if row["completed_at"] else None,
    )


def _row_to_milestone(row) -> Milestone:
    """Convert a database row to a Milestone model."""
    from datetime import date as date_type

    target_date = row["target_date"]
    if isinstance(target_date, str):
        target_date = date_type.fromisoformat(target_date)

    return Milestone(
        id=row["id"],
        project_id=row["project_id"],
        name=row["name"],
        description=row["description"],
        target_date=target_date,
        status=row["status"],
        completed_at=_parse_datetime(row["completed_at"]) if row["completed_at"] else None,
        created_at=_parse_datetime(row["created_at"]),
        updated_at=_parse_datetime(row["updated_at"]),
    )


def _row_to_project(row) -> Project:
    """Convert a database row to a Project model."""
    import json

    config = None
    if row["config"]:
        try:
            config = json.loads(row["config"])
        except json.JSONDecodeError:
            pass

    return Project(
        id=row["id"],
        company_id=row["company_id"],
        name=row["name"],
        description=row["description"],
        methodology=row["methodology"],
        status=row["status"],
        config=config,
        created_at=_parse_datetime(row["created_at"]),
        updated_at=_parse_datetime(row["updated_at"]),
    )
