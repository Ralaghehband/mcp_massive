"""Launch the Massive MCP uvicorn server and an ngrok tunnel together.

This helper assumes you are already running inside the desired virtual
environment (so `sys.executable` points at the right Python) and that
ngrok is installed and available on PATH.

Example:
    python scripts/launch_server_with_ngrok.py \
        --port 8010 \
        --ngrok-domain vacationless-unpersonally-glennie.ngrok-free.dev
"""
from __future__ import annotations

import argparse
import os
import shutil
import signal
import subprocess
import sys
from typing import List, Optional
from pathlib import Path

import psutil


def _load_env_file(filename: str = ".env") -> None:
    env_path = Path(__file__).resolve().parent.parent / filename
    if not env_path.exists():
        return

    for raw_line in env_path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


_load_env_file()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--transport",
        choices=("sse", "streamable-http"),
        default="sse",
        help="MCP transport to expose via uvicorn (default: sse)",
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host interface for uvicorn to bind (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8010,
        help="Port for uvicorn (and local ngrok target) to use (default: 8010)",
    )
    parser.add_argument(
        "--ngrok-domain",
        default=None,
        help="Optional reserved ngrok domain to bind (e.g. example.ngrok-free.app).",
    )
    parser.add_argument(
        "--ngrok-extra-args",
        nargs=argparse.REMAINDER,
        default=[],
        help="Additional arguments to pass to the ngrok command.",
    )
    return parser.parse_args()


def ensure_prereqs() -> None:
    if not os.environ.get("MASSIVE_API_KEY"):
        raise SystemExit("MASSIVE_API_KEY environment variable is not set.")

    if shutil.which("ngrok") is None:
        raise SystemExit("ngrok executable not found in PATH. Install ngrok first.")


def free_port(port: int) -> None:
    """Terminate any process currently listening on the given port."""
    offenders: List[psutil.Process] = []
    for proc in psutil.process_iter(["pid", "name"]):
        try:
            for conn in proc.connections(kind="inet"):
                if conn.status == psutil.CONN_LISTEN and conn.laddr.port == port:
                    offenders.append(proc)
                    break
        except psutil.Error:
            continue

    for proc in offenders:
        try:
            print(f"Stopping process {proc.pid} ({proc.name()}) on port {port}...")
            proc.terminate()
        except psutil.Error:
            continue

    for proc in offenders:
        try:
            proc.wait(timeout=5)
        except (psutil.TimeoutExpired, psutil.Error):
            try:
                proc.kill()
            except psutil.Error:
                pass


def build_uvicorn_cmd(host: str, port: int, transport: str) -> List[str]:
    return [
        sys.executable,
        "scripts/run_server_uvicorn.py",
        "--host",
        host,
        "--port",
        str(port),
        "--transport",
        transport,
    ]


def build_ngrok_cmd(port: int, domain: Optional[str], extra: List[str]) -> List[str]:
    base = ["ngrok", "http"]
    if domain:
        base.extend(["--domain", domain, f"http://127.0.0.1:{port}"])
    else:
        base.append(str(port))
    return base + list(extra)


def main() -> None:
    args = parse_args()
    ensure_prereqs()
    free_port(args.port)

    uvicorn_cmd = build_uvicorn_cmd(args.host, args.port, args.transport)
    ngrok_cmd = build_ngrok_cmd(args.port, args.ngrok_domain, args.ngrok_extra_args)

    print(f"Starting uvicorn: {' '.join(uvicorn_cmd)}")
    uvicorn_proc = subprocess.Popen(uvicorn_cmd)

    try:
        print(f"Starting ngrok: {' '.join(ngrok_cmd)}")
        ngrok_proc = subprocess.Popen(ngrok_cmd)
    except Exception:
        uvicorn_proc.terminate()
        uvicorn_proc.wait(timeout=10)
        raise

    def shutdown(signum: int, _: Optional[object]) -> None:
        print(f"Received signal {signum}, shutting down processes...")
        for proc in (ngrok_proc, uvicorn_proc):
            if proc.poll() is None:
                proc.terminate()
        for proc in (ngrok_proc, uvicorn_proc):
            try:
                proc.wait(timeout=15)
            except subprocess.TimeoutExpired:
                proc.kill()

    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, shutdown)

    exit_code = uvicorn_proc.wait()
    print(f"uvicorn exited with code {exit_code}, stopping ngrok.")
    if ngrok_proc.poll() is None:
        ngrok_proc.terminate()
        ngrok_proc.wait(timeout=10)

    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
