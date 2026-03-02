import asyncio
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import time
import uuid

from lib.models.pipeline_job_models import (
    PipelineJob,
    PipelineJobStatus,
    PipelineStage,
    SegmentUploadRecord,
    SegmentUploadStatus,
)
from lib.utils.route_logger_utils import log_route
from lib.utils.segment_uploader_utils import (
    list_segments_for_upload,
    post_route_upload_finalize,
    pre_route_upload_init,
    upload_segment,
)


class PipelineJobService:
    def __init__(
        self,
        max_segment_retries: int = 3,
        segment_upload_concurrency: int = 4,
    ):
        if max_segment_retries < 1:
            raise ValueError("max_segment_retries must be >= 1")
        if segment_upload_concurrency < 1:
            raise ValueError("segment_upload_concurrency must be >= 1")

        self._max_segment_retries = max_segment_retries
        self._segment_upload_concurrency = segment_upload_concurrency
        self._logging_queue: asyncio.Queue[str] = asyncio.Queue()
        self._jobs: dict[str, PipelineJob] = {}
        self._lock = asyncio.Lock()
        self._cancel_requested: set[str] = set()
        self._logging_runner_task: asyncio.Task | None = None
        self._upload_tasks: dict[str, asyncio.Task] = {}
        self._logging_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="pipeline-log-worker")
        self._upload_executor = ThreadPoolExecutor(
            max_workers=max(4, segment_upload_concurrency),
            thread_name_prefix="pipeline-upload-worker",
        )

    async def start(self) -> None:
        if self._logging_runner_task is None:
            self._logging_runner_task = asyncio.create_task(self._logging_runner_loop())

    async def stop(self) -> None:
        if self._logging_runner_task:
            self._logging_runner_task.cancel()
            try:
                await self._logging_runner_task
            except asyncio.CancelledError:
                pass

        async with self._lock:
            upload_tasks = list(self._upload_tasks.values())
            self._upload_tasks.clear()

        for task in upload_tasks:
            task.cancel()
        if upload_tasks:
            await asyncio.gather(*upload_tasks, return_exceptions=True)

        self._logging_runner_task = None
        self._logging_executor.shutdown(wait=False, cancel_futures=True)
        self._upload_executor.shutdown(wait=False, cancel_futures=True)

    async def enqueue(self, route_id: str) -> PipelineJob:
        job_id = uuid.uuid4().hex
        job = PipelineJob(id=job_id, route_id=route_id)
        async with self._lock:
            self._jobs[job_id] = job
        await self._logging_queue.put(job_id)
        return job

    async def get(self, job_id: str) -> PipelineJob:
        async with self._lock:
            job = self._jobs.get(job_id)
        if job is None:
            raise KeyError(job_id)
        return job

    async def get_jobs(self) -> list[PipelineJob]:
        async with self._lock:
            return list(self._jobs.values())

    async def cancel(self, job_id: str) -> None:
        async with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                raise KeyError(job_id)
            if job.status == PipelineJobStatus.uploading:
                self._cancel_requested.add(job_id)
                self._touch(job)
                return
            job.status = PipelineJobStatus.canceled
            job.stage = PipelineStage.finished
            self._touch(job)

    async def remove_job(self, job_id: str) -> None:
        async with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                raise KeyError(job_id)
            if job.status in (
                PipelineJobStatus.queued,
                PipelineJobStatus.logging,
                PipelineJobStatus.uploading,
            ):
                raise ValueError(f"Cannot remove job {job_id} while it is {job.status}")
            del self._jobs[job_id]

    async def _logging_runner_loop(self) -> None:
        while True:
            job_id = await self._logging_queue.get()
            try:
                await self._run_logging_stage(job_id)
            finally:
                self._logging_queue.task_done()

    async def _run_logging_stage(self, job_id: str) -> None:
        async with self._lock:
            job = self._jobs.get(job_id)
            if job is None or job.status == PipelineJobStatus.canceled:
                return
            job.status = PipelineJobStatus.logging
            job.stage = PipelineStage.logging
            self._touch(job)

        try:
            loop = asyncio.get_running_loop()
            output_dir: str = await loop.run_in_executor(
                self._logging_executor,
                self._run_blocking_logging,
                job.route_id,
            )

            async with self._lock:
                job = self._jobs.get(job_id)
                if job is None or job.status == PipelineJobStatus.canceled:
                    return
                job.output_dir = output_dir
                job.status = PipelineJobStatus.uploading
                job.stage = PipelineStage.uploading_init
                self._touch(job)
                route_id = job.route_id

            task = asyncio.create_task(self._run_upload_pipeline(job_id, route_id, output_dir))
            async with self._lock:
                self._upload_tasks[job_id] = task
        except Exception as error:
            async with self._lock:
                job = self._jobs.get(job_id)
                if job is not None and job.status != PipelineJobStatus.canceled:
                    job.status = PipelineJobStatus.failed
                    job.stage = PipelineStage.finished
                    job.error = str(error)
                    self._touch(job)

    async def _run_upload_pipeline(self, job_id: str, route_id: str, output_dir: str) -> None:
        try:
            pre_route_upload_init(route_id=route_id, output_dir=output_dir)

            async with self._lock:
                job = self._jobs.get(job_id)
                if job is None:
                    return
                job.stage = PipelineStage.uploading_segments
                self._touch(job)

            segment_paths = list_segments_for_upload(output_dir)
            async with self._lock:
                job = self._jobs.get(job_id)
                if job is None:
                    return
                job.segments = [
                    SegmentUploadRecord(
                        segment_id=path.name,
                        max_attempts=self._max_segment_retries,
                    )
                    for path in segment_paths
                ]
                self._touch(job)

            await self._run_parallel_segment_uploads(job_id, route_id, segment_paths)

            async with self._lock:
                job = self._jobs.get(job_id)
                if job is None:
                    return
                canceled = job_id in self._cancel_requested
                if canceled:
                    job.status = PipelineJobStatus.canceled
                    job.stage = PipelineStage.finished
                    self._touch(job)
                    return

                job.stage = PipelineStage.uploading_finalize
                self._touch(job)

            summary = await self._segment_summary(job_id)
            post_route_upload_finalize(
                route_id=route_id,
                output_dir=output_dir,
                segment_summary=summary,
            )

            async with self._lock:
                job = self._jobs.get(job_id)
                if job is None:
                    return
                failed_count = summary["failed"]
                success_count = summary["succeeded"]
                if failed_count == 0:
                    job.status = PipelineJobStatus.completed
                elif success_count > 0:
                    job.status = PipelineJobStatus.partial_failed
                else:
                    job.status = PipelineJobStatus.failed
                job.stage = PipelineStage.finished
                self._touch(job)
        except Exception as error:
            async with self._lock:
                job = self._jobs.get(job_id)
                if job is not None and job.status != PipelineJobStatus.canceled:
                    job.status = PipelineJobStatus.failed
                    job.stage = PipelineStage.finished
                    job.error = str(error)
                    self._touch(job)
        finally:
            async with self._lock:
                self._upload_tasks.pop(job_id, None)
                self._cancel_requested.discard(job_id)

    async def _run_parallel_segment_uploads(
        self,
        job_id: str,
        route_id: str,
        segment_paths: list[Path],
    ) -> None:
        queue: asyncio.Queue[tuple[int, Path]] = asyncio.Queue()
        for index, path in enumerate(segment_paths):
            queue.put_nowait((index, path))

        worker_count = min(self._segment_upload_concurrency, len(segment_paths))
        if worker_count == 0:
            return

        async def worker() -> None:
            while True:
                try:
                    segment_index, segment_path = queue.get_nowait()
                except asyncio.QueueEmpty:
                    return

                try:
                    if await self._is_cancel_requested(job_id):
                        return

                    async with self._lock:
                        job = self._jobs.get(job_id)
                        if job is None:
                            return
                        segment = job.segments[segment_index]
                        segment.status = SegmentUploadStatus.uploading
                        self._touch(job)

                    await self._upload_one_segment_with_retries(
                        job_id=job_id,
                        route_id=route_id,
                        segment_path=segment_path,
                        segment_index=segment_index,
                    )
                finally:
                    queue.task_done()

        workers = [asyncio.create_task(worker()) for _ in range(worker_count)]
        await asyncio.gather(*workers)

    async def _upload_one_segment_with_retries(
        self,
        job_id: str,
        route_id: str,
        segment_path: Path,
        segment_index: int,
    ) -> None:
        for _ in range(self._max_segment_retries):
            async with self._lock:
                job = self._jobs.get(job_id)
                if job is None:
                    return
                segment = job.segments[segment_index]
                segment.attempts += 1
                self._touch(job)

            try:
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(
                    self._upload_executor,
                    self._run_blocking_segment_upload,
                    route_id,
                    segment_path,
                )
                async with self._lock:
                    job = self._jobs.get(job_id)
                    if job is None:
                        return
                    segment = job.segments[segment_index]
                    segment.status = SegmentUploadStatus.succeeded
                    segment.error = None
                    self._touch(job)
                return
            except Exception as error:
                async with self._lock:
                    job = self._jobs.get(job_id)
                    if job is None:
                        return
                    segment = job.segments[segment_index]
                    segment.error = str(error)
                    self._touch(job)

        async with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return
            segment = job.segments[segment_index]
            segment.status = SegmentUploadStatus.failed
            self._touch(job)

    async def _segment_summary(self, job_id: str) -> dict[str, int]:
        async with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return {"succeeded": 0, "failed": 0, "total": 0}
            succeeded = len(
                [segment for segment in job.segments if segment.status == SegmentUploadStatus.succeeded]
            )
            failed = len([segment for segment in job.segments if segment.status == SegmentUploadStatus.failed])
            total = len(job.segments)
            return {"succeeded": succeeded, "failed": failed, "total": total}

    async def _is_cancel_requested(self, job_id: str) -> bool:
        async with self._lock:
            return job_id in self._cancel_requested

    def _run_blocking_logging(self, route_id: str) -> str:
        return log_route(route=route_id)

    def _run_blocking_segment_upload(self, route_id: str, segment_path: Path):
        return upload_segment(route_id=route_id, dir_path=segment_path)

    def _touch(self, job: PipelineJob) -> None:
        job.updated_at = time.time()
