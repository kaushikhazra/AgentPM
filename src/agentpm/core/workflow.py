"""Status workflow shortcuts."""

from agentpm.graph import get_node, update_node
from agentpm.core.project import get_project
from agentpm.core.time_entry import start_timer, stop_timer, get_active_timer
from agentpm.methodologies import get_methodology
from agentpm.exceptions import NotFoundError, ValidationError
from agentpm.db.models import Node


def _get_node_methodology(node_id: str):
    """Get the methodology for a node's project."""
    node = get_node(node_id)
    if node is None:
        raise NotFoundError("Node", node_id)
    project = get_project(node.project_id)
    if project is None:
        raise NotFoundError("Project", node.project_id)
    return node, get_methodology(project.methodology)


def start_node(node_id: str, actor: str | None = None) -> Node:
    """
    Start working on a node:
    1. Transition to in_progress (or methodology equivalent)
    2. Start timer
    """
    node, methodology = _get_node_methodology(node_id)
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
    node, methodology = _get_node_methodology(node_id)
    done_status = methodology.get_done_status(node.node_type)

    # Stop timer if running on this node
    active = get_active_timer()
    if active and active.node_id == node_id:
        stop_timer(actor=actor)

    # Update status (this also sets completed_at)
    return update_node(node_id, status=done_status, actor=actor)


def block_node(node_id: str, reason: str, actor: str | None = None) -> Node:
    """Block a node with a reason."""
    node, methodology = _get_node_methodology(node_id)

    blocked_status = methodology.get_blocked_status(node.node_type)
    if blocked_status is None:
        raise ValidationError(
            f"Node type '{node.node_type}' does not support blocked status"
        )

    return update_node(
        node_id,
        status=blocked_status,
        blocked_reason=reason,
        actor=actor,
    )


def unblock_node(node_id: str, actor: str | None = None) -> Node:
    """Unblock a node, returning to in_progress."""
    node, methodology = _get_node_methodology(node_id)

    if node.status != "blocked":
        raise ValidationError(f"Node is not blocked, current status: {node.status}")

    in_progress_status = methodology.get_in_progress_status(node.node_type)

    # Use empty string to clear blocked_reason (gets converted to None in DB)
    return update_node(
        node_id,
        status=in_progress_status,
        blocked_reason="",
        actor=actor,
    )


def submit_for_review(node_id: str, actor: str | None = None) -> Node:
    """Submit a node for review (transition to in_review status)."""
    node, methodology = _get_node_methodology(node_id)

    # Check if in_review is a valid status
    node_type_def = methodology.get_node_type(node.node_type)
    if node_type_def is None or "in_review" not in node_type_def.valid_statuses:
        raise ValidationError(
            f"Node type '{node.node_type}' does not support review workflow"
        )

    # Stop timer if running
    active = get_active_timer()
    if active and active.node_id == node_id:
        stop_timer(actor=actor)

    return update_node(node_id, status="in_review", actor=actor)


def approve(node_id: str, actor: str | None = None) -> Node:
    """Approve a node that is in review (transition to done)."""
    node, methodology = _get_node_methodology(node_id)

    if node.status != "in_review":
        raise ValidationError(
            f"Node must be in_review to approve, current status: {node.status}"
        )

    done_status = methodology.get_done_status(node.node_type)
    return update_node(node_id, status=done_status, actor=actor)


def reject(node_id: str, reason: str | None = None, actor: str | None = None) -> Node:
    """Reject a node that is in review (return to in_progress)."""
    node, methodology = _get_node_methodology(node_id)

    if node.status != "in_review":
        raise ValidationError(
            f"Node must be in_review to reject, current status: {node.status}"
        )

    in_progress_status = methodology.get_in_progress_status(node.node_type)

    properties = node.properties or {}
    if reason:
        properties["rejection_reason"] = reason

    return update_node(
        node_id,
        status=in_progress_status,
        properties=properties if properties else None,
        actor=actor,
    )
