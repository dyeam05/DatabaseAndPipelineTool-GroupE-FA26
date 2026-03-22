import asyncio
import logging
import os
import shlex
import signal
from pathlib import Path
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from db.models.route import Route
from db.url import build_database_url
from repositories.route_repository import RouteRepository
from services.errors import RouteNotFoundError
from services.route_service import RouteService, RouteStatus


POLL_INTERVAL_SECONDS = 2.0
OPENPILOT_DIR = Path("/app/openpilot")
DATA_ROOT = Path("/app/data")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)


def _output_dir_snapshot(output_dir: Path, *, sample_limit: int = 10) -> tuple[int, list[str]]:
    if not output_dir.exists():
        return 0, []

    files: list[str] = []
    total = 0
    for item in output_dir.rglob("*"):
        if item.is_file():
            total += 1
            if len(files) < sample_limit:
                files.append(str(item.relative_to(output_dir)))
    return total, files


def _build_openpilot_bash(inner_command: str) -> str:
    conda_env_name = os.getenv("CONDA_ENV_NAME", "openpilot")
    quoted_conda_env = shlex.quote(conda_env_name)
    return (
        "set -euo pipefail\n"
        "export TERM=xterm\n"
        "source ~/miniconda3/etc/profile.d/conda.sh\n"
        f"conda activate {quoted_conda_env}\n"
        f"cd {shlex.quote(str(OPENPILOT_DIR))}\n"
        "source ./.venv/bin/activate\n"
        f"{inner_command}"
    )


async def _start_extraction_process(output_dir: Path) -> asyncio.subprocess.Process:
    command = _build_openpilot_bash(
        "python ./selfdrive/modeld/extract_data.py --output_dir "
        f"{shlex.quote(str(output_dir))}"
    )
    return await asyncio.create_subprocess_exec(
        "bash",
        "-lc",
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
        preexec_fn=os.setsid,
    )


async def _start_replay_process(route_id: str) -> asyncio.subprocess.Process:
    replay_command = f"./tools/replay/replay {shlex.quote(route_id)} --all --ecam"
    command = _build_openpilot_bash(
        f"script -q -f -c {shlex.quote(replay_command)} /dev/null"
    )
    return await asyncio.create_subprocess_exec(
        "bash",
        "-lc",
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
        preexec_fn=os.setsid,
    )


async def _stream_process_output(
    process: asyncio.subprocess.Process,
    process_name: str,
    route_id: str,
) -> None:
    if process.stdout is None:
        return

    chunk_size = 4096
    max_partial_line = 64 * 1024
    buffer = ""

    while True:
        raw = await process.stdout.read(chunk_size)
        if not raw:
            break

        buffer += raw.decode(errors="replace")

        while "\n" in buffer:
            line, buffer = buffer.split("\n", 1)
            logger.info("[%s] route=%s %s", process_name, route_id, line.rstrip("\r"))

        if len(buffer) > max_partial_line:
            logger.info(
                "[%s] route=%s %s ... [long line truncated]",
                process_name,
                route_id,
                buffer[:1024].rstrip("\r"),
            )
            buffer = ""

    if buffer:
        logger.info("[%s] route=%s %s", process_name, route_id, buffer.rstrip("\r"))


async def _force_stop_process(process: asyncio.subprocess.Process | None) -> None:
    if process is None or process.returncode is not None:
        return

    try:
        pgid = os.getpgid(process.pid)
        os.killpg(pgid, signal.SIGKILL)
    except ProcessLookupError:
        return
    except Exception:
        process.kill()

    try:
        await asyncio.wait_for(process.wait(), timeout=5.0)
    except asyncio.TimeoutError:
        pass


async def _mark_stale_downloading_routes_as_failed(route_service: RouteService) -> None:
    stale_routes = await route_service.get_routes_by_status(status=RouteStatus.DOWNLOADING)
    if not stale_routes:
        return

    for route in stale_routes:
        await route_service.set_status(route.route_id, RouteStatus.FAILED)
        logger.warning("Marked stale route as failed on startup: route=%s", route.route_id)


