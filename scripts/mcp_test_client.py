#!/usr/bin/env python3
"""
Generic MCP Test Client

A command-line tool for testing MCP (Model Context Protocol) servers.
Can be used with any MCP server that supports stdio transport.

Usage:
    # List all tools
    python mcp_test_client.py "python -m agentpm.mcp" --list-tools

    # Call a tool
    python mcp_test_client.py "python -m agentpm.mcp" --call tool_name '{"param": "value"}'

    # Interactive mode
    python mcp_test_client.py "python -m agentpm.mcp" --interactive
"""

import argparse
import json
import subprocess
import sys
from typing import Any


class MCPTestClient:
    """Simple MCP client for testing servers via stdio."""

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

    def _send_request(self, method: str, params: dict | None = None) -> dict:
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

    def initialize(self) -> dict:
        """Initialize the MCP connection."""
        return self._send_request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "mcp-test-client",
                "version": "1.0.0"
            }
        })

    def list_tools(self) -> list[dict]:
        """List available tools."""
        response = self._send_request("tools/list")
        if "result" in response and "tools" in response["result"]:
            return response["result"]["tools"]
        elif "error" in response:
            raise RuntimeError(f"Error: {response['error']}")
        return []

    def call_tool(self, name: str, arguments: dict | None = None) -> Any:
        """Call a tool with the given arguments."""
        response = self._send_request("tools/call", {
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
        response = self._send_request("resources/list")
        if "result" in response and "resources" in response["result"]:
            return response["result"]["resources"]
        elif "error" in response:
            raise RuntimeError(f"Error: {response['error']}")
        return []

    def read_resource(self, uri: str) -> Any:
        """Read a resource by URI."""
        response = self._send_request("resources/read", {"uri": uri})
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
        print(f"  {desc}")

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


def main():
    parser = argparse.ArgumentParser(
        description="MCP Test Client - Test MCP servers via stdio",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List tools from AgentPM MCP server
  python mcp_test_client.py "python -m agentpm.mcp" --list-tools

  # Call a tool
  python mcp_test_client.py "python -m agentpm.mcp" --call list_projects

  # Call with arguments
  python mcp_test_client.py "python -m agentpm.mcp" --call create_company '{"name": "Test"}'

  # Interactive mode
  python mcp_test_client.py "python -m agentpm.mcp" -i

  # With environment variables
  python mcp_test_client.py "python -m agentpm.mcp" --env AGENTPM_DB=test.db --list-tools
        """
    )

    parser.add_argument("command", help="Command to start the MCP server")
    parser.add_argument("--list-tools", "-l", action="store_true", help="List available tools")
    parser.add_argument("--list-resources", "-r", action="store_true", help="List available resources")
    parser.add_argument("--call", "-c", nargs="+", metavar=("TOOL", "ARGS"), help="Call a tool with optional JSON arguments")
    parser.add_argument("--read", metavar="URI", help="Read a resource by URI")
    parser.add_argument("--interactive", "-i", action="store_true", help="Interactive mode")
    parser.add_argument("--env", "-e", action="append", metavar="KEY=VALUE", help="Environment variables")
    parser.add_argument("--raw", action="store_true", help="Output raw JSON")

    args = parser.parse_args()

    # Parse environment variables
    env = {}
    if args.env:
        for item in args.env:
            if "=" in item:
                key, value = item.split("=", 1)
                env[key] = value

    client = MCPTestClient(args.command, env if env else None)

    try:
        print(f"Starting MCP server: {args.command}")
        client.start()

        print("Initializing connection...")
        init_response = client.initialize()

        if args.raw:
            print(json.dumps(init_response, indent=2))
        else:
            server_info = init_response.get("result", {}).get("serverInfo", {})
            print(f"Connected to: {server_info.get('name', 'unknown')} v{server_info.get('version', '?')}")

        if args.list_tools:
            tools = client.list_tools()
            if args.raw:
                print(json.dumps(tools, indent=2))
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
            # Default: list tools
            tools = client.list_tools()
            if args.raw:
                print(json.dumps(tools, indent=2))
            else:
                print_tools(tools)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        client.stop()


if __name__ == "__main__":
    main()
