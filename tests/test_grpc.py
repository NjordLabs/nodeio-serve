"""gRPC Run on an in-process aio server."""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import pytest

pytest.importorskip("grpc")

import grpc  # noqa: E402
import httpx  # noqa: E402

from nodeio_serve import GraphServicer, create_ingress  # noqa: E402
from nodeio_serve.gen.nodeio.v1 import graph_pb2, graph_pb2_grpc  # noqa: E402
from nodeio_serve.grpc import aio_server, receive_cap_option  # noqa: E402


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


@asynccontextmanager
async def _stub(
    servicer: GraphServicer,
) -> AsyncIterator[graph_pb2_grpc.GraphServiceStub]:
    """Yield a client connected to a server on port 0."""
    server = aio_server(servicer)
    port = server.add_insecure_port("127.0.0.1:0")
    await server.start()
    channel = grpc.aio.insecure_channel(f"127.0.0.1:{port}")
    try:
        yield graph_pb2_grpc.GraphServiceStub(channel)
    finally:
        await channel.close()
        await server.stop(0)


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
            await servicer.Run(graph_pb2.RunRequest(payload=b"0123456789"), context)

    asyncio.run(call())
    assert context.code == grpc.StatusCode.RESOURCE_EXHAUSTED

    class _QuietAbort:
        async def abort(self, code: grpc.StatusCode, details: str) -> None:
            """Do not stop the call."""
            del code, details

    async def fallback() -> None:
        """Run this step."""
        with pytest.raises(RuntimeError, match="max_bytes"):
            await servicer.Run(
                graph_pb2.RunRequest(payload=b"0123456789"), _QuietAbort()
            )

    asyncio.run(fallback())
    with pytest.raises(ValueError):
        GraphServicer(_echo, max_bytes=0)


def test_server_runs_and_rejects() -> None:
    """A real aio server encodes results and maps bad JSON and size."""
    servicer = GraphServicer(_echo, max_bytes=32)

    async def call() -> None:
        """Run this step."""
        async with _stub(servicer) as stub:
            result = await stub.Run(
                graph_pb2.RunRequest(payload=json.dumps({"n": 2}).encode())
            )
            assert json.loads(result.payload) == {"echo": 2}
            with pytest.raises(grpc.aio.AioRpcError) as bad:
                await stub.Run(graph_pb2.RunRequest(payload=b"[1]"))
            with pytest.raises(grpc.aio.AioRpcError) as large:
                await stub.Run(graph_pb2.RunRequest(payload=b"0123456789" * 8))
        assert bad.value.code() == grpc.StatusCode.INVALID_ARGUMENT
        assert large.value.code() == grpc.StatusCode.RESOURCE_EXHAUSTED

    asyncio.run(call())


def test_server_hides_a_non_json_result() -> None:
    """A value the codec cannot encode is an internal status."""

    async def handler(payload: dict[str, object]) -> dict[str, object]:
        """Run this step."""
        del payload
        return {"bad": object()}

    async def call() -> None:
        """Run this step."""
        async with _stub(GraphServicer(handler, max_bytes=1000)) as stub:
            with pytest.raises(grpc.aio.AioRpcError) as caught:
                await stub.Run(graph_pb2.RunRequest(payload=b'{"n": 1}'))
        assert caught.value.code() == grpc.StatusCode.INTERNAL
        assert "Traceback" not in (caught.value.details() or "")

    asyncio.run(call())


def test_http_and_grpc_share_one_limit() -> None:
    """The second ingress waits while the first holds the semaphore."""
    started = asyncio.Event()
    release = asyncio.Event()

    async def handler(payload: dict[str, object]) -> dict[str, object]:
        """Run this step."""
        del payload
        started.set()
        await release.wait()
        return {"ok": True}

    app, servicer = create_ingress(handler, limit=1, max_bytes=1000)
    assert isinstance(servicer, GraphServicer)
    assert app.state.run_semaphore is servicer.semaphore

    async def call() -> None:
        """Run this step."""
        async with _stub(servicer) as stub:
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(
                transport=transport, base_url="http://test"
            ) as client:
                first = asyncio.create_task(client.post("/v1/run", json={"n": 1}))
                await started.wait()

                async def second_call() -> graph_pb2.RunResponse:
                    """Run this step."""
                    return await stub.Run(graph_pb2.RunRequest(payload=b'{"n": 2}'))

                second = asyncio.create_task(second_call())
                await asyncio.sleep(0.05)
                assert not second.done()
                release.set()
                assert (await first).status_code == 200
                assert json.loads((await second).payload) == {"ok": True}

    asyncio.run(call())