async def _process_route(
    route: Route,
    route_service: RouteService,
    session: AsyncSession,
) -> None:
    output_dir = DATA_ROOT / uuid4().hex
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info("Picked route=%s output_dir=%s", route.route_id, output_dir)

    try:
        logger.info("Setting status DOWNLOADING for route=%s", route.route_id)
        await route_service.set_status(route.route_id, RouteStatus.DOWNLOADING)
        await session.commit()
        logger.info("Committed status DOWNLOADING for route=%s", route.route_id)
    except RouteNotFoundError:
        await session.rollback()
        logger.warning("Route disappeared before processing start: route=%s", route.route_id)
        return

    extraction_process: asyncio.subprocess.Process | None = None
    replay_process: asyncio.subprocess.Process | None = None
    extraction_stream_task: asyncio.Task[None] | None = None
    replay_stream_task: asyncio.Task[None] | None = None
    extraction_exit_code: int | None = None

    try:
        extraction_process = await _start_extraction_process(output_dir)
        logger.info(
            "Started extraction for route=%s pid=%s",
            route.route_id,
            extraction_process.pid,
        )
        extraction_stream_task = asyncio.create_task(
            _stream_process_output(extraction_process, "extract", route.route_id)
        )

        replay_process = await _start_replay_process(route.route_id)
        logger.info(
            "Started replay for route=%s pid=%s",
            route.route_id,
            replay_process.pid,
        )
        replay_stream_task = asyncio.create_task(
            _stream_process_output(replay_process, "replay", route.route_id)
        )

        extraction_exit_code = await extraction_process.wait()
        logger.info(
            "Extraction exited for route=%s code=%s",
            route.route_id,
            extraction_exit_code,
        )
        if extraction_exit_code != 0:
            raise RuntimeError(
                f"extraction exited with code {extraction_exit_code} "
                f"for route {route.route_id}"
            )

        file_count, file_sample = _output_dir_snapshot(output_dir)
        logger.info(
            "Output snapshot before save route=%s dir=%s file_count=%s sample=%s",
            route.route_id,
            output_dir,
            file_count,
            file_sample,
        )
        logger.info("Saving file_path for route=%s path=%s", route.route_id, output_dir)
        await route_service.set_file_path(route.route_id, str(output_dir))
        logger.info("Setting status UPLOAD_QUEUE for route=%s", route.route_id)
        await route_service.set_status(route.route_id, RouteStatus.UPLOAD_QUEUE)
        await session.commit()
        route_after_save = await route_service.get_route(route.route_id)
        logger.info(
            "Committed route update route=%s status=%s file_path=%s",
            route.route_id,
            route_after_save.status if route_after_save is not None else None,
            route_after_save.file_path if route_after_save is not None else None,
        )
    except RouteNotFoundError:
        await session.rollback()
        logger.warning("Route missing during finalize: route=%s", route.route_id)
    except Exception as exc:
        logger.exception("Route failed route=%s error=%s", route.route_id, exc)
        try:
            logger.info("Setting status FAILED for route=%s", route.route_id)
            await route_service.set_status(route.route_id, RouteStatus.FAILED)
            await session.commit()
            logger.info("Committed status FAILED for route=%s", route.route_id)
        except RouteNotFoundError:
            await session.rollback()
            logger.warning("Route removed before FAILED update: route=%s", route.route_id)
    finally:
        await _force_stop_process(replay_process)
        await _force_stop_process(extraction_process)

        if extraction_stream_task is not None:
            await extraction_stream_task
        if replay_stream_task is not None:
            await replay_stream_task


async def main():
    engine = create_async_engine(build_database_url(), pool_pre_ping=True)
    SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)
    stop_event = asyncio.Event()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop_event.set)

    try:
        async with SessionLocal() as session:
            route_repository = RouteRepository(session=session)
            route_service = RouteService(route_repository=route_repository)

            await _mark_stale_downloading_routes_as_failed(route_service)
            await session.commit()

            while not stop_event.is_set():
                route_to_process = await route_service.get_next_route_by_status(
                    status=RouteStatus.DOWNLOAD_QUEUE
                )
                if route_to_process is None:
                    await session.rollback()
                    await asyncio.sleep(POLL_INTERVAL_SECONDS)
                    continue

                await _process_route(route_to_process, route_service, session)

            logger.info("Stop event received, shutting down worker")
    finally:
        await engine.dispose()
        logger.info("Worker shutdown complete")


if __name__ == "__main__":
    asyncio.run(main())
