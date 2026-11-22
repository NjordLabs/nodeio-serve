"""HTTP and gRPC ingress for a nodeio graph."""

from __future__ import annotations

from nodeio_serve.app import create_app
from nodeio_serve.ingress import create_ingress

__all__ = ["create_app", "create_ingress"]


def __getattr__(name: str) -> object:
    """Load the gRPC servicer on demand.

    Args:
        name: Attribute name.

    Returns:
        The servicer class.

    Raises:
        AttributeError: ``name`` is not a lazy export.
    """
    if name == "GraphServicer":
        from nodeio_serve.grpc import (  # pylint: disable=import-outside-toplevel
            GraphServicer,
        )

        return GraphServicer
    raise AttributeError(name)
