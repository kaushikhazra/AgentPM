"""Health check route — connectivity status."""

import logging

from fastapi import APIRouter

from ..deps import get_mcp_client

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    """Check API and MCP server health.

    Returns:
        - status: "healthy" if MCP connected, "degraded" if MCP unreachable
        - mcp: MCP server connectivity status
        - tools_count: Number of available MCP tools (if connected)
    """
    try:
        client = get_mcp_client()
        tools = await client.list_tools()
        return {
            "status": "healthy",
            "mcp": "connected",
            "tools_count": len(tools),
        }
    except Exception as e:
        logger.warning("MCP health check failed: %s", e)
        return {
            "status": "degraded",
            "mcp": "unreachable",
            "error": str(e),
        }
