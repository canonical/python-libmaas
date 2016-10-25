"""Objects for MAASs."""

__all__ = [
    "MAAS",
]

import enum
import re
from typing import (
    Optional,
    Sequence,
)

from . import (
    Object,
    ObjectType,
)
from ..bones import CallError
from ..utils.typecheck import typed


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

    @typed
    def get_name(cls) -> str:
        """The name of the MAAS instance."""
        return cls.get_config("maas_name")

    @typed
    def set_name(cls, name: str):
        """See `get_name`."""
        return cls.set_config("maas_name", name)

    @typed
    def get_main_archive(cls) -> str:
        """Main archive URL.

        Archive used by nodes to retrieve packages for Intel architectures,
        e.g. http://archive.ubuntu.com/ubuntu.
        """
        return cls.get_config("main_archive")

    @typed
    def set_main_archive(cls, url: str):
        """See `get_main_archive`."""
        cls.set_config("main_archive", url)

    @typed
    def get_ports_archive(cls) -> str:
        """Ports archive.

        Archive used by nodes to retrieve packages for non-Intel
        architectures. E.g. http://ports.ubuntu.com/ubuntu-ports.
        """
        return cls.get_config("ports_archive")

    @typed
    def set_ports_archive(cls, series: str):
        """See `get_ports_archive`."""
        cls.set_config("ports_archive", series)

    @typed
    def get_default_os(cls) -> str:
        """Default OS used for deployment."""
        return cls.get_config("default_osystem")

    @typed
    def set_default_os(cls, series: str):
        """See `get_default_os`."""
        cls.set_config("default_osystem", series)

    @typed
    def get_default_distro_series(cls) -> str:
        """Default OS release used for deployment."""
        return cls.get_config("default_distro_series")

    @typed
    def set_default_distro_series(cls, series: str):
        """See `get_default_distro_series`."""
        cls.set_config("default_distro_series", series)

    @typed
    def get_commissioning_distro_series(cls) -> str:
        """Default Ubuntu release used for commissioning."""
        return cls.get_config("commissioning_distro_series")

    @typed
    def set_commissioning_distro_series(cls, series: str):
        """See `get_commissioning_distro_series`."""
        cls.set_config("commissioning_distro_series", series)

    @typed
    def get_http_proxy(cls) -> Optional[str]:
        """Proxy for APT and HTTP/HTTPS.

        This will be passed onto provisioned nodes to use as a proxy for APT
        traffic. MAAS also uses the proxy for downloading boot images. If no
        URL is provided, the built-in MAAS proxy will be used.
        """
        data = cls.get_config("http_proxy")
        return None if data is None or data == "" else data

    @typed
    def set_http_proxy(cls, url: Optional[str]):
        """See `get_http_proxy`."""
        cls.set_config("http_proxy", "" if url is None else url)

    @typed
    def get_enable_http_proxy(cls) -> bool:
        """Enable the use of an APT and HTTP/HTTPS proxy.

        Provision nodes to use the built-in HTTP proxy (or user specified
        proxy) for APT. MAAS also uses the proxy for downloading boot images.
        """
        return cls.get_config("enable_http_proxy")

    @typed
    def set_enable_http_proxy(cls, enabled: bool):
        """See `get_enable_http_proxy`."""
        cls.set_config("enable_http_proxy", "1" if enabled else "0")

    @typed
    def get_curtin_verbose(cls) -> bool:
        """Should `curtin` log with high verbosity?

        Run the fast-path installer with higher verbosity. This provides more
        detail in the installation logs.
        """
        return cls.get_config("curtin_verbose")

    @typed
    def set_curtin_verbose(cls, verbose: bool):
        """See `get_curtin_verbose`."""
        cls.set_config("curtin_verbose", "1" if verbose else "0")

    @typed
    def get_kernel_options(cls) -> Optional[str]:
        """Kernel options.

        Boot parameters to pass to the kernel by default.
        """
        data = cls.get_config("kernel_opts")
        return None if data is None or data == "" else data

    @typed
    def set_kernel_options(cls, options: Optional[str]):
        """See `get_kernel_options`."""
        cls.set_config("kernel_opts", "" if options is None else options)

    @typed
    def get_upstream_dns(cls) -> list:
        """Upstream DNS server addresses.

        Upstream DNS servers used to resolve domains not managed by this MAAS
        (space-separated IP addresses). Only used when MAAS is running its own
        DNS server. This value is used as the value of 'forwarders' in the DNS
        server config.
        """
        data = cls.get_config("upstream_dns")
        return [] if data is None else re.split("[,\s]+", data)

    @typed
    def set_upstream_dns(cls, addresses: Optional[Sequence[str]]):
        """See `get_upstream_dns`."""
        cls.set_config("upstream_dns", (
            "" if addresses is None else",".join(addresses)))

    class DNSSEC(DescriptiveEnum):
        """DNSSEC validation settings.

        See `get_dnssec_validation` and `set_dnssec_validation`.
        """

        AUTO = "auto", "Automatic (use default root key)"
        YES = "yes", "Yes (manually configured root key)"
        NO = "no", "No (disable DNSSEC)"

    @typed
    def get_dnssec_validation(cls) -> DNSSEC:
        """Enable DNSSEC validation of upstream zones.

        Only used when MAAS is running its own DNS server. This value is used
        as the value of 'dnssec_validation' in the DNS server config.
        """
        data = cls.get_config("dnssec_validation")
        return cls.DNSSEC.lookup(data)

    @typed
    def set_dnssec_validation(cls, validation: DNSSEC):
        """See `get_dnssec_validation`."""
        cls.set_config("dnssec_validation", validation.parameter)

    @typed
    def get_default_dns_ttl(cls) -> int:
        """Default Time-To-Live for DNS records.

        If no TTL value is specified at a more specific point this is how long
        DNS responses are valid, in seconds.
        """
        return int(cls.get_config("default_dns_ttl"))

    @typed
    def set_default_dns_ttl(cls, ttl: int):
        """See `get_default_dns_ttl`."""
        cls.set_config("default_dns_ttl", str(ttl))

    @typed
    def get_enable_disk_erasing_on_release(cls) -> bool:
        """Should nodes' disks be erased prior to releasing."""
        return cls.get_config("enable_disk_erasing_on_release")

    @typed
    def set_enable_disk_erasing_on_release(cls, erase: bool):
        """Should nodes' disks be erased prior to releasing."""
        cls.set_config("enable_disk_erasing_on_release", "1" if erase else "0")

    @typed
    def get_windows_kms_host(cls) -> Optional[str]:
        """Windows KMS activation host.

        FQDN or IP address of the host that provides the KMS Windows
        activation service. (Only needed for Windows deployments using KMS
        activation.)
        """
        data = cls.get_config("windows_kms_host")
        return None if data is None or data == "" else data

    @typed
    def set_windows_kms_host(cls, host: Optional[str]):
        """See `get_windows_kms_host`."""
        cls.set_config("windows_kms_host", "" if host is None else host)

    @typed
    def get_boot_images_auto_import(cls) -> bool:
        """Automatically import/refresh the boot images every 60 minutes."""
        return cls.get_config("boot_images_auto_import")

    @typed
    def set_boot_images_auto_import(cls, auto: bool):
        """See `get_boot_images_auto_import`."""
        cls.set_config("boot_images_auto_import", "1" if auto else "0")

    @typed
    def get_ntp_server(cls) -> str:
        """Address of NTP server.

        NTP server address passed to nodes via a DHCP response. e.g.
        ntp.ubuntu.com.
        """
        return cls.get_config("ntp_server")

    @typed
    def set_ntp_server(cls, server: str):
        """See `get_ntp_server`."""
        cls.set_config("ntp_server", server)

    class StorageLayout(DescriptiveEnum):

        FLAT = "flat", "Flat layout"
        LVM = "lvm", "LVM layout"
        BCACHE = "bcache", "Bcache layout"

    @typed
    def get_default_storage_layout(cls) -> StorageLayout:
        """Default storage layout.

        Storage layout that is applied to a node when it is deployed.
        """
        data = cls.get_config("default_storage_layout")
        return cls.StorageLayout.lookup(data)

    @typed
    def set_default_storage_layout(cls, series: StorageLayout):
        """See `get_default_storage_layout`."""
        cls.set_config("default_storage_layout", series.parameter)

    @typed
    def get_default_min_hwe_kernel(cls) -> Optional[str]:
        """Default minimum kernel version.

        The minimum kernel version used on new and commissioned nodes.
        """
        data = cls.get_config("default_min_hwe_kernel")
        return None if data is None or data == "" else data

    @typed
    def set_default_min_hwe_kernel(cls, version: Optional[str]):
        """See `get_default_min_hwe_kernel`."""
        cls.set_config(
            "default_min_hwe_kernel", "" if version is None else version)

    @typed
    def get_enable_third_party_drivers(cls) -> bool:
        """Enable the installation of proprietary drivers, e.g. HPVSA."""
        return cls.get_config("enable_third_party_drivers")

    @typed
    def set_enable_third_party_drivers(cls, enabled: bool):
        """See `get_enable_third_party_drivers`."""
        cls.set_config("enable_third_party_drivers", "1" if enabled else "0")

    def get_config(cls, name: str):
        """Get a configuration value from MAAS.

        Consult your MAAS server for recognised settings. Alternatively, use
        the pre-canned functions also defined on this object.
        """
        return cls._handler.get_config(name=[name])

    def set_config(cls, name: str, value):
        """Set a configuration value in MAAS.

        Consult your MAAS server for recognised settings. Alternatively, use
        the pre-canned functions also defined on this object.
        """
        return cls._handler.set_config(name=[name], value=[value])

    def _roundtrip(cls):
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
            value = getter()
            print(" ->", repr(value))
            print("   ", type(value))
            setter = setters[name]
            try:
                setter(value)
            except CallError as error:
                print(error)
                print(error.content.decode("utf-8", "replace"))
            else:
                value2 = getter()
                if value2 != value:
                    print(
                        "!!! Round-trip failed:", repr(value),
                        "-->", repr(value2))

        getters_without_setters = set(getters).difference(setters)
        if getters_without_setters:
            print(
                "!!! Getters without setters:",
                " ".join(getters_without_setters))

        setters_without_getters = set(setters).difference(getters)
        if setters_without_getters:
            print(
                "!!! Setters without getters:",
                " ".join(setters_without_getters))


class MAAS(Object, metaclass=MAASType):
    """The current MAAS."""
