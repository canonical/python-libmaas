# Copyright 2016 Canonical Ltd.
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

"""Tests for asynchronous helpers."""

import asyncio
from inspect import isawaitable

from testtools.matchers import (
    Equals,
    Is,
    MatchesPredicate,
)

from .. import async
from ...testing import TestCase


IsAwaitable = MatchesPredicate(isawaitable, "%s is not awaitable")


class TestAsynchronousWrapper(TestCase):
    """Tests for `asynchronous`."""

    def test_returns_plain_result_unaltered_when_loop_not_running(self):
        token = object()
        func = async.asynchronous(lambda: token)
        self.assertThat(func(), Is(token))

    def test_returns_plain_result_unaltered_when_loop_running(self):
        token = object()
        func = async.asynchronous(lambda: token)

        async def within_event_loop():
            loop = asyncio.get_event_loop()
            self.assertTrue(loop.is_running())
            return func()

        self.assertThat(
            self.loop.run_until_complete(within_event_loop()),
            Is(token))

    def test_blocks_on_awaitable_result_when_loop_not_running(self):
        token = asyncio.sleep(0.0)
        func = async.asynchronous(lambda: token)
        self.assertThat(func(), Is(None))

    def test_returns_awaitable_result_unaltered_when_loop_running(self):
        token = asyncio.sleep(0.0)
        func = async.asynchronous(lambda: token)

        async def within_event_loop():
            loop = asyncio.get_event_loop()
            self.assertTrue(loop.is_running())
            return func()

        result = self.loop.run_until_complete(within_event_loop())
        self.assertThat(result, Is(token))
        self.assertThat(result, IsAwaitable)
        result = self.loop.run_until_complete(result)
        self.assertThat(result, Is(None))


class TestAsynchronousType(TestCase):
    """Tests for `Asynchronous`."""

    def test_callable_attributes_are_wrapped(self):
        # `Asynchronous` groks class- and static-methods.

        class Class(metaclass=async.Asynchronous):

            attribute = 123

            def imethod(self):
                return self, "instancemethod"

            @classmethod
            def cmethod(cls):
                return cls, "classmethod"

            @staticmethod
            def smethod():
                return None, "staticmethod"

        self.assertThat(Class.attribute, Equals(123))
        self.assertThat(Class.smethod(), Equals((None, "staticmethod")))
        self.assertThat(Class.cmethod(), Equals((Class, "classmethod")))

        inst = Class()
        self.assertThat(inst.attribute, Equals(123))
        self.assertThat(inst.smethod(), Equals((None, "staticmethod")))
        self.assertThat(inst.cmethod(), Equals((Class, "classmethod")))
        self.assertThat(inst.imethod(), Equals((inst, "instancemethod")))
