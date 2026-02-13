"""Spec-Driven methodology v2.

Hierarchy (all levels mandatory):
    spec
    ├── requirement
    │   ├── e2e_verification
    │   └── design
    │       ├── functional_verification
    │       └── implementation
    │           ├── unit_verification
    │           └── task

Verification nodes are scoped to specific hierarchy levels and cascade
parent status on failure. Time tracking is only allowed on task and
verification nodes; actual_time rolls up through the hierarchy.
"""

from taskyn.methodologies.base import (
    BaseMethodology,
    NodeTypeDefinition,
    EdgeTypeDefinition,
)

_ALL_TYPES = [
    "spec",
    "requirement",
    "design",
    "implementation",
    "task",
    "e2e_verification",
    "functional_verification",
    "unit_verification",
]

_VERIFICATION_TYPES = [
    "e2e_verification",
    "functional_verification",
    "unit_verification",
]


def _verification_node(name: str) -> NodeTypeDefinition:
    """Shared definition for all verification node types."""
    return NodeTypeDefinition(
        name=name,
        valid_statuses=["pending", "in_progress", "passed", "failed"],
        initial_status="pending",
        terminal_statuses={"passed"},
        allowed_transitions={
            "pending": ["in_progress"],
            "in_progress": ["passed", "failed"],
            "passed": [],
            "failed": ["pending"],  # Gated: only when parent is back to terminal
        },
        can_track_time=True,
    )


class SpecDrivenMethodology(BaseMethodology):
    """Spec-Driven methodology with 5-level hierarchy and scoped verification."""

    @property
    def name(self) -> str:
        return "spec_driven"

    @property
    def display_name(self) -> str:
        return "Spec-Driven"

    @property
    def node_types(self) -> dict[str, NodeTypeDefinition]:
        return {
            "spec": NodeTypeDefinition(
                name="spec",
                valid_statuses=["draft", "approved", "in_progress", "done", "cancelled"],
                initial_status="draft",
                terminal_statuses={"done", "cancelled"},
                allowed_transitions={
                    "draft": ["approved", "cancelled"],
                    "approved": ["in_progress", "draft", "cancelled"],
                    "in_progress": ["done", "cancelled"],
                    "done": [],
                    "cancelled": [],
                },
                can_track_time=False,
                optional_properties=["acceptance_criteria", "approver"],
            ),
            "requirement": NodeTypeDefinition(
                name="requirement",
                valid_statuses=["draft", "approved", "in_progress", "rework", "done"],
                initial_status="draft",
                terminal_statuses={"done"},
                allowed_transitions={
                    "draft": ["approved"],
                    "approved": ["in_progress", "draft"],
                    "in_progress": ["done", "rework"],
                    "rework": ["in_progress"],
                    "done": [],
                },
                can_track_time=False,
            ),
            "design": NodeTypeDefinition(
                name="design",
                valid_statuses=["draft", "in_review", "approved", "rejected"],
                initial_status="draft",
                terminal_statuses={"approved"},
                allowed_transitions={
                    "draft": ["in_review"],
                    "in_review": ["approved", "rejected"],
                    "approved": ["rejected"],  # Cascade from functional_verification
                    "rejected": ["draft"],
                },
                can_track_time=False,
                optional_properties=["design_doc", "reviewer"],
            ),
            "implementation": NodeTypeDefinition(
                name="implementation",
                valid_statuses=["todo", "in_progress", "in_review", "done", "rework"],
                initial_status="todo",
                terminal_statuses={"done"},
                allowed_transitions={
                    "todo": ["in_progress"],
                    "in_progress": ["in_review", "rework"],
                    "in_review": ["done", "rework"],
                    "done": ["rework"],  # Cascade from unit_verification
                    "rework": ["in_progress"],
                },
                can_track_time=False,
                optional_properties=["implementation_notes", "reviewer"],
            ),
            "task": NodeTypeDefinition(
                name="task",
                valid_statuses=["todo", "in_progress", "done"],
                initial_status="todo",
                terminal_statuses={"done"},
                allowed_transitions={
                    "todo": ["in_progress"],
                    "in_progress": ["done"],
                    "done": [],
                },
                can_track_time=True,
            ),
            "e2e_verification": _verification_node("e2e_verification"),
            "functional_verification": _verification_node("functional_verification"),
            "unit_verification": _verification_node("unit_verification"),
        }

    @property
    def edge_types(self) -> dict[str, EdgeTypeDefinition]:
        return {
            "parent": EdgeTypeDefinition(
                name="parent",
                source_types=[
                    "requirement",
                    "design",
                    "implementation",
                    "task",
                    "e2e_verification",
                    "functional_verification",
                    "unit_verification",
                ],
                target_types=["spec", "requirement", "design", "implementation"],
                max_per_source=1,
                allows_cycles=False,
            ),
            "depends_on": EdgeTypeDefinition(
                name="depends_on",
                source_types=_ALL_TYPES,
                target_types=_ALL_TYPES,
                allows_cycles=False,
            ),
            "blocks": EdgeTypeDefinition(
                name="blocks",
                source_types=_ALL_TYPES,
                target_types=_ALL_TYPES,
                allows_cycles=False,
            ),
        }

    @property
    def valid_parent_pairs(self) -> dict[str, list[str]]:
        return {
            "requirement": ["spec"],
            "design": ["requirement"],
            "implementation": ["design"],
            "task": ["implementation"],
            "e2e_verification": ["requirement"],
            "functional_verification": ["design"],
            "unit_verification": ["implementation"],
        }

    def get_story_type(self) -> str:
        return "spec"

    def get_task_type(self) -> str:
        return "task"

    def get_in_progress_status(self, node_type: str) -> str:
        status_map = {
            "spec": "in_progress",
            "requirement": "in_progress",
            "design": "in_review",
            "implementation": "in_progress",
            "task": "in_progress",
            "e2e_verification": "in_progress",
            "functional_verification": "in_progress",
            "unit_verification": "in_progress",
        }
        return status_map.get(node_type, "in_progress")

    def get_done_status(self, node_type: str) -> str:
        status_map = {
            "spec": "done",
            "requirement": "done",
            "design": "approved",
            "implementation": "done",
            "task": "done",
            "e2e_verification": "passed",
            "functional_verification": "passed",
            "unit_verification": "passed",
        }
        return status_map.get(node_type, "done")
