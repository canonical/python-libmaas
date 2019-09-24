"""Tests for `maas.client.viscera.domains`."""

import random

from testtools.matchers import Equals, IsInstance, MatchesStructure

from .. import domains

from ..testing import bind
from ...testing import make_string_without_spaces, TestCase


def make_origin():
    """
    Create a new origin with Domain and Domains. The former
    refers to the latter via the origin, hence why it must be bound.
    """
    return bind(domains.Domains, domains.Domain)


class TestDomains(TestCase):
    def test__domains_create(self):
        origin = make_origin()
        domain_id = random.randint(0, 100)
        ttl = random.randint(0, 100)
        name = make_string_without_spaces()
        origin.Domains._handler.create.return_value = {
            "id": domain_id,
            "name": name,
            "ttl": ttl,
            "authoritative": False,
        }
        domain = origin.Domains.create(name=name, authoritative=False, ttl=ttl)
        origin.Domains._handler.create.assert_called_once_with(
            name=name, authoritative=False, ttl=ttl
        )
        self.assertThat(domain, IsInstance(origin.Domain))
        self.assertThat(
            domain,
            MatchesStructure.byEquality(
                id=domain_id, name=name, ttl=ttl, authoritative=False
            ),
        )

    def test__domains_create_without_ttl(self):
        origin = make_origin()
        domain_id = random.randint(0, 100)
        name = make_string_without_spaces()
        origin.Domains._handler.create.return_value = {"id": domain_id, "name": name}
        domain = origin.Domains.create(name=name)
        origin.Domains._handler.create.assert_called_once_with(
            name=name, authoritative=True
        )
        self.assertThat(domain, IsInstance(origin.Domain))
        self.assertThat(domain, MatchesStructure.byEquality(id=domain_id, name=name))

    def test__domains_read(self):
        """Domains.read() returns a list of Domains."""
        Domains = make_origin().Domains
        domains = [
            {"id": random.randint(0, 100), "name": make_string_without_spaces()}
            for _ in range(3)
        ]
        Domains._handler.read.return_value = domains
        domains = Domains.read()
        self.assertThat(len(domains), Equals(3))


class TestDomain(TestCase):
    def test__domain_read(self):
        Domain = make_origin().Domain
        domain = {"id": random.randint(0, 100), "name": make_string_without_spaces()}
        Domain._handler.read.return_value = domain
        self.assertThat(Domain.read(id=domain["id"]), Equals(Domain(domain)))
        Domain._handler.read.assert_called_once_with(id=domain["id"])

    def test__domain_delete(self):
        Domain = make_origin().Domain
        domain = Domain(
            {
                "id": random.randint(0, 100),
                "name": make_string_without_spaces(),
                "description": make_string_without_spaces(),
            }
        )
        domain.delete()
        Domain._handler.delete.assert_called_once_with(id=domain.id)
