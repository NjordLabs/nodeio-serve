"""gRPC ingress generated from ``proto/nodeio/v1/graph.proto``.

Importing this module requires the ``grpc`` extra. The HTTP application
does not import it.
"""

from __future__ import annotations

import asyncio
from typing import NoReturn

import grpc
import grpc.aio

from nodeio_serve._gen.nodeio.v1 import graph_pb2, graph_pb2_grpc
from nodeio_serve.app import Handler
from nodeio_serve.bounds import require_caps
from nodeio_serve.codec import json_from_object, object_from_json

_RECEIVE_CAP = "grpc.max_receive_message_length"
_FRAMING_HEADROOM = 128


class GraphServicer(graph_pb2_grpc.GraphServiceServicer):
    """Async ``Run`` implementation.

    The method uses the same body cap as HTTP. Pass the HTTP
    semaphore so both ingresses share one limit.
    """

    def __init__(
        self,
        handler: Handler,
        *,
        max_bytes: int = 1_000_000,
        limit: int = 4,
        semaphore: asyncio.Semaphore | None = None,
    ) -> None:
        """Store the handler and the caps.

        Args:
            handler: Same callable the HTTP route uses.
            max_bytes: Maximum payload size.
            limit: Maximum number of runs at once.
            semaphore: Shared run limit. A new semaphore is created when
                this is omitted.

        Raises:
            ValueError: ``max_bytes`` or ``limit`` is not positive.
        """
        require_caps(max_bytes, limit)
        self._handler = handler
        self._max_bytes = max_bytes
        self._semaphore = asyncio.Semaphore(limit) if semaphore is None else semaphore

    @property
    def max_bytes(self) -> int:
        """Return the payload cap.

        Returns:
            The maximum payload size in bytes.
        """
        return self._max_bytes

    @property
    def semaphore(self) -> asyncio.Semaphore:
        """Return the run limit.

        Returns:
            The semaphore shared with HTTP when both were built together.
        """
        return self._semaphore

    async def Run(  # pylint: disable=invalid-name,invalid-overridden-method
        self,
        request: graph_pb2.RunRequest,
        context: grpc.aio.ServicerContext[graph_pb2.RunRequest, graph_pb2.RunResponse],
    ) -> graph_pb2.RunResponse:
        """Run one request.

        Args:
            request: Generated request. ``payload`` is a JSON object.
            context: gRPC call context.

        Returns:
            The handler result encoded with the shared codec.
        """
        if len(request.payload) > self._max_bytes:
            await _abort(
                context,
                grpc.StatusCode.RESOURCE_EXHAUSTED,
                "request exceeds max_bytes",
            )
        try:
            parsed = object_from_json(request.payload)
        except ValueError:
            await _abort(
                context, grpc.StatusCode.INVALID_ARGUMENT, "body must be an object"
            )
        async with self._semaphore:
            result = await self._handler(parsed)
        try:
            encoded = json_from_object(result)
        except ValueError:
            await _abort(context, grpc.StatusCode.INTERNAL, "result is not JSON")
        return graph_pb2.RunResponse(payload=encoded)  # pylint: disable=no-member


def run_request(payload: bytes) -> graph_pb2.RunRequest:
    """Build a Run request.

    Args:
        payload: JSON bytes.

    Returns:
        The generated request.
    """
    return graph_pb2.RunRequest(payload=payload)  # pylint: disable=no-member


def receive_cap_option(max_bytes: int) -> tuple[str, int]:
    """Return the gRPC option that enforces the payload cap.

    The limit is the payload cap plus a small framing allowance. The
    protobuf message is larger than the JSON bytes it carries.

    Args:
        max_bytes: Maximum payload size.

    Returns:
        The server option pair.
    """
    return (_RECEIVE_CAP, max_bytes + _FRAMING_HEADROOM)


def aio_server(servicer: GraphServicer) -> grpc.aio.Server:
    """Build an aio server whose receive cap is the servicer cap.

    The server is not started and has no port yet.

    Args:
        servicer: Run implementation.

    Returns:
        The server.
    """
    server = grpc.aio.server(options=[receive_cap_option(servicer.max_bytes)])
    graph_pb2_grpc.add_GraphServiceServicer_to_server(servicer, server)
    return server


async def _abort(
    context: grpc.aio.ServicerContext[graph_pb2.RunRequest, graph_pb2.RunResponse],
    code: grpc.StatusCode,
    detail: str,
) -> NoReturn:
    """End the call. This function does not return.

    Args:
        context: gRPC call context.
        code: Status sent to the client.
        detail: Short reason.
    """
    await context.abort(code, detail)
    raise RuntimeError(detail)
