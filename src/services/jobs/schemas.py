from typing import Any

from pydantic import BaseModel

from src.services.jobs.enums import JobStatus


class Job(BaseModel):
    """Representation of a queued background job."""

    id: str
    status: JobStatus = JobStatus.pending
    detail: str = ""
    result: Any = None
    started_at: str | None = None
    finished_at: str | None = None
    duration_seconds: float | None = None
    total_tasks: int | None = None

    model_config = {
        "extra": "ignore",
    }
