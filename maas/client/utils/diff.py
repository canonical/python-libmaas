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

"""Helpers for calulating difference between objects."""

__all__ = [
    "calculate_dict_diff",
]


from . import remove_None


def calculate_dict_diff(old_params: dict, new_params: dict):
    """Return the parameters based on the difference.

    If a parameter exists in `old_params` but not in `new_params` then
    parameter will be set to an empty string.
    """
    # Ignore all None values as those cannot be saved.
    old_params = remove_None(old_params)
    new_params = remove_None(new_params)
    params_diff = {}
    for key, value in old_params.items():
        if key in new_params:
            if value != new_params[key]:
                params_diff[key] = new_params[key]
        else:
            params_diff[key] = ''
    for key, value in new_params.items():
        if key not in old_params:
            params_diff[key] = value
    return params_diff
