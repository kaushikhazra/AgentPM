# Design: Fix list_nodes Default Limit

## Change

Single-point fix in `src/taskyn/graph/nodes.py` — change the `list_nodes()` function signature:

```python
# Before
def list_nodes(..., limit: int = 100, offset: int = 0):

# After
def list_nodes(..., limit: int | None = None, offset: int = 0):
```

When `limit` is `None`, the SQL query omits the `LIMIT` clause entirely. When an explicit limit is passed, behavior is unchanged.

## Why this approach

- **Single-point fix** — no changes needed in any caller (`pm_list_nodes`, `get_project_stats`, etc.) since they already don't pass a limit.
- **No silent truncation** — a data access function should not silently cap results by default. Pagination is the caller's responsibility.
- **Backward compatible** — callers that pass an explicit `limit` are unaffected.

## Affected code path

```
React UI → GET /nodes?project_id=...
         → FastAPI: call_mcp_tool("pm_list_nodes", args)
         → MCP: pm_list_nodes() → list_nodes(project_id=...)  ← fix here

get_project_stats() → list_nodes(project_id=...)              ← also fixed
```

## Risk

Low. The only change is removing a default cap. Projects in Taskyn are personal-scale (tens to low hundreds of nodes), so unbounded queries are safe.
