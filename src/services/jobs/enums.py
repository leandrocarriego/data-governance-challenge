from enum import StrEnum


class JobStatus(StrEnum):
    """Allowed states for background jobs."""

    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"
