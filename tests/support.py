"""Shared HTTP client for the in-process application."""

import asyncio
from collections.abc import Awaitable, Callable

import httpx
from fastapi import FastAPI


def holding_handler(
    started: asyncio.Event,
    release: asyncio.Event,
) -> Callable[[dict[str, object]], Awaitable[dict[str, object]]]:
    """Return a handler that waits on ``release`` after setting ``started``."""

    async def handler(payload: dict[str, object]) -> dict[str, object]:
        """Wait until the test releases the shared limit."""
        del payload
        started.set()
        await release.wait()
        return {"ok": True}

    return handler


def asgi_client(app: FastAPI) -> httpx.AsyncClient:
    """Open a client bound to the in-process application."""
    return httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    )
