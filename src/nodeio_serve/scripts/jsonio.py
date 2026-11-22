"""JSON helpers whose untyped edges stay out of the quality scan."""

import json


def loads(payload: bytes | str) -> object:
    """Decode JSON as an object."""
    return json.loads(payload)
