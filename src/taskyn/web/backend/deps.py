"""FastAPI dependencies — MCP integration and auth."""

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError

from taskyn.exceptions import (
    CycleDetectedError,
    NotFoundError,
    TaskynError,
    ValidationError,
)
from taskyn.mcp.server import mcp as mcp_server

from .auth.jwt import decode_token
from .auth.users import User, get_user

security = HTTPBearer()


async def get_mcp():
    """Dependency that provides the MCP server instance."""
    return mcp_server


def call_mcp_tool(tool_name: str, args: dict):
    """Call an MCP tool by name and map errors to HTTP exceptions.

    MCP tools are synchronous functions registered on the server.
    This helper looks them up and calls them directly (in-process).
    """
    # Look up the tool function from the registry
    tool_func = _get_tool_func(tool_name)
    try:
        return tool_func(**args)
    except NotFoundError as e:
        raise HTTPException(404, detail=str(e))
    except CycleDetectedError as e:
        raise HTTPException(409, detail=str(e))
    except ValidationError as e:
        raise HTTPException(422, detail=str(e))
    except TaskynError as e:
        raise HTTPException(422, detail=str(e))
    except ValueError as e:
        msg = str(e).lower()
        if "not found" in msg:
            raise HTTPException(404, detail=str(e))
        if "already exists" in msg or "cycle" in msg:
            raise HTTPException(409, detail=str(e))
        raise HTTPException(422, detail=str(e))
    except Exception:
        raise HTTPException(500, detail="Internal server error")


def _get_tool_func(tool_name: str):
    """Get the underlying Python function for an MCP tool by name.

    FastMCP wraps tool functions in FunctionTool objects.
    We access the original function via the `.fn` attribute.
    """
    import taskyn.mcp.server as server_module
    tool = getattr(server_module, tool_name, None)
    if tool is None:
        raise HTTPException(500, detail=f"Unknown MCP tool: {tool_name}")
    # FastMCP wraps functions in FunctionTool; get the original
    return getattr(tool, "fn", tool)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> User:
    """Dependency that extracts and validates the current user from JWT."""
    token = credentials.credentials
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise HTTPException(401, detail="Invalid token type")

        user_id = payload["sub"]
        user = get_user(user_id)
        if not user:
            raise HTTPException(401, detail="User not found")

        return user
    except JWTError:
        raise HTTPException(401, detail="Invalid or expired token")
