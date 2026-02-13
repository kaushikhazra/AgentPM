"""Verification failure cascade logic.

When a verification node transitions to 'failed', the parent node is
automatically cascaded back to a rework/draft state. Re-verification
is gated: the verification node cannot retry (failed → pending) until
the parent is back in its terminal state.
"""

from taskyn.exceptions import ValidationError

# Verification type → rework status for parent
_CASCADE_STATUS: dict[str, str] = {
    "unit_verification": "rework",          # implementation → rework
    "functional_verification": "rejected",  # design → rejected (then auto → draft)
    "e2e_verification": "rework",           # requirement → rework
}

VERIFICATION_TYPES = frozenset(_CASCADE_STATUS.keys())


def on_status_changed(
    node_id: str,
    node_type: str,
    old_status: str,
    new_status: str,
) -> None:
    """Post-transition hook. Cascade parent on verification failure."""
    if node_type not in VERIFICATION_TYPES:
        return
    if new_status != "failed":
        return

    _cascade_parent(node_id, node_type)


def validate_reverification(
    node_id: str,
    node_type: str,
    old_status: str,
    new_status: str,
) -> list[str]:
    """Pre-transition check: block failed → pending unless parent is terminal."""
    if node_type not in VERIFICATION_TYPES:
        return []
    if old_status != "failed" or new_status != "pending":
        return []

    from taskyn.graph.edges import list_edges
    from taskyn.graph.nodes import get_node
    from taskyn.core.project import get_project
    from taskyn.methodologies import get_methodology

    # Find parent via parent edge (source=this node, target=parent)
    parent_edges = list_edges(source_id=node_id, edge_type="parent")
    if not parent_edges:
        return []  # No parent — allow retry

    parent = get_node(parent_edges[0].target_id)
    if parent is None:
        return []

    project = get_project(parent.project_id)
    methodology = get_methodology(project.methodology)

    if not methodology.is_terminal_status(parent.node_type, parent.status):
        done_status = methodology.get_done_status(parent.node_type)
        return [
            f"Cannot re-verify: parent '{parent.title}' must be in "
            f"terminal state ('{done_status}'), currently '{parent.status}'"
        ]

    return []


def _cascade_parent(node_id: str, node_type: str) -> None:
    """Push the parent node back to rework/draft state."""
    from taskyn.graph.edges import list_edges
    from taskyn.graph.nodes import get_node, update_node

    # Find parent
    parent_edges = list_edges(source_id=node_id, edge_type="parent")
    if not parent_edges:
        return

    parent = get_node(parent_edges[0].target_id)
    if parent is None:
        return

    cascade_status = _CASCADE_STATUS.get(node_type)
    if cascade_status is None:
        return

    # Cascade to rework/rejected status
    update_node(parent.id, status=cascade_status, actor="system:cascade")

    # For design: rejected → draft is a two-step cascade
    if node_type == "functional_verification" and cascade_status == "rejected":
        update_node(parent.id, status="draft", actor="system:cascade")
