from pathlib import Path
from typing import Any, Optional

import pytest
from ansible.cli.adhoc import AdHocCLI
from pytest_ansible.module_dispatcher.v2 import ModuleDispatcherV2
import os

EXAMPLE_CONTENT_1 = (
    "console=serial0,115200 console=tty1 root=PARTUUID=5492573e-02 rootfstype=ext4 fsck.repair=yes rootwait"
)


@pytest.fixture()
def example_file(tmp_path: Path) -> Path:
    file_path = Path(tmp_path / "cmdline.txt")
    file_path.write_text(EXAMPLE_CONTENT_1)
    return file_path


_CHECKED_MODE_INDICATOR = "#---CHECK_MODE---"
_HIJACKED_CHECK_MODE_OPTION = "become_user"
_ORIGINAL_ADHOC_CLI_INIT = AdHocCLI.__init__


def _check_mode_hacker(self, args, **kwargs):
    for i in range(len(args)):
        if args[i].startswith(f"--{_HIJACKED_CHECK_MODE_OPTION.replace('_', '-')}="):
            if args[i].endswith(_CHECKED_MODE_INDICATOR):
                args.append("--check")
                args[i] = args[i].replace(_CHECKED_MODE_INDICATOR, "")
            break
    _ORIGINAL_ADHOC_CLI_INIT(self, args, **kwargs)


# Hack to allow run with check mode
AdHocCLI.__init__ = _check_mode_hacker


@pytest.fixture()
def check_mode(request) -> bool:
    return request.param


@pytest.fixture()
def runner(check_mode: bool, localhost: ModuleDispatcherV2) -> ModuleDispatcherV2:
    # Hack to allow tests to be ran without setting --module-path flag on pytest
    localhost.options["module_path"] = (
        Path(__file__).parent.parent.parent.parent.parent / "plugins/modules"
    ).as_posix()

    # check_mode = request.param
    if check_mode:
        # Hack to allow run with check mode (not currently supported without hacks):
        # `_HIJACKED_CHECK_MODE_OPTION` is one of the paramters that gets passed through to
        # `AdHocCLI`. We add an indicator to allow the hijacked `AdHocCLI.__init__` method
        # to know that check mode is requested. The indicator will be removed `module_path`
        # is used.
        localhost.options[_HIJACKED_CHECK_MODE_OPTION] += _CHECKED_MODE_INDICATOR

    # Working around bug where localhost is called twice:
    # https://github.com/ansible/pytest-ansible/issues/135
    del localhost.options["extra_inventory_manager"]

    return localhost


@pytest.mark.parametrize("check_mode", [False, True], indirect=True)
def test_add_no_configuration(runner: ModuleDispatcherV2, example_file: Path):
    original_content = example_file.read_text()
    result = _run_boot_cmdline(runner, example_file, {})
    assert not result["changed"]
    assert example_file.read_text() == original_content


@pytest.mark.parametrize("check_mode", [False, True], indirect=True)
def test_add_no_configuration_change(runner: ModuleDispatcherV2, example_file: Path):
    original_content = example_file.read_text()
    result = _run_boot_cmdline(runner, example_file, dict(items={"fsck.repair": "yes", "rootwait": None}))
    assert not result["changed"]
    assert example_file.read_text() == original_content


@pytest.mark.parametrize("check_mode", [False, True], indirect=True)
def test_add_new_items(runner: ModuleDispatcherV2, example_file: Path, check_mode: bool):
    result = _run_boot_cmdline(
        runner, example_file, dict(items={"new_key": "new_value", "no_value": None, "other_key": "other=value"})
    )
    assert result["changed"]
    assert set(result["changed_keys"]) == {"new_key", "no_value", "other_key"}
    _expect_in_cmdline("new_key", "new_value", example_file, check_mode)
    _expect_in_cmdline("other_key", "other=value", example_file, check_mode)
    _expect_in_cmdline("no_value", None, example_file, check_mode)


@pytest.mark.parametrize("check_mode", [False, True], indirect=True)
def test_checked(runner: ModuleDispatcherV2, example_file: Path):
    result = _run_boot_cmdline(runner, example_file, paramters=dict(items={"no_value": "some"}))

    raise Exception(example_file.read_text())
    assert not result["changed"]
    _expect_not_in_cmdline("no_value", None, example_file)


def _run_boot_cmdline(localhost: ModuleDispatcherV2, path: Path, paramters: dict[str, Any]):
    contacted = localhost.boot_cmdline(path=path.as_posix(), **paramters)
    return contacted.localhost


def _expect_in_cmdline(key: str, value: Optional[str], path: Path, invert: bool = False):
    padded_content = f" {path.read_text()} "
    if value is not None:
        assert (f" {key}={value}" in padded_content) != invert
    else:
        assert (f"{key}" in padded_content) != invert


def _expect_not_in_cmdline(key: str, value: Optional[str], path: Path):
    return _expect_in_cmdline(key, value, path, invert=True)
