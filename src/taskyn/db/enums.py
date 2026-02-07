"""Enumerations for Taskyn entities."""

from enum import Enum


class EntityType(str, Enum):
    """Lifecycle stage for companies and projects.

    Values map to fixed colors in the UI:
    - DISCOVERY: Ocean Blue (#0077B6)
    - POTENTIAL: Chrome Yellow (#FFD60A)
    - MATURED: Ocean Green (#2A9D8F)
    - ENGAGED: Moss Green (#606C38)
    - ACTIVE: Coral Red (#E63946)
    - DORMANT: Grey (#6C757D)
    """

    DISCOVERY = "discovery"
    POTENTIAL = "potential"
    MATURED = "matured"
    ENGAGED = "engaged"
    ACTIVE = "active"
    DORMANT = "dormant"


class Methodology(str, Enum):
    """Project management methodology.

    Defines the valid node types, statuses, and transitions for a project.
    """

    CLASSIC_AGILE = "classic_agile"
    SPEC_DRIVEN = "spec_driven"
