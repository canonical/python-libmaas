<h1>Other objects</h1>

There are several other object types available via the client API. Use
``dir()`` and tab-completion to dig around interactively, or read the
code; we've tried to keep it readable.


## Files, users, tags

Similarly to nodes, these sets of objects can be fetched:

```pycon
>>> tags = client.tags.list()
>>> files = client.files.list()
>>> users = client.users.list()
```

When reading from collections, as above, the returned object is
list-like:

```pycon
>>> len(tags)
5
>>> tags[3]
<Tag comment="Foo's stuff" definition='' kernel_opts='' name='foo'>
>>> tags[3] in tags
True
>>> not_foo = [tag for tag in tags if tag.name != 'foo']
>>> len(not_foo)
4
```

However, it's read-only:

```pycon
>>> tags[0] = "bob"
…
TypeError: 'Tags' object does not support item assignment
```
