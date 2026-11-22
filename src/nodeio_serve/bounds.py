"""Shared caps for the HTTP and gRPC ingress."""

from __future__ import annotations


def require_caps(max_bytes: int, limit: int) -> None:
    """Reject a non-positive cap.

    Args:
        max_bytes: Maximum payload size.
        limit: Maximum number of runs at once.

    Raises:
        ValueError: ``max_bytes`` or ``limit`` is not positive.
    """
    if max_bytes < 1 or limit < 1:
        raise ValueError("max_bytes and limit must be positive")
