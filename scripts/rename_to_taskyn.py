#!/usr/bin/env python3
"""Script to rename AgentPM to Taskyn across the codebase."""

import os
import re
from pathlib import Path

def replace_in_file(filepath: Path, replacements: list[tuple[str, str]]) -> bool:
    """Replace patterns in a file. Returns True if changes were made."""
    try:
        content = filepath.read_text(encoding='utf-8')
        original = content

        for old, new in replacements:
            content = content.replace(old, new)

        if content != original:
            filepath.write_text(content, encoding='utf-8')
            print(f"Updated: {filepath}")
            return True
        return False
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return False

def main():
    root = Path("C:/Projects/AgentPM")

    # Define replacements
    replacements = [
        # Import statements
        ("from agentpm.", "from taskyn."),
        ("import agentpm.", "import taskyn."),
        ("import agentpm", "import taskyn"),

        # Module references
        ('"agentpm"', '"taskyn"'),
        ("'agentpm'", "'taskyn'"),

        # Class names
        ("AgentPMError", "TaskynError"),

        # Branding
        ("AgentPM", "Taskyn"),

        # Environment variables
        ("AGENTPM_DB", "TASKYN_DB"),
        ("AGENTPM_ACTOR", "TASKYN_ACTOR"),
        ("AGENTPM_MCP_HOST", "TASKYN_MCP_HOST"),
        ("AGENTPM_MCP_PORT", "TASKYN_MCP_PORT"),

        # Paths
        (".agentpm", ".taskyn"),
        ("agentpm.db", "taskyn.db"),

        # CLI
        ('name="apm"', 'name="taskyn"'),
        ("apm ", "taskyn "),

        # MCP module
        ("agentpm.mcp", "taskyn.mcp"),
        ("agentpm.cli", "taskyn.cli"),
    ]

    # Process Python files in src/taskyn
    src_path = root / "src" / "taskyn"
    for filepath in src_path.rglob("*.py"):
        replace_in_file(filepath, replacements)

    # Process test files
    tests_path = root / "tests"
    for filepath in tests_path.rglob("*.py"):
        replace_in_file(filepath, replacements)

    # Process config files
    config_files = [
        root / "Dockerfile",
        root / "docker-compose.yml",
        root / "docker-compose.https.yml",
        root / "Caddyfile",
        root / "README.md",
        root / "CLAUDE.md",
    ]

    docker_replacements = replacements + [
        ("agentpm:", "taskyn:"),
        ("agentpm:latest", "taskyn:latest"),
        ("container_name: agentpm", "container_name: taskyn"),
        ("service: agentpm", "service: taskyn"),
        ("reverse_proxy agentpm", "reverse_proxy taskyn"),
        ("groupadd --gid 1000 agentpm", "groupadd --gid 1000 taskyn"),
        ("useradd --uid 1000 --gid 1000 --create-home agentpm", "useradd --uid 1000 --gid 1000 --create-home taskyn"),
        ("USER agentpm", "USER taskyn"),
        ("pip install agentpm", "pip install taskyn"),
    ]

    for filepath in config_files:
        if filepath.exists():
            replace_in_file(filepath, docker_replacements)

    # Process scripts
    scripts_path = root / "scripts"
    if scripts_path.exists():
        for filepath in scripts_path.rglob("*.py"):
            if filepath.name != "rename_to_taskyn.py":
                replace_in_file(filepath, replacements)

    print("\nRename complete!")

if __name__ == "__main__":
    main()
