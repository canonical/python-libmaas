## Welcome to MAAS's new command-line tool & Python client libraries. ##

For documentation on the MAAS server components, visit
[maas.ubuntu.com](https://maas.ubuntu.com/docs/).


## Client libraries

There are two client libraries that make use of MAAS's Web API:

* A lower-level library that closely mirrors MAAS's Web API, referred to
  as _bones_. The MAAS server publishes a description of its Web API and
  _bones_ provides a convenient mechanism to interact with it.

* A higher-level library that's designed for developers, referred to as
  _viscera_. MAAS's Web API is sometimes unfriendly or inconsistent, but
  _viscera_ presents a saner API, designed for developers rather than
  machines.

The implementation of [_viscera_](viscera/index.md) makes use of
[_bones_](bones/index.md). _Viscera_ is the API that should be preferred
for application development.

Next: [Get started with _viscera_](viscera/getting-started.md)
