#!/usr/bin/env python3
"""
Generic MCP Test Client

A command-line tool for testing MCP (Model Context Protocol) servers.
Supports both stdio and streamable-http transports.

Usage:
    # Stdio transport - List all tools
    python mcp_test_client.py stdio "python -m agentpm.mcp" --list-tools

    # HTTP transport - List all tools
    python mcp_test_client.py http "http://localhost:8000" --list-tools

    # Call a tool
    python mcp_test_client.py stdio "python -m agentpm.mcp" --call tool_name '{"param": "value"}'

    # Interactive mode
    python mcp_test_client.py http "http://localhost:8000" --interactive
"""

import argparse
import json
import subprocess
import sys
from abc import ABC, abstractmethod
from typing import Any


class MCPTransport(ABC):
    """Abstract base class for MCP transports."""

    @abstractmethod
    def start(self) -> None:
        """Start/connect to the transport."""
        pass

    @abstractmethod
    def stop(self) -> None:
        """Stop/disconnect the transport."""
        pass

    @abstractmethod
    def send_request(self, method: str, params: dict | None = None) -> dict:
        """Send a JSON-RPC request and get response."""
        pass


class StdioTransport(MCPTransport):
    """MCP transport over stdio (subprocess)."""

    def __init__(self, command: str, env: dict[str, str] | None = None):
        self.command = command
        self.env = env
        self.process: subprocess.Popen | None = None
        self.request_id = 0

    def start(self) -> None:
        """Start the MCP server process."""
        import os
        import shlex

        # Merge with current environment
        full_env = os.environ.copy()
        if self.env:
            full_env.update(self.env)

        # Parse command (handle Windows vs Unix)
        if sys.platform == "win32":
            args = self.command
            shell = True
        else:
            args = shlex.split(self.command)
            shell = False

        self.process = subprocess.Popen(
            args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=full_env,
            shell=shell,
            text=True,
            bufsize=1,
        )

    def stop(self) -> None:
        """Stop the MCP server process."""
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            self.process = None

    def send_request(self, method: str, params: dict | None = None) -> dict:
        """Send a JSON-RPC request and get response."""
        if not self.process:
            raise RuntimeError("MCP server not started")

        self.request_id += 1
        request = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": method,
        }
        if params:
            request["params"] = params

        request_line = json.dumps(request) + "\n"

        try:
            self.process.stdin.write(request_line)
            self.process.stdin.flush()

            response_line = self.process.stdout.readline()
            if not response_line:
                stderr = self.process.stderr.read()
                raise RuntimeError(f"No response from server. Stderr: {stderr}")

            return json.loads(response_line)
        except Exception as e:
            stderr = ""
            if self.process and self.process.stderr:
                try:
                    stderr = self.process.stderr.read()
                except:
                    pass
            raise RuntimeError(f"Communication error: {e}. Stderr: {stderr}")


