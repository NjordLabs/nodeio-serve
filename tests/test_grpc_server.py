"""gRPC Run through an in-process aio server."""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import grpc
import pytest

from nodeio_serve import create_ingress
from nodeio_serve.grpc import GraphServicer, aio_server, run_request
from nodeio_serve.scripts.gen.nodeio.v1 import graph_pb2_grpc
from tests.support import asgi_client, holding_handler


async def _echo(payload: dict[str, object]) -> dict[str, object]:
    """Return the payload under ``echo``."""
    return {"echo": payload["n"]}


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


def test_server_runs_and_rejects() -> None:
    """A real aio server encodes results and maps bad JSON and size."""
    servicer = GraphServicer(_echo, max_bytes=32)

    async def call() -> None:
        """Call the server with a valid body, a list, and an oversized body."""
        async with _stub(servicer) as stub:
            result = await stub.Run(run_request(payload=json.dumps({"n": 2}).encode()))
            assert json.loads(result.payload) == {"echo": 2}
            with pytest.raises(grpc.aio.AioRpcError) as bad:
                await stub.Run(run_request(payload=b"[1]"))
            with pytest.raises(grpc.aio.AioRpcError) as large:
                await stub.Run(run_request(payload=b"0123456789" * 8))
        assert bad.value.code() == grpc.StatusCode.INVALID_ARGUMENT
        assert large.value.code() == grpc.StatusCode.RESOURCE_EXHAUSTED

    asyncio.run(call())


def test_server_hides_a_non_json_result() -> None:
    """A value the codec cannot encode is an internal status."""

    async def handler(payload: dict[str, object]) -> dict[str, object]:
        """Return a value the codec cannot encode."""
        del payload
        return {"bad": object()}

    async def call() -> None:
        """Call the server and read the status."""
        async with _stub(GraphServicer(handler, max_bytes=1000)) as stub:
            with pytest.raises(grpc.aio.AioRpcError) as caught:
                await stub.Run(run_request(payload=b'{"n": 1}'))
        assert caught.value.code() == grpc.StatusCode.INTERNAL
        assert "Traceback" not in (caught.value.details() or "")

    asyncio.run(call())


def test_http_and_grpc_share_one_limit() -> None:
    """The second ingress waits while the first holds the semaphore."""
    started = asyncio.Event()
    release = asyncio.Event()

    app, servicer = create_ingress(
        holding_handler(started, release), limit=1, max_bytes=1000
    )
    assert isinstance(servicer, GraphServicer)
    assert app.state.run_semaphore is servicer.semaphore

    async def call() -> None:
        """Hold the HTTP call, then release both ingresses."""
        async with _stub(servicer) as stub:
            async with asgi_client(app) as client:
                first = asyncio.create_task(client.post("/v1/run", json={"n": 1}))
                await started.wait()

                async def second_call() -> object:
                    """Send the gRPC call that shares the limit."""
                    return await stub.Run(run_request(payload=b'{"n": 2}'))

                second = asyncio.create_task(second_call())
                await asyncio.sleep(0.05)
                assert not second.done()
                release.set()
                assert (await first).status_code == 200
                assert json.loads((await second).payload) == {"ok": True}

    asyncio.run(call())
