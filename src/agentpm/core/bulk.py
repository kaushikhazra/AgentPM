"""Bulk operations for managing multiple items."""

from dataclasses import dataclass

from agentpm.core.tag import tag_node
from agentpm.db.models import Node
from agentpm.exceptions import NotFoundError, ValidationError


@dataclass
class BulkResult:
    """Result of a bulk operation."""

    succeeded: list[str]  # IDs that succeeded
    failed: list[tuple[str, str]]  # (ID, error message) for failures


def bulk_move_to_milestone(
    node_ids: list[str],
    milestone_id: str | None,
    actor: str | None = None,
) -> BulkResult:
    """Move multiple nodes to a milestone (or remove from milestone if None)."""
    from agentpm.graph import get_node, update_node

    succeeded = []
    failed = []

    for node_id in node_ids:
        try:
            node = get_node(node_id)
            if node is None:
                failed.append((node_id, "Node not found"))
                continue

            update_node(node_id, milestone_id=milestone_id, actor=actor)
            succeeded.append(node_id)
        except Exception as e:
            failed.append((node_id, str(e)))

    return BulkResult(succeeded=succeeded, failed=failed)


def bulk_update_status(
    node_ids: list[str],
    status: str,
    actor: str | None = None,
) -> BulkResult:
    """
    Change status of multiple nodes.

    Validates each transition individually - some may succeed while others fail.
    """
    from agentpm.graph import get_node, update_node

    succeeded = []
    failed = []

    for node_id in node_ids:
        try:
            node = get_node(node_id)
            if node is None:
                failed.append((node_id, "Node not found"))
                continue

            update_node(node_id, status=status, actor=actor)
            succeeded.append(node_id)
        except ValidationError as e:
            failed.append((node_id, str(e)))
        except Exception as e:
            failed.append((node_id, str(e)))

    return BulkResult(succeeded=succeeded, failed=failed)


def bulk_reassign(
    node_ids: list[str],
    assignee: str | None,
    actor: str | None = None,
) -> BulkResult:
    """Reassign multiple nodes to a new assignee (or unassign if None)."""
    from agentpm.graph import get_node, update_node

    succeeded = []
    failed = []

    for node_id in node_ids:
        try:
            node = get_node(node_id)
            if node is None:
                failed.append((node_id, "Node not found"))
                continue

            update_node(node_id, assignee=assignee, actor=actor)
            succeeded.append(node_id)
        except Exception as e:
            failed.append((node_id, str(e)))

    return BulkResult(succeeded=succeeded, failed=failed)


def bulk_tag(
    node_ids: list[str],
    tag_name: str,
    actor: str | None = None,
) -> BulkResult:
    """Add a tag to multiple nodes."""
    from agentpm.graph import get_node

    succeeded = []
    failed = []

    for node_id in node_ids:
        try:
            node = get_node(node_id)
            if node is None:
                failed.append((node_id, "Node not found"))
                continue

            tag_node(node_id, tag_name, actor=actor)
            succeeded.append(node_id)
        except Exception as e:
            failed.append((node_id, str(e)))

    return BulkResult(succeeded=succeeded, failed=failed)


def bulk_delete(
    node_ids: list[str],
    actor: str | None = None,
) -> BulkResult:
    """Delete multiple nodes."""
    from agentpm.graph import delete_node

    succeeded = []
    failed = []

    for node_id in node_ids:
        try:
            result = delete_node(node_id, actor=actor)
            if result:
                succeeded.append(node_id)
            else:
                failed.append((node_id, "Node not found or already deleted"))
        except Exception as e:
            failed.append((node_id, str(e)))

    return BulkResult(succeeded=succeeded, failed=failed)


def bulk_update_priority(
    node_ids: list[str],
    priority: str,
    actor: str | None = None,
) -> BulkResult:
    """Update priority of multiple nodes."""
    from agentpm.graph import get_node, update_node

    valid_priorities = ["low", "medium", "high", "critical"]
    if priority not in valid_priorities:
        raise ValidationError(
            f"Invalid priority: {priority}. Must be one of: {valid_priorities}"
        )

    succeeded = []
    failed = []

    for node_id in node_ids:
        try:
            node = get_node(node_id)
            if node is None:
                failed.append((node_id, "Node not found"))
                continue

            update_node(node_id, priority=priority, actor=actor)
            succeeded.append(node_id)
        except Exception as e:
            failed.append((node_id, str(e)))

    return BulkResult(succeeded=succeeded, failed=failed)
