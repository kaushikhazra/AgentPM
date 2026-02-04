# MCP Changes Required for Web UI

Changes to the MCP server identified during the Web UI route & data audit.

Source: `.claude/temp/web-ui-route-audit.md`

---

## Current State Analysis

Before listing changes, here's what the relevant MCP tools **already** return
today (from `src/taskyn/mcp/server.py`):

### `pm_get_node(node_id)` — Already Composite

Returns node data **plus**:
- `outgoing_edges` — all edges where this node is source
- `incoming_edges` — all edges where this node is target
- `time_entries` — full list of time entries
- `rollup` — aggregated stats (time, completion %, story points, etc.)

This means the audit's Issue 5 overstated the problem. The node detail page
does **not** need 4 separate calls. It needs:

| Call | Data |
|------|------|
| `pm_get_node(id)` | Node + edges + time entries + rollup |
| `pm_get_ancestors(id)` | Breadcrumb chain |

**2 calls**, not 4.

### `pm_get_project(project_id)` — Already Includes Stats

Returns project data **plus**:
- `stats.total_nodes`
- `stats.completed_nodes`
- `stats.in_progress_nodes`
- `stats.blocked_nodes`
- `stats.total_time_minutes`

This means the audit's Issue 7 overstated the problem. The project detail page
needs:

| Call | Data |
|------|------|
| `pm_get_project(id)` | Project info + summary stats |
| `pm_list_nodes(project_id=id)` | Child nodes list |
| `pm_get_methodology_info(id)` | Methodology config for UI rendering |

**3 calls**, not 4. And these can be parallelized by TanStack Query.

### `pm_get_company(company_id)` — No Stats

Returns company data + list of projects (basic info only). No aggregated stats
across projects.

### `pm_list_projects(...)` — No Stats

Returns basic project objects only. No per-project stats.

### `pm_list_companies()` — No Stats

Returns basic company objects only. No per-company stats.

---

## Change 1: New Tool — `pm_get_company_stats`

**Problem**: The company card and modal (mockup: `company.html`) display:
- Number of projects
- Total tasks across all projects
- Total time tracked
- Overall completion percentage

No existing tool provides this data.

**Solution**: Add `pm_get_company_stats(company_id)` tool.

**Implementation approach**:

```python
@mcp.tool()
def pm_get_company_stats(company_id: str) -> dict:
    """
    Get aggregated statistics for a company across all its projects.

    Args:
        company_id: Company ID

    Returns:
        Aggregated stats (project count, node counts, time, completion %)
    """
    from taskyn.core import get_company, list_projects, get_project_stats

    company = get_company(company_id)
    if company is None:
        raise ValueError(f"Company not found: {company_id}")

    projects = list_projects(company_id=company_id)

    total_projects = len(projects)
    total_nodes = 0
    completed_nodes = 0
    total_time_minutes = 0

    for project in projects:
        stats = get_project_stats(project.id)
        total_nodes += sum(stats.total_nodes.values())
        completed_nodes += stats.nodes_by_status.get("done", 0)
        total_time_minutes += stats.time_total

    completion_pct = (completed_nodes / total_nodes * 100) if total_nodes > 0 else 0

    return {
        "company_id": company_id,
        "total_projects": total_projects,
        "total_nodes": total_nodes,
        "completed_nodes": completed_nodes,
        "completion_percentage": round(completion_pct, 1),
        "total_time_minutes": total_time_minutes,
    }
```

**Where to add**: In `src/taskyn/mcp/server.py`, under the Company Tools section,
after `pm_delete_company`.

**Core dependency**: Uses existing `get_project_stats` from `taskyn.core`. No new
core functions needed.

**AI agent benefit**: AI agents can ask "how is this company doing overall?" without
calling multiple tools.

---

## Change 2: Enhance `pm_list_projects` — Add `include_stats`

**Problem**: The projects list page (mockup: `projects.html`) shows per-project:
- Node counts by type ("3 epics, 12 stories, 47 tasks")
- Progress bar with completion percentage

Currently requires N+1 calls: 1 `pm_list_projects` + N `pm_get_project_stats`.

**Solution**: Add optional `include_stats: bool = False` parameter.

**Implementation approach**:

```python
@mcp.tool()
def pm_list_projects(
    company_id: str | None = None,
    status: str | None = None,
    include_stats: bool = False
) -> list[dict]:
    """
    List projects with optional filters.

    Args:
        company_id: Filter by company
        status: Filter by status (active, on_hold, completed, archived)
        include_stats: Include per-project stats (node counts, completion %)

    Returns:
        List of project objects, optionally with stats
    """
    from taskyn.core import list_projects, get_project_stats

    projects = list_projects(company_id=company_id, status=status)
    result = []

    for p in projects:
        data = p.model_dump()
        if include_stats:
            stats = get_project_stats(p.id)
            total_nodes = sum(stats.total_nodes.values())
            completed_nodes = stats.nodes_by_status.get("done", 0)
            data["stats"] = {
                "total_nodes": total_nodes,
                "completed_nodes": completed_nodes,
                "completion_percentage": (
                    round(completed_nodes / total_nodes * 100, 1)
                    if total_nodes > 0 else 0
                ),
                "total_time_minutes": stats.time_total,
                "nodes_by_type": stats.total_nodes,
            }
        result.append(data)

    return result
```

