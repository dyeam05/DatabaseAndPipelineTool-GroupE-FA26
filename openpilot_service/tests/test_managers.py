from __future__ import annotations

import subprocess

import pytest # pyright: ignore[reportMissingImports]

from lib.openpilot.process_management import OpenpilotDockerEnv
from openpilot_service.lib.utils.route_logger_utils import log_route


CONTAINER = "custom_openpilot-dev-1"
ROUTE = "db478799b6f9f210/00000040--8afe968813/23"


def _container_is_running(name: str) -> bool:
    p = subprocess.run(
        ["docker", "inspect", "-f", "{{.State.Running}}", name],
        capture_output=True,
        text=True,
    )
    return p.returncode == 0 and p.stdout.strip() == "true"


@pytest.mark.integration
def test_log_route_creates_non_empty_output_dir() -> None:
    if not _container_is_running(CONTAINER):
        pytest.skip(f"container {CONTAINER} is not running")

    output_dir = log_route(route=ROUTE, container=CONTAINER)
    env = OpenpilotDockerEnv(container=CONTAINER)

    exists = env.run_capture(f'test -d "{output_dir}" && echo YES || echo NO')
    assert exists.strip() == "YES"

    has_files = env.run_capture(f'find "{output_dir}" -mindepth 1 -print -quit | wc -l')
    assert has_files.strip() != "0"
