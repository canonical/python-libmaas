# Events

Events are similar... but different. The only way to get events is by
the ``query`` method:

```pycon
>>> events = origin.Events.query()
```

This accepts a plethora of optional arguments to narrow down the results:

```pycon
>>> events = origin.Events.query(hostnames={"foo", "bar"})
>>> events = origin.Events.query(domains={"example.com", "maas.io"})
>>> events = origin.Events.query(zones=["red", "blue"])
>>> events = origin.Events.query(macs=("12:34:56:78:90:ab", ))
>>> events = origin.Events.query(system_ids=…)
>>> events = origin.Events.query(agent_name=…)
>>> events = origin.Events.query(level=…)
>>> events = origin.Events.query(after=…, limit=…)
```

These arguments can be combined to narrow the results even further.

The ``level`` argument is a little special. It's a choice from a
predefined set. For convenience, those choices are defined in the
``Level`` enum:

```pycon
>>> events = origin.Events.query(level=origin.Events.Level.ERROR)
```

but you can also pass in the string "ERROR" or the number 40.
