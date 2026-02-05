"""Milestone routes — list, create, get, update, complete."""

from fastapi import APIRouter, Depends

from ..auth.users import User
from ..deps import call_mcp_tool, get_current_user
from ..schemas.milestones import MilestoneCreate, MilestoneUpdate

router = APIRouter(prefix="/milestones", tags=["milestones"])


@router.get("")
async def list_milestones(
    project_id: str,
    status: str | None = None,
    current_user: User = Depends(get_current_user),
):
    """List milestones for a project."""
    args = {"project_id": project_id}
    if status:
        args["status"] = status
    return await call_mcp_tool("pm_list_milestones", args)


@router.get("/{milestone_id}")
async def get_milestone(
    milestone_id: str,
    current_user: User = Depends(get_current_user),
):
    """Get a milestone by ID."""
    return await call_mcp_tool("pm_get_milestone", {"milestone_id": milestone_id})


@router.post("", status_code=201)
async def create_milestone(
    data: MilestoneCreate,
    current_user: User = Depends(get_current_user),
):
    """Create a new milestone."""
    args = data.model_dump(exclude_none=True)
    if "target_date" in args:
        args["target_date"] = str(args["target_date"])
    return await call_mcp_tool("pm_create_milestone", args)


@router.patch("/{milestone_id}")
async def update_milestone(
    milestone_id: str,
    data: MilestoneUpdate,
    current_user: User = Depends(get_current_user),
):
    """Update a milestone."""
    args = {"milestone_id": milestone_id, **data.model_dump(exclude_unset=True)}
    if "target_date" in args and args["target_date"] is not None:
        args["target_date"] = str(args["target_date"])
    return await call_mcp_tool("pm_update_milestone", args)


@router.post("/{milestone_id}/complete")
async def complete_milestone(
    milestone_id: str,
    current_user: User = Depends(get_current_user),
):
    """Mark a milestone as complete."""
    return await call_mcp_tool("pm_complete_milestone", {"milestone_id": milestone_id})


@router.delete("/{milestone_id}", status_code=204)
async def delete_milestone(
    milestone_id: str,
    current_user: User = Depends(get_current_user),
):
    """Delete a milestone."""
    await call_mcp_tool("pm_delete_milestone", {"milestone_id": milestone_id})
    return None
