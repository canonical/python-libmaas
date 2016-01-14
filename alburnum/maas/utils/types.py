"""Miscellaneous types.

Bear in mind that `typecheck` cannot yet check generic types, so using types
like `JSONObject` is currently only partly useful. However, it's still worth
adding such annotations because they also serve a documentary purpose.
"""

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
