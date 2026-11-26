"""Property checks for the JSON codec.

Hypothesis draws objects and the codec must return the same mapping.
"""

from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st

from nodeio_serve.codec import json_from_object, object_from_json

_value = st.one_of(
    st.none(),
    st.booleans(),
    st.integers(min_value=-1000, max_value=1000),
    st.text(),
)
_objects = st.dictionaries(st.text(min_size=1, max_size=12), _value, max_size=8)


@given(_objects)
def test_json_object_round_trip(payload: dict[str, object]) -> None:
    """A JSON object survives encode and decode."""
    assert object_from_json(json_from_object(payload)) == payload
