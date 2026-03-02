import asyncio
import uuid
from dataclasses import dataclass
from enum import Enum

from lib.models.segment_uploader_models import UploadJob, UploadJobStatus


class SegmentUploadingService:
    def __init__(self, worker_count: int = 4):
        if worker_count < 1:
            raise ValueError("worker_count must be >= 1")
        self._worker_count = worker_count
        self._queue: asyncio.Queue[str] = asyncio.Queue()
        self._jobs: dict[str, UploadJob] = {}
        self._lock = asyncio.Lock()
        self._runner_tasks: list[asyncio.Task] = []

    async def start(self) -> None:
        if self._runner_tasks:
            return
        self._runner_tasks = [
            asyncio.create_task(self._runner_loop(i))
            for i in range(self._worker_count)
        ]

    async def stop(self) -> None:
        for task in self._runner_tasks:
            task.cancel()
        if self._runner_tasks:
            await asyncio.gather(*self._runner_tasks, return_exceptions=True)
        self._runner_tasks = []

    async def enqueue(self, dir_path: str) -> UploadJob:
        job_id = uuid.uuid4().hex
        job = UploadJob(id=job_id, dir_path=dir_path)
        async with self._lock:
            self._jobs[job_id] = job
        await self._queue.put(job_id)
        return job

    async def get(self, job_id: str) -> UploadJob:
        async with self._lock:
            job = self._jobs.get(job_id)
        if not job:
            raise KeyError(job_id)
        return job

    async def get_jobs(self) -> list[UploadJob]:
        async with self._lock:
            return list(self._jobs.values())

    async def cancel(self, job_id: str) -> None:
        async with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                raise KeyError(job_id)
            if job.status == UploadJobStatus.running:
                raise ValueError(f"Cannot cancel running job {job_id}")
            job.status = UploadJobStatus.canceled

    async def remove_job(self, job_id: str) -> None:
        async with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                raise KeyError(job_id)
            if job.status in (UploadJobStatus.queued, UploadJobStatus.running):
                raise ValueError(f"Cannot remove job {job_id} while {job.status}")
            del self._jobs[job_id]

    async def _runner_loop(self, worker_idx: int) -> None:
        while True:
            job_id = await self._queue.get()
            try:
                async with self._lock:
                    job = self._jobs.get(job_id)
                    if not job or job.status == UploadJobStatus.canceled:
                        continue
                    job.status = UploadJobStatus.running
                    file_path = job.dir_path

                # Replace with real upload implementation
                result = await self._upload_file(file_path, worker_idx)

                async with self._lock:
                    job = self._jobs.get(job_id)
                    if job and job.status != UploadJobStatus.canceled:
                        job.status = UploadJobStatus.succeeded
                        job.result = result
            except Exception as e:
                async with self._lock:
                    job = self._jobs.get(job_id)
                    if job and job.status != UploadJobStatus.canceled:
                        job.status = UploadJobStatus.failed
                        job.error = str(e)
            finally:
                self._queue.task_done()

    async def _upload_file(self, file_path: str, worker_idx: int) -> str:
        # TODO: 
        await asyncio.sleep(0.1)
        return f"uploaded:{file_path}:worker={worker_idx}"