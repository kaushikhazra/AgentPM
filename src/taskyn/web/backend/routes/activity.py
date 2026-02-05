"""Activity route — recent activity log."""

from fastapi import APIRouter, Depends

from ..auth.users import User
from ..deps import call_mcp_tool, get_current_user

router = APIRouter(tags=["reporting"])


@router.get("/activity")
async def get_activity(
    limit: int = 20,
    entity_type: str | None = None,
    entity_id: str | None = None,
    current_user: User = Depends(get_current_user),
):
    """Get recent activity log."""
    args = {"limit": limit}
    if entity_type:
        args["entity_type"] = entity_type
    if entity_id:
        args["entity_id"] = entity_id
    return await call_mcp_tool("pm_get_recent_activity", args)
