"""Time entry routes — log manual time."""

from fastapi import APIRouter, Depends

from ..auth.users import User
from ..deps import call_mcp_tool, get_current_user
from ..schemas.timer import TimeEntryCreate

router = APIRouter(prefix="/time-entries", tags=["time-entries"])


@router.post("", status_code=201)
async def log_time(
    data: TimeEntryCreate,
    current_user: User = Depends(get_current_user),
):
    """Log a manual time entry."""
    return call_mcp_tool("pm_log_time", data.model_dump(exclude_none=True))
