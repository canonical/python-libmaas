"""Test for `maas.client.viscera.vlans`."""

import random
from operator import itemgetter

from testtools.matchers import Equals

from ..controllers import RackController
from ..fabrics import Fabric, Fabrics
from ..vlans import Vlan, Vlans

from ..testing import bind
from ...testing import TestCase


def make_origin():
    """
    Create a new origin with Vlans, Vlan, Fabric and RackController. The former
    refers to the latter via the origin, hence why it must be bound.
    """
    return bind(Vlans, Vlan, Fabric, Fabrics, RackController)


class TestVlans(TestCase):
    def test__vlans_create(self):
        Vlans = make_origin().Vlans
        fabric_id = random.randint(1, 100)
        vid = random.randint(1, 100)
        Vlans._handler.create.return_value = {
            "id": 5001,
            "fabric_id": fabric_id,
            "vid": vid,
            "mtu": 1500,
        }
        Vlans.create(fabric_id, vid)
        Vlans._handler.create.assert_called_once_with(
            fabric_id=fabric_id, vid=vid, dhcp_on=False
        )

    def test__vlans_create_with_fabric(self):
        Vlans = make_origin().Vlans
        Fabric = make_origin().Fabric
        fabric_id = random.randint(1, 100)
        fabric = Fabric({"id": fabric_id})
        vid = random.randint(1, 100)
        Vlans._handler.create.return_value = {
            "id": 5001,
            "fabric_id": fabric_id,
            "vid": vid,
            "mtu": 1500,
        }
        Vlans.create(fabric, vid)
        Vlans._handler.create.assert_called_once_with(
            fabric_id=fabric_id, vid=vid, dhcp_on=False
        )

    def test__vlans_read(self):
        Vlans = make_origin().Vlans
        fabric_id = random.randint(1, 100)
        vlans = [
            {"id": random.randint(5001, 6000), "vid": random.randint(1, 4096)}
            for _ in range(3)
        ]
        Vlans._handler.read.return_value = vlans
        vlans = Vlans.read(fabric_id)
        self.assertThat(len(vlans), Equals(3))

    def test__vlans_read_with_fabric(self):
        Vlans = make_origin().Vlans
        Fabric = make_origin().Fabric
        fabric_id = random.randint(1, 100)
        fabric = Fabric({"id": fabric_id})
        vlans = [
            {"id": random.randint(5001, 6000), "vid": random.randint(1, 4096)}
            for _ in range(3)
        ]
        Vlans._handler.read.return_value = vlans
        vlans = Vlans.read(fabric)
        self.assertThat(len(vlans), Equals(3))

    def test__vlans_get_default(self):
        Vlans = make_origin().Vlans
        Fabric = make_origin().Fabric
        fabric_id = random.randint(1, 100)
        fabric = Fabric({"id": fabric_id})
        vlans = [
            {"id": random.randint(5001, 6000), "vid": random.randint(1, 4096)}
            for _ in range(3)
        ]
        default_vlan = sorted(vlans, key=itemgetter("id"))[0]
        Vlans._handler.read.return_value = vlans
        vlans = Vlans.read(fabric)
        observed = vlans.get_default()
        self.assertThat(observed.id, Equals(default_vlan["id"]))


