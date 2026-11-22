"""HTTP ingress.

One process-wide limit bounds concurrent runs. A request larger than
the cap is rejected before the body is buffered, and the buffered
length is checked again.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import Response

from nodeio_serve.bounds import require_caps
from nodeio_serve.codec import json_from_object, object_from_json
from nodeio_serve.scripts.state import remember

Handler = Callable[[dict[str, object]], Awaitable[dict[str, object]]]


@asynccontextmanager
async def _lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Leave in-flight handlers for the server shutdown timeout.

    This lifespan does not cancel work. Uvicorn applies
    ``timeout_graceful_shutdown`` before the lifespan exits, and only
    when that timeout is set.
    """
    yield


def create_app(
    handler: Handler,
    *,
    max_bytes: int = 1_000_000,
    limit: int = 4,
    semaphore: asyncio.Semaphore | None = None,
) -> FastAPI:
    """Build the HTTP application.

    Args:
        handler: Runs one graph request and returns a JSON object.
        max_bytes: Maximum request body size.
        limit: Maximum number of runs at once.
        semaphore: Shared run limit. A new semaphore is created when
            this is omitted.

    Returns:
        The FastAPI application.

    Raises:
        ValueError: ``max_bytes`` or ``limit`` is not positive.
    """
    require_caps(max_bytes, limit)
    gate = asyncio.Semaphore(limit) if semaphore is None else semaphore
    application = FastAPI(max_body_size=max_bytes, lifespan=_lifespan)
    remember(application, gate)

    @application.get("/health")
    async def health() -> Response:
        """Report that the process is up.

        Returns:
            A status object.
        """
        return _json_response({"status": "ok"})

    @application.post("/v1/run")
    async def run_graph(request: Request) -> Response:
        """Run one JSON object through the handler.

        Args:
            request: Incoming HTTP request.

        Returns:
            The handler result encoded with the shared codec.

        Raises:
            HTTPException: The body is too large, is not an object, or
                the handler result is not JSON.
        """
        body = await request.body()
        _reject_large(body, max_bytes)
        payload = _object(body)
        async with gate:
            result = await handler(payload)
        return _json_response(result)

    return application


def _reject_large(body: bytes, max_bytes: int) -> None:
    if len(body) > max_bytes:
        raise HTTPException(status_code=413, detail="request exceeds max_bytes")


def _json_response(payload: dict[str, object]) -> Response:
    try:
        encoded = json_from_object(payload)
    except ValueError as exc:
        raise HTTPException(status_code=500, detail="result is not JSON") from exc
    return Response(content=encoded, media_type="application/json")


def _object(body: bytes) -> dict[str, object]:
    try:
        return object_from_json(body)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="body must be an object") from exc