class HttpTransport(MCPTransport):
    """MCP transport over streamable HTTP."""

    def __init__(self, base_url: str, headers: dict[str, str] | None = None):
        self.base_url = base_url.rstrip("/")
        self.headers = headers or {}
        self.request_id = 0
        self.session_id: str | None = None
        self._session = None
        self._use_httpx = True

    def start(self) -> None:
        """Initialize HTTP session."""
        try:
            import httpx
            self._session = httpx.Client(timeout=30.0)
            self._use_httpx = True
        except ImportError:
            # Fallback to requests if httpx not available
            try:
                import requests
                self._session = requests.Session()
                self._use_httpx = False
            except ImportError:
                raise RuntimeError("Either 'httpx' or 'requests' package is required for HTTP transport. Install with: pip install httpx")

    def stop(self) -> None:
        """Close HTTP session."""
        if self._session:
            self._session.close()
            self._session = None

    def send_request(self, method: str, params: dict | None = None) -> dict:
        """Send a JSON-RPC request over HTTP."""
        if not self._session:
            raise RuntimeError("HTTP session not started")

        self.request_id += 1
        request = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": method,
        }
        if params:
            request["params"] = params

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            **self.headers,
        }

        # Add session ID if we have one
        if self.session_id:
            headers["Mcp-Session-Id"] = self.session_id

        try:
            # MCP streamable-http endpoint
            endpoint = f"{self.base_url}/mcp"

            if self._use_httpx:
                response = self._session.post(endpoint, json=request, headers=headers)
                response.raise_for_status()
                response_headers = response.headers
                response_text = response.text
            else:
                response = self._session.post(endpoint, json=request, headers=headers, timeout=30)
                response.raise_for_status()
                response_headers = response.headers
                response_text = response.text

            # Capture session ID from response headers
            if "Mcp-Session-Id" in response_headers:
                self.session_id = response_headers["Mcp-Session-Id"]

            # Handle SSE response
            content_type = response_headers.get("Content-Type", "")
            if "text/event-stream" in content_type:
                return self._parse_sse_response(response_text)

            return json.loads(response_text)

        except Exception as e:
            raise RuntimeError(f"HTTP request failed: {e}")

    def _parse_sse_response(self, text: str) -> dict:
        """Parse Server-Sent Events response to extract JSON-RPC result."""
        result = None
        for line in text.split("\n"):
            line = line.strip()
            if line.startswith("data:"):
                data = line[5:].strip()
                if data:
                    try:
                        parsed = json.loads(data)
                        # Keep the last complete response (with result or error)
                        if "result" in parsed or "error" in parsed:
                            result = parsed
                    except json.JSONDecodeError:
                        continue
        if result:
            return result
        raise RuntimeError(f"No valid JSON-RPC response in SSE stream: {text[:200]}")


class MCPTestClient:
    """MCP client for testing servers via any transport."""

    def __init__(self, transport: MCPTransport):
        self.transport = transport

    def start(self) -> None:
        """Start the transport."""
        self.transport.start()

    def stop(self) -> None:
        """Stop the transport."""
        self.transport.stop()

    def initialize(self) -> dict:
        """Initialize the MCP connection."""
        return self.transport.send_request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "mcp-test-client",
                "version": "1.0.0"
            }
        })

    def list_tools(self) -> list[dict]:
        """List available tools."""
        response = self.transport.send_request("tools/list")
        if "result" in response and "tools" in response["result"]:
            return response["result"]["tools"]
        elif "error" in response:
            raise RuntimeError(f"Error: {response['error']}")
        return []

    def call_tool(self, name: str, arguments: dict | None = None) -> Any:
        """Call a tool with the given arguments."""
        response = self.transport.send_request("tools/call", {
            "name": name,
            "arguments": arguments or {}
        })
        if "result" in response:
            return response["result"]
        elif "error" in response:
            raise RuntimeError(f"Tool error: {response['error']}")
        return response

    def list_resources(self) -> list[dict]:
        """List available resources."""
        response = self.transport.send_request("resources/list")
        if "result" in response and "resources" in response["result"]:
            return response["result"]["resources"]
        elif "error" in response:
            raise RuntimeError(f"Error: {response['error']}")
        return []

    def read_resource(self, uri: str) -> Any:
        """Read a resource by URI."""
        response = self.transport.send_request("resources/read", {"uri": uri})
        if "result" in response:
            return response["result"]
        elif "error" in response:
            raise RuntimeError(f"Resource error: {response['error']}")
        return response


def print_tools(tools: list[dict]) -> None:
    """Pretty print tools list."""
    print(f"\n{'='*60}")
    print(f"Available Tools ({len(tools)})")
    print('='*60)

    for tool in tools:
        name = tool.get("name", "unknown")
        desc = tool.get("description", "No description")
        print(f"\n[{name}]")
        # Print first line of description
        first_line = desc.split("\n")[0] if desc else "No description"
        print(f"  {first_line}")

        schema = tool.get("inputSchema", {})
        props = schema.get("properties", {})
        required = schema.get("required", [])

        if props:
            print("  Parameters:")
            for prop_name, prop_info in props.items():
                req_marker = "*" if prop_name in required else " "
                prop_type = prop_info.get("type", "any")
                prop_desc = prop_info.get("description", "")
                print(f"    {req_marker} {prop_name}: {prop_type}")
                if prop_desc:
                    print(f"        {prop_desc}")


