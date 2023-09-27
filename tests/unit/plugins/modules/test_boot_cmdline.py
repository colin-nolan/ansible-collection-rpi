from pathlib import Path
from typing import Any

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
    return localhost


def test_no_configuration(runner: ModuleDispatcherV2, example_file: Path):
    contacted = run_boot_cmdline(runner, example_file, {})
    assert not contacted["changed"]


def run_boot_cmdline(localhost: ModuleDispatcherV2, path: Path, paramters: dict[str, Any]):
    contacted = localhost.boot_cmdline(path=path.as_posix(), **paramters)
    return contacted.localhost
