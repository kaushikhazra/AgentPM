# AgentPM Core Business Logic - Tasks

## Methodology Extensions
- [x] Add helper methods to BaseMethodology
  _COR-1: Work Item Convenience API_
  - [x] get_story_type()
  - [x] get_task_type()
  - [x] get_in_progress_status()
  - [x] get_done_status()
  - [x] get_blocked_status()
- [x] Implement helpers in ClassicAgileMethodology
  _COR-1: Work Item Convenience API_
- [x] Write tests for methodology helpers
  _COR-1: Work Item Convenience API_

## Work Items API
- [x] Create core/work_items.py
  _COR-1: Work Item Convenience API_
  - [x] create_story() methodology-aware
  - [x] create_task() with auto parent edge
  - [x] get_story_with_tasks() convenience function
- [x] Write tests for work item helpers
  _COR-1: Work Item Convenience API_

## Workflow Shortcuts
- [x] Create core/workflow.py
  _COR-2: Status Workflow_
  - [x] start_node() - status + timer
  - [x] complete_node() - status + stop timer
  - [x] block_node() - with reason
  - [x] unblock_node()
- [x] Add review workflow functions
  _COR-2: Status Workflow_
  - [x] submit_for_review()
  - [x] approve()
  - [x] reject()
- [x] Write tests for workflow functions
  _COR-2: Status Workflow_

## Rollup Calculations
- [x] Create core/rollup.py
  _COR-3: Rollup Calculations_
  - [x] RollupStats dataclass
  - [x] get_node_rollup()
  - [x] get_milestone_rollup()
  - [x] get_project_rollup()
- [x] Handle edge cases (empty nodes, no estimates)
  _COR-3: Rollup Calculations_
- [x] Write tests for rollup calculations
  _COR-3: Rollup Calculations_

## Dashboard
- [x] Create core/reporting.py
  _COR-4: Dashboard_
  - [x] Dashboard dataclass
  - [x] get_dashboard()
  - [x] Helper: list_time_entries_since()
- [x] Write tests for dashboard
  _COR-4: Dashboard_

## Project Statistics
- [x] Add to core/reporting.py
  _COR-5: Project Statistics_
  - [x] ProjectStats dataclass
  - [x] MilestoneProgress dataclass
  - [x] get_project_stats()
  - [x] Calculate velocity (completions per week)
- [x] Write tests for project stats
  _COR-5: Project Statistics_

## Search
- [x] Add search functions to core/reporting.py
  _COR-6: Search_
  - [x] SearchResult dataclass
  - [x] search() main function
  - [x] search_nodes() helper
  - [x] search_milestones() helper
  - [x] extract_context() for snippets
- [x] Write tests for search
  _COR-6: Search_

## Bulk Operations
- [x] Create core/bulk.py
  _COR-7: Bulk Operations_
  - [x] bulk_move_to_milestone()
  - [x] bulk_update_status()
  - [x] bulk_reassign()
  - [x] bulk_tag()
  - [x] bulk_delete()
- [x] Handle partial failures (some succeed, some fail)
  _COR-7: Bulk Operations_
- [x] Write tests for bulk operations
  _COR-7: Bulk Operations_

## Integration Tests
- [x] Test: create story → create tasks → start → complete → verify rollup
  _COR-3: Rollup Calculations_
- [x] Test: dashboard shows correct active state
  _COR-4: Dashboard_
- [x] Test: search finds nodes by title and description
  _COR-6: Search_
