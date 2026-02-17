"""Phase gating logic for spec-driven v3 methodology.

Strict gating enforces sequential phase flow:
- Requirement can go active when parent Spec is active or done
- Design can go active when ALL sibling Requirements under same Spec are done
- Task can go active when ALL sibling Designs under same Spec are done
- Todo can start (in_progress) when parent phase is active or done
"""

# Phase gating: node_type → required sibling type that must all be done
_PHASE_GATE: dict[str, str] = {
    "design": "requirement",
    "task": "design",
}

# Parent must be active/done for these node types to activate
_PARENT_ACTIVE_GATE: set[str] = {"requirement", "design", "task", "todo"}


def validate_phase_gate(
    node_id: str,
    node_type: str,
    old_status: str,
    new_status: str,
) -> list[str]:
    """Pre-transition check: enforce strict phase gating for spec_driven v3.

    Returns a list of validation errors (empty if valid).
    Only applies to spec_driven methodology nodes.
    """
    # Only gate transitions TO active (phases) or TO in_progress (todos)
    is_activating_phase = node_type in _PARENT_ACTIVE_GATE and new_status == "active"
    is_starting_todo = node_type == "todo" and new_status == "in_progress"

    if not is_activating_phase and not is_starting_todo:
        return []

    from taskyn.graph.edges import list_edges
    from taskyn.graph.nodes import get_node, list_nodes
    from taskyn.core.project import get_project
    from taskyn.methodologies import get_methodology

    # Find parent via parent edge
    parent_edges = list_edges(source_id=node_id, edge_type="parent")
    if not parent_edges:
        return []  # No parent — allow (top-level spec has no parent)

    parent = get_node(parent_edges[0].target_id)
    if parent is None:
        return []

    project = get_project(parent.project_id)
    methodology = get_methodology(project.methodology)

    # Only apply gating for spec_driven methodology
    if methodology.name != "spec_driven":
        return []

    errors = []

    # Gate 1: Parent must be active or done
    if parent.status not in ("active", "done"):
        errors.append(
            f"Cannot activate '{node_type}': parent '{parent.title}' "
            f"must be active or done, currently '{parent.status}'"
        )
        return errors  # No point checking sibling gates if parent isn't ready

    # Gate 2: For design and task, check sibling prerequisites
    required_sibling_type = _PHASE_GATE.get(node_type)
    if required_sibling_type is not None:
        # Find the spec (parent of this node's parent, or direct parent if parent is spec)
        spec_id = None
        if parent.node_type == "spec":
            spec_id = parent.id
        else:
            # Walk up to find spec
            spec_edges = list_edges(source_id=parent.id, edge_type="parent")
            if spec_edges:
                spec = get_node(spec_edges[0].target_id)
                if spec and spec.node_type == "spec":
                    spec_id = spec.id

        if spec_id is not None:
            # Find all sibling nodes of the required type under the same spec
            all_nodes = list_nodes(project_id=parent.project_id, node_type=required_sibling_type)
            siblings = []
            for n in all_nodes:
                n_parent_edges = list_edges(source_id=n.id, edge_type="parent")
                for e in n_parent_edges:
                    if e.target_id == spec_id:
                        siblings.append(n)
                        break

            if siblings:
                incomplete = [
                    s for s in siblings
                    if not methodology.is_terminal_status(s.node_type, s.status)
                ]
                if incomplete:
                    names = ", ".join(f"'{s.title}'" for s in incomplete)
                    errors.append(
                        f"Cannot activate '{node_type}': all {required_sibling_type}s "
                        f"must be done first. Incomplete: {names}"
                    )

    return errors


def on_status_changed(
    node_id: str,
    node_type: str,
    old_status: str,
    new_status: str,
) -> None:
    """Post-transition hook. No cascading in v3 — kept for interface compatibility."""
    pass
