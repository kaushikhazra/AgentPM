"""Tag routes — list and create."""

from fastapi import APIRouter, Depends

from ..auth.users import User
from ..deps import call_mcp_tool, get_current_user
from ..schemas.tags import TagCreate

router = APIRouter(prefix="/tags", tags=["tags"])


@router.get("")
async def list_tags(
    current_user: User = Depends(get_current_user),
):
    """List all tags."""
    return await call_mcp_tool("pm_list_tags", {})


@router.post("", status_code=201)
async def create_tag(
    data: TagCreate,
    current_user: User = Depends(get_current_user),
):
    """Create a new tag."""
    return await call_mcp_tool("pm_create_tag", data.model_dump(exclude_none=True))


@router.get("/{tag_name}/usage")
async def get_tag_usage(
    tag_name: str,
    current_user: User = Depends(get_current_user),
):
    """Get usage count for a tag."""
    return await call_mcp_tool("pm_get_tag_usage", {"tag_name": tag_name})


@router.delete("/{tag_name}", status_code=200)
async def delete_tag(
    tag_name: str,
    current_user: User = Depends(get_current_user),
):
    """Delete a tag. Returns info about how many nodes had this tag."""
    return await call_mcp_tool("pm_delete_tag", {"tag_name": tag_name})
