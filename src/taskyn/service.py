"""Service management for Taskyn MCP server and Web UI.

Primary: Windows Task Scheduler (zero extra dependencies, any Python).
Fallback: Startup folder shortcut (if Task Scheduler is denied).
"""

from __future__ import annotations

import logging
import os
import subprocess
import sys
from pathlib import Path

LOG_DIR = Path.home() / ".taskyn"
LOG_FILE = LOG_DIR / "service.log"
DATA_DIR = LOG_DIR / "data"
DB_FILE = DATA_DIR / "taskyn.db"

TASK_NAME_MCP = "TaskynMCP"
TASK_NAME_WEB = "TaskynWeb"
STARTUP_BAT_MCP = "TaskynMCP.bat"
STARTUP_BAT_WEB = "TaskynWeb.bat"

MCP_PORT = 8020
WEB_PORT = 3020
MCP_URL = "http://127.0.0.1:8020/mcp"


def _setup_logging() -> logging.Logger:
    """Configure file-based logging for the service."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("taskyn")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.FileHandler(str(LOG_FILE))
        handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
        logger.addHandler(handler)
    return logger


# === Task Scheduler ===

def _install_task() -> bool:
    """Install both services as Windows Scheduled Tasks via PowerShell. Returns True on success."""
    # Use pythonw.exe (windowless) so the tasks run hidden — no console window
    pythonw = Path(sys.executable).parent / "pythonw.exe"
    python_exe = str(pythonw if pythonw.exists() else sys.executable).replace("'", "''")

    # TaskynMCP: MCP server, starts at logon immediately
    ps_mcp = (
        f"$action = New-ScheduledTaskAction -Execute '{python_exe}' "
        f"-Argument '-m taskyn.mcp --transport streamable-http --host 127.0.0.1 --port {MCP_PORT}'; "
        f"$trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME; "
        f"$settings = New-ScheduledTaskSettingsSet -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1) "
        f"-ExecutionTimeLimit 0 -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries; "
        f"Register-ScheduledTask -TaskName '{TASK_NAME_MCP}' -Action $action -Trigger $trigger -Settings $settings -Force"
    )

    # TaskynWeb: Web UI, starts at logon with 15-second delay so MCP is ready first
    ps_web = (
        f"$action = New-ScheduledTaskAction -Execute '{python_exe}' "
        f"-Argument '-m uvicorn taskyn.web.backend.main:app --host 0.0.0.0 --port {WEB_PORT}'; "
        f"$trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME; "
        f"$trigger.Delay = 'PT15S'; "
        f"$settings = New-ScheduledTaskSettingsSet -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1) "
        f"-ExecutionTimeLimit 0 -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries; "
        f"Register-ScheduledTask -TaskName '{TASK_NAME_WEB}' -Action $action -Trigger $trigger -Settings $settings -Force"
    )

    success = True
    for task_name, ps_script in [(TASK_NAME_MCP, ps_mcp), (TASK_NAME_WEB, ps_web)]:
        try:
            result = subprocess.run(
                ["powershell", "-Command", ps_script],
                capture_output=True, text=True, timeout=15,
            )
            if result.returncode == 0:
                print(f"Installed scheduled task '{task_name}'.")
            else:
                print(f"Task Scheduler failed for '{task_name}': {result.stderr.strip()}")
                success = False
        except subprocess.TimeoutExpired:
            print(f"Task Scheduler timed out for '{task_name}'.")
            success = False

    if success:
        print(f"  Both tasks auto-start at logon, restart on failure (3x, 1 min apart).")
        print(f"  MCP server: port {MCP_PORT}  |  Web UI: port {WEB_PORT} (15s delay)")
        print(f"  Logs: {LOG_FILE}")

    return success


def _install_startup_folder() -> bool:
    """Fallback: create .bat files in the user's Startup folder."""
    startup = Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
    if not startup.exists():
        print(f"Startup folder not found: {startup}")
        return False

    pythonw = Path(sys.executable).parent / "pythonw.exe"
    python_exe = str(pythonw if pythonw.exists() else sys.executable)

    bat_mcp = startup / STARTUP_BAT_MCP
    bat_mcp.write_text(
        f'@echo off\n'
        f'set TASKYN_DB={DB_FILE}\n'
        f'set TASKYN_MCP_URL={MCP_URL}\n'
        f'"{python_exe}" -m taskyn.mcp --transport streamable-http --host 127.0.0.1 --port {MCP_PORT}\n'
    )
    print(f"Installed startup script: {bat_mcp}")

    bat_web = startup / STARTUP_BAT_WEB
    bat_web.write_text(
        f'@echo off\n'
        f'set TASKYN_DB={DB_FILE}\n'
        f'set TASKYN_MCP_URL={MCP_URL}\n'
        f'timeout /t 15 /nobreak >nul\n'
        f'"{python_exe}" -m uvicorn taskyn.web.backend.main:app --host 0.0.0.0 --port {WEB_PORT}\n'
    )
    print(f"Installed startup script: {bat_web}")

    print(f"  Both services will start at next login.")
    return True


def _remove_startup_folder() -> bool:
    """Remove Startup folder .bat files if they exist."""
    startup = Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
    removed = False
    for bat_name in (STARTUP_BAT_MCP, STARTUP_BAT_WEB):
        bat = startup / bat_name
        if bat.exists():
            bat.unlink()
            print(f"Removed startup script: {bat}")
            removed = True
    return removed


