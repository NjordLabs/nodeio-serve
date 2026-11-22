"""Process entrypoint. The handler echoes the JSON object."""

from __future__ import annotations

import os

import uvicorn

from nodeio_serve.app import create_app

# Uvicorn waits this long for in-flight handlers, then cancels them.
# The application lifespan does not cancel that work itself.
GRACEFUL_SHUTDOWN_SECONDS = 30


async def echo(payload: dict[str, object]) -> dict[str, object]:
    """Return the request object.

    Args:
        payload: JSON object from the request.

    Returns:
        The same object.
    """
    return payload


def serve_config() -> uvicorn.Config:
    """Build the server config without binding a socket.

    Returns:
        A uvicorn config for the echo application.
    """
    host = os.environ.get("NODEIO_SERVE_HOST", "127.0.0.1")
    return uvicorn.Config(
        create_app(echo),
        host=host,
        port=8080,
        timeout_graceful_shutdown=GRACEFUL_SHUTDOWN_SECONDS,
        lifespan="on",
    )


def main() -> None:
    """Serve the echo handler on port 8080."""
    uvicorn.Server(serve_config()).run()


if __name__ == "__main__":
    main()
