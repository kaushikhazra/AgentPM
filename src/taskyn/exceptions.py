"""Custom exceptions for Taskyn."""


class TaskynError(Exception):
    """Base exception for Taskyn."""

    def __init__(self, message: str, context: dict | None = None, suggestions: list | None = None):
        self.message = message
        self.context = context or {}
        self.suggestions = suggestions or []
        super().__init__(self.format())

    def format(self) -> str:
        msg = self.message
        if self.context:
            ctx = ", ".join(f"{k}={v}" for k, v in self.context.items())
            msg = f"{msg} ({ctx})"
        if self.suggestions:
            msg += "\n\nSuggestions:\n" + "\n".join(f"  - {s}" for s in self.suggestions)
        return msg


class NotFoundError(TaskynError):
    """Raised when an entity is not found."""

    def __init__(self, entity_type: str, entity_id: str):
        super().__init__(
            f"{entity_type} not found: {entity_id}",
            context={"entity_type": entity_type, "id": entity_id},
        )


class ValidationError(TaskynError):
    """Raised when validation fails."""
    pass


class InvalidTransitionError(ValidationError):
    """Raised when a status transition is not allowed."""

    def __init__(self, node_type: str, current: str, target: str, allowed: list[str]):
        super().__init__(
            f"Cannot transition {node_type} from '{current}' to '{target}'",
            context={"node_type": node_type, "current_status": current, "target_status": target},
            suggestions=[
                f"Valid transitions from '{current}': {', '.join(allowed) or 'none'}",
            ],
        )


class CycleDetectedError(ValidationError):
    """Raised when creating an edge would create a cycle."""

    def __init__(self, source_id: str, target_id: str, edge_type: str):
        super().__init__(
            f"Creating edge would create a cycle",
            context={"source_id": source_id, "target_id": target_id, "edge_type": edge_type},
        )


class CardinalityError(ValidationError):
    """Raised when cardinality constraints are violated."""

    def __init__(self, message: str, edge_type: str, limit: int):
        super().__init__(
            message,
            context={"edge_type": edge_type, "limit": limit},
        )
