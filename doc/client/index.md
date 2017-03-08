# The Web API client

Calling ``maas.client.login`` or ``maas.client.connect`` will return a
``maas.client.facade.Client`` instance. This provides an easy to
understand starting point for working with MAAS's Web API.


## An example

```python
#!/usr/bin/env python3.5

from maas.client import login

client = login(
    "http://localhost:5240/MAAS/",
    username="foo", password="bar",
)

# Get a reference to self.
myself = client.users.whoami()
assert myself.is_admin, "%s is not an admin" % myself.username

# Check for a MAAS server capability.
version = client.version.get()
assert "devices-management" in version.capabilities

# Check the default OS and distro series for deployments.
print(client.maas.get_default_os())
print(client.maas.get_default_distro_series())

# Set the HTTP proxy.
client.maas.set_http_proxy("http://localhost:3128")

# Allocate and deploy a machine.
machine = client.machines.allocate()
machine.deploy()
```
