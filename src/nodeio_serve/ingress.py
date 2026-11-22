"""Build the HTTP application and the gRPC servicer together."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from fastapi import FastAPI

from nodeio_serve.app import Handler, create_app
from nodeio_serve.bounds import require_caps

if TYPE_CHECKING:
    from nodeio_serve.grpc import GraphServicer


def create_ingress(
    handler: Handler,
    *,
    max_bytes: int = 1_000_000,
    limit: int = 4,
) -> tuple[FastAPI, GraphServicer]:
    """Build both ingresses on one concurrency limit.

    Args:
        handler: Runs one graph request and returns a JSON object.
        max_bytes: Maximum request body size.
        limit: Maximum number of runs at once.

    Returns:
        The HTTP application and the gRPC servicer.

    Raises:
        ValueError: ``max_bytes`` or ``limit`` is not positive.
    """
    require_caps(max_bytes, limit)
    from nodeio_serve.grpc import (  # pylint: disable=import-outside-toplevel
        GraphServicer,
    )

    gate = asyncio.Semaphore(limit)
    application = create_app(handler, max_bytes=max_bytes, limit=limit, semaphore=gate)
    servicer = GraphServicer(handler, max_bytes=max_bytes, limit=limit, semaphore=gate)
    return application, servicer
