"""gRPC ingress that shares the HTTP handler.

The generated stub is not required for the size and concurrency checks.
A caller passes the request payload bytes.
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import Awaitable, Callable

Handler = Callable[[dict[str, object]], Awaitable[dict[str, object]]]


class RequestTooLarge(Exception):
    """The payload is larger than the configured cap."""


class GraphServicer:
    """Unary ``Run`` implementation.

    Args are stored on the instance so a test can call :meth:`run`
    without a server.
    """

    def __init__(self, handler: Handler, *, max_bytes: int = 1_000_000, limit: int = 4) -> None:
        """Store the handler and the caps.

        Args:
            handler: Same callable the HTTP route uses.
            max_bytes: Maximum payload size.
            limit: Maximum number of runs at once.

        Raises:
            ValueError: ``max_bytes`` or ``limit`` is not positive.
        """
        if max_bytes < 1 or limit < 1:
            raise ValueError("max_bytes and limit must be positive")
        self._handler = handler
        self._max_bytes = max_bytes
        self._semaphore = asyncio.Semaphore(limit)

    async def run(self, payload: bytes) -> bytes:
        """Run one request.

        Args:
            payload: JSON object encoded as UTF-8.

        Returns:
            The handler result encoded as UTF-8 JSON.

        Raises:
            RequestTooLarge: ``payload`` exceeds the cap.
            ValueError: ``payload`` is not a JSON object.
        """
        if len(payload) > self._max_bytes:
            raise RequestTooLarge("request exceeds max_bytes")
        parsed = json.loads(payload)
        if not isinstance(parsed, dict):
            raise ValueError("body must be an object")
        async with self._semaphore:
            result = await self._handler(parsed)
        return json.dumps(result).encode()
