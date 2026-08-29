"""
Convenience script to start both backend and frontend servers.

Usage:
    python run.py          # Start both servers
    python run.py backend  # Start only the backend
    python run.py frontend # Start only the frontend
"""

import subprocess
import sys
import time


def start_backend():
    """Start the FastAPI backend with uvicorn."""
    return subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.main:app", "--reload", "--port", "8000"],
    )


def start_frontend():
    """Start the Streamlit frontend."""
    return subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "frontend/app.py", "--server.port", "8501"],
    )


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else "all"
    processes = []

    try:
        if target in ("all", "backend"):
            print("Starting backend on http://localhost:8000 ...")
            processes.append(start_backend())

        if target in ("all", "frontend"):
            # Give the backend a moment to boot when starting both
            if target == "all":
                time.sleep(2)
            print("Starting frontend on http://localhost:8501 ...")
            processes.append(start_frontend())

        for proc in processes:
            proc.wait()

    except KeyboardInterrupt:
        print("\nShutting down...")
        for proc in processes:
            proc.terminate()


if __name__ == "__main__":
    main()
