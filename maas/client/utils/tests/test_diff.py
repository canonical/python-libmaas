# Copyright 2017 Canonical Ltd.
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

"""Tests for handling the calculation of object difference."""

import copy

from ...testing import TestCase
from ..diff import calculate_dict_diff


class TestCalculateDictDiff(TestCase):
    """Test `calculate_dict_diff`."""

    def test_calcs_no_difference(self):
        orig_data = {
            'key1': 'value1',
            'key2': 'value2',
        }
        new_data = copy.deepcopy(orig_data)
        self.assertEquals({}, calculate_dict_diff(orig_data, new_data))

    def test_calcs_changed_value(self):
        orig_data = {
            'key1': 'value1',
            'key2': 'value2',
        }
        new_data = copy.deepcopy(orig_data)
        new_data['key2'] = 'new_value'
        self.assertEquals(
            {'key2': 'new_value'}, calculate_dict_diff(orig_data, new_data))

    def test_calcs_deleted_value(self):
        orig_data = {
            'key1': 'value1',
            'key2': 'value2',
        }
        new_data = copy.deepcopy(orig_data)
        del new_data['key2']
        self.assertEquals(
            {'key2': ''}, calculate_dict_diff(orig_data, new_data))

    def test_calcs_changes_and_deleted(self):
        orig_data = {
            'key1': 'value1',
            'key2': 'value2',
        }
        new_data = copy.deepcopy(orig_data)
        new_data['key1'] = 'new_value'
        del new_data['key2']
        self.assertEquals({
            'key1': 'new_value',
            'key2': '',
        }, calculate_dict_diff(orig_data, new_data))
