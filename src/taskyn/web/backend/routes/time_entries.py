"""Time entry routes — log manual time."""

from fastapi import APIRouter, Depends

from ..auth.users import User
from ..deps import call_mcp_tool, get_current_user
from ..schemas.timer import TimeEntryCreate

router = APIRouter(prefix="/time-entries", tags=["time-entries"])


@router.get("")
async def list_time_entries(
    project_id: str | None = None,
    limit: int = 200,
    current_user: User = Depends(get_current_user),
):
    """List time entries across all nodes."""
    args: dict = {}
    if project_id:
        args["project_id"] = project_id
    if limit != 200:
        args["limit"] = limit
    return await call_mcp_tool("pm_list_time_entries", args)


@router.post("", status_code=201)
async def log_time(
    data: TimeEntryCreate,
    current_user: User = Depends(get_current_user),
):
    """Log a manual time entry."""
    return await call_mcp_tool("pm_log_time", data.model_dump(exclude_none=True))


@router.get("/{entry_id}")
async def get_time_entry(
    entry_id: str,
    current_user: User = Depends(get_current_user),
):
    """Get a time entry by ID."""
    return await call_mcp_tool("pm_get_time_entry", {"entry_id": entry_id})


@router.delete("/{entry_id}", status_code=204)
async def delete_time_entry(
    entry_id: str,
    current_user: User = Depends(get_current_user),
):
    """Delete a time entry."""
    await call_mcp_tool("pm_delete_time_entry", {"entry_id": entry_id})
    return None
