"""Helpers for calulating difference between objects."""

__all__ = [
    "calculate_dict_diff",
]


def remove_None(params: dict):
    """Remove all keys in `params` that have the value of `None`."""
    return {
        key: value
        for key, value in params.items()
        if value is not None
    }


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
