# Copyright 2016-2017 Canonical Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for handling of MAAS API credentials."""

from testtools.matchers import IsInstance

from ...testing import TestCase
from ..creds import Credentials


class TestCredentials(TestCase):
    """Tests for `maas.client.creds.Credentials`."""

    def test_str_form_is_colon_separated_triple(self):
        creds = Credentials("foo", "bar", "baz")
        self.assertEqual(':'.join(creds), str(creds))

    def test_parse_reads_a_colon_separated_triple(self):
        creds = Credentials.parse("foo:bar:baz")
        self.assertEqual(("foo", "bar", "baz"), creds)
        self.assertThat(creds, IsInstance(Credentials))
        self.assertEqual("foo", creds.consumer_key)
        self.assertEqual("bar", creds.token_key)
        self.assertEqual("baz", creds.token_secret)

    def test_parse_reads_a_sequence(self):
        creds = Credentials.parse(("foo", "bar", "baz"))
        self.assertEqual(("foo", "bar", "baz"), creds)
        self.assertThat(creds, IsInstance(Credentials))
        self.assertEqual("foo", creds.consumer_key)
        self.assertEqual("bar", creds.token_key)
        self.assertEqual("baz", creds.token_secret)

    def test_parse_rejects_too_few_parts(self):
        self.assertRaises(ValueError, Credentials.parse, "foo:bar")
        self.assertRaises(ValueError, Credentials.parse, ("foo", "bar"))

    def test_parse_rejects_too_many_parts(self):
        self.assertRaises(ValueError, Credentials.parse, "a:b:c:d")
        self.assertRaises(ValueError, Credentials.parse, ("a", "b", "c", "d"))

    def test_parse_returns_None_when_there_are_no_parts(self):
        self.assertIsNone(Credentials.parse(""))
        self.assertIsNone(Credentials.parse(()))

    def test_parse_returns_None_when_passed_None(self):
        self.assertIsNone(Credentials.parse(None))

    def test_parse_returns_credentials_when_passed_credentials(self):
        creds = Credentials("foo", "bar", "baz")
        self.assertIs(creds, Credentials.parse(creds))
