<h1><em>bones</em> &mdash; Low-level Python client API</h1>

You may prefer the [higher-level API _viscera_](../viscera/index.md),
but maybe you need to do something that you can't do in _viscera_ yet
(please file a bug!), or you're developing _viscera_ itself (which uses
_bones_ behind the scenes).


## Some example code

```python
#!/usr/bin/env python3.5

from http import HTTPStatus
from pprint import pprint
from maas.client import bones

# Replace "a:b:c" with an API key obtained from the UI at
# http://$host:$port/MAAS/account/prefs/.
profile, session = bones.SessionAPI.connect(
    "http://localhost:5240/MAAS/", apikey="a:b:c")

# Create a tag if it doesn't exist.
tag_name = "gryphon"
tag_comment = "Gryphon's Stuff"
try:
    tag = session.Tag.read(name=tag_name)
except bones.CallError as error:
    if error.status == HTTPStatus.NOT_FOUND:
        tag = session.Tags.new(
            name=tag_name, comment=tag_comment)
    else:
        raise

# List all the tags.
print(">>> Tags.list()")
pprint(session.Tags.list())

# Get the system IDs for all nodes.
print(">>> Nodes.list()")
all_nodes_system_ids = [
    node["system_id"] for node in session.Nodes.list()
]
pprint(all_nodes_system_ids)

# Associate the tag with all nodes.
print(">>> Tag.update_nodes()")
pprint(session.Tag.update_nodes(
    name=tag["name"], add=all_nodes_system_ids))
```
