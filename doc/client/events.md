<h1>Events</h1>

Events are similar to other client objects... but a little different
too. The only way to get events is by the ``query`` method:

```pycon
>>> events = client.events.query()
```

This accepts a plethora of optional arguments to narrow down the results:

```pycon
>>> events = client.events.query(hostnames={"foo", "bar"})
>>> events = client.events.query(domains={"example.com", "maas.io"})
>>> events = client.events.query(zones=["red", "blue"])
>>> events = client.events.query(macs=("12:34:56:78:90:ab", ))
>>> events = client.events.query(system_ids=…)
>>> events = client.events.query(agent_name=…)
>>> events = client.events.query(level=…)
>>> events = client.events.query(after=…, limit=…)
>>> events = client.events.query(owner=…)
```

These arguments can be combined to narrow the results even further.

The ``level`` argument is a little special. It's a choice from a
predefined set. For convenience, those choices are available in
``client.events``:

```pycon
>>> events = client.events.query(level=client.events.ERROR)
```

but you can also pass in the string "ERROR" or the number 40.
