"""Project routes — CRUD + methodology + stats."""

from fastapi import APIRouter, Depends, Response

from ..auth.users import User
from ..deps import call_mcp_tool, get_current_user
from ..schemas.projects import ProjectCreate, ProjectUpdate

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("/")
async def list_projects(
    company_id: str | None = None,
    status: str | None = None,
    include_stats: bool = False,
    current_user: User = Depends(get_current_user),
):
    """List projects with optional filters."""
    args = {"include_stats": include_stats}
    if company_id:
        args["company_id"] = company_id
    if status:
        args["status"] = status
    return call_mcp_tool("pm_list_projects", args)


@router.get("/{project_id}")
async def get_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
):
    """Get a project by ID."""
    return call_mcp_tool("pm_get_project", {"project_id": project_id})


@router.post("/", status_code=201)
async def create_project(
    data: ProjectCreate,
    current_user: User = Depends(get_current_user),
):
    """Create a new project."""
    return call_mcp_tool("pm_create_project", data.model_dump(exclude_none=True))


@router.patch("/{project_id}")
async def update_project(
    project_id: str,
    data: ProjectUpdate,
    current_user: User = Depends(get_current_user),
):
    """Update a project."""
    args = {"project_id": project_id, **data.model_dump(exclude_none=True)}
    return call_mcp_tool("pm_update_project", args)


@router.delete("/{project_id}", status_code=204)
async def delete_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
):
    """Delete a project."""
    call_mcp_tool("pm_delete_project", {"project_id": project_id})
    return Response(status_code=204)


@router.get("/{project_id}/methodology")
async def get_methodology(
    project_id: str,
    current_user: User = Depends(get_current_user),
):
    """Get methodology info for a project."""
    return call_mcp_tool("pm_get_methodology_info", {"project_id": project_id})


@router.get("/{project_id}/stats")
async def get_project_stats(
    project_id: str,
    current_user: User = Depends(get_current_user),
):
    """Get project stats."""
    return call_mcp_tool("pm_get_project_stats", {"project_id": project_id})
