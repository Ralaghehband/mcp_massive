from __future__ import annotations

import os
from typing import Any, Dict, Optional

import httpx


_BASE_URL = os.environ.get("MASSIVE_BASE_URL", "https://api.massive.com")
_client = httpx.Client(base_url=_BASE_URL, timeout=30)


def massive_get(path: str, params: Optional[Dict[str, Any]] = None) -> httpx.Response:
    from .server import ensure_api_key  # local import to avoid cycle during init

    query = dict(params) if params else {}
    query.setdefault("apiKey", ensure_api_key())
    response = _client.get(path, params=query)
    response.raise_for_status()
    return response
