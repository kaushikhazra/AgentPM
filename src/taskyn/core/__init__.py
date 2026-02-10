"""Core business logic for Taskyn."""

from taskyn.exceptions import ValidationError

from taskyn.core.company import (
    create_company,
    get_company,
    list_companies,
    update_company,
    delete_company,
)
from taskyn.core.project import (
    create_project,
    get_project,
    list_projects,
    update_project,
    delete_project,
)
from taskyn.core.milestone import (
    create_milestone,
    get_milestone,
    list_milestones,
    update_milestone,
    complete_milestone,
    delete_milestone,
)
from taskyn.core.time_entry import (
    start_timer,
    stop_timer,
    log_time,
    get_active_timer,
    list_time_entries,
    get_time_total,
    get_time_entry,
    delete_time_entry,
    propagate_actual_time,
)
from taskyn.core.tag import (
    create_tag,
    get_tag,
    get_tag_by_name,
    list_tags,
    delete_tag,
    delete_tag_by_name,
    get_tag_usage_count,
    tag_node,
    untag_node,
    get_node_tags,
    list_nodes_by_tag,
)
from taskyn.core.activity import (
    log_activity,
    list_activity,
    get_entity_activity,
)
from taskyn.core.work_items import (
    create_story,
    create_task,
    get_story_with_tasks,
)
from taskyn.core.workflow import (
    start_node,
    complete_node,
    block_node,
    unblock_node,
    submit_for_review,
    approve,
    reject,
)
from taskyn.core.rollup import (
    RollupStats,
    get_node_rollup,
    get_milestone_rollup,
    get_project_rollup,
)
from taskyn.core.reporting import (
    Dashboard,
    get_dashboard,
    ProjectStats,
    MilestoneProgress,
    get_project_stats,
    SearchResult,
    search,
    list_time_entries_since,
)
from taskyn.core.bulk import (
    BulkResult,
    bulk_move_to_milestone,
    bulk_update_status,
    bulk_reassign,
    bulk_tag,
    bulk_delete,
    bulk_update_priority,
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
    "get_time_entry",
    "delete_time_entry",
    "propagate_actual_time",
    # Tag
    "create_tag",
    "get_tag",
    "get_tag_by_name",
    "list_tags",
    "delete_tag",
    "delete_tag_by_name",
    "get_tag_usage_count",
    "tag_node",
    "untag_node",
    "get_node_tags",
    "list_nodes_by_tag",
    # Activity
    "log_activity",
    "list_activity",
    "get_entity_activity",
    # Work Items
    "create_story",
    "create_task",
    "get_story_with_tasks",
    # Workflow
    "start_node",
    "complete_node",
    "block_node",
    "unblock_node",
    "submit_for_review",
    "approve",
    "reject",
    # Rollup
    "RollupStats",
    "get_node_rollup",
    "get_milestone_rollup",
    "get_project_rollup",
    # Reporting
    "Dashboard",
    "get_dashboard",
    "ProjectStats",
    "MilestoneProgress",
    "get_project_stats",
    "SearchResult",
    "search",
    "list_time_entries_since",
    # Bulk Operations
    "BulkResult",
    "bulk_move_to_milestone",
    "bulk_update_status",
    "bulk_reassign",
    "bulk_tag",
    "bulk_delete",
    "bulk_update_priority",
]
