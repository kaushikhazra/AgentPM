"""Search route — full-text search."""

from fastapi import APIRouter, Depends

from ..auth.users import User
from ..deps import call_mcp_tool, get_current_user

router = APIRouter(tags=["reporting"])


@router.get("/search")
async def search(
    query: str,
    entity_type: str | None = None,
    project_id: str | None = None,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
):
    """Full-text search across entities."""
    args = {"query": query, "limit": limit}
    if entity_type:
        args["entity_type"] = entity_type
    if project_id:
        args["project_id"] = project_id
    return await call_mcp_tool("pm_search", args)
