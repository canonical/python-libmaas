"""Miscellaneous types."""

__all__ = [
    "JSONArray",
    "JSONObject",
    "JSONValue",
]

from typing import (
    Dict,
    Sequence,
    Union,
)

#
# Types that can be represented in JSON.
#

JSONValue = Union[str, int, float, bool, None, "JSONArray", "JSONObject"]
JSONArray = Sequence[JSONValue]
JSONObject = Dict[str, JSONValue]
