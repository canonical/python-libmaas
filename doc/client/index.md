<h1>The Web API client</h1>

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


### Again, but asynchronous

At first glance _python-libmaas_ appears to be a blocking API, but it's
actually asynchronous under the skin, based on [asyncio][]. If you call
into _python-libmaas_ from within a running event loop it will behave
asynchronously, but called from outside it behaves synchronously, and
blocks.

Using _python-libmaas_ interactively, when exploring the library or
trying something out, is familiar and natural because it behaves as a
synchronous, blocking API. This mode can be used of in scripts too, but
the same code can be easily repurposed for use in an asynchronous,
non-blocking application.

Below shows the earlier example but implemented in an asynchronous
style. Note the use of the ``asynchronous`` decorator: this is used
heavily in _python-libmaas_ — along with the ``Asynchronous`` metaclass
— to create the automatic blocking/not-blocking behaviour.

```python
#!/usr/bin/env python3.5

from maas.client import login
from maas.client.utils.async import asynchronous

@asynchronous
async def work_with_maas():
    client = await login(
        "http://eucula.local:5240/MAAS/",
        username="gavin", password="f00b4r")

    # Get a reference to self.
    myself = await client.users.whoami()
    assert myself.is_admin, "%s is not an admin" % myself.username

    # Check for a MAAS server capability.
    version = await client.version.get()
    assert "devices-management" in version.capabilities

    # Check the default OS and distro series for deployments.
    print(await client.maas.get_default_os())
    print(await client.maas.get_default_distro_series())

    # Set the HTTP proxy.
    await client.maas.set_http_proxy("http://localhost:3128")

    # Allocate and deploy a machine.
    machine = await client.machines.allocate()
    await machine.deploy()

work_with_maas()
```


[asyncio]: https://docs.python.org/3/library/asyncio.html
