import asyncio
from concurrent.futures import ThreadPoolExecutor
from enum import Enum
from dataclasses import dataclass, field
from typing import Any
import time
import uuid

from lib.route_logger import log_route


class JobStatus(str, Enum):
    queued = "queued"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"
    canceled = "canceled"

@dataclass
class Job:
    id: str
    route_id: str
    created_at: float = field(default_factory=time.time)
    status: JobStatus = JobStatus.queued
    result: Any | None = None
    error: str | None  = None




class RouteLoggerService:
    def __init__(self):
        self._queue: asyncio.Queue[str] = asyncio.Queue()
        self._jobs: dict[str, Job] = {}
        self._lock = asyncio.Lock()
        self._runner_task: asyncio.Task | None = None
        self._current_job_id: str | None = None

        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="route-logger-worker")

    async def start(self) -> None:
        if self._runner_task is None:
            self._runner_task = asyncio.create_task(self._runner_loop())

    async def stop(self) -> None:
        if self._runner_task:
            self._runner_task.cancel()
            try:
                await self._runner_task
            except asyncio.CancelledError:
                pass
            self._runner_task = None
        self._executor.shutdown(wait=False, cancel_futures=True)

    async def enqueue(self, route_id: str) -> Job:
        job_id = uuid.uuid4().hex
        job = Job(id=job_id, route_id=route_id)
        async with self._lock:
            self._jobs[job_id] = job
        await self._queue.put(job_id)
        return job

    async def get(self, job_id: str) -> Job:
        async with self._lock:
            job = self._jobs.get(job_id)
        if not job:
            raise KeyError(job_id)
        return job

    async def cancel(self, job_id: str) -> None:
        async with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                raise KeyError(job_id)
            if job.status == JobStatus.running:
                raise Exception(f"Can not cancel job with job id {job_id} because it is running")
            job.status = JobStatus.canceled

    async def _runner_loop(self) -> None:
        while True:
            job_id = await self._queue.get()
            try:
                async with self._lock:
                    job = self._jobs.get(job_id)
                    if not job:
                        continue
                    if job.status == JobStatus.canceled:
                        continue
                    job.status = JobStatus.running
                    self._current_job_id = job_id

                loop = asyncio.get_running_loop()
                result: str = await loop.run_in_executor(
                    self._executor,
                    self._run_blocking, 
                    job.route_id
                )

                async with self._lock:
                    job = self._jobs.get(job_id)
                    if job and job.status != JobStatus.canceled:
                        job.status = JobStatus.succeeded
                        job.result = result

            except Exception as e:
                async with self._lock:
                    job = self._jobs.get(job_id)
                    if job and job.status != JobStatus.canceled:
                        job.status = JobStatus.failed
                        job.error = str(e)
            finally:
                async with self._lock:
                    if self._current_job_id == job_id:
                        self._current_job_id = None
                    self._queue.task_done()

    def _run_blocking(self, route_id: str) -> str:
        return log_route(route=route_id)

    async def get_jobs(self):
        async with self._lock:
            jobs = list(self._jobs.values())

        return jobs

                    

