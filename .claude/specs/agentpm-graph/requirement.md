# AgentPM Graph Layer - Requirements

## Overview
Implement the graph operations layer for creating, managing, and traversing nodes and edges. This includes the tracking layer (time entries, tags, activity logging).

## Dependencies
- Requires: agentpm-foundation (database, models, methodology system)

## User Stories

### GRP-1: Node Creation
As a user, I want to create work item nodes so that I can track work in my projects.

**Acceptance Criteria:**
- Create node with project_id, node_type, title, and optional fields
- Node type validated against project's methodology
- Initial status set from methodology's node type definition
- Properties validated against methodology's required/optional properties
- Activity logged on creation

### GRP-2: Node Updates
As a user, I want to update nodes so that I can track progress and changes.

**Acceptance Criteria:**
- Update title, description, assignee, priority, properties
- Status changes validated against methodology's allowed transitions
- Blocked status requires blocked_reason
- completed_at set automatically when entering terminal status
- Activity logged on all changes

### GRP-3: Node Queries
As a user, I want to query nodes so that I can find work items.

**Acceptance Criteria:**
- List nodes by project, node_type, status, assignee, milestone
- Get single node by ID with full details
- Include edge count in node details
- Support pagination for large result sets

### GRP-4: Edge Creation
As a user, I want to create relationships between nodes so that I can model dependencies and hierarchies.

**Acceptance Criteria:**
- Create edge with source_id, target_id, edge_type
- Edge type validated against methodology (source/target types)
- Cardinality constraints enforced (e.g., max 1 parent)
- Cycle detection for non-cyclical edge types
- Activity logged on creation

### GRP-5: Edge Queries
As a user, I want to query edges so that I can understand relationships.

**Acceptance Criteria:**
- List edges by project, source, target, edge_type
- Get ancestors of a node (follow edges up)
- Get descendants of a node (follow edges down)
- Get direct parents/children

### GRP-6: Milestone Management
As a user, I want to assign nodes to milestones so that I can group work by target dates.

**Acceptance Criteria:**
- Create milestone with name, target_date, description
- Assign/unassign nodes to milestones
- List nodes by milestone
- Complete milestone (sets completed_at)
- List milestones with node counts and completion stats

### GRP-7: Time Tracking
As a user, I want to track time spent on any node so that I can measure effort.

**Acceptance Criteria:**
- Start timer on a node (creates time_entry with started_at)
- Stop active timer (sets ended_at, calculates duration)
- Only one active timer at a time (globally)
- Log manual time entry with duration and notes
- Get active timer status
- List time entries for a node
- Activity logged on time entries

### GRP-8: Tag System
As a user, I want to tag nodes so that I can categorize and filter work.

**Acceptance Criteria:**
- Create tag with name and optional color
- Add tag to node
- Remove tag from node
- List all tags
- List nodes by tag
- Delete tag (removes from all nodes)

### GRP-9: Activity Logging
As a developer, I want all changes automatically logged so that I have an audit trail.

**Acceptance Criteria:**
- Log entity creation (node, edge, time_entry, etc.)
- Log status changes with old/new values
- Log assignment changes
- Log time entries
- Include actor (human or AI identifier)
- Query activity by entity, time range, actor