**Backward compatible**: Existing callers (AI agents, CLI) are not affected.
The parameter defaults to `False`.

**AI agent benefit**: An AI agent building a project overview can get everything
in one call instead of N+1.

---

## Change 3: Enhance `pm_list_companies` — Add `include_stats`

**Problem**: Same pattern as projects. Company cards (mockup: `company.html`) need
per-company stats, but `pm_list_companies` returns basic info only.

Without this, the companies page would need N+1 calls: 1 `pm_list_companies` +
N `pm_get_company_stats`.

**Solution**: Add optional `include_stats: bool = False` parameter.

**Implementation approach**:

```python
@mcp.tool()
def pm_list_companies(include_stats: bool = False) -> list[dict]:
    """
    List all companies.

    Args:
        include_stats: Include per-company aggregated stats

    Returns:
        List of companies, optionally with stats
    """
    from taskyn.core import list_companies, list_projects, get_project_stats

    companies = list_companies()
    result = []

    for c in companies:
        data = c.model_dump()
        if include_stats:
            projects = list_projects(company_id=c.id)
            total_nodes = 0
            completed_nodes = 0
            total_time_minutes = 0

            for project in projects:
                stats = get_project_stats(project.id)
                total_nodes += sum(stats.total_nodes.values())
                completed_nodes += stats.nodes_by_status.get("done", 0)
                total_time_minutes += stats.time_total

            completion_pct = (
                round(completed_nodes / total_nodes * 100, 1)
                if total_nodes > 0 else 0
            )

            data["stats"] = {
                "total_projects": len(projects),
                "total_nodes": total_nodes,
                "completed_nodes": completed_nodes,
                "completion_percentage": completion_pct,
                "total_time_minutes": total_time_minutes,
            }
        result.append(data)

    return result
```

**Backward compatible**: Defaults to `False`.

---

## What Does NOT Need MCP Changes

### Node Detail Page (Audit Issue 5)

The audit recommended a composite FastAPI endpoint calling 4 MCP tools. After
reviewing the code, `pm_get_node` already returns edges, time entries, and
rollup. Only `pm_get_ancestors` is separate.

**Revised approach**: The frontend calls 2 MCP-backed REST endpoints in parallel:
- `GET /api/v1/nodes/:id` → `pm_get_node`
- `GET /api/v1/nodes/:id/ancestors` → `pm_get_ancestors`

TanStack Query can parallelize these. A composite FastAPI endpoint is
**not justified** for 2 calls.

### Project Detail Page (Audit Issue 7)

`pm_get_project` already includes stats. The frontend calls 3 endpoints in parallel:
- `GET /api/v1/projects/:id` → `pm_get_project` (includes stats)
- `GET /api/v1/nodes?project_id=:id` → `pm_list_nodes`
- `GET /api/v1/projects/:id/methodology` → `pm_get_methodology_info`

TanStack Query can parallelize these. A composite FastAPI endpoint is
**not justified** for 3 parallel calls.

### Planner & Dashboard Routes (Audit Issues 4, 6)

These are frontend routing changes only. No MCP changes needed.

---

## Summary

| # | Change | Type | Backward Compatible |
|---|--------|------|---------------------|
| 1 | `pm_get_company_stats(company_id)` | New tool | N/A |
| 2 | `pm_list_projects(..., include_stats)` | Enhancement | Yes (defaults False) |
| 3 | `pm_list_companies(include_stats)` | Enhancement | Yes (defaults False) |

### Corrected Assessments from Audit

| Audit Issue | Audit Said | Actual |
|-------------|-----------|--------|
| Issue 5 (Node Detail) | 4 calls, needs composite endpoint | 2 calls (`pm_get_node` is already composite), parallel OK |
| Issue 7 (Project Detail) | 4 calls, needs composite endpoint | 3 calls (`pm_get_project` includes stats), parallel OK |

### No Composite FastAPI Endpoints Needed

The original audit recommended composite FastAPI endpoints for node and project
detail pages. After verifying the MCP tool implementations, the existing tools
already aggregate most of the data. The remaining parallel calls (2-3) are well
within TanStack Query's ability to handle efficiently. This keeps the FastAPI
layer as a pure thin bridge with no aggregation responsibility.
