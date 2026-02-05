"""Company routes — CRUD + stats."""

from fastapi import APIRouter, Depends, Response

from ..auth.users import User
from ..deps import call_mcp_tool, get_current_user
from ..schemas.companies import CompanyCreate, CompanyUpdate

router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("")
async def list_companies(
    include_stats: bool = False,
    current_user: User = Depends(get_current_user),
):
    """List all companies."""
    return await call_mcp_tool("pm_list_companies", {"include_stats": include_stats})


@router.get("/{company_id}")
async def get_company(
    company_id: str,
    current_user: User = Depends(get_current_user),
):
    """Get a company by ID."""
    return await call_mcp_tool("pm_get_company", {"company_id": company_id})


@router.post("", status_code=201)
async def create_company(
    data: CompanyCreate,
    current_user: User = Depends(get_current_user),
):
    """Create a new company."""
    return await call_mcp_tool("pm_create_company", data.model_dump(exclude_none=True))


@router.patch("/{company_id}")
async def update_company(
    company_id: str,
    data: CompanyUpdate,
    current_user: User = Depends(get_current_user),
):
    """Update a company."""
    args = {"company_id": company_id, **data.model_dump(exclude_unset=True)}
    return await call_mcp_tool("pm_update_company", args)


@router.delete("/{company_id}", status_code=204)
async def delete_company(
    company_id: str,
    current_user: User = Depends(get_current_user),
):
    """Delete a company."""
    await call_mcp_tool("pm_delete_company", {"company_id": company_id})
    return Response(status_code=204)


@router.get("/{company_id}/stats")
async def get_company_stats(
    company_id: str,
    current_user: User = Depends(get_current_user),
):
    """Get aggregated stats for a company."""
    return await call_mcp_tool("pm_get_company_stats", {"company_id": company_id})
