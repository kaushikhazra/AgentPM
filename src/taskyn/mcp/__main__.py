"""Entry point for python -m taskyn.mcp."""

import argparse
import os

from taskyn.mcp.server import mcp


def main():
    parser = argparse.ArgumentParser(description="Taskyn MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "streamable-http"],
        default="stdio",
        help="Transport protocol (default: stdio)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("TASKYN_MCP_PORT", "8000")),
        help="Port for HTTP transport (default: 8000)"
    )
    parser.add_argument(
        "--host",
        default=os.getenv("TASKYN_MCP_HOST", "127.0.0.1"),
        help="Host for HTTP transport (default: 127.0.0.1)"
    )

    args = parser.parse_args()

    if args.transport == "streamable-http":
        mcp.run(transport="streamable-http", host=args.host, port=args.port)
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
