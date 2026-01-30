# AgentPM Graph Layer - Tasks

## Exceptions
- [x] Create exceptions.py with custom exception classes
  _GRP-1: Node Creation_
  - [x] AgentPMError base class
  - [x] NotFoundError
  - [x] ValidationError
  - [x] InvalidTransitionError
  - [x] CycleDetectedError
  - [x] CardinalityError

## Graph Validation
- [x] Create graph/validation.py
  _GRP-1: Node Creation_
  - [x] validate_node_creation()
  - [x] validate_node_update()
  - [x] validate_status_transition()
  - [x] validate_edge_creation()
- [x] Write tests for validation functions
  _GRP-1: Node Creation_

## Node Operations
- [x] Create graph/nodes.py
  _GRP-1: Node Creation_
  - [x] create_node() with methodology validation
  - [x] get_node() by ID
  - [x] list_nodes() with filters
  - [x] update_node() with transition validation
  - [x] delete_node()
- [x] Integrate activity logging into node operations
  _GRP-9: Activity Logging_
- [x] Write tests for node CRUD
  _GRP-1: Node Creation, GRP-2: Node Updates, GRP-3: Node Queries_

## Edge Operations
- [x] Create graph/edges.py
  _GRP-4: Edge Creation_
  - [x] create_edge() with methodology validation
  - [x] delete_edge()
  - [x] list_edges() with filters
- [x] Implement cardinality constraint checking
  _GRP-4: Edge Creation_
- [x] Integrate activity logging into edge operations
  _GRP-9: Activity Logging_
- [x] Write tests for edge CRUD
  _GRP-4: Edge Creation, GRP-5: Edge Queries_

## Graph Traversal
- [x] Create graph/traversal.py
  _GRP-5: Edge Queries_
  - [x] detect_cycle() using DFS
  - [x] get_ancestors() using BFS
  - [x] get_descendants() using BFS
  - [x] get_parents() (depth=1)
  - [x] get_children() (depth=1)
- [x] Write tests for traversal functions
  _GRP-5: Edge Queries_

## Milestone Operations
- [x] Create core/milestone.py
  _GRP-6: Milestone Management_
  - [x] create_milestone()
  - [x] get_milestone()
  - [x] list_milestones() with stats
  - [x] update_milestone()
  - [x] complete_milestone()
  - [x] delete_milestone()
- [x] Add milestone_id handling in node operations
  _GRP-6: Milestone Management_
- [x] Write tests for milestone operations
  _GRP-6: Milestone Management_

## Time Tracking
- [x] Create core/time_entry.py
  _GRP-7: Time Tracking_
  - [x] start_timer() with auto-stop of existing
  - [x] stop_timer()
  - [x] log_time() for manual entries
  - [x] get_active_timer()
  - [x] list_time_entries()
  - [x] get_time_total()
- [x] Integrate activity logging
  _GRP-9: Activity Logging_
- [x] Write tests for time tracking
  _GRP-7: Time Tracking_

## Tag System
- [x] Create core/tag.py
  _GRP-8: Tag System_
  - [x] create_tag()
  - [x] list_tags()
  - [x] delete_tag()
  - [x] tag_node()
  - [x] untag_node()
  - [x] list_nodes_by_tag()
  - [x] get_node_tags()
- [x] Integrate activity logging
  _GRP-9: Activity Logging_
- [x] Write tests for tag operations
  _GRP-8: Tag System_

## Activity Logging
- [x] Create core/activity.py
  _GRP-9: Activity Logging_
  - [x] log_activity()
  - [x] list_activity() with filters
  - [x] get_entity_activity()
- [x] Write tests for activity logging
  _GRP-9: Activity Logging_

## Integration Tests
- [x] Write test: create story → create tasks under it → verify parent edges
  _GRP-4: Edge Creation_
- [x] Write test: status transitions through full lifecycle
  _GRP-2: Node Updates_
- [x] Write test: timer start → stop → verify time entry
  _GRP-7: Time Tracking_
- [x] Write test: verify activity log captures all changes
  _GRP-9: Activity Logging_
