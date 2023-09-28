from pathlib import Path
from typing import Any, Optional

import pytest
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
def runner(localhost: ModuleDispatcherV2) -> ModuleDispatcherV2:
    # Hack to allow tests to be ran without setting --module-path flag on pytest
    localhost.options["module_path"] = (
        Path(__file__).parent.parent.parent.parent.parent / "plugins/modules"
    ).as_posix()
    # Working around bug where localhost is called twice:
    # https://github.com/ansible/pytest-ansible/issues/135
    del localhost.options["extra_inventory_manager"]
    return localhost


def test_no_configuration(runner: ModuleDispatcherV2, example_file: Path):
    original_content = example_file.read_text()
    result = _run_boot_cmdline(runner, example_file, {})
    assert not result["changed"]
    assert example_file.read_text() == original_content


def test_no_configuration_change(runner: ModuleDispatcherV2, example_file: Path):
    original_content = example_file.read_text()
    result = _run_boot_cmdline(runner, example_file, dict(items={"fsck.repair": "yes", "rootwait": None}))
    assert not result["changed"]
    assert example_file.read_text() == original_content


def test_add_new_key_value_item(runner: ModuleDispatcherV2, example_file: Path):
    result = _run_boot_cmdline(runner, example_file, dict(items={"new_key": "new_value", "other_key": "other_value"}))
    assert result["changed"]
    assert set(result["changed_keys"]) == {"new_key", "other_key"}
    _expect_in_cmdline("new_key", "new_value", example_file)
    _expect_in_cmdline("other_key", "other_value", example_file)


def _run_boot_cmdline(localhost: ModuleDispatcherV2, path: Path, paramters: dict[str, Any]):
    contacted = localhost.boot_cmdline(path=path.as_posix(), **paramters)
    return contacted.localhost


def _expect_in_cmdline(key: str, value: Optional[str], path: Path):
    padded_content = f" {path.read_text()} "
    if value is not None:
        assert f" {key}={value}" in padded_content
    else:
        assert f"{key}" in padded_content
