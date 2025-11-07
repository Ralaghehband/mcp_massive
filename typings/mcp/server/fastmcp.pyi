from collections.abc import Awaitable, Callable
from typing import Any, Optional, TypeVar

from ..types import ToolAnnotations

_FuncT = TypeVar("_FuncT", bound=Callable[..., Awaitable[Any]])


class FastMCP:
    def __init__(self, name: str) -> None: ...

    def tool(
        self,
        *,
        annotations: Optional[ToolAnnotations] = ...
    ) -> Callable[[_FuncT], _FuncT]: ...

    def sse_app(self) -> Any: ...
    def streamable_http_app(self) -> Any: ...
    def run(self, transport: str) -> None: ...
