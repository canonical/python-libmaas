<h1><em>viscera</em> &mdash; High-level Python client API</h1>


## Some example code

```python
#!/usr/bin/env python3.5

from pprint import pprint
from maas.client import viscera

profile, origin = viscera.Origin.login(
    "http://localhost:5240/MAAS/", username="alice",
    password="wonderland")

# List all the tags.
print(">>> origin.Tags.read()")
pprint(origin.Tags.read())

# List all machines.
print(">>> origin.Machines.read()")
pprint(origin.Machines.read())
```
