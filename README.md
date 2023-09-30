[![Build Status](https://ci.colinnolan.uk/api/badges/colin-nolan/ansible-collection-rpi/status.svg)](https://ci.colinnolan.uk/colin-nolan/ansible-collection-rpi)

# Ansible Collection - colin_nolan.rpi

Collection of Ansible modules for managing Raspberry Pis. Contains modules to:

- Set kernel boot parameters in `/boot/cmdline.txt` (or similar files).

## Installation

This collection is not yet published on [Ansible Galaxy](https://galaxy.ansible.com/) but it can be installed from GitHub.

If you are [using a `requirements.yml` file](https://docs.ansible.com/ansible/latest/galaxy/user_guide.html#installing-multiple-roles-from-a-file)

```yml
collections:
  - name: git+https://github.com/colin-nolan/ansible-collection-rpi.git,1.0.1
```

else install from the command line using:

```shell
ansible-galaxy collection install git+https://github.com/colin-nolan/ansible-collection-rpi.git,1.0.1
```

## Usage

Create a task in your role/playbook that uses the module, e.g.:

```yml
- name: Set kernel boot parameters
  become: true
  colin_nolan.rpi.boot_cmdline:
    state: present
    items:
      cgroup_memory: 1
      cgroup_enable: memory
      key_only: null
  notify: reboot
```

It is likely you will want to reboot handler to apply any changes, e.g.:

```yml
- name: Reboot the machine
  become: true
  ansible.builtin.reboot:
  listen: reboot
```

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

#### Build Distributable

```shell
make build
```

Requires: see Linting.

#### CI

The [`drone` CLI](https://docs.drone.io/cli/install/) can be used to run CI pipelines locally, e.g.

```shell
drone exec --pipeline=lint .drone.yml
```

## Alternatives

- [`escalate.cmdline`](https://github.com/escalate/ansible-raspberry-cmdline): role for setting all parameters in `/boot/cmdline.txt`. Preserves `root` but resets all other parameters.
- [`jm1.rpi_cmdline`](https://github.com/JM1/ansible-role-jm1-rpi-cmdline): role for setting all parameters in `/boot/firmware/cmdline.txt`.

## Legal

MIT (contact for other licencing). Copyright 2023 Colin Nolan.

This work is in no way related to any company that I may work for.
