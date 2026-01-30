# MCP Test Plan

Testing AgentPM via MCP server using FastMCP client or Claude.

## Setup Option 1: FastMCP Dev Mode
```bash
cd C:\Projects\AgentPM
pip install -e .
set AGENTPM_DB=test_mcp.db
fastmcp dev src/agentpm/mcp/server.py
```
Opens browser UI at http://localhost:5173 for interactive testing.

## Setup Option 2: Claude Desktop
Add to `~/.claude/claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "agentpm": {
      "command": "python",
      "args": ["-m", "agentpm.mcp"],
      "env": {
        "AGENTPM_DB": "C:/Users/<you>/.agentpm/test_mcp.db",
        "AGENTPM_ACTOR": "claude"
      }
    }
  }
}
```
Restart Claude Desktop, then test via conversation.

## Setup Option 3: Python Client
```python
import asyncio
from fastmcp import Client
from agentpm.mcp.server import mcp

async def test():
    client = Client(mcp)
    async with client:
        result = await client.call_tool("pm_list_companies", {})
        print(result)

asyncio.run(test())
```

---

## 1. Company Tools

### 1.1 List Companies (empty)
**Tool**: `pm_list_companies`
**Args**: `{}`
**Expected**: Empty list `[]`

### 1.2 Create Company
**Tool**: `pm_create_company`
**Args**: `{"name": "MCP Test Corp", "description": "Testing via MCP"}`
**Expected**: Company object with id, name, description

### 1.3 Get Company
**Tool**: `pm_get_company`
**Args**: `{"company_id": "<id from above>"}`
**Expected**: Company with projects list (empty)

---

## 2. Project Tools

### 2.1 Create Project
**Tool**: `pm_create_project`
**Args**:
```json
{
  "company_id": "<company_id>",
  "name": "MCP Project",
  "methodology": "classic_agile"
}
```
**Expected**: Project object with methodology

### 2.2 Get Methodology Info
**Tool**: `pm_get_methodology_info`
**Args**: `{"project_id": "<project_id>"}`
**Expected**: Object with node_types (story, task) and edge_types

### 2.3 List Projects
**Tool**: `pm_list_projects`
**Args**: `{}`
**Expected**: List containing "MCP Project"

### 2.4 Get Project Stats
**Tool**: `pm_get_project_stats`
**Args**: `{"project_id": "<project_id>"}`
**Expected**: Stats object with total_nodes, nodes_by_status, etc.

---

## 3. Node Tools

### 3.1 Create Story
**Tool**: `pm_create_node`
**Args**:
```json
{
  "project_id": "<project_id>",
  "node_type": "story",
  "title": "User Registration"
}
```
**Expected**: Node with status "backlog"

### 3.2 Create Task
**Tool**: `pm_create_node`
**Args**:
```json
{
  "project_id": "<project_id>",
  "node_type": "task",
  "title": "Create signup form"
}
```
**Expected**: Node with status "todo"

### 3.3 Create Parent Edge
**Tool**: `pm_create_edge`
**Args**:
```json
{
  "source_id": "<task_id>",
  "target_id": "<story_id>",
  "edge_type": "parent"
}
```
**Expected**: Edge object (task → story)

### 3.4 List Nodes
**Tool**: `pm_list_nodes`
**Args**: `{"project_id": "<project_id>"}`
**Expected**: List with story and task

### 3.5 Get Node with Details
**Tool**: `pm_get_node`
**Args**: `{"node_id": "<story_id>"}`
**Expected**: Node with edges, time_entries, rollup stats

### 3.6 Start Node
**Tool**: `pm_start_node`
**Args**: `{"node_id": "<task_id>"}`
**Expected**: Status → "in_progress", timer started

### 3.7 Complete Node
**Tool**: `pm_complete_node`
**Args**: `{"node_id": "<task_id>"}`
**Expected**: Status → "done"

### 3.8 Block Node
**Tool**: `pm_block_node`
**Args**: `{"node_id": "<task_id>", "reason": "Waiting for design"}`
**Expected**: Status includes blocked_reason

---

## 4. Time Tracking Tools

### 4.1 Start Timer
**Tool**: `pm_start_timer`
**Args**: `{"node_id": "<node_id>", "notes": "Working on feature"}`
**Expected**: Time entry object with started_at

### 4.2 Get Active Timer
**Tool**: `pm_get_active_timer`
**Args**: `{}`
**Expected**: Active timer with node info

### 4.3 Stop Timer
**Tool**: `pm_stop_timer`
**Args**: `{}`
**Expected**: Stopped timer with duration_minutes

### 4.4 Log Time
**Tool**: `pm_log_time`
**Args**: `{"node_id": "<node_id>", "duration_minutes": 30, "notes": "Review"}`
**Expected**: Time entry with 30 minutes

---

## 5. Reporting Tools

