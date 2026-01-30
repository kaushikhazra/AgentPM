"""Rollup calculations for aggregated metrics."""

from dataclasses import dataclass

from agentpm.graph import get_node, get_descendants, list_nodes
from agentpm.core.project import get_project
from agentpm.core.time_entry import get_time_total
from agentpm.core.milestone import get_milestone, list_milestones
from agentpm.methodologies import get_methodology
from agentpm.exceptions import NotFoundError


@dataclass
class RollupStats:
    """Aggregated statistics for a node, milestone, or project."""

    total_time_minutes: int
    estimated_time_minutes: int
    total_nodes: int
    completed_nodes: int
    blocked_nodes: int
    in_progress_nodes: int
    completion_percentage: float
    story_points: int | None


def _get_terminal_statuses(project_id: str, node_type: str) -> set[str]:
    """Get terminal statuses for a node type."""
    project = get_project(project_id)
    if project is None:
        return {"done", "cancelled"}
    methodology = get_methodology(project.methodology)
    node_type_def = methodology.get_node_type(node_type)
    if node_type_def:
        return node_type_def.terminal_statuses
    return {"done", "cancelled"}


def _calculate_rollup(nodes: list) -> RollupStats:
    """Calculate rollup stats for a list of nodes."""
    if not nodes:
        return RollupStats(
            total_time_minutes=0,
            estimated_time_minutes=0,
            total_nodes=0,
            completed_nodes=0,
            blocked_nodes=0,
            in_progress_nodes=0,
            completion_percentage=0.0,
            story_points=None,
        )

    total_time = sum(get_time_total(n.id) for n in nodes)
    estimated = sum(n.estimated_minutes or 0 for n in nodes)

    # Get terminal statuses from first node's project
    terminal_statuses = _get_terminal_statuses(nodes[0].project_id, nodes[0].node_type)

    completed = sum(1 for n in nodes if n.status in terminal_statuses)
    blocked = sum(1 for n in nodes if n.status == "blocked")
    in_progress = sum(1 for n in nodes if n.status == "in_progress")

    story_points_sum = sum(n.story_points or 0 for n in nodes)

    return RollupStats(
        total_time_minutes=total_time,
        estimated_time_minutes=estimated,
        total_nodes=len(nodes),
        completed_nodes=completed,
        blocked_nodes=blocked,
        in_progress_nodes=in_progress,
        completion_percentage=round(completed / len(nodes) * 100, 1) if nodes else 0.0,
        story_points=story_points_sum if story_points_sum > 0 else None,
    )


def get_node_rollup(node_id: str) -> RollupStats:
    """
    Calculate aggregated stats for a node and all descendants.

    1. Get all descendants via graph traversal
    2. Sum time entries across all
    3. Sum estimates
    4. Count by status
    5. Calculate percentages
    """
    node = get_node(node_id)
    if node is None:
        raise NotFoundError("Node", node_id)

    descendants = get_descendants(node_id, edge_type="parent")
    all_nodes = [node] + descendants

    return _calculate_rollup(all_nodes)


def get_milestone_rollup(milestone_id: str) -> RollupStats:
    """Rollup for all nodes in a milestone."""
    milestone = get_milestone(milestone_id)
    if milestone is None:
        raise NotFoundError("Milestone", milestone_id)

    nodes = list_nodes(milestone_id=milestone_id)
    return _calculate_rollup(nodes)


def get_project_rollup(project_id: str) -> RollupStats:
    """Rollup for entire project."""
    project = get_project(project_id)
    if project is None:
        raise NotFoundError("Project", project_id)

    nodes = list_nodes(project_id=project_id)
    return _calculate_rollup(nodes)
