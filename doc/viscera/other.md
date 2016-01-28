# Other objects


## Files, users, tags

Similarly to nodes, these sets of objects can be fetched:

```pycon
>>> tags = origin.Tags.read()
>>> files = origin.Files.read()
>>> users = origin.Users.read()
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
