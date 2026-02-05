"""Timer routes — start, stop, current."""

from fastapi import APIRouter, Depends

from ..auth.users import User
from ..deps import call_mcp_tool, get_current_user
from ..schemas.timer import TimerStart, TimerStop

router = APIRouter(prefix="/timer", tags=["timer"])


@router.post("/start")
async def start_timer(
    data: TimerStart,
    current_user: User = Depends(get_current_user),
):
    """Start a timer on a node."""
    return await call_mcp_tool("pm_start_timer", data.model_dump(exclude_none=True))


@router.post("/stop")
async def stop_timer(
    data: TimerStop = TimerStop(),
    current_user: User = Depends(get_current_user),
):
    """Stop the active timer (or a specific timer by entry_id)."""
    return await call_mcp_tool("pm_stop_timer", data.model_dump(exclude_none=True))


@router.get("/current")
async def get_active_timer(
    current_user: User = Depends(get_current_user),
):
    """Get the currently active timer."""
    return await call_mcp_tool("pm_get_active_timer", {})
