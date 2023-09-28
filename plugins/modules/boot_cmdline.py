#!/usr/bin/python

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
TODO
"""

RETURN = r"""
TODO
"""

import tempfile
from collections import OrderedDict
from pathlib import Path
from typing import Any, Callable, TypeAlias

from ansible.module_utils.basic import AnsibleModule

DEFAULT_CMDLINE_FILE_LOCATION = Path("/boot/cmdline.txt")

STATE_MODULE_PARAMETER = "state"
ITEMS_MODULE_PARAMETER = "items"
PATH_MODULE_PARAMETER = "path"

PRESENT_STATE = "present"

MODULE_SPEC = {
    STATE_MODULE_PARAMETER: dict(type=str, required=False, default=PRESENT_STATE, choices=[PRESENT_STATE]),
    ITEMS_MODULE_PARAMETER: dict(type=dict[str, Any], required=False, default={}),
    PATH_MODULE_PARAMETER: dict(type=str, required=False, default=DEFAULT_CMDLINE_FILE_LOCATION),
}

_MISSING_SENTINEL = object()

Configuration: TypeAlias = OrderedDict[str, str | None]


def run_module():
    module = AnsibleModule(argument_spec=MODULE_SPEC, supports_check_mode=True)

    path = Path(module.params[PATH_MODULE_PARAMETER])
    state = module.params[STATE_MODULE_PARAMETER]

    try:
        configuration = _read_boot_cmdline(path)
    except Exception as e:
        module.fail_json(msg=f"Failed to read cmdline file {path}: {e}")
        return

    changed_keys = []
    if module.params[STATE_MODULE_PARAMETER] != PRESENT_STATE:
        module.fail_json(msg=f"Unknown state: {state}")

    for key, value in module.params[ITEMS_MODULE_PARAMETER].items():
        # Need to use sentinel as a unique value that cannot exist in the config (unlike `None`)
        if configuration.get(key, _MISSING_SENTINEL) != value:
            configuration[key] = value
            changed_keys.append(key)

    if not module.check_mode and len(changed_keys) > 0:
        _write_boot_cmdline(path, configuration, module.atomic_move)

    module.exit_json(changed=len(changed_keys) > 0, changed_keys=changed_keys)


def _read_boot_cmdline(file_location: Path) -> Configuration:
    configuration = OrderedDict()
    with file_location.open(mode="r") as file:
        for line in file.readlines():
            items = line.split(" ")
            for item in items:
                if "=" in item:
                    key, value = item.split("=", maxsplit=1)
                    configuration[key] = value
                else:
                    configuration[item] = None
    return configuration


def _write_boot_cmdline(file_location: Path, configuration: Configuration, atomic_move: Callable[[str, str], None]):
    items = []
    for key, value in configuration.items():
        if value is not None:
            items.append(f"{key}={value}")
        else:
            items.append(f"{key}")

    try:
        # Following advice as to not write to files directly:
        # https://docs.ansible.com/ansible/latest/dev_guide/developing_modules_best_practices.html#general-guidelines-tips
        with tempfile.NamedTemporaryFile(mode="w") as file:
            file.write(" ".join(items))
            atomic_move(file.name, file_location.as_posix())
    except FileNotFoundError:
        # Expecting a failure in the success case, as the file has been removed
        pass


def main():
    run_module()


if __name__ == "__main__":
    main()
