"""Client facade."""

import enum
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
    def boot_sources(origin):
        return {
            "create": origin.BootSources.create,
            "get": origin.BootSource.read,
            "list": origin.BootSources.read,
        }

    @facade
    def devices(origin):
        return {
            "get": origin.Device.read,
            "list": origin.Devices.read,
        }

    @facade
    def events(origin):
        namespace = {
            "query": origin.Events.query,
        }
        namespace.update({
            level.name: level
            for level in origin.Events.Level
        })
        return namespace

    @facade
    def fabrics(origin):
        return {
            "create": origin.Fabrics.create,
            "get": origin.Fabric.read,
            "get_default": origin.Fabric.get_default,
            "list": origin.Fabrics.read,
        }

    @facade
    def static_routes(origin):
        return {
            "create": origin.StaticRoutes.create,
            "get": origin.StaticRoute.read,
            "list": origin.StaticRoutes.read,
        }

    @facade
    def subnets(origin):
        return {
            "create": origin.Subnets.create,
            "get": origin.Subnet.read,
            "list": origin.Subnets.read,
        }

    @facade
    def spaces(origin):
        return {
            "create": origin.Spaces.create,
            "get": origin.Space.read,
            "get_default": origin.Space.get_default,
            "list": origin.Spaces.read,
        }

    @facade
    def files(origin):
        return {
            "list": origin.Files.read,
        }

    @facade
    def ip_ranges(origin):
        return {
            "create": origin.IPRanges.create,
            "get": origin.IPRange.read,
            "list": origin.IPRanges.read,
        }

    @facade
    def maas(origin):
        attrs = (
            (name, getattr(origin.MAAS, name))
            for name in dir(origin.MAAS)
            if not name.startswith("_")
        )
        return {
            name: attr for name, attr in attrs if
            isinstance(attr, enum.EnumMeta) or
            name.startswith(("get_", "set_"))
        }

    @facade
    def machines(origin):
        return {
            "allocate": origin.Machines.allocate,
            "create": origin.Machines.create,
            "get": origin.Machine.read,
            "list": origin.Machines.read,
            "get_power_parameters_for":
                origin.Machines.get_power_parameters_for,
        }

    @facade
    def rack_controllers(origin):
        return {
            "get": origin.RackController.read,
            "list": origin.RackControllers.read,
        }

    @facade
    def region_controllers(origin):
        return {
            "get": origin.RegionController.read,
            "list": origin.RegionControllers.read,
        }

    @facade
    def ssh_keys(origin):
        return {
            "create": origin.SSHKeys.create,
            "get": origin.SSHKey.read,
            "list": origin.SSHKeys.read,
        }

    @facade
    def tags(origin):
        return {
            "create": origin.Tags.create,
            "get": origin.Tag.read,
            "list": origin.Tags.read,
        }

    @facade
    def users(origin):
        return {
            "create": origin.Users.create,
            "list": origin.Users.read,
            "whoami": origin.Users.whoami,
        }

    @facade
    def version(origin):
        return {
            "get": origin.Version.read,
        }

    @facade
    def zones(origin):
        return {
            "create": origin.Zones.create,
            "get": origin.Zone.read,
            "list": origin.Zones.read,
        }