def print_tools_compact(tools: list[dict]) -> None:
    """Print tools in compact format (names only)."""
    print(f"\nAvailable Tools ({len(tools)}):")
    for tool in tools:
        name = tool.get("name", "unknown")
        desc = tool.get("description", "No description")
        first_line = desc.split("\n")[0][:60] if desc else "No description"
        print(f"  - {name}: {first_line}")


def print_resources(resources: list[dict]) -> None:
    """Pretty print resources list."""
    print(f"\n{'='*60}")
    print(f"Available Resources ({len(resources)})")
    print('='*60)

    for resource in resources:
        uri = resource.get("uri", "unknown")
        name = resource.get("name", uri)
        desc = resource.get("description", "")
        print(f"\n[{name}]")
        print(f"  URI: {uri}")
        if desc:
            print(f"  {desc}")


def print_result(result: Any) -> None:
    """Pretty print a tool result."""
    print(f"\n{'='*60}")
    print("Result")
    print('='*60)

    if isinstance(result, dict):
        if "content" in result:
            for item in result["content"]:
                if item.get("type") == "text":
                    print(item.get("text", ""))
        else:
            print(json.dumps(result, indent=2))
    else:
        print(json.dumps(result, indent=2))


def interactive_mode(client: MCPTestClient) -> None:
    """Run interactive testing session."""
    print("\nMCP Test Client - Interactive Mode")
    print("Commands: list, resources, call <tool> [json_args], read <uri>, quit")
    print("-" * 40)

    while True:
        try:
            cmd = input("\nmcp> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting...")
            break

        if not cmd:
            continue

        parts = cmd.split(maxsplit=2)
        action = parts[0].lower()

        try:
            if action in ("quit", "exit", "q"):
                break
            elif action == "list":
                tools = client.list_tools()
                print_tools(tools)
            elif action == "resources":
                resources = client.list_resources()
                print_resources(resources)
            elif action == "call" and len(parts) >= 2:
                tool_name = parts[1]
                args = json.loads(parts[2]) if len(parts) > 2 else {}
                result = client.call_tool(tool_name, args)
                print_result(result)
            elif action == "read" and len(parts) >= 2:
                uri = parts[1]
                result = client.read_resource(uri)
                print_result(result)
            else:
                print("Unknown command. Try: list, resources, call <tool> [args], read <uri>, quit")
        except json.JSONDecodeError as e:
            print(f"Invalid JSON: {e}")
        except Exception as e:
            print(f"Error: {e}")


def create_stdio_parser(subparsers):
    """Create the stdio subcommand parser."""
    parser = subparsers.add_parser("stdio", help="Connect via stdio (subprocess)")
    parser.add_argument("command", help="Command to start the MCP server")
    parser.add_argument("--env", "-e", action="append", metavar="KEY=VALUE", help="Environment variables")
    return parser


def create_http_parser(subparsers):
    """Create the http subcommand parser."""
    parser = subparsers.add_parser("http", help="Connect via streamable HTTP")
    parser.add_argument("url", help="Base URL of the MCP server (e.g., http://localhost:8000)")
    parser.add_argument("--header", "-H", action="append", metavar="KEY:VALUE", help="HTTP headers")
    return parser


