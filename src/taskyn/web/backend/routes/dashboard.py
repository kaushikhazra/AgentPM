"""Dashboard route — aggregated stats."""

from fastapi import APIRouter, Depends

from ..auth.users import User
from ..deps import call_mcp_tool, get_current_user

router = APIRouter(tags=["reporting"])


@router.get("/dashboard")
async def get_dashboard(
    current_user: User = Depends(get_current_user),
):
    """Get dashboard aggregates."""
    return await call_mcp_tool("pm_get_dashboard", {})
