"""Decode JSON without narrowing the result."""

import json


def loads(payload: bytes | str) -> object:
    """Decode JSON as an object."""
    return json.loads(payload)
