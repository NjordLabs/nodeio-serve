"""Ingress behaviour."""

from __future__ import annotations

import asyncio
import json
import runpy

import httpx
import pytest

from nodeio_serve import GraphServicer, create_app
from nodeio_serve.grpc import RequestTooLarge


async def _echo(payload: dict[str, object]) -> dict[str, object]:
    """Run this step."""
    return {"echo": payload["n"]}


def test_health_and_run() -> None:
    """Run this step."""
    app = create_app(_echo)

    async def call() -> None:
        """Run this step."""
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            health = await client.get("/health")
            ran = await client.post("/v1/run", json={"n": 1})
        assert health.json() == {"status": "ok"}
        assert ran.json() == {"echo": 1}

    asyncio.run(call())


def test_rejects_a_large_body_and_a_list() -> None:
    """Run this step."""
    app = create_app(_echo, max_bytes=8)

    async def call() -> None:
        """Run this step."""
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            large = await client.post("/v1/run", content=b"0123456789")
            listed = await client.post("/v1/run", json=[1])
        assert large.status_code == 413
        assert listed.status_code == 422

    asyncio.run(call())
    with pytest.raises(ValueError):
        create_app(_echo, limit=0)


def test_limit_holds_the_second_call() -> None:
    """Run this step."""
    started = asyncio.Event()
    release = asyncio.Event()

    async def handler(payload: dict[str, object]) -> dict[str, object]:
        """Run this step."""
        del payload
        started.set()
        await release.wait()
        return {"ok": True}

    app = create_app(handler, limit=1)

    async def call() -> None:
        """Run this step."""
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            first = asyncio.create_task(client.post("/v1/run", json={"n": 1}))
            await started.wait()
            second = asyncio.create_task(client.post("/v1/run", json={"n": 2}))
            await asyncio.sleep(0.05)
            assert not second.done()
            release.set()
            assert (await first).status_code == 200
            assert (await second).status_code == 200

    asyncio.run(call())


def test_grpc_run_caps_the_payload() -> None:
    """Run this step."""
    servicer = GraphServicer(_echo, max_bytes=8)

    async def call() -> None:
        """Run this step."""
        result = await servicer.run(json.dumps({"n": 2}).encode())
        assert json.loads(result) == {"echo": 2}
        with pytest.raises(RequestTooLarge):
            await servicer.run(b"0123456789")
        with pytest.raises(ValueError):
            await servicer.run(b"[1]")

    asyncio.run(call())
    with pytest.raises(ValueError):
        GraphServicer(_echo, max_bytes=0)


def test_echo_returns_its_argument() -> None:
    """The process entrypoint handler returns the object it was given."""
    from nodeio_serve.__main__ import echo

    assert asyncio.run(echo({"n": 1})) == {"n": 1}


def test_module_entrypoint(monkeypatch: pytest.MonkeyPatch) -> None:
    """Run this step."""
    monkeypatch.setattr("uvicorn.run", lambda *args, **kwargs: None)
    runpy.run_module("nodeio_serve", run_name="__main__")
