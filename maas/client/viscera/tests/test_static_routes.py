"""Test for `maas.client.viscera.static_routes`."""

import random

from testtools.matchers import Equals

from ..static_routes import (
    StaticRoute,
    StaticRoutes,
)

from .. testing import bind
from ...testing import (
    make_string_without_spaces,
    TestCase,
)


def make_origin():
    """
    Create a new origin with StaticRoutes and StaticRoute. The former
    refers to the latter via the origin, hence why it must be bound.
    """
    return bind(StaticRoutes, StaticRoute)


class TestStaticRoutes(TestCase):

    def test__static_routes_create(self):
        StaticRoutes = make_origin().StaticRoutes
        destination = random.randint(0, 100)
        source = random.randint(0, 100)
        gateway_ip = make_string_without_spaces()
        metric = make_string_without_spaces()
        StaticRoutes._handler.create.return_value = {
            "id": 1,
            "destination": destination,
            "source": source,
            "gateway_ip": gateway_ip,
            "metric": metric
        }
        StaticRoutes.create(
            destination=destination,
            source=source,
            gateway_ip=gateway_ip,
            metric=metric,
        )
        StaticRoutes._handler.create.assert_called_once_with(
            destination=destination,
            source=source,
            gateway_ip=gateway_ip,
            metric=metric,
        )

    def test__static_routes_read(self):
        """StaticRoutes.read() returns a list of StaticRoutes."""
        StaticRoutes = make_origin().StaticRoutes
        static_routes = [
            {
                "id": random.randint(0, 100),
                "destination": random.randint(0, 100),
                "source": random.randint(0, 100),
                "gateway_ip": make_string_without_spaces(),
                "metric": make_string_without_spaces(),
            }
            for _ in range(3)
        ]
        StaticRoutes._handler.read.return_value = static_routes
        static_routes = StaticRoutes.read()
        self.assertThat(len(static_routes), Equals(3))


class TestStaticRoute(TestCase):

    def test__static_route_read(self):
        StaticRoute = make_origin().StaticRoute
        static_route = {
            "id": random.randint(0, 100),
            "destination": random.randint(0, 100),
            "source": random.randint(0, 100),
            "gateway_ip": make_string_without_spaces(),
            "metric": make_string_without_spaces(),
        }
        StaticRoute._handler.read.return_value = static_route
        self.assertThat(StaticRoute.read(
            id=static_route["id"]), Equals(StaticRoute(static_route)))
        StaticRoute._handler.read.assert_called_once_with(
            id=static_route["id"])

    def test__static_route_delete(self):
        StaticRoute = make_origin().StaticRoute
        static_route_id = random.randint(1, 100)
        static_route = StaticRoute({
            "id": static_route_id,
            "destination": random.randint(0, 100),
            "source": random.randint(0, 100),
            "gateway_ip": make_string_without_spaces(),
            "metric": make_string_without_spaces(),
        })
        static_route.delete()
        StaticRoute._handler.delete.assert_called_once_with(id=static_route_id)
