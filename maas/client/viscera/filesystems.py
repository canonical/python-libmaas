"""Objects for filesystems."""

__all__ = [
    "Filesystem",
]

from . import (
    check,
    Object,
    ObjectField,
)


class Filesystem(Object):
    """A filesystem on either a partition or block device."""

    label = ObjectField.Checked(
        "label", check(str), readonly=True)
    fstype = ObjectField.Checked(
        "fstype", check(str), readonly=True)
    mount_point = ObjectField.Checked(
        "mount_point", check(str), readonly=True)
    mount_options = ObjectField.Checked(
        "mount_options", check(str), readonly=True)
    uuid = ObjectField.Checked(
        "uuid", check(str), readonly=True)

    def __repr__(self):
        return super(Filesystem, self).__repr__(
            fields={"fstype", "mount_point"})
