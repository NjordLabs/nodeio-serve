"""Process entrypoint and lifespan."""

from __future__ import annotations

import asyncio
import runpy

import pytest

import nodeio_serve
from nodeio_serve import create_app
from nodeio_serve.__main__ import echo, serve_config
from nodeio_serve.app import _lifespan


async def _echo(payload: dict[str, object]) -> dict[str, object]:
    """Return the payload unchanged."""
    return payload


def test_echo_returns_its_argument() -> None:
    """The process entrypoint handler returns the object it was given."""
    assert asyncio.run(echo({"n": 1})) == {"n": 1}


def test_lifespan_yields_without_cancelling() -> None:
    """The application lifespan does not cancel the caller."""
    app = create_app(_echo)

    async def call() -> None:
        """Enter the lifespan and read the semaphore."""
        async with _lifespan(app):
            assert app.state.run_semaphore.locked() is False

    asyncio.run(call())


def test_serve_config_sets_graceful_shutdown() -> None:
    """The process config sets the shutdown timeout without listening."""
    config = serve_config()
    assert config.timeout_graceful_shutdown == 30
    assert config.lifespan == "on"


def test_module_entrypoint(monkeypatch: pytest.MonkeyPatch) -> None:
    """The module entrypoint reaches uvicorn and returns."""

    def do_not_listen(server: object) -> None:
        """Skip the real server."""
        del server

    monkeypatch.setattr("uvicorn.Server.run", do_not_listen)
    runpy.run_module("nodeio_serve", run_name="__main__")


def test_package_loads_the_servicer() -> None:
    """The package root imports the servicer only when asked."""
    assert nodeio_serve.GraphServicer.__name__ == "GraphServicer"


def test_unknown_export() -> None:
    """The package root only lazy-loads the servicer name."""
    with pytest.raises(AttributeError):
        getattr(nodeio_serve, "missing")
