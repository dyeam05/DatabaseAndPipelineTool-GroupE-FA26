import asyncio
import logging
import time

import docker
from docker.errors import APIError, NotFound
from fastapi import APIRouter, HTTPException, status

logger = logging.getLogger(__name__)

cvat_router = APIRouter(prefix="/cvat")

CVAT_CONTAINER_NAME = "cvat_server"
RESTART_TIMEOUT_SECONDS = 10


def _restart_container() -> None:
    client = docker.from_env()
    container = client.containers.get(CVAT_CONTAINER_NAME)
    container.restart(timeout=RESTART_TIMEOUT_SECONDS)


@cvat_router.post("/restart")
async def restart_cvat_server() -> dict[str, object]:
    logger.info("Restarting %s container", CVAT_CONTAINER_NAME)
    started = time.monotonic()

    try:
        await asyncio.to_thread(_restart_container)
    except NotFound:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Container '{CVAT_CONTAINER_NAME}' not found",
        )
    except APIError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Docker API error while restarting CVAT: {exc}",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Unable to reach Docker daemon: {exc}",
        )

    return {
        "status": "restarted",
        "elapsed_seconds": round(time.monotonic() - started, 1),
    }
