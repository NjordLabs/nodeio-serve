"""Process entrypoint. The handler echoes the JSON object."""

from __future__ import annotations

import os

import uvicorn

from nodeio_serve.app import create_app


async def echo(payload: dict[str, object]) -> dict[str, object]:
    """Return the request object.

    Args:
        payload: JSON object from the request.

    Returns:
        The same object.
    """
    return payload


def main() -> None:
    """Serve the echo handler on port 8080."""
    host = os.environ.get("NODEIO_SERVE_HOST", "127.0.0.1")
    uvicorn.run(create_app(echo), host=host, port=8080)


if __name__ == "__main__":
    main()
