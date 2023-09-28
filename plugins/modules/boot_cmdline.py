#!/usr/bin/python

from __future__ import absolute_import, division, print_function

__metaclass__ = type

STATE_MODULE_PARAMETER = "state"
ITEMS_MODULE_PARAMETER = "items"
PATH_MODULE_PARAMETER = "path"

PRESENT_STATE = "present"

DOCUMENTATION = rf"""
module: boot_cmdline

short_description: manages kernel boot parameters in `/boot/cmdline.txt`

options:
    {STATE_MODULE_PARAMETER}:
        description: Whether the parameters should be present (implemented) or absent (unimplemented).
        required: true
        type: str
    {ITEMS_MODULE_PARAMETER}:
        description: A dictionary of parameter keys and their corresponding argument values. Use `null` for parameters with no argument (i.e. `parameter` instead of `parameter=argument`).
        required: true
        type: dict
    {PATH_MODULE_PARAMETER}:
        description: An alternative path to `/boot/cmdline.txt` to   the file containing the kernel boot parameters.
        required: false
        type: str
"""

EXAMPLES = r"""
- name: Set parameter with corresponding argument (parameter1=value)
  become: true
  colin_nolan.rpi.boot_cmdline:
    state: present
    items:
      parameter1: value
  notify: reboot

- name: Set parameter with no argument (parameter2)
  become: true
  colin_nolan.rpi.boot_cmdline:
    state: present
    items:
      parameter2: null
  notify: reboot

- name: Set multiple parameters (parameter1=value, parameter2)
  become: true
  colin_nolan.rpi.boot_cmdline:
    state: present
    items:
      parameter1: value
      parameter2: null
  notify: reboot
"""

RETURN = rf"""
changed_keys:
    description: List of changed parameters.
    type: list[str]
    returned: always
"""

import tempfile
from collections import OrderedDict
from pathlib import Path
from typing import Any, Callable, Optional

from ansible.module_utils.basic import AnsibleModule

DEFAULT_CMDLINE_FILE_LOCATION = Path("/boot/cmdline.txt")


MODULE_SPEC = {
    STATE_MODULE_PARAMETER: dict(type=str, required=False, default=PRESENT_STATE, choices=[PRESENT_STATE]),
    ITEMS_MODULE_PARAMETER: dict(type=dict[str, Any], required=False, default={}),
    PATH_MODULE_PARAMETER: dict(type=str, required=False, default=DEFAULT_CMDLINE_FILE_LOCATION),
}

_MISSING_SENTINEL = object()

# Note: not using `TypeAlias` to support Python 3.9
Configuration = OrderedDict[str, Optional[str]]


def run_module():
    module = AnsibleModule(argument_spec=MODULE_SPEC, supports_check_mode=True)

    path = Path(module.params[PATH_MODULE_PARAMETER])
    state = module.params[STATE_MODULE_PARAMETER]

    try:
        configuration = _read_boot_cmdline(path)
    except Exception as e:
        module.fail_json(msg=f"Failed to read cmdline file {path}: {e}")
        return

    changed_parameters = []
    if module.params[STATE_MODULE_PARAMETER] != PRESENT_STATE:
        module.fail_json(msg=f"Unknown state: {state}")

    for parameter, argument in module.params[ITEMS_MODULE_PARAMETER].items():
        parameter = str(parameter)
        argument = str(argument) if argument is not None else None
        # Need to use sentinel as a unique value that cannot exist in the config (unlike `None`)
        if configuration.get(parameter, _MISSING_SENTINEL) != argument:
            configuration[parameter] = argument
            changed_parameters.append(parameter)

    if not module.check_mode and len(changed_parameters) > 0:
        _write_boot_cmdline(path, configuration, module.atomic_move)

    module.exit_json(changed=len(changed_parameters) > 0, changed_parameters=changed_parameters)


def _read_boot_cmdline(file_location: Path) -> Configuration:
    configuration = OrderedDict()
    with file_location.open(mode="r") as file:
        for line in file.readlines():
            items = line.split(" ")
            for item in items:
                if "=" in item:
                    parameter, argument = item.split("=", maxsplit=1)
                    configuration[parameter] = argument.rstrip()
                else:
                    configuration[item.rstrip()] = None
    return configuration


def _write_boot_cmdline(file_location: Path, configuration: Configuration, atomic_move: Callable[[str, str], None]):
    items = []
    for parameter, argument in configuration.items():
        if argument is not None:
            items.append(f"{parameter}={argument}")
        else:
            items.append(f"{parameter}")

    try:
        # Following advice as to not write to files directly:
        # https://docs.ansible.com/ansible/latest/dev_guide/developing_modules_best_practices.html#general-guidelines-tips
        with tempfile.NamedTemporaryFile(mode="w") as file:
            file.write(" ".join(items))
            file.flush()
            atomic_move(file.name, file_location.as_posix())
    except FileNotFoundError:
        # Expecting a failure in the success case, as the file has been removed
        pass


def main():
    run_module()


if __name__ == "__main__":
    main()
