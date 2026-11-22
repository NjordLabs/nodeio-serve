"""Types for the aio server symbols this package calls."""

from collections.abc import Sequence
from typing import Generic, TypeVar

Req = TypeVar("Req")
Resp = TypeVar("Resp")


class Channel:
    """Async client channel."""


class Server:
    """Async server."""

    def add_insecure_port(self, address: str) -> int:
        """Bind an insecure port."""

    async def start(self) -> None:
        """Start the server."""

    async def stop(self, grace: float | None) -> None:
        """Stop the server."""


class ServicerContext(Generic[Req, Resp]):
    """Call context."""

    async def abort(self, code: object, details: str) -> None:
        """Stop the call."""


class UnaryUnaryMultiCallable(Generic[Req, Resp]):
    """Client method."""

    async def __call__(self, request: Req, timeout: float | None = None) -> Resp:
        """Send one request."""


def server(options: Sequence[tuple[str, int]] | None = None) -> Server:
    """Build a server."""
