"""Types for the generated gRPC client and server."""

import grpc.aio

from nodeio_serve._gen.nodeio.v1.graph_pb2 import RunRequest, RunResponse


class GraphServiceStub:
    """Client for Run."""

    def __init__(self, channel: grpc.aio.Channel) -> None:
        """Bind ``channel``."""

    Run: grpc.aio.UnaryUnaryMultiCallable[RunRequest, RunResponse]


class GraphServiceServicer:
    """Server base class."""

    def __init__(self) -> None:
        """Create a servicer."""


def add_GraphServiceServicer_to_server(
    servicer: GraphServiceServicer,
    server: grpc.aio.Server,
) -> None:
    """Register ``servicer``."""
