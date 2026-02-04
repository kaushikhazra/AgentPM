"""
Concurrent dev server — starts FastAPI (uvicorn) and Vite in parallel.

Usage:
    python scripts/dev_server.py

Ctrl+C stops both processes.
"""

import subprocess
import sys
import signal
import os
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
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

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
    print("[dev] Vite started on http://localhost:5173")

    print("[dev] Press Ctrl+C to stop both servers\n")

    # Wait for either to exit
    try:
        while True:
            for p in procs:
                ret = p.poll()
                if ret is not None:
                    print(f"[dev] Process {p.args} exited with code {ret}")
                    shutdown()
            import time
            time.sleep(0.5)
    except KeyboardInterrupt:
        shutdown()


if __name__ == "__main__":
    main()
