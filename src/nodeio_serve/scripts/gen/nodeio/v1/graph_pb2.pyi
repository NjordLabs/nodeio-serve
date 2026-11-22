"""Types for the generated request and response."""


class RunRequest:
    """JSON payload sent to Run."""

    payload: bytes

    def __init__(self, payload: bytes) -> None:
        """Store ``payload``."""


class RunResponse:
    """JSON payload returned by Run."""

    payload: bytes

    def __init__(self, payload: bytes) -> None:
        """Store ``payload``."""
