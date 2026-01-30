"""High-level work item convenience API."""

from agentpm.core.project import get_project
from agentpm.methodologies import get_methodology
from agentpm.exceptions import NotFoundError
from agentpm.db.models import Node


def get_project_methodology(project_id: str):
    """Get the methodology for a project."""
    project = get_project(project_id)
    if project is None:
        raise NotFoundError("Project", project_id)
    return get_methodology(project.methodology)


def create_story(
    project_id: str,
    title: str,
    description: str | None = None,
    milestone_id: str | None = None,
    priority: str = "medium",
    story_points: int | None = None,
    acceptance_criteria: str | None = None,
    actor: str | None = None,
) -> Node:
    """
    Create a story node (or equivalent in current methodology).

    For classic_agile: creates node_type="story"
    """
    from agentpm.graph import create_node

    methodology = get_project_methodology(project_id)
    node_type = methodology.get_story_type()

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
        properties=properties if properties else None,
        actor=actor,
    )


def create_task(
    parent_id: str,
    title: str,
    description: str | None = None,
    assignee: str | None = None,
    estimated_minutes: int | None = None,
    priority: str = "medium",
    actor: str | None = None,
) -> Node:
    """
    Create a task under a story (or equivalent hierarchy).

    Automatically creates parent edge.
    """
    from agentpm.graph import create_node, get_node, create_edge

    parent = get_node(parent_id)
    if parent is None:
        raise NotFoundError("Node", parent_id)

    methodology = get_project_methodology(parent.project_id)
    node_type = methodology.get_task_type()

    task = create_node(
        project_id=parent.project_id,
        node_type=node_type,
        title=title,
        description=description,
        assignee=assignee,
        estimated_minutes=estimated_minutes,
        priority=priority,
        actor=actor,
    )

    # Create parent edge
    create_edge(
        source_id=task.id,
        target_id=parent_id,
        edge_type="parent",
        actor=actor,
    )

    return task


def get_story_with_tasks(story_id: str) -> dict:
    """
    Get a story with all its tasks.

    Returns:
        dict with 'story' and 'tasks' keys
    """
    from agentpm.graph import get_node, get_children

    story = get_node(story_id)
    if story is None:
        raise NotFoundError("Node", story_id)

    tasks = get_children(story_id, edge_type="parent")

    return {
        "story": story,
        "tasks": tasks,
    }
