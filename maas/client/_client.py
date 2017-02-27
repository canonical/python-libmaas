"""Client facade."""

from functools import update_wrapper


class Facade:
    """Present a simplified API for interacting with MAAS.

    The viscera API separates set-based interactions from those on individual
    objects — e.g. Machines and Machine — which mirrors the way MAAS's API is
    actually constructed, helps to avoid namespace clashes, and makes testing
    cleaner.

    However, we want to present a simplified commingled namespace to users of
    MAAS's *client* API. For example, all entry points related to machines
    should be available as ``client.machines``. This facade class allows us to
    present that commingled namespace without coding it as such.
    """

    def __init__(self, client, name, methods):
        super(Facade, self).__init__()
        self._client = client
        self._name = name
        self._populate(methods)

    def _populate(self, methods):
        for name, func in methods.items():
            setattr(self, name, func)

    def __repr__(self):
        return "<%s>" % self._name


class FacadeDescriptor:
    """Lazily create a facade on first use.

    It will be stored in the instance dictionary using the given name. This
    should match the name by which the descriptor is bound into the instance
    class's namespace: as this is a non-data descriptor [1] this will yield
    create-on-first-use behaviour.

    The factory function should accept a single argument, an `Origin`, and
    return a dict mapping method names to methods of objects obtained from the
    origin.

    [1] https://docs.python.org/3.5/howto/descriptor.html#descriptor-protocol
    """

    def __init__(self, name, factory):
        super(FacadeDescriptor, self).__init__()
        self.name, self.factory = name, factory

    def __get__(self, obj, typ=None):
        methods = self.factory(obj._origin)
        facade = Facade(obj, self.name, methods)
        obj.__dict__[self.name] = facade
        return facade


def facade(factory):
    """Declare a method as a facade factory."""
    wrapper = FacadeDescriptor(factory.__name__, factory)
    return update_wrapper(wrapper, factory)


class Client:
    """A simplified API for interacting with MAAS."""

    def __init__(self, origin):
        super(Client, self).__init__()
        self._origin = origin

    @facade
    def account(origin):
        return {
            "create_credentials": origin.Account.create_credentials,
            "delete_credentials": origin.Account.delete_credentials,
        }

    @facade
    def boot_resources(origin):
        return {
            "create": origin.BootResources.create,
            "get": origin.BootResource.read,
            "list": origin.BootResources.read,
            "start_import": origin.BootResources.start_import,
            "stop_import": origin.BootResources.stop_import,
        }

    @facade
    def machines(origin):
        return {
            "allocate": origin.Machines.allocate,
            "get": origin.Machine.read,
            "list": origin.Machines.read,
        }

    @facade
    def devices(origin):
        return {
            "get": origin.Device.read,
            "list": origin.Devices.read,
        }
