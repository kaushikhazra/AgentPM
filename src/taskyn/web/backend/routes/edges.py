"""Edge routes — CRUD."""

from fastapi import APIRouter, Depends, Response

from ..auth.users import User
from ..deps import call_mcp_tool, get_current_user
from ..schemas.edges import EdgeCreate

router = APIRouter(prefix="/edges", tags=["edges"])


@router.get("")
async def list_edges(
    project_id: str | None = None,
    source_id: str | None = None,
    target_id: str | None = None,
    edge_type: str | None = None,
    current_user: User = Depends(get_current_user),
):
    """List edges with optional filters."""
    args = {}
    if project_id:
        args["project_id"] = project_id
    if source_id:
        args["source_id"] = source_id
    if target_id:
        args["target_id"] = target_id
    if edge_type:
        args["edge_type"] = edge_type
    return call_mcp_tool("pm_list_edges", args)


@router.post("", status_code=201)
async def create_edge(
    data: EdgeCreate,
    current_user: User = Depends(get_current_user),
):
    """Create a new edge."""
    return call_mcp_tool("pm_create_edge", data.model_dump())


@router.delete("/{edge_id}", status_code=204)
async def delete_edge(
    edge_id: str,
    current_user: User = Depends(get_current_user),
):
    """Delete an edge."""
    call_mcp_tool("pm_delete_edge", {"edge_id": edge_id})
    return Response(status_code=204)
