"""Core business logic for AgentPM."""

from agentpm.exceptions import ValidationError

from agentpm.core.company import (
    create_company,
    get_company,
    list_companies,
    update_company,
    delete_company,
)
from agentpm.core.project import (
    create_project,
    get_project,
    list_projects,
    update_project,
    delete_project,
)
from agentpm.core.milestone import (
    create_milestone,
    get_milestone,
    list_milestones,
    update_milestone,
    complete_milestone,
    delete_milestone,
)
from agentpm.core.time_entry import (
    start_timer,
    stop_timer,
    log_time,
    get_active_timer,
    list_time_entries,
    get_time_total,
)
from agentpm.core.tag import (
    create_tag,
    get_tag,
    get_tag_by_name,
    list_tags,
    delete_tag,
    tag_node,
    untag_node,
    get_node_tags,
    list_nodes_by_tag,
)
from agentpm.core.activity import (
    log_activity,
    list_activity,
    get_entity_activity,
)

__all__ = [
    # Exceptions (re-exported for convenience)
    "ValidationError",
    # Company
    "create_company",
    "get_company",
    "list_companies",
    "update_company",
    "delete_company",
    # Project
    "create_project",
    "get_project",
    "list_projects",
    "update_project",
    "delete_project",
    # Milestone
    "create_milestone",
    "get_milestone",
    "list_milestones",
    "update_milestone",
    "complete_milestone",
    "delete_milestone",
    # Time Entry
    "start_timer",
    "stop_timer",
    "log_time",
    "get_active_timer",
    "list_time_entries",
    "get_time_total",
    # Tag
    "create_tag",
    "get_tag",
    "get_tag_by_name",
    "list_tags",
    "delete_tag",
    "tag_node",
    "untag_node",
    "get_node_tags",
    "list_nodes_by_tag",
    # Activity
    "log_activity",
    "list_activity",
    "get_entity_activity",
]
