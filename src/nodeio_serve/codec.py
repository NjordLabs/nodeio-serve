"""JSON conversions kept out of the request handlers."""

from __future__ import annotations

import json


def object_from_json(payload: bytes | str) -> dict[str, object]:
    """Decode a JSON object.

    Args:
        payload: UTF-8 JSON text.

    Returns:
        The object.

    Raises:
        ValueError: ``payload`` is not a JSON object.
    """
    parsed = json.loads(payload)
    if not isinstance(parsed, dict):
        raise ValueError("body must be an object")
    return {str(key): value for key, value in parsed.items()}


def json_from_object(payload: dict[str, object]) -> bytes:
    """Encode an object as UTF-8 JSON.

    Args:
        payload: JSON object.

    Returns:
        The encoded bytes.

    Raises:
        ValueError: ``payload`` is not JSON-serializable.
    """
    try:
        encoded = json.dumps(payload)
    except (TypeError, ValueError) as exc:
        raise ValueError("result is not JSON") from exc
    return encoded.encode()
