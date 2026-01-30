# AgentPM MCP Server - Tasks

## Server Setup
- [x] Add fastmcp package to dependencies in pyproject.toml
  _MCP-1: MCP Server Setup_
- [x] Create mcp/server.py with FastMCP server
  _MCP-1: MCP Server Setup_
  - [x] Initialize FastMCP with name "agentpm"
  - [x] Configure database from AGENTPM_DB env var
  - [x] Add get_actor() helper for AGENTPM_ACTOR env var
- [x] Create mcp/__main__.py for `python -m agentpm.mcp` entry
  _MCP-1: MCP Server Setup_
- [x] Test server starts without errors
  _MCP-1: MCP Server Setup_

## Company Tools
- [x] Implement pm_list_companies tool
  _MCP-2: Company Tools_
- [x] Implement pm_create_company tool
  _MCP-2: Company Tools_
- [x] Implement pm_get_company tool
  _MCP-2: Company Tools_
- [x] Write tests for company tools
  _MCP-2: Company Tools_

## Project Tools
- [x] Implement pm_list_projects tool
  _MCP-3: Project Tools_
- [x] Implement pm_create_project tool
  _MCP-3: Project Tools_
- [x] Implement pm_get_project tool
  _MCP-3: Project Tools_
- [x] Implement pm_update_project tool
  _MCP-3: Project Tools_
- [x] Implement pm_get_methodology_info tool
  _MCP-3: Project Tools_
- [x] Write tests for project tools
  _MCP-3: Project Tools_

## Milestone Tools
- [x] Implement pm_list_milestones tool
  _MCP-4: Milestone Tools_
- [x] Implement pm_create_milestone tool
  _MCP-4: Milestone Tools_
- [x] Implement pm_complete_milestone tool
  _MCP-4: Milestone Tools_
- [x] Write tests for milestone tools
  _MCP-4: Milestone Tools_

## Node Tools
- [x] Implement pm_list_nodes tool
  _MCP-5: Node Tools_
- [x] Implement pm_create_node tool
  _MCP-5: Node Tools_
- [x] Implement pm_get_node tool
  _MCP-5: Node Tools_
- [x] Implement pm_update_node tool
  _MCP-5: Node Tools_
- [x] Implement pm_start_node tool
  _MCP-5: Node Tools_
- [x] Implement pm_complete_node tool
  _MCP-5: Node Tools_
- [x] Implement pm_block_node tool
  _MCP-5: Node Tools_
- [x] Write tests for node tools
  _MCP-5: Node Tools_

## Edge Tools
- [x] Implement pm_list_edges tool
  _MCP-6: Edge Tools_
- [x] Implement pm_create_edge tool
  _MCP-6: Edge Tools_
- [x] Implement pm_delete_edge tool
  _MCP-6: Edge Tools_
- [x] Implement pm_get_ancestors tool
  _MCP-6: Edge Tools_
- [x] Implement pm_get_descendants tool
  _MCP-6: Edge Tools_
- [x] Write tests for edge tools
  _MCP-6: Edge Tools_

## Time Tracking Tools
- [x] Implement pm_start_timer tool
  _MCP-7: Time Tracking Tools_
- [x] Implement pm_stop_timer tool
  _MCP-7: Time Tracking Tools_
- [x] Implement pm_log_time tool
  _MCP-7: Time Tracking Tools_
- [x] Implement pm_get_active_timer tool
  _MCP-7: Time Tracking Tools_
- [x] Write tests for time tracking tools
  _MCP-7: Time Tracking Tools_

## Reporting Tools
- [x] Implement pm_get_dashboard tool
  _MCP-8: Reporting Tools_
- [x] Implement pm_get_project_stats tool
  _MCP-8: Reporting Tools_
- [x] Implement pm_search tool
  _MCP-8: Reporting Tools_
- [x] Implement pm_get_recent_activity tool
  _MCP-8: Reporting Tools_
- [x] Implement pm_get_rollup tool
  _MCP-8: Reporting Tools_
- [x] Write tests for reporting tools
  _MCP-8: Reporting Tools_

## Tag Tools
- [x] Implement pm_list_tags tool
  _MCP-9: Tag Tools_
- [x] Implement pm_create_tag tool
  _MCP-9: Tag Tools_
- [x] Implement pm_tag_node tool
  _MCP-9: Tag Tools_
- [x] Implement pm_untag_node tool
  _MCP-9: Tag Tools_
- [x] Write tests for tag tools
  _MCP-9: Tag Tools_

## MCP Resources
- [x] Implement pm://dashboard resource
  _MCP-10: MCP Resources_
- [x] Implement pm://project/{id} resource
  _MCP-10: MCP Resources_
- [x] Implement pm://project/{id}/methodology resource
  _MCP-10: MCP Resources_
- [x] Implement pm://node/{id} resource
  _MCP-10: MCP Resources_
- [x] Implement pm://activity/recent resource
  _MCP-10: MCP Resources_

## Actor Identification
- [x] Add AGENTPM_ACTOR environment variable support
  _MCP-11: Actor Identification_
- [x] Pass actor to all tool implementations
  _MCP-11: Actor Identification_

## Integration Tests
- [x] Test full workflow via MCP: create company → project → story → task → timer
  _MCP-5: Node Tools_
