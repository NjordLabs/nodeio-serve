"""HTTP ingress.

One process-wide limit bounds concurrent runs. A request larger than
the cap is rejected before the handler runs.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, HTTPException, Request

from nodeio_serve.codec import object_from_json

Handler = Callable[[dict[str, object]], Awaitable[dict[str, object]]]


def create_app(
    handler: Handler,
    *,
    max_bytes: int = 1_000_000,
    limit: int = 4,
) -> FastAPI:
    """Build the HTTP application.

    Args:
        handler: Runs one graph request and returns a JSON object.
        max_bytes: Maximum request body size.
        limit: Maximum number of runs at once.

    Returns:
        The FastAPI application.

    Raises:
        ValueError: ``max_bytes`` or ``limit`` is not positive.
    """
    if max_bytes < 1 or limit < 1:
        raise ValueError("max_bytes and limit must be positive")
    application = FastAPI()
    semaphore = asyncio.Semaphore(limit)

    @application.get("/health")
    async def health() -> dict[str, str]:
        """Report that the process is up.

        Returns:
            A status object.
        """
        return {"status": "ok"}

    @application.post("/v1/run")
    async def run_graph(request: Request) -> dict[str, object]:
        """Run one JSON object through the handler.

        Args:
            request: Incoming HTTP request.

        Returns:
            The handler result.

        Raises:
            HTTPException: The body is too large or is not an object.
        """
        body = await request.body()
        if len(body) > max_bytes:
            raise HTTPException(status_code=413, detail="request exceeds max_bytes")
        payload = _object(body)
        async with semaphore:
            return await handler(payload)

    return application


def _object(body: bytes) -> dict[str, object]:
    try:
        return object_from_json(body)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="body must be an object") from exc
