"""Run the MCP server's ASGI app directly with uvicorn.

This uses the FastMCP instance from the package to create a Starlette
application for the requested transport (sse or streamable-http) and
runs uvicorn directly so the process stays attached to the terminal.

Usage:
  # run SSE app
  python scripts/run_server_uvicorn.py --transport sse

  # run Streamable HTTP app
  python scripts/run_server_uvicorn.py --transport streamable-http

Environment:
  MASSIVE_API_KEY must be set in the environment before running.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.datastructures import MutableHeaders

from mcp_massive import server as massive_server


def _load_env_file(filename: str = ".env") -> None:
    """Load KEY=VALUE pairs from a .env file if present."""
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


class SecurityHeadersMiddleware:
    """Lightweight ASGI middleware to set common security headers.

    BaseHTTPMiddleware can interfere with streaming responses (e.g. SSE),
    so implement the ASGI protocol directly.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                headers["X-Content-Type-Options"] = "nosniff"
                headers["X-Frame-Options"] = "DENY"
                headers["Content-Security-Policy"] = "default-src 'self'; connect-src *"
                headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
            await send(message)

        await self.app(scope, receive, send_wrapper)


def create_app(poly_mcp, transport: str = "sse") -> FastAPI:
    """Create the MCP FastAPI app with common middleware."""
    if transport == "sse":
        app = poly_mcp.sse_app()
    else:
        app = poly_mcp.streamable_http_app()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(SecurityHeadersMiddleware)
    return app

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--transport", choices=("sse", "streamable-http"), default="sse")
    parser.add_argument("--host", default=os.environ.get("FASTMCP_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("FASTMCP_PORT", "8000")))
    parser.add_argument("--log-level", choices=("debug", "info", "warning", "error", "critical"), default="info")
    args = parser.parse_args()

    try:
        massive_server.ensure_api_key()
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc

    # Use the poly_mcp instance defined in the package
    poly_mcp = massive_server.poly_mcp

    app = create_app(poly_mcp, args.transport)

    print(f"Starting MCP server ({args.transport}) on http://{args.host}:{args.port}")
    uvicorn.run(app, host=args.host, port=args.port, log_level=args.log_level)


if __name__ == "__main__":
    main()
