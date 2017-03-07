"""Objects for MAASs."""

__all__ = [
    "MAAS",
]

import enum
import re
import typing

from . import (
    Object,
    ObjectType,
)
from ..bones import CallError


def _django_boolean(boolean):
    """Render a string suitable for use in a Django form.

    Django's `BooleanField` understands "true", "false", "1", "0", "t", and
    "f" as valid form values, but the widget `CheckboxInput` that is used by
    `BooleanField` by default gets a shot at converting the form input first.
    It inexplicably has different rules. See in `value_from_datadict`:

      values = {'true': True, 'false': False}
      if isinstance(value, six.string_types):
          value = values.get(value.lower(), value)
      return bool(value)

    Sigh.
    """
    return "true" if boolean else "false"


class DescriptiveEnum(enum.Enum):
    """An enum where each member is a `(parameter, description)` tuple."""

    @property
    def parameter(self):
        return self.value[0]

    @property
    def description(self):
        return self.value[1]

    @classmethod
    def lookup(cls, parameter):
        for member in cls:
            if member.parameter == parameter:
                return member
        else:
            raise KeyError(
                "%s value %r not recognised."
                % (cls.__name__, parameter))


class MAASType(ObjectType):
    """Metaclass for `MAAS`."""

    async def get_name(cls) -> str:
        """The name of the MAAS instance."""
        return await cls.get_config("maas_name")

    async def set_name(cls, name: str):
        """See `get_name`."""
        return await cls.set_config("maas_name", name)

    async def get_main_archive(cls) -> str:
        """Main archive URL.

        Archive used by nodes to retrieve packages for Intel architectures,
        e.g. http://archive.ubuntu.com/ubuntu.
        """
        return await cls.get_config("main_archive")

    async def set_main_archive(cls, url: str):
        """See `get_main_archive`."""
        await cls.set_config("main_archive", url)

    async def get_ports_archive(cls) -> str:
        """Ports archive.

        Archive used by nodes to retrieve packages for non-Intel
        architectures. E.g. http://ports.ubuntu.com/ubuntu-ports.
        """
        return await cls.get_config("ports_archive")

    async def set_ports_archive(cls, series: str):
        """See `get_ports_archive`."""
        await cls.set_config("ports_archive", series)

    async def get_default_os(cls) -> str:
        """Default OS used for deployment."""
        return await cls.get_config("default_osystem")

    async def set_default_os(cls, series: str):
        """See `get_default_os`."""
        await cls.set_config("default_osystem", series)

    async def get_default_distro_series(cls) -> str:
        """Default OS release used for deployment."""
        return await cls.get_config("default_distro_series")

    async def set_default_distro_series(cls, series: str):
        """See `get_default_distro_series`."""
        await cls.set_config("default_distro_series", series)

    async def get_commissioning_distro_series(cls) -> str:
        """Default Ubuntu release used for commissioning."""
        return await cls.get_config("commissioning_distro_series")

    async def set_commissioning_distro_series(cls, series: str):
        """See `get_commissioning_distro_series`."""
        await cls.set_config("commissioning_distro_series", series)

    async def get_http_proxy(cls) -> typing.Optional[str]:
        """Proxy for APT and HTTP/HTTPS.

        This will be passed onto provisioned nodes to use as a proxy for APT
        traffic. MAAS also uses the proxy for downloading boot images. If no
        URL is provided, the built-in MAAS proxy will be used.
        """
        data = await cls.get_config("http_proxy")
        return None if data is None or data == "" else data

    async def set_http_proxy(cls, url: typing.Optional[str]):
        """See `get_http_proxy`."""
        await cls.set_config("http_proxy", "" if url is None else url)

    async def get_enable_http_proxy(cls) -> bool:
        """Enable the use of an APT and HTTP/HTTPS proxy.

        Provision nodes to use the built-in HTTP proxy (or user specified
        proxy) for APT. MAAS also uses the proxy for downloading boot images.
        """
        return await cls.get_config("enable_http_proxy")

    async def set_enable_http_proxy(cls, enabled: bool):
        """See `get_enable_http_proxy`."""
        await cls.set_config("enable_http_proxy", _django_boolean(enabled))

    async def get_curtin_verbose(cls) -> bool:
        """Should `curtin` log with high verbosity?

        Run the fast-path installer with higher verbosity. This provides more
        detail in the installation logs.
        """
        return await cls.get_config("curtin_verbose")

    async def set_curtin_verbose(cls, verbose: bool):
        """See `get_curtin_verbose`."""
        await cls.set_config("curtin_verbose", _django_boolean(verbose))

    async def get_kernel_options(cls) -> typing.Optional[str]:
        """Kernel options.

        Boot parameters to pass to the kernel by default.
        """
        data = await cls.get_config("kernel_opts")
        return None if data is None or data == "" else data

    async def set_kernel_options(cls, options: typing.Optional[str]):
        """See `get_kernel_options`."""
        await cls.set_config("kernel_opts", "" if options is None else options)

    async def get_upstream_dns(cls) -> list:
        """Upstream DNS server addresses.

        Upstream DNS servers used to resolve domains not managed by this MAAS
        (space-separated IP addresses). Only used when MAAS is running its own
        DNS server. This value is used as the value of 'forwarders' in the DNS
        server config.
        """
        data = await cls.get_config("upstream_dns")
        return [] if data is None else re.split("[,\s]+", data)

    async def set_upstream_dns(
            cls, addresses: typing.Optional[typing.Sequence[str]]):
        """See `get_upstream_dns`."""
        await cls.set_config("upstream_dns", (
            "" if addresses is None else",".join(addresses)))

    class DNSSEC(DescriptiveEnum):
        """DNSSEC validation settings.

        See `get_dnssec_validation` and `set_dnssec_validation`.
        """

        AUTO = "auto", "Automatic (use default root key)"
        YES = "yes", "Yes (manually configured root key)"
        NO = "no", "No (disable DNSSEC)"

    async def get_dnssec_validation(cls) -> DNSSEC:
        """Enable DNSSEC validation of upstream zones.

        Only used when MAAS is running its own DNS server. This value is used
        as the value of 'dnssec_validation' in the DNS server config.
        """
        data = await cls.get_config("dnssec_validation")
        return cls.DNSSEC.lookup(data)

    async def set_dnssec_validation(cls, validation: DNSSEC):
        """See `get_dnssec_validation`."""
        await cls.set_config("dnssec_validation", validation.parameter)

    async def get_default_dns_ttl(cls) -> int:
        """Default Time-To-Live for DNS records.

        If no TTL value is specified at a more specific point this is how long
        DNS responses are valid, in seconds.
        """
        return int(await cls.get_config("default_dns_ttl"))

    async def set_default_dns_ttl(cls, ttl: int):
        """See `get_default_dns_ttl`."""
        await cls.set_config("default_dns_ttl", str(ttl))

    async def get_enable_disk_erasing_on_release(cls) -> bool:
        """Should nodes' disks be erased prior to releasing."""
        return await cls.get_config("enable_disk_erasing_on_release")

    async def set_enable_disk_erasing_on_release(cls, erase: bool):
        """Should nodes' disks be erased prior to releasing."""
        await cls.set_config(
            "enable_disk_erasing_on_release", _django_boolean(erase))

    async def get_windows_kms_host(cls) -> typing.Optional[str]:
        """Windows KMS activation host.

        FQDN or IP address of the host that provides the KMS Windows
        activation service. (Only needed for Windows deployments using KMS
        activation.)
        """
        data = await cls.get_config("windows_kms_host")
        return None if data is None or data == "" else data

    async def set_windows_kms_host(cls, host: typing.Optional[str]):
        """See `get_windows_kms_host`."""
        await cls.set_config("windows_kms_host", "" if host is None else host)

    async def get_boot_images_auto_import(cls) -> bool:
        """Automatically import/refresh the boot images every 60 minutes."""
        return await cls.get_config("boot_images_auto_import")

    async def set_boot_images_auto_import(cls, auto: bool):
        """See `get_boot_images_auto_import`."""
        await cls.set_config("boot_images_auto_import", _django_boolean(auto))

    async def get_ntp_server(cls) -> str:
        """Address of NTP server.

        NTP server address passed to nodes via a DHCP response. e.g.
        ntp.ubuntu.com.
        """
        return await cls.get_config("ntp_server")

    async def set_ntp_server(cls, server: str):
        """See `get_ntp_server`."""
        await cls.set_config("ntp_server", server)

    class StorageLayout(DescriptiveEnum):

        FLAT = "flat", "Flat layout"
        LVM = "lvm", "LVM layout"
        BCACHE = "bcache", "Bcache layout"

    async def get_default_storage_layout(cls) -> StorageLayout:
        """Default storage layout.

        Storage layout that is applied to a node when it is deployed.
        """
        data = await cls.get_config("default_storage_layout")
        return cls.StorageLayout.lookup(data)

    async def set_default_storage_layout(cls, series: StorageLayout):
        """See `get_default_storage_layout`."""
        await cls.set_config("default_storage_layout", series.parameter)

    async def get_default_min_hwe_kernel(cls) -> typing.Optional[str]:
        """Default minimum kernel version.

        The minimum kernel version used on new and commissioned nodes.
        """
        data = await cls.get_config("default_min_hwe_kernel")
        return None if data is None or data == "" else data

    async def set_default_min_hwe_kernel(cls, version: typing.Optional[str]):
        """See `get_default_min_hwe_kernel`."""
        await cls.set_config(
            "default_min_hwe_kernel", "" if version is None else version)

    async def get_enable_third_party_drivers(cls) -> bool:
        """Enable the installation of proprietary drivers, e.g. HPVSA."""
        return await cls.get_config("enable_third_party_drivers")

    async def set_enable_third_party_drivers(cls, enabled: bool):
        """See `get_enable_third_party_drivers`."""
        await cls.set_config(
            "enable_third_party_drivers", _django_boolean(enabled))

    async def get_config(cls, name: str):
        """Get a configuration value from MAAS.

        Consult your MAAS server for recognised settings. Alternatively, use
        the pre-canned functions also defined on this object.
        """
        return await cls._handler.get_config(name=[name])

    async def set_config(cls, name: str, value):
        """Set a configuration value in MAAS.

        Consult your MAAS server for recognised settings. Alternatively, use
        the pre-canned functions also defined on this object.
        """
        return await cls._handler.set_config(name=[name], value=[value])

    async def _roundtrip(cls):
        """Testing helper: gets each value and sets it again."""
        getters = {
            name[4:]: getattr(cls, name) for name in dir(cls)
            if name.startswith("get_") and name != "get_config"
        }
        setters = {
            name[4:]: getattr(cls, name) for name in dir(cls)
            if name.startswith("set_") and name != "set_config"
        }

        for name, getter in getters.items():
            print(">>>", name)
            value = await getter()
            print(" ->", repr(value))
            print("   ", type(value))
            setter = setters[name]
            try:
                await setter(value)
            except CallError as error:
                print(error)
                print(error.content.decode("utf-8", "replace"))
            else:
                value2 = await getter()
                if value2 != value:
                    print(
                        "!!! Round-trip failed:", repr(value),
                        "-->", repr(value2))


class MAAS(Object, metaclass=MAASType):
    """The current MAAS."""
