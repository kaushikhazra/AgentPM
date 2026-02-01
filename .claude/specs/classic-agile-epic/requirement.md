# Epic Support for Classic Agile Methodology

## Overview
Add Epic as a top-level work item type in the classic_agile methodology to support better organization of large features and initiatives.

## User Stories

### EPIC-CREATE: Create Epic
**As a** project manager
**I want to** create epics to group related stories
**So that** I can organize large features and track progress at a higher level

**Acceptance Criteria:**
- Can create an epic with title and description
- Epic has its own status workflow
- Epic can be assigned to a milestone

### EPIC-HIERARCHY: Epic-Story Hierarchy
**As a** project manager
**I want to** link stories to an epic as children
**So that** I can see all work items that contribute to a larger goal

**Acceptance Criteria:**
- A story can have an epic as its parent
- Can view all stories under an epic
- Epic rollup shows aggregated progress of child stories

### EPIC-WORKFLOW: Epic Status Workflow
**As a** project manager
**I want to** track epic progress through statuses
**So that** I can communicate feature readiness to stakeholders

**Acceptance Criteria:**
- Epic statuses: draft → ready → in_progress → done → cancelled
- Status transitions follow agile principles
- Epic can be marked blocked with a reason

### EPIC-MCP: Epic in MCP Tools
**As an** AI agent
**I want to** create and manage epics via MCP tools
**So that** I can help organize project work programmatically

**Acceptance Criteria:**
- pm_create_node supports node_type="epic"
- pm_list_nodes can filter by epic type
- pm_get_descendants shows epic → story → task hierarchy

## Out of Scope
- Epic-level time tracking (use rollup from children)
- Epic-to-epic relationships (keep hierarchy simple)
- Automatic epic status updates based on child status (future enhancement)
