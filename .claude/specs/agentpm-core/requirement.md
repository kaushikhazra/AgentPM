# AgentPM Core Business Logic - Requirements

## Overview
Implement high-level business logic that wraps the graph layer, providing convenient APIs for common operations, rollup calculations, and reporting.

## Dependencies
- Requires: agentpm-foundation, agentpm-graph

## User Stories

### US-1: Work Item Convenience API
As a user, I want simple functions to create stories and tasks so that I don't need to know the underlying graph structure.

**Acceptance Criteria:**
- create_story() creates node with type="story" and validates methodology
- create_task() creates node with type="task" and parent edge to story
- start_work() sets status to in_progress and starts timer
- complete_work() sets terminal status and stops timer
- block_work() sets blocked status with reason
- Functions work with any node type from any methodology

### US-2: Status Workflow
As a user, I want shortcut functions for common status changes so that updates are quick.

**Acceptance Criteria:**
- start_node(id) → in_progress status + start timer
- complete_node(id) → done status + stop timer
- block_node(id, reason) → blocked status
- unblock_node(id) → previous status or in_progress
- Review workflow: submit_for_review(id), approve(id), reject(id)

### US-3: Rollup Calculations
As a user, I want to see aggregated metrics for parent items so that I can understand effort at different levels.

**Acceptance Criteria:**
- Rollup time spent from all descendants
- Rollup estimated time from all descendants
- Calculate completion percentage (done tasks / total tasks)
- Calculate story points rollup
- Support rollup at any level (story, milestone, project)

### US-4: Dashboard
As a user, I want a dashboard view so that I can see my current work state at a glance.

**Acceptance Criteria:**
- Active timer info (node, duration)
- In-progress nodes across all projects
- Blocked nodes with reasons
- Today's time total
- Recent activity (last 10 items)

### US-5: Project Statistics
As a user, I want project statistics so that I can track progress.

**Acceptance Criteria:**
- Total nodes by type and status
- Time spent this week/month/total
- Velocity (nodes completed per week)
- Blockers count
- Milestone progress

### US-6: Search
As a user, I want to search across all entities so that I can find items quickly.

**Acceptance Criteria:**
- Search by text (matches title, description)
- Search across nodes, milestones, projects
- Filter by entity type
- Return relevance-ranked results
- Include context (project name, status)

### US-7: Bulk Operations
As a user, I want to perform bulk operations so that I can efficiently manage multiple items.

**Acceptance Criteria:**
- Move multiple nodes to a milestone
- Change status of multiple nodes
- Reassign multiple nodes
- Add tag to multiple nodes
- Delete multiple nodes
