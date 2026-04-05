"""Entry point for python -m taskyn.mcp."""

import os

os.environ["PYTHONIOENCODING"] = "utf-8"

import argparse
import sys
from pathlib import Path

from taskyn.mcp.server import mcp


def main():
    # pythonw.exe (Windows Task Scheduler) has no console — redirect to log file
    if not sys.stdout or not sys.stdout.writable():
        log_dir = Path.home() / ".taskyn"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = str(log_dir / "service.log")
        sys.stdout = open(log_file, "a", encoding="utf-8")
        sys.stderr = sys.stdout

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
        default=int(os.getenv("TASKYN_MCP_PORT", "8020")),
        help="Port for HTTP transport (default: 8020)"
    )
    parser.add_argument(
        "--host",
        default=os.getenv("TASKYN_MCP_HOST", "127.0.0.1"),
        help="Host for HTTP transport (default: 127.0.0.1)"
    )

    args = parser.parse_args()

    if args.transport == "streamable-http":
        import uvicorn
        uvicorn.run(
            mcp.streamable_http_app(),
            host=args.host,
            port=args.port,
            log_level="info",
        )
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
