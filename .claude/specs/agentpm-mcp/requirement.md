# AgentPM MCP Server - Requirements

## Overview
Implement an MCP (Model Context Protocol) server that exposes AgentPM to AI assistants. This is the PRIMARY interface for AgentPM - designed for AI-first interaction.

## Dependencies
- Requires: agentpm-foundation, agentpm-graph, agentpm-core

## User Stories

### MCP-1: MCP Server Setup
As a developer, I want a properly configured MCP server so that AI assistants can connect to AgentPM.

**Acceptance Criteria:**
- MCP server using official Python SDK
- Support stdio transport (for Claude Code)
- Support SSE transport (for future Claude.ai integration)
- Configurable database path via environment variable
- Proper error handling and logging

### MCP-2: Company Tools
As an AI assistant, I want tools for company management so that I can help users organize projects.

**Acceptance Criteria:**
- `pm_list_companies()` - list all companies
- `pm_create_company(name, description?)` - create company
- `pm_get_company(id)` - get company with project summary

### MCP-3: Project Tools
As an AI assistant, I want tools for project management so that I can help users manage their work.

**Acceptance Criteria:**
- `pm_list_projects(company_id?, status?)` - list projects
- `pm_create_project(company_id, name, methodology?, description?)` - create project
- `pm_get_project(id)` - get project with methodology info and stats
- `pm_update_project(id, status?, name?, description?)` - update project
- `pm_get_methodology_info(project_id)` - get valid types, statuses, transitions

### MCP-4: Milestone Tools
As an AI assistant, I want tools for milestone management.

**Acceptance Criteria:**
- `pm_list_milestones(project_id, status?)` - list milestones
- `pm_create_milestone(project_id, name, target_date?, description?)` - create
- `pm_complete_milestone(id)` - mark complete

### MCP-5: Node Tools
As an AI assistant, I want tools for node (work item) management.

**Acceptance Criteria:**
- `pm_list_nodes(project_id, node_type?, status?, assignee?)` - list nodes
- `pm_create_node(project_id, node_type, title, description?, properties?)` - create
- `pm_get_node(id)` - get node with edges and time entries
- `pm_update_node(id, status?, assignee?, properties?)` - update
- `pm_start_node(id)` - start work (status + timer)
- `pm_complete_node(id)` - complete (status + stop timer)
- `pm_block_node(id, reason)` - block with reason

### MCP-6: Edge Tools
As an AI assistant, I want tools for managing relationships between nodes.

**Acceptance Criteria:**
- `pm_list_edges(project_id?, source_id?, target_id?, edge_type?)` - list edges
- `pm_create_edge(source_id, target_id, edge_type, properties?)` - create edge
- `pm_delete_edge(id)` - delete edge
- `pm_get_ancestors(node_id, edge_type?)` - traverse up
- `pm_get_descendants(node_id, edge_type?)` - traverse down

### MCP-7: Time Tracking Tools
As an AI assistant, I want tools for time tracking so that agents can log their work.

**Acceptance Criteria:**
- `pm_start_timer(node_id, notes?)` - start timer
- `pm_stop_timer(node_id?, entry_id?)` - stop timer
- `pm_log_time(node_id, duration_minutes, notes?)` - manual entry
- `pm_get_active_timer()` - get current timer status

### MCP-8: Reporting Tools
As an AI assistant, I want reporting tools for context and insights.

**Acceptance Criteria:**
- `pm_get_dashboard()` - current state summary
- `pm_get_project_stats(project_id)` - project statistics
- `pm_search(query)` - search across entities
- `pm_get_recent_activity(limit?, entity_type?, entity_id?)` - activity feed
- `pm_get_rollup(node_id)` - aggregated stats for node

### MCP-9: Tag Tools
As an AI assistant, I want tools for tag management.

**Acceptance Criteria:**
- `pm_list_tags()` - list all tags
- `pm_create_tag(name, color?)` - create tag
- `pm_tag_node(node_id, tag_name)` - add tag
- `pm_untag_node(node_id, tag_name)` - remove tag

### MCP-10: MCP Resources
As an AI assistant, I want read-only resources for context without calling tools.

**Acceptance Criteria:**
- `pm://dashboard` - current state summary
- `pm://project/{id}` - project details with methodology
- `pm://project/{id}/methodology` - valid types, statuses, transitions
- `pm://node/{id}` - node details with edges
- `pm://activity/recent` - recent activity feed

### MCP-11: Actor Identification
As a system, I want AI actors to be identified so that activity logs distinguish between human and AI actions.

**Acceptance Criteria:**
- All tools accept implicit actor identification
- Actor derived from MCP client metadata when available
- Defaults to "mcp" if not specified
- Activity logs show actor (e.g., "claude_code", "claude", "mcp")
