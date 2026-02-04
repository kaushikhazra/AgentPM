"""Milestone routes — list, create, complete."""

from fastapi import APIRouter, Depends

from ..auth.users import User
from ..deps import call_mcp_tool, get_current_user
from ..schemas.milestones import MilestoneCreate

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
    return call_mcp_tool("pm_list_milestones", args)


@router.post("", status_code=201)
async def create_milestone(
    data: MilestoneCreate,
    current_user: User = Depends(get_current_user),
):
    """Create a new milestone."""
    args = data.model_dump(exclude_none=True)
    if "target_date" in args:
        args["target_date"] = str(args["target_date"])
    return call_mcp_tool("pm_create_milestone", args)


@router.post("/{milestone_id}/complete")
async def complete_milestone(
    milestone_id: str,
    current_user: User = Depends(get_current_user),
):
    """Mark a milestone as complete."""
    return call_mcp_tool("pm_complete_milestone", {"milestone_id": milestone_id})
