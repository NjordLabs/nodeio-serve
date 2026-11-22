"""Ingress behaviour."""

from __future__ import annotations

import asyncio
import runpy

import httpx
import pytest
from fastapi import HTTPException

from nodeio_serve import create_app, create_ingress
from nodeio_serve.__main__ import echo, serve_config
from nodeio_serve.app import _lifespan, _reject_large


async def _echo(payload: dict[str, object]) -> dict[str, object]:
    """Run this step."""
    return {"echo": payload["n"]}


def test_health_and_run() -> None:
    """Run this step."""
    app = create_app(_echo)

    async def call() -> None:
        """Run this step."""
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            health = await client.get("/health")
            ran = await client.post("/v1/run", json={"n": 1})
        assert health.json() == {"status": "ok"}
        assert ran.json() == {"echo": 1}

    asyncio.run(call())


def test_rejects_a_large_body_and_a_list() -> None:
    """Run this step."""
    seen = False

    async def handler(payload: dict[str, object]) -> dict[str, object]:
        """Run this step."""
        nonlocal seen
        seen = True
        return {"echo": payload["n"]}

    app = create_app(handler, max_bytes=8)

    async def call() -> None:
        """Run this step."""
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            large = await client.post("/v1/run", content=b"0123456789")
            listed = await client.post("/v1/run", json=[1])
        assert large.status_code == 413
        assert listed.status_code == 422
        assert seen is False

    asyncio.run(call())
    with pytest.raises(HTTPException) as caught:
        _reject_large(b"0123456789", 8)
    assert caught.value.status_code == 413
    with pytest.raises(ValueError):
        create_app(_echo, limit=0)
    with pytest.raises(ValueError):
        create_app(_echo, max_bytes=0)
    with pytest.raises(ValueError):
        create_ingress(_echo, limit=0)


def test_non_json_result_is_an_error() -> None:
    """A value the codec cannot encode becomes an error response."""

    async def handler(payload: dict[str, object]) -> dict[str, object]:
        """Run this step."""
        del payload
        return {"bad": object()}

    app = create_app(handler)

    async def call() -> None:
        """Run this step."""
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            response = await client.post("/v1/run", json={"n": 1})
        assert response.status_code == 500
        assert response.json()["detail"] == "result is not JSON"
        assert "Traceback" not in response.text

    asyncio.run(call())


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
        async with httpx.AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            first = asyncio.create_task(client.post("/v1/run", json={"n": 1}))
            await started.wait()
            second = asyncio.create_task(client.post("/v1/run", json={"n": 2}))
            await asyncio.sleep(0.05)
            assert not second.done()
            release.set()
            assert (await first).status_code == 200
            assert (await second).status_code == 200

    asyncio.run(call())


def test_echo_returns_its_argument() -> None:
    """The process entrypoint handler returns the object it was given."""
    assert asyncio.run(echo({"n": 1})) == {"n": 1}


def test_lifespan_yields_without_cancelling() -> None:
    """The application lifespan does not cancel the caller."""
    app = create_app(_echo)

    async def call() -> None:
        """Run this step."""
        async with _lifespan(app):
            assert app.state.run_semaphore.locked() is False

    asyncio.run(call())


def test_serve_config_sets_graceful_shutdown() -> None:
    """The process config sets the shutdown timeout without listening."""
    config = serve_config()
    assert config.timeout_graceful_shutdown == 30
    assert config.lifespan == "on"


def test_module_entrypoint(monkeypatch: pytest.MonkeyPatch) -> None:
    """Run this step."""
    monkeypatch.setattr("uvicorn.Server.run", lambda self: None)
    runpy.run_module("nodeio_serve", run_name="__main__")


def test_unknown_export() -> None:
    """The package root only lazy-loads the servicer name."""
    import nodeio_serve

    with pytest.raises(AttributeError):
        getattr(nodeio_serve, "missing")
