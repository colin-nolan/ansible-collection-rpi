from pathlib import Path
from typing import Any, Optional
from unittest.mock import patch

import ansible.context
import pytest
from ansible.utils.context_objects import CLIArgs
from pytest_ansible.module_dispatcher.v2 import ModuleDispatcherV2

EXAMPLE_CONTENT_1 = (
    "console=serial0,115200 console=tty1 root=PARTUUID=5492573e-02 rootfstype=ext4 fsck.repair=yes rootwait"
)


@pytest.fixture()
def example_file(tmp_path: Path) -> Path:
    file_path = Path(tmp_path / "cmdline.txt")
    file_path.write_text(EXAMPLE_CONTENT_1)
    return file_path


@pytest.fixture()
def check_mode(request) -> bool:
    return request.param


@pytest.fixture()
def runner(localhost: ModuleDispatcherV2) -> ModuleDispatcherV2:
    # Hack to allow tests to be ran without setting --module-path flag on pytest
    localhost.options["module_path"] = (
        Path(__file__).parent.parent.parent.parent.parent / "plugins/modules"
    ).as_posix()

    # Working around bug where localhost is called twice:
    # https://github.com/ansible/pytest-ansible/issues/135
    del localhost.options["extra_inventory_manager"]

    return localhost


@pytest.mark.parametrize("check_mode", [False, True], indirect=True)
def test_add_no_configuration(runner: ModuleDispatcherV2, example_file: Path, check_mode: bool):
    original_content = example_file.read_text()
    result = _run_boot_cmdline(runner, example_file, {}, check_mode)
    assert not result["changed"]
    assert example_file.read_text() == original_content


@pytest.mark.parametrize("check_mode", [False, True], indirect=True)
def test_add_no_configuration_change(runner: ModuleDispatcherV2, example_file: Path, check_mode: bool):
    original_content = example_file.read_text()
    result = _run_boot_cmdline(runner, example_file, dict(items={"fsck.repair": "yes", "rootwait": None}), check_mode)
    assert not result["changed"]
    assert example_file.read_text() == original_content


@pytest.mark.parametrize("check_mode", [False, True], indirect=True)
def test_add_new_items(runner: ModuleDispatcherV2, example_file: Path, check_mode: bool):
    result = _run_boot_cmdline(
        runner,
        example_file,
        dict(items={"new_key": "new_value", "no_value": None, "other_key": "other=value"}),
        check_mode,
    )
    assert result["changed"]
    assert set(result["changed_keys"]) == {"new_key", "no_value", "other_key"}
    _expect_in_cmdline("new_key", "new_value", example_file, check_mode)
    _expect_in_cmdline("other_key", "other=value", example_file, check_mode)
    _expect_in_cmdline("no_value", None, example_file, check_mode)


def _run_boot_cmdline(localhost: ModuleDispatcherV2, path: Path, paramters: dict[str, Any], check_mode: bool):
    def _init_global_context_replacement(cli_args):
        # Injects checked mode
        cli_args.check = check_mode
        # Deviates from the original as uses `CLIArgs` instead of the immutable `GlobalCLIArgs` singleton
        # `CLIARGS` must be referred to by its full path (does not work if CLIARGS is imported from its module)
        ansible.context.CLIARGS = CLIArgs.from_options(cli_args)

    # Hack to stop check_mode getting immutably set into an immutable global singleton
    with patch("ansible.context._init_global_context", _init_global_context_replacement):
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