### 5.1 Dashboard
**Tool**: `pm_get_dashboard`
**Args**: `{}`
**Expected**: Object with in_progress_nodes, blocked_nodes, today_time_minutes

### 5.2 Search
**Tool**: `pm_search`
**Args**: `{"query": "Registration"}`
**Expected**: Results containing "User Registration"

### 5.3 Recent Activity
**Tool**: `pm_get_recent_activity`
**Args**: `{"limit": 10}`
**Expected**: List of activity entries

### 5.4 Get Rollup
**Tool**: `pm_get_rollup`
**Args**: `{"node_id": "<story_id>"}`
**Expected**: Aggregated stats for story + children

---

## 6. Tag Tools

### 6.1 Create Tag
**Tool**: `pm_create_tag`
**Args**: `{"name": "priority", "color": "#ff0000"}`
**Expected**: Tag object

### 6.2 Tag Node
**Tool**: `pm_tag_node`
**Args**: `{"node_id": "<node_id>", "tag_name": "priority"}`
**Expected**: true

### 6.3 List Tags
**Tool**: `pm_list_tags`
**Args**: `{}`
**Expected**: List containing "priority"

### 6.4 Untag Node
**Tool**: `pm_untag_node`
**Args**: `{"node_id": "<node_id>", "tag_name": "priority"}`
**Expected**: true

---

## 7. Milestone Tools

### 7.1 Create Milestone
**Tool**: `pm_create_milestone`
**Args**:
```json
{
  "project_id": "<project_id>",
  "name": "Phase 1",
  "target_date": "2025-06-01"
}
```
**Expected**: Milestone object

### 7.2 List Milestones
**Tool**: `pm_list_milestones`
**Args**: `{"project_id": "<project_id>"}`
**Expected**: List with Phase 1

### 7.3 Complete Milestone
**Tool**: `pm_complete_milestone`
**Args**: `{"milestone_id": "<milestone_id>"}`
**Expected**: Status → "completed"

---

## 8. Edge Tools

### 8.1 List Edges
**Tool**: `pm_list_edges`
**Args**: `{"project_id": "<project_id>"}`
**Expected**: List of edges

### 8.2 Get Descendants
**Tool**: `pm_get_descendants`
**Args**: `{"node_id": "<story_id>"}`
**Expected**: List of child tasks

### 8.3 Get Ancestors
**Tool**: `pm_get_ancestors`
**Args**: `{"node_id": "<task_id>"}`
**Expected**: List containing parent story

### 8.4 Delete Edge
**Tool**: `pm_delete_edge`
**Args**: `{"edge_id": "<edge_id>"}`
**Expected**: true

---

## 9. Resources

### 9.1 Dashboard Resource
**URI**: `pm://dashboard`
**Expected**: JSON with current state

### 9.2 Project Resource
**URI**: `pm://project/<project_id>`
**Expected**: Project details with stats

### 9.3 Methodology Resource
**URI**: `pm://project/<project_id>/methodology`
**Expected**: Methodology definition

### 9.4 Node Resource
**URI**: `pm://node/<node_id>`
**Expected**: Node with edges and rollup

### 9.5 Activity Resource
**URI**: `pm://activity/recent`
**Expected**: Recent activity list

---

## 10. Full Workflow Test

Test a complete workflow via MCP:

1. `pm_create_company` → "Test Corp"
2. `pm_create_project` → "Test Project" (classic_agile)
3. `pm_create_milestone` → "Sprint 1"
4. `pm_create_node` → story "Feature A"
5. `pm_create_node` → task "Task 1"
6. `pm_create_edge` → parent (task → story)
7. `pm_start_node` → start task (timer starts)
8. `pm_get_dashboard` → verify task in progress
9. `pm_stop_timer` → stop timer
10. `pm_log_time` → add 30 more minutes
11. `pm_complete_node` → complete task
12. `pm_tag_node` → add "done" tag
13. `pm_get_rollup` → verify story rollup
14. `pm_get_project_stats` → verify counts
15. `pm_search` → find "Feature"

**Expected**: All operations succeed, data consistent

---

## MCP Test Checklist

### Tools
- [ ] Company tools (list, create, get)
- [ ] Project tools (list, create, get, update, methodology)
- [ ] Node tools (list, create, get, update, start, complete, block)
- [ ] Edge tools (list, create, delete, ancestors, descendants)
- [ ] Timer tools (start, stop, log, get_active)
- [ ] Tag tools (list, create, tag, untag)
- [ ] Milestone tools (list, create, complete)
- [ ] Reporting tools (dashboard, search, activity, rollup, stats)

### Resources
- [ ] pm://dashboard
- [ ] pm://project/{id}
- [ ] pm://project/{id}/methodology
- [ ] pm://node/{id}
- [ ] pm://activity/recent

### Integration
- [ ] Full workflow completes successfully
- [ ] Actor shows correctly in activity log
- [ ] Error handling returns useful messages
