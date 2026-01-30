# AgentPM Graph Layer - Tasks

## Exceptions
- [ ] Create exceptions.py with custom exception classes
  _US-1: Node Creation_
  - [ ] AgentPMError base class
  - [ ] NotFoundError
  - [ ] ValidationError
  - [ ] InvalidTransitionError
  - [ ] CycleDetectedError
  - [ ] CardinalityError

## Graph Validation
- [ ] Create graph/validation.py
  _US-1: Node Creation_
  - [ ] validate_node_creation()
  - [ ] validate_node_update()
  - [ ] validate_status_transition()
  - [ ] validate_edge_creation()
- [ ] Write tests for validation functions
  _US-1: Node Creation_

## Node Operations
- [ ] Create graph/nodes.py
  _US-1: Node Creation_
  - [ ] create_node() with methodology validation
  - [ ] get_node() by ID
  - [ ] list_nodes() with filters
  - [ ] update_node() with transition validation
  - [ ] delete_node()
- [ ] Integrate activity logging into node operations
  _US-9: Activity Logging_
- [ ] Write tests for node CRUD
  _US-1: Node Creation, US-2: Node Updates, US-3: Node Queries_

## Edge Operations
- [ ] Create graph/edges.py
  _US-4: Edge Creation_
  - [ ] create_edge() with methodology validation
  - [ ] delete_edge()
  - [ ] list_edges() with filters
- [ ] Implement cardinality constraint checking
  _US-4: Edge Creation_
- [ ] Integrate activity logging into edge operations
  _US-9: Activity Logging_
- [ ] Write tests for edge CRUD
  _US-4: Edge Creation, US-5: Edge Queries_

## Graph Traversal
- [ ] Create graph/traversal.py
  _US-5: Edge Queries_
  - [ ] detect_cycle() using DFS
  - [ ] get_ancestors() using BFS
  - [ ] get_descendants() using BFS
  - [ ] get_parents() (depth=1)
  - [ ] get_children() (depth=1)
- [ ] Write tests for traversal functions
  _US-5: Edge Queries_

## Milestone Operations
- [ ] Create core/milestone.py
  _US-6: Milestone Management_
  - [ ] create_milestone()
  - [ ] get_milestone()
  - [ ] list_milestones() with stats
  - [ ] update_milestone()
  - [ ] complete_milestone()
  - [ ] delete_milestone()
- [ ] Add milestone_id handling in node operations
  _US-6: Milestone Management_
- [ ] Write tests for milestone operations
  _US-6: Milestone Management_

## Time Tracking
- [ ] Create core/time_entry.py
  _US-7: Time Tracking_
  - [ ] start_timer() with auto-stop of existing
  - [ ] stop_timer()
  - [ ] log_time() for manual entries
  - [ ] get_active_timer()
  - [ ] list_time_entries()
  - [ ] get_time_total()
- [ ] Integrate activity logging
  _US-9: Activity Logging_
- [ ] Write tests for time tracking
  _US-7: Time Tracking_

## Tag System
- [ ] Create core/tag.py
  _US-8: Tag System_
  - [ ] create_tag()
  - [ ] list_tags()
  - [ ] delete_tag()
  - [ ] tag_node()
  - [ ] untag_node()
  - [ ] list_nodes_by_tag()
  - [ ] get_node_tags()
- [ ] Integrate activity logging
  _US-9: Activity Logging_
- [ ] Write tests for tag operations
  _US-8: Tag System_

## Activity Logging
- [ ] Create core/activity.py
  _US-9: Activity Logging_
  - [ ] log_activity()
  - [ ] list_activity() with filters
  - [ ] get_entity_activity()
- [ ] Write tests for activity logging
  _US-9: Activity Logging_

## Integration Tests
- [ ] Write test: create story → create tasks under it → verify parent edges
  _US-4: Edge Creation_
- [ ] Write test: status transitions through full lifecycle
  _US-2: Node Updates_
- [ ] Write test: timer start → stop → verify time entry
  _US-7: Time Tracking_
- [ ] Write test: verify activity log captures all changes
  _US-9: Activity Logging_
