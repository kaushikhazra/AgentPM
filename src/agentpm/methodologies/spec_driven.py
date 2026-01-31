"""Spec-Driven methodology for Kiro-style development.

This methodology follows a gated workflow:
  spec (approved) → design (approved) → implementation (done) → validation (passed)

Each phase requires approval before the next can begin. Validation can fail
and loop back to implementation for rework.
"""

from agentpm.methodologies.base import (
    BaseMethodology,
    NodeTypeDefinition,
    EdgeTypeDefinition,
)


class SpecDrivenMethodology(BaseMethodology):
    """Spec-Driven methodology with gated approval workflow."""

    name = "spec_driven"
    display_name = "Spec-Driven (Kiro-style)"

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
                    "in_progress": ["done", "draft", "cancelled"],
                    "done": [],
                    "cancelled": [],
                },
                required_properties=[],
                optional_properties=["requirements", "acceptance_criteria", "approver"],
            ),
            "design": NodeTypeDefinition(
                name="design",
                valid_statuses=["draft", "in_review", "approved", "rejected"],
                initial_status="draft",
                terminal_statuses={"approved"},
                allowed_transitions={
                    "draft": ["in_review"],
                    "in_review": ["approved", "rejected"],
                    "approved": [],
                    "rejected": ["draft"],
                },
                required_properties=[],
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
                    "done": [],
                    "rework": ["in_progress"],
                },
                required_properties=[],
                optional_properties=["implementation_notes", "reviewer"],
            ),
            "validation": NodeTypeDefinition(
                name="validation",
                valid_statuses=["pending", "in_progress", "passed", "failed"],
                initial_status="pending",
                terminal_statuses={"passed"},
                allowed_transitions={
                    "pending": ["in_progress"],
                    "in_progress": ["passed", "failed"],
                    "passed": [],
                    "failed": ["pending"],  # Can retry
                },
                required_properties=[],
                optional_properties=["test_results", "validator"],
            ),
        }

    @property
    def edge_types(self) -> dict[str, EdgeTypeDefinition]:
        return {
            "parent": EdgeTypeDefinition(
                name="parent",
                source_types=["design", "implementation", "validation"],
                target_types=["spec", "design", "implementation"],
                max_per_source=1,  # Each node has one parent
                allows_cycles=False,
            ),
            "gates": EdgeTypeDefinition(
                name="gates",
                source_types=["design", "implementation", "validation"],
                target_types=["spec", "design", "implementation"],
                max_per_source=1,  # Each phase gates one predecessor
                allows_cycles=False,
            ),
            "validates": EdgeTypeDefinition(
                name="validates",
                source_types=["validation"],
                target_types=["implementation"],
                max_per_source=1,
                allows_cycles=False,
            ),
            "depends_on": EdgeTypeDefinition(
                name="depends_on",
                source_types=["spec", "design", "implementation", "validation"],
                target_types=["spec", "design", "implementation", "validation"],
                allows_cycles=False,
            ),
        }

    def get_story_type(self) -> str:
        """Return the top-level work item type."""
        return "spec"

    def get_task_type(self) -> str:
        """Return the child work item type."""
        return "implementation"

    def get_in_progress_status(self, node_type: str) -> str:
        """Get the in-progress status for a node type."""
        status_map = {
            "spec": "in_progress",
            "design": "in_review",
            "implementation": "in_progress",
            "validation": "in_progress",
        }
        return status_map.get(node_type, "in_progress")

    def get_done_status(self, node_type: str) -> str:
        """Get the done/terminal status for a node type."""
        status_map = {
            "spec": "done",
            "design": "approved",
            "implementation": "done",
            "validation": "passed",
        }
        return status_map.get(node_type, "done")