def _install() -> None:
    """Install: ensure data dir, set env vars, try Task Scheduler, fall back to Startup folder."""
    # Ensure ~/.taskyn/data/ exists
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Data directory: {DATA_DIR}")

    # Set user-level environment variables so both tasks pick them up
    for name, value in [("TASKYN_DB", str(DB_FILE)), ("TASKYN_MCP_URL", MCP_URL)]:
        result = subprocess.run(["setx", name, value], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"Set environment variable: {name}={value}")
        else:
            print(f"Warning: could not set {name}: {result.stderr.strip()}")

    if _install_task():
        return
    print("Falling back to Startup folder...")
    if _install_startup_folder():
        return
    print("ERROR: Could not install service via any method.")
    sys.exit(1)


def _remove() -> None:
    """Remove scheduled tasks and/or startup scripts."""
    removed = False

    for task_name in (TASK_NAME_MCP, TASK_NAME_WEB):
        result = subprocess.run(
            ["powershell", "-Command", f"Unregister-ScheduledTask -TaskName '{task_name}' -Confirm:$false"],
            capture_output=True, text=True,
        )
        if result.returncode == 0:
            print(f"Removed scheduled task '{task_name}'.")
            removed = True

    if _remove_startup_folder():
        removed = True

    if not removed:
        print("Nothing to remove — service was not installed.")


def _start() -> None:
    """Start both scheduled tasks now."""
    any_failed = False
    for task_name in (TASK_NAME_MCP, TASK_NAME_WEB):
        result = subprocess.run(
            ["powershell", "-Command", f"Start-ScheduledTask -TaskName '{task_name}'"],
            capture_output=True, text=True,
        )
        if result.returncode == 0:
            print(f"Started '{task_name}'.")
        else:
            print(f"Failed to start '{task_name}': {result.stderr.strip()}")
            any_failed = True
    if any_failed:
        print("Is the service installed? Run: taskyn-service install")


def _stop() -> None:
    """Stop both scheduled tasks."""
    for task_name in (TASK_NAME_MCP, TASK_NAME_WEB):
        result = subprocess.run(
            ["powershell", "-Command", f"Stop-ScheduledTask -TaskName '{task_name}'"],
            capture_output=True, text=True,
        )
        if result.returncode == 0:
            print(f"Stopped '{task_name}'.")
        else:
            print(f"Failed to stop '{task_name}': {result.stderr.strip()}")


def _check_listening(port: int, path: str = "/") -> bool:
    """Check if the server is actually responding on the port."""
    import urllib.error
    import urllib.request
    try:
        req = urllib.request.Request(f"http://127.0.0.1:{port}{path}", method="GET")
        urllib.request.urlopen(req, timeout=2)
        return True
    except urllib.error.HTTPError:
        return True  # Any HTTP response means the server is up
    except (urllib.error.URLError, ConnectionRefusedError, OSError):
        return False


def _status() -> None:
    """Show current status of both services with operational details."""
    db_path = os.environ.get("TASKYN_DB", str(DB_FILE))
    log_file = LOG_FILE

    # Task state for each scheduled task
    for task_name in (TASK_NAME_MCP, TASK_NAME_WEB):
        result = subprocess.run(
            ["powershell", "-Command", f"Get-ScheduledTask -TaskName '{task_name}' | Format-List TaskName,State"],
            capture_output=True, text=True,
        )
        if result.returncode == 0 and result.stdout.strip():
            for line in result.stdout.strip().splitlines():
                print(line.strip())
        else:
            print(f"Task '{task_name}': not installed")

    # Startup folder fallback presence
    startup = Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
    for bat_name in (STARTUP_BAT_MCP, STARTUP_BAT_WEB):
        bat = startup / bat_name
        if bat.exists():
            print(f"Startup script : {bat}")

    # Server health
    mcp_up = _check_listening(MCP_PORT, "/mcp")
    web_up = _check_listening(WEB_PORT, "/")
    print(f"MCP listening  : {'yes' if mcp_up else 'no'}  (http://127.0.0.1:{MCP_PORT}/mcp)")
    print(f"Web listening  : {'yes' if web_up else 'no'}  (http://127.0.0.1:{WEB_PORT})")
    print(f"Database       : {db_path}")
    db_file = Path(db_path)
    if db_file.exists():
        db_size = db_file.stat().st_size
        if db_size >= 1024 * 1024:
            print(f"DB size        : {db_size / (1024 * 1024):.1f} MB")
        else:
            print(f"DB size        : {db_size / 1024:.1f} KB")
    print(f"Log file       : {log_file}")
    if log_file.exists():
        log_size = log_file.stat().st_size
        print(f"Log size       : {log_size / 1024:.1f} KB")


def _debug() -> None:
    """Run MCP server in foreground for development."""
    print("Running MCP server in debug mode (foreground)...")
    logger = _setup_logging()
    logger.addHandler(logging.StreamHandler())
    from .mcp.server import mcp
    mcp.run(transport="streamable-http", host="127.0.0.1", port=MCP_PORT)


USAGE = """\
Taskyn — service management

Usage:
  taskyn-service install   Install (Task Scheduler + auto-restart)
  taskyn-service remove    Uninstall
  taskyn-service start     Start now
  taskyn-service stop      Stop
  taskyn-service status    Show status
  taskyn-service debug     Run MCP server in foreground (development)
"""


def handle_command_line():
    """CLI entrypoint for service management."""
    if len(sys.argv) < 2:
        print(USAGE)
        sys.exit(0)

    command = sys.argv[1].lower()

    commands = {
        "install": _install,
        "remove": _remove,
        "uninstall": _remove,
        "start": _start,
        "stop": _stop,
        "status": _status,
        "debug": _debug,
    }

    fn = commands.get(command)
    if fn is None:
        print(f"Unknown command: {command}")
        print(USAGE)
        sys.exit(1)

    fn()


if __name__ == "__main__":
    handle_command_line()
