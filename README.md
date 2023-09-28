[![Build Status](https://ci.colinnolan.uk/api/badges/colin-nolan/ansible-module-boot-cmdline/status.svg)](https://ci.colinnolan.uk/colin-nolan/ansible-module-boot-cmdline)

# Ansible Collection - colin_nolan.boot_cmdline

Ansible module (not role) for managing `/boot/cmdline.txt` or similar files.

## Installation

TODO

## Development

### Test

```shell
make test
```

Requires: `pip install -r tests/unit/plugins/requirements.txt`.

### Linting

```shell
make lint
```

Requires: `pip install -r requirements.style.txt`.

#### Apply Format

```shell
make format
```

Requires: see Linting.

#### CI

The [`drone` CLI](https://docs.drone.io/cli/install/) can be used to run CI pipelines locally, e.g.

```shell
drone exec --pipeline=lint .drone.yml
```

## Alternatives

- https://github.com/jtyr/ansible-grub_cmdline
- https://github.com/escalate/ansible-raspberry-cmdline
- https://github.com/JM1/ansible-role-jm1-rpi-cmdline

## Legal

MIT (contact for other licencing). Copyright 2023 Colin Nolan.

This work is in no way related to any company that I may work for.