def add_common_args(parser):
    """Add common arguments to a parser."""
    parser.add_argument("--list-tools", "-l", action="store_true", help="List available tools")
    parser.add_argument("--list-resources", "-r", action="store_true", help="List available resources")
    parser.add_argument("--call", "-c", nargs="+", metavar=("TOOL", "ARGS"), help="Call a tool with optional JSON arguments")
    parser.add_argument("--read", metavar="URI", help="Read a resource by URI")
    parser.add_argument("--interactive", "-i", action="store_true", help="Interactive mode")
    parser.add_argument("--raw", action="store_true", help="Output raw JSON")
    parser.add_argument("--compact", action="store_true", help="Compact output (tool names only)")
    parser.add_argument("--quiet", "-q", action="store_true", help="Minimal output")


def main():
    parser = argparse.ArgumentParser(
        description="MCP Test Client - Test MCP servers via stdio or HTTP",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Stdio transport
  python mcp_test_client.py stdio "python -m agentpm.mcp" --list-tools
  python mcp_test_client.py stdio "python -m agentpm.mcp" --call pm_list_companies
  python mcp_test_client.py stdio "python -m agentpm.mcp" -i

  # HTTP transport (streamable-http)
  python mcp_test_client.py http "http://localhost:8000" --list-tools
  python mcp_test_client.py http "http://localhost:8000" --call pm_get_dashboard
  python mcp_test_client.py http "http://localhost:8000" -H "Authorization:Bearer token" -l

  # With environment variables (stdio only)
  python mcp_test_client.py stdio "python -m agentpm.mcp" --env AGENTPM_DB=test.db -l
        """
    )

    subparsers = parser.add_subparsers(dest="transport", required=True)

    # Create transport-specific parsers
    stdio_parser = create_stdio_parser(subparsers)
    http_parser = create_http_parser(subparsers)

    # Add common args to both
    add_common_args(stdio_parser)
    add_common_args(http_parser)

    args = parser.parse_args()

    # Create appropriate transport
    if args.transport == "stdio":
        env = {}
        if args.env:
            for item in args.env:
                if "=" in item:
                    key, value = item.split("=", 1)
                    env[key] = value
        transport = StdioTransport(args.command, env if env else None)
        connect_info = f"stdio: {args.command}"
    else:  # http
        headers = {}
        if args.header:
            for item in args.header:
                if ":" in item:
                    key, value = item.split(":", 1)
                    headers[key.strip()] = value.strip()
        transport = HttpTransport(args.url, headers if headers else None)
        connect_info = f"http: {args.url}"

    client = MCPTestClient(transport)

    try:
        if not args.quiet:
            print(f"Connecting to MCP server ({connect_info})...")
        client.start()

        if not args.quiet:
            print("Initializing connection...")
        init_response = client.initialize()

        if args.raw:
            print(json.dumps(init_response, indent=2))
        elif not args.quiet:
            server_info = init_response.get("result", {}).get("serverInfo", {})
            print(f"Connected to: {server_info.get('name', 'unknown')} v{server_info.get('version', '?')}")

        if args.list_tools:
            tools = client.list_tools()
            if args.raw:
                print(json.dumps(tools, indent=2))
            elif args.compact:
                print_tools_compact(tools)
            else:
                print_tools(tools)

        elif args.list_resources:
            resources = client.list_resources()
            if args.raw:
                print(json.dumps(resources, indent=2))
            else:
                print_resources(resources)

        elif args.call:
            tool_name = args.call[0]
            tool_args = json.loads(args.call[1]) if len(args.call) > 1 else {}
            result = client.call_tool(tool_name, tool_args)
            if args.raw:
                print(json.dumps(result, indent=2))
            else:
                print_result(result)

        elif args.read:
            result = client.read_resource(args.read)
            if args.raw:
                print(json.dumps(result, indent=2))
            else:
                print_result(result)

        elif args.interactive:
            interactive_mode(client)

        else:
            # Default: list tools in compact mode
            tools = client.list_tools()
            if args.raw:
                print(json.dumps(tools, indent=2))
            else:
                print_tools_compact(tools)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        client.stop()


if __name__ == "__main__":
    main()
