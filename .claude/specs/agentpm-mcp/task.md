# AgentPM MCP Server - Tasks

## Server Setup
- [ ] Add mcp package to dependencies in pyproject.toml
  _MCP-1: MCP Server Setup_
- [ ] Create mcp/server.py with basic MCP server
  _MCP-1: MCP Server Setup_
  - [ ] Initialize Server with name "agentpm"
  - [ ] Configure database from AGENTPM_DB env var
  - [ ] Set up stdio transport
  - [ ] Add get_actor() helper
- [ ] Create mcp/__main__.py for `python -m agentpm.mcp` entry
  _MCP-1: MCP Server Setup_
- [ ] Test server starts without errors
  _MCP-1: MCP Server Setup_

## Company Tools
- [ ] Implement pm_list_companies tool
  _MCP-2: Company Tools_
- [ ] Implement pm_create_company tool
  _MCP-2: Company Tools_
- [ ] Implement pm_get_company tool
  _MCP-2: Company Tools_
- [ ] Write tests for company tools
  _MCP-2: Company Tools_

## Project Tools
- [ ] Implement pm_list_projects tool
  _MCP-3: Project Tools_
- [ ] Implement pm_create_project tool
  _MCP-3: Project Tools_
- [ ] Implement pm_get_project tool
  _MCP-3: Project Tools_
- [ ] Implement pm_update_project tool
  _MCP-3: Project Tools_
- [ ] Implement pm_get_methodology_info tool
  _MCP-3: Project Tools_
- [ ] Write tests for project tools
  _MCP-3: Project Tools_

## Milestone Tools
- [ ] Implement pm_list_milestones tool
  _MCP-4: Milestone Tools_
- [ ] Implement pm_create_milestone tool
  _MCP-4: Milestone Tools_
- [ ] Implement pm_complete_milestone tool
  _MCP-4: Milestone Tools_
- [ ] Write tests for milestone tools
  _MCP-4: Milestone Tools_

## Node Tools
- [ ] Implement pm_list_nodes tool
  _MCP-5: Node Tools_
- [ ] Implement pm_create_node tool
  _MCP-5: Node Tools_
- [ ] Implement pm_get_node tool
  _MCP-5: Node Tools_
- [ ] Implement pm_update_node tool
  _MCP-5: Node Tools_
- [ ] Implement pm_start_node tool
  _MCP-5: Node Tools_
- [ ] Implement pm_complete_node tool
  _MCP-5: Node Tools_
- [ ] Implement pm_block_node tool
  _MCP-5: Node Tools_
- [ ] Write tests for node tools
  _MCP-5: Node Tools_

## Edge Tools
- [ ] Implement pm_list_edges tool
  _MCP-6: Edge Tools_
- [ ] Implement pm_create_edge tool
  _MCP-6: Edge Tools_
- [ ] Implement pm_delete_edge tool
  _MCP-6: Edge Tools_
- [ ] Implement pm_get_ancestors tool
  _MCP-6: Edge Tools_
- [ ] Implement pm_get_descendants tool
  _MCP-6: Edge Tools_
- [ ] Write tests for edge tools
  _MCP-6: Edge Tools_

## Time Tracking Tools
- [ ] Implement pm_start_timer tool
  _MCP-7: Time Tracking Tools_
- [ ] Implement pm_stop_timer tool
  _MCP-7: Time Tracking Tools_
- [ ] Implement pm_log_time tool
  _MCP-7: Time Tracking Tools_
- [ ] Implement pm_get_active_timer tool
  _MCP-7: Time Tracking Tools_
- [ ] Write tests for time tracking tools
  _MCP-7: Time Tracking Tools_

## Reporting Tools
- [ ] Implement pm_get_dashboard tool
  _MCP-8: Reporting Tools_
- [ ] Implement pm_get_project_stats tool
  _MCP-8: Reporting Tools_
- [ ] Implement pm_search tool
  _MCP-8: Reporting Tools_
- [ ] Implement pm_get_recent_activity tool
  _MCP-8: Reporting Tools_
- [ ] Implement pm_get_rollup tool
  _MCP-8: Reporting Tools_
- [ ] Write tests for reporting tools
  _MCP-8: Reporting Tools_

## Tag Tools
- [ ] Implement pm_list_tags tool
  _MCP-9: Tag Tools_
- [ ] Implement pm_create_tag tool
  _MCP-9: Tag Tools_
- [ ] Implement pm_tag_node tool
  _MCP-9: Tag Tools_
- [ ] Implement pm_untag_node tool
  _MCP-9: Tag Tools_
- [ ] Write tests for tag tools
  _MCP-9: Tag Tools_

## MCP Resources
- [ ] Create mcp/resources.py
  _MCP-10: MCP Resources_
- [ ] Implement list_resources handler
  _MCP-10: MCP Resources_
- [ ] Implement pm://dashboard resource
  _MCP-10: MCP Resources_
- [ ] Implement pm://project/{id} resource
  _MCP-10: MCP Resources_
- [ ] Implement pm://project/{id}/methodology resource
  _MCP-10: MCP Resources_
- [ ] Implement pm://node/{id} resource
  _MCP-10: MCP Resources_
- [ ] Implement pm://activity/recent resource
  _MCP-10: MCP Resources_
- [ ] Write tests for resources
  _MCP-10: MCP Resources_

## Actor Identification
- [ ] Add AGENTPM_ACTOR environment variable support
  _MCP-11: Actor Identification_
- [ ] Pass actor to all tool implementations
  _MCP-11: Actor Identification_
- [ ] Test activity logs show correct actor
  _MCP-11: Actor Identification_

## Error Handling
- [ ] Create error handling decorator for tools
  _MCP-1: MCP Server Setup_
- [ ] Map AgentPM exceptions to MCP error codes
  _MCP-1: MCP Server Setup_
- [ ] Test error responses
  _MCP-1: MCP Server Setup_

## Documentation
- [ ] Document Claude Desktop configuration
  _MCP-1: MCP Server Setup_
- [ ] Document Claude Code configuration
  _MCP-1: MCP Server Setup_
- [ ] Create example MCP interaction scripts
  _MCP-1: MCP Server Setup_

## Integration Tests
- [ ] Test full workflow via MCP: create company → project → story → task → timer
  _MCP-5: Node Tools_
- [ ] Test with Claude Code (manual)
  _MCP-1: MCP Server Setup_
