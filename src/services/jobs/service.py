import logging
from typing import Any
from uuid import uuid4

from src.services.jobs.schemas import Job
from src.services.jobs.enums import JobStatus


logger = logging.getLogger(__name__)


class JobManager:
    def __init__(self):
        """In-memory manager for background jobs with optional idempotency keys."""
        self._jobs: dict[str, Job] = {}
        self._keys: dict[str, str] = {}

    def create(
        self,
        key: str | None = None,
    ) -> tuple[Job, bool]:
        """
        Return (job, created_flag). If key exists, return existing without creating.
        Background task scheduling is handled by the caller.
        """
        
        if existing_job := self._get_job_by_key(key):
            return existing_job, False

        job = self._make_new_job()

        if key:
            self._keys[key] = job.id

        return job, True

    def _make_new_job(self) -> Job:
        """Create and store a new pending job."""

        job_id = str(uuid4())
        job = Job(id=job_id, status=JobStatus.pending)

        self._jobs[job.id] = job

        return job

    def _get_job_by_key(self, key: str | None) -> Job | None:
        """Return an existing job associated with the idempotency key, if any."""

        if not key:
            return None

        job_id = self._keys.get(key)

        return self._jobs.get(job_id) if job_id else None

    def set_status(self, job: Job) -> None:
        """Replace a stored job with the provided instance."""

        if job.id in self._jobs:
            self._jobs[job.id] = job.model_copy()

    def update_status(
        self,
        job_id: str,
        status: JobStatus,
        detail: str = "",
        result: Any = None,
        started_at: str | None = None,
        finished_at: str | None = None,
        duration_seconds: float | None = None,
        total_tasks: int | None = None,
    ) -> None:
        """Update fields for an existing job by id."""

        if job_id not in self._jobs:
            logger.warning("Job %s not found in jobs", job_id)
            return

        job = self._jobs[job_id].model_copy()
        job.status = status
        job.detail = detail
        job.result = result

        if started_at:
            job.started_at = started_at

        if finished_at:
            job.finished_at = finished_at

        if duration_seconds is not None:
            job.duration_seconds = duration_seconds

        if total_tasks is not None:
            job.total_tasks = total_tasks

        self._jobs[job_id] = job

        match status:
            case JobStatus.running:
                logger.info("Job %s running", job_id)
            case JobStatus.completed:
                logger.info("Job %s completed in %.3fs. detail=%s", job_id, duration_seconds or 0.0, detail)
            case JobStatus.failed:
                logger.error("Job %s failed. detail=%s", job_id, detail)
            case JobStatus.pending:
                logger.info("Job %s pending", job_id)
            case _:
                logger.info("Job %s status=%s detail=%s", job_id, status, detail)

    def get(self, job_id: str) -> Job | None:
        """Retrieve a job by id."""

        return self._jobs.get(job_id)

    def list(self) -> list[Job]:
        """List all jobs."""

        return list(self._jobs.values())
