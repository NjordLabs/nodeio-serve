"""gRPC Run on an in-process aio server."""

from __future__ import annotations

import asyncio

import grpc
import pytest

from nodeio_serve.grpc import GraphServicer, receive_cap_option, run_request


async def _echo(payload: dict[str, object]) -> dict[str, object]:
    """Run this step."""
    return {"echo": payload["n"]}


class _AbortContext:
    """Stand-in that records abort and stops the call."""

    def __init__(self) -> None:
        """Remember the status from abort."""
        self.code: grpc.StatusCode | None = None
        self.details = ""

    async def abort(self, code: grpc.StatusCode, details: str) -> None:
        """Record the status and leave the servicer."""
        self.code = code
        self.details = details
        raise RuntimeError(details)


def test_receive_cap_option_uses_the_cap() -> None:
    """The server option is the configured payload cap."""
    assert receive_cap_option(32) == ("grpc.max_receive_message_length", 32)


def test_run_rejects_an_oversized_payload_in_process() -> None:
    """The servicer maps a payload over the cap before the handler runs."""
    servicer = GraphServicer(_echo, max_bytes=8)
    context = _AbortContext()

    async def call() -> None:
        """Run this step."""
        with pytest.raises(RuntimeError, match="max_bytes"):
            await servicer.Run(run_request(payload=b"0123456789"), context)

    asyncio.run(call())
    assert context.code == grpc.StatusCode.RESOURCE_EXHAUSTED

    class _QuietAbort:
        async def abort(self, code: grpc.StatusCode, details: str) -> None:
            """Do not stop the call."""
            del code, details

    async def fallback() -> None:
        """Run this step."""
        with pytest.raises(RuntimeError, match="max_bytes"):
            await servicer.Run(run_request(payload=b"0123456789"), _QuietAbort())

    asyncio.run(fallback())
    with pytest.raises(ValueError):
        GraphServicer(_echo, max_bytes=0)
