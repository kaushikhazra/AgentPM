# AgentPM Core Business Logic - Tasks

## Methodology Extensions
- [ ] Add helper methods to BaseMethodology
  _COR-1: Work Item Convenience API_
  - [ ] get_story_type()
  - [ ] get_task_type()
  - [ ] get_in_progress_status()
  - [ ] get_done_status()
  - [ ] get_blocked_status()
- [ ] Implement helpers in ClassicAgileMethodology
  _COR-1: Work Item Convenience API_
- [ ] Write tests for methodology helpers
  _COR-1: Work Item Convenience API_

## Work Items API
- [ ] Create core/work_items.py
  _COR-1: Work Item Convenience API_
  - [ ] create_story() methodology-aware
  - [ ] create_task() with auto parent edge
  - [ ] get_story_with_tasks() convenience function
- [ ] Write tests for work item helpers
  _COR-1: Work Item Convenience API_

## Workflow Shortcuts
- [ ] Create core/workflow.py
  _COR-2: Status Workflow_
  - [ ] start_node() - status + timer
  - [ ] complete_node() - status + stop timer
  - [ ] block_node() - with reason
  - [ ] unblock_node()
- [ ] Add review workflow functions
  _COR-2: Status Workflow_
  - [ ] submit_for_review()
  - [ ] approve()
  - [ ] reject()
- [ ] Write tests for workflow functions
  _COR-2: Status Workflow_

## Rollup Calculations
- [ ] Create core/rollup.py
  _COR-3: Rollup Calculations_
  - [ ] RollupStats dataclass
  - [ ] get_node_rollup()
  - [ ] get_milestone_rollup()
  - [ ] get_project_rollup()
- [ ] Handle edge cases (empty nodes, no estimates)
  _COR-3: Rollup Calculations_
- [ ] Write tests for rollup calculations
  _COR-3: Rollup Calculations_

## Dashboard
- [ ] Create core/reporting.py
  _COR-4: Dashboard_
  - [ ] Dashboard dataclass
  - [ ] get_dashboard()
  - [ ] Helper: list_time_entries_since()
- [ ] Write tests for dashboard
  _COR-4: Dashboard_

## Project Statistics
- [ ] Add to core/reporting.py
  _COR-5: Project Statistics_
  - [ ] ProjectStats dataclass
  - [ ] MilestoneProgress dataclass
  - [ ] get_project_stats()
  - [ ] Calculate velocity (completions per week)
- [ ] Write tests for project stats
  _COR-5: Project Statistics_

## Search
- [ ] Add search functions to core/reporting.py
  _COR-6: Search_
  - [ ] SearchResult dataclass
  - [ ] search() main function
  - [ ] search_nodes() helper
  - [ ] search_milestones() helper
  - [ ] extract_context() for snippets
- [ ] Write tests for search
  _COR-6: Search_

## Bulk Operations
- [ ] Create core/bulk.py
  _COR-7: Bulk Operations_
  - [ ] bulk_move_to_milestone()
  - [ ] bulk_update_status()
  - [ ] bulk_reassign()
  - [ ] bulk_tag()
  - [ ] bulk_delete()
- [ ] Handle partial failures (some succeed, some fail)
  _COR-7: Bulk Operations_
- [ ] Write tests for bulk operations
  _COR-7: Bulk Operations_

## Integration Tests
- [ ] Test: create story → create tasks → start → complete → verify rollup
  _COR-3: Rollup Calculations_
- [ ] Test: dashboard shows correct active state
  _COR-4: Dashboard_
- [ ] Test: search finds nodes by title and description
  _COR-6: Search_
