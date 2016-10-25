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

# These are belt-n-braces, but they also seem to help resolve
# forward-references reliably. Without them, things break.
assert issubclass(str, JSONValue)
assert issubclass(int, JSONValue)
assert issubclass(float, JSONValue)
assert issubclass(bool, JSONValue)
assert issubclass(type(None), JSONValue)
assert issubclass(list, JSONValue)
assert issubclass(tuple, JSONValue)
assert issubclass(dict, JSONValue)
