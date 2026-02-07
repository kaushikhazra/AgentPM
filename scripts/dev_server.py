"""
Concurrent dev server — starts FastAPI (uvicorn) and Vite in parallel.

Usage:
    python scripts/dev_server.py

Ctrl+C stops both processes.
"""

import atexit
import subprocess
import sys
import signal
import os
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FRONTEND = ROOT / "src" / "taskyn" / "web" / "frontend"


def main():
    procs: list[subprocess.Popen] = []

    def shutdown(*_args):
        for p in procs:
            try:
                p.terminate()
            except OSError:
                pass
        # Give processes time to clean up, then force-kill stragglers
        for p in procs:
            try:
                p.wait(timeout=5)
            except subprocess.TimeoutExpired:
                p.kill()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)
    atexit.register(shutdown)  # Safety net for unexpected exits (CR-17)

    # Start FastAPI backend
    backend = subprocess.Popen(
        [
            sys.executable, "-m", "uvicorn",
            "taskyn.web.backend.main:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload",
        ],
        cwd=str(ROOT),
        env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
    )
    procs.append(backend)
    print("[dev] FastAPI started on http://localhost:8000")

    # Start Vite frontend
    npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
    frontend = subprocess.Popen(
        [npm_cmd, "run", "dev"],
        cwd=str(FRONTEND),
    )
    procs.append(frontend)
    print("[dev] Vite started on http://localhost:3020")

    print("[dev] Press Ctrl+C to stop both servers\n")

    # Wait for either to exit
    try:
        while True:
            for p in procs:
                ret = p.poll()
                if ret is not None:
                    print(f"[dev] Process {p.args} exited with code {ret}")
                    shutdown()
            time.sleep(0.5)
    except KeyboardInterrupt:
        shutdown()


if __name__ == "__main__":
    main()
