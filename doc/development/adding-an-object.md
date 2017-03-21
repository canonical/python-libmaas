<h1>Adding a new object type</h1>

This will show the process by which we can add support for _Space_
objects, but it should be roughly applicable to other objects.

----


## Skeleton

Start by creating a new file in _viscera_. Following the example of
existing objects, name it `maas/client/viscera/spaces.py` (i.e. plural).

> Why _viscera_? The client we recommend for users is a façade of
> _viscera_, allowing us to present a simplified interface which mingles
> set-like operations with individual ones. This is friendlier to a new
> developer, but _viscera_ itself keeps the two separate for cleanliness
> of implementation.

Create a skeleton for _Space_ and _Spaces_:

```python
"""Objects for spaces."""

__all__ = [
    "Space",
    "Spaces",
]

from . import (
    Object,
    ObjectSet,
    ObjectType,
)


class SpacesType(ObjectType):
    """Metaclass for `Spaces`."""


class Spaces(ObjectSet, metaclass=SpacesType):
    """The set of spaces."""


class SpaceType(ObjectType):
    """Metaclass for `Space`."""


class Space(Object, metaclass=SpaceType):
    """A space."""
```

We create explicit type classes as a place to put class-specific
information and methods. Most interestingly, methods created on the type
classes are _class_ methods on instances of the type. For example:

```pycon
>>> class FooType(type):
...    def hello(cls):
...        return "Hello, %s" % cls

>>> class Foo(metaclass=FooType):
...    def goodbye(self):
...        return "Goodbye, %s" % self

>>> Foo.hello()
"Hello, <class '__main__.Foo'>"

>>> foo = Foo()
>>> foo.goodbye()
'Goodbye, <__main__.Foo object at ...>'
```

The difference between using `@classmethod` and this is that those class
methods are not available on instances:

```pycon

>>> foo.hello()
Traceback (most recent call last):
...
AttributeError: 'Foo' object has no attribute 'hello'
```

This keeps the namespace uncluttered, which is good for interactive,
exploratory development, and it keeps code cleaner too: a class method
**must** be called via the class.


## Getting this into the default `Origin`

In `maas/client/viscera/__init__.py` is the default `Origin` class. This
loads object definitions, like those above, and *binds* them to a
particular server. More about that later, but for now you need to add
`".spaces"` to `Origin.__init__`:

```diff
             ".files",
             ".maas",
             ".machines",
+            ".spaces",
             ".tags",
             ".users",
             ".version",
```


## Basic accessors

Add the following basic accessor method to `SpacesType`:

```python
class SpacesType(ObjectType):

    async def read(cls):
        data = await cls._handler.read()
        return cls(map(cls._object, data))
```

Let's start working against a real MAAS server:

```console
$ bin/maas login my-server http://.../MAAS username p4ssw0rd
$ bin/pip install -IU IPython  # Don't leave home without it.
$ bin/maas shell --viscera
Welcome to the MAAS shell.

Predefined objects:

  client:
    A pre-canned client for 'madagascar'.

  origin:
    A pre-canned `viscera` origin for 'madagascar'.
```
```pycon
>>> origin.Spaces.read()
<Spaces length=2 items=[<Space>, <Space>]>

>>> origin.Spaces._handler
<Handler Spaces http://.../MAAS/api/2.0/spaces/>

>>> origin.Spaces._origin
<maas.client.viscera.Origin at ...>
```

The `_handler` attribute is the _bones_ handler for spaces. We named the
class "Spaces" and `Origin` paired that up with the _bones_ handler of
the same name. This let us call the lower-level `read()` method. Try
calling it now:

```pycon
>>> origin.Spaces._handler.read()
[{'id': 0,
  'name': 'space-0',
  'resource_uri': '/MAAS/api/2.0/spaces/0/',
  'subnets': [],
  'vlans': []},
 {'id': -1,
  'name': 'undefined',
  'resource_uri': '/MAAS/api/2.0/spaces/undefined/',
  'subnets': [{'active_discovery': False,
    'allow_proxy': True,
    'cidr': '192.168.1.0/24',
    'dns_servers': [],
    'gateway_ip': '192.168.1.254',
    'id': 1,
    'managed': True,
    'name': '192.168.1.0/24',
    'rdns_mode': 2,
    'resource_uri': '/MAAS/api/2.0/subnets/1/',
    'space': 'undefined',
    'vlan': {'dhcp_on': True,
     'external_dhcp': None,
     'fabric': 'fabric-0',
     'fabric_id': 0,
     'id': 5001,
     'mtu': 1500,
     'name': 'untagged',
     'primary_rack': '4y3h7n',
     'relay_vlan': None,
     'resource_uri': '/MAAS/api/2.0/vlans/5001/',
     'secondary_rack': 'xfaxgw',
     'space': 'undefined',
     'vid': 0}}],
  'vlans': [{'dhcp_on': True,
    'external_dhcp': None,
    'fabric': 'fabric-0',
    'fabric_id': 0,
    'id': 5001,
    'mtu': 1500,
    'name': 'untagged',
    'primary_rack': '4y3h7n',
    'relay_vlan': None,
    'resource_uri': '/MAAS/api/2.0/vlans/5001/',
    'secondary_rack': 'xfaxgw',
    'space': 'undefined',
    'vid': 0}]}]
```

Lots of information!

> By the way, many or most of the IO methods in _python-libmaas_ can be
> called interactively or in a script and they work the same as any
> other synchronous or blocking call. Internally, however, they're all
> asynchronous. They're wrapped in such a way that, when called from
> outside of an _asyncio_ event-loop, they block, but inside they work
> just the same as any other asynchronous call.

Let's look at those `Space` objects:

```pycon
>>> space, *_ = origin.Spaces.read()

>>> dir(space)
[..., '_data', '_handler', '_origin']

>>> space._data
{'id': 0,
 'name': 'space-0',
 'resource_uri': '/MAAS/api/2.0/spaces/0/',
 'subnets': [],
 'vlans': []}

>>> space._handler
<Handler Space http://madagascar.local:5240/MAAS/api/2.0/spaces/{space_id}/>

>>> space._origin is origin
True
```

The handler has been associated with this object type like it was for
`Spaces`, so now's a good time to add another accessor method:

```python
class SpaceType(ObjectType):

    async def read(cls):
        data = await cls._handler.read()
        return cls(data)
```

Try it out:

```pycon
>>> space = origin.Space.read(0)

>>> space._data
{'id': 0,
 'name': 'space-0',
 'resource_uri': '/MAAS/api/2.0/spaces/0/',
 'subnets': [],
 'vlans': []}
```


## Getting at the data

We don't want to work with that `_data` dictionary, we want attributes:

```python
class Space(Object, metaclass=SpaceType):
    """A space."""

    id = ObjectField.Checked("id", check(int), readonly=True)
    name = ObjectField.Checked("name", check(str), readonly=True)
```

Try it out in the shell:

```pycon
>>> space.id, space, name
(0, 'space-0')
```


## Next steps

That's enough for now, but there's plenty of ground yet to be covered:

* How to work with the information about subnets and VLANs data that was
  returned.

* How to create, modify, and delete objects.

* How to test all of this.