class TestVlan(TestCase):
    def test__vlan_read(self):
        Vlan = make_origin().Vlan
        Vlan._handler.read.return_value = {"id": 5001, "vid": 10}
        fabric_id = random.randint(1, 100)
        Vlan.read(fabric_id, 10)
        Vlan._handler.read.assert_called_once_with(fabric_id=fabric_id, vid=10)

    def test__vlan_delete(self):
        Vlan = make_origin().Vlan
        fabric_id = random.randint(1, 100)
        vlan = Vlan({"id": 5001, "fabric_id": fabric_id, "vid": 10})
        vlan.delete()
        Vlan._handler.delete.assert_called_once_with(fabric_id=fabric_id, vid=10)

    def test__vlan_update_fabric_to_default(self):
        origin = make_origin()
        Fabric, Vlan = origin.Fabric, origin.Vlan
        Vlan._handler.params = ["fabric_id", "vid"]
        fabric_id = random.randint(1, 100)
        vlan_id = random.randint(5001, 6000)
        vid = random.randint(100, 200)
        vlan = Vlan({"id": vlan_id, "fabric_id": fabric_id, "vid": vid})
        default_fabric = Fabric({"id": 0})
        vlan.fabric = default_fabric
        Vlan._handler.update.return_value = {"id": vlan_id, "vid": vid}
        vlan.save()
        Vlan._handler.update.assert_called_once_with(
            fabric_id=fabric_id, vid=vid, _vid=vid, fabric=default_fabric.id
        )
        self.assertThat(vlan.fabric.id, Equals(default_fabric.id))

    def test__vlan_update_fabric(self):
        origin = make_origin()
        Fabric, Vlan = origin.Fabric, origin.Vlan
        Vlan._handler.params = ["fabric_id", "vid"]
        fabric_id = random.randint(1, 100)
        vlan_id = random.randint(5001, 6000)
        vid = random.randint(100, 200)
        vlan = Vlan({"id": vlan_id, "fabric_id": fabric_id, "vid": vid})
        new_fabric = Fabric({"id": random.randint(101, 200)})
        vlan.fabric = new_fabric
        Vlan._handler.update.return_value = {"id": vlan_id, "vid": vid}
        vlan.save()
        Vlan._handler.update.assert_called_once_with(
            fabric_id=fabric_id, vid=vid, _vid=vid, fabric=new_fabric.id
        )
        self.assertThat(vlan.fabric.id, Equals(new_fabric.id))

    def test__vlan_update_vid(self):
        origin = make_origin()
        Vlan = origin.Vlan
        Vlan._handler.params = ["fabric_id", "vid"]
        fabric_id = random.randint(1, 100)
        vlan_id = random.randint(5001, 6000)
        vid = random.randint(100, 200)
        new_vid = random.randint(201, 300)
        vlan = Vlan({"id": vlan_id, "fabric_id": fabric_id, "vid": vid})
        vlan.vid = new_vid
        Vlan._handler.update.return_value = {"id": vlan_id, "vid": new_vid}
        vlan.save()
        Vlan._handler.update.assert_called_once_with(
            fabric_id=fabric_id, vid=vid, _vid=new_vid
        )
        self.assertThat(new_vid, Equals(new_vid))

    def test__vlan_update_vid_twice(self):
        origin = make_origin()
        Vlan = origin.Vlan
        Vlan._handler.params = ["fabric_id", "vid"]
        fabric_id = random.randint(1, 100)
        vlan_id = random.randint(5001, 6000)
        vid = random.randint(100, 200)
        new_vid = random.randint(201, 300)
        vlan = Vlan({"id": vlan_id, "fabric_id": fabric_id, "vid": vid})
        vlan.vid = new_vid
        Vlan._handler.update.return_value = {"id": vlan_id, "vid": new_vid}
        vlan.save()
        Vlan._handler.update.assert_called_once_with(
            fabric_id=fabric_id, vid=vid, _vid=new_vid
        )
        self.assertThat(vlan.vid, Equals(new_vid))

        # Second call should pass the new_vid as the vid, and not the old vid.
        new_vid_2 = random.randint(301, 400)
        vlan.vid = new_vid_2
        Vlan._handler.update.return_value = {"id": vlan_id, "vid": new_vid_2}
        vlan.save()
        Vlan._handler.update.assert_called_with(
            fabric_id=fabric_id, vid=new_vid, _vid=new_vid_2
        )
        self.assertThat(vlan.vid, Equals(new_vid_2))

    def test__vlan_update_relay_vlan_with_object(self):
        origin = make_origin()
        Vlan = origin.Vlan
        Vlan._handler.params = ["fabric_id", "vid"]
        fabric_id = random.randint(1, 100)
        vlan_id = random.randint(5001, 6000)
        vid = random.randint(100, 200)
        vlan = Vlan(
            {
                "id": vlan_id,
                "fabric_id": fabric_id,
                "vid": vid,
                "name": "",
                "relay_vlan": None,
            }
        )
        relay_vlan = Vlan(
            {"id": vlan_id + 1, "fabric_id": fabric_id, "vid": vid + 10, "name": ""}
        )
        vlan.relay_vlan = relay_vlan
        Vlan._handler.update.return_value = {
            "id": vlan_id,
            "vid": vid,
            "name": "",
            "relay_vlan": relay_vlan._data,
        }
        vlan.save()
        Vlan._handler.update.assert_called_once_with(
            fabric_id=fabric_id, vid=vid, _vid=vid, relay_vlan=relay_vlan.id
        )
        self.assertThat(vlan.relay_vlan.id, Equals(relay_vlan.id))

    def test__vlan_update_relay_vlan_with_integer_id(self):
        self.skip("see https://github.com/canonical/python-libmaas/issues/180")
        origin = make_origin()
        Vlan = origin.Vlan
        Vlan._handler.params = ["fabric_id", "vid"]
        fabric_id = random.randint(1, 100)
        vlan_id = random.randint(5001, 6000)
        vid = random.randint(100, 200)
        vlan = Vlan(
            {"id": vlan_id, "fabric_id": fabric_id, "vid": vid, "relay_vlan": None}
        )
        relay_vlan = Vlan({"id": vlan_id + 1, "fabric_id": fabric_id, "vid": vid + 10})
        vlan.relay_vlan = str(vlan_id + 1)
        Vlan._handler.update.return_value = {
            "id": vlan_id,
            "vid": vid,
            "name": "",
            "relay_vlan": relay_vlan._data,
        }
        vlan.save()
        Vlan._handler.update.assert_called_once_with(
            fabric_id=fabric_id, vid=vid, _vid=vid, relay_vlan=relay_vlan.id
        )
        self.assertThat(vlan.relay_vlan.id, Equals(relay_vlan.id))
