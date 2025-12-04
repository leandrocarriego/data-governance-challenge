from pydantic import BaseModel, Field
from src.services.jobs.enums import JobStatus


class ItemDescriptionsRequest(BaseModel):
    item_ids: list[str] = Field(
        ...,
        min_length=1,
        description="List of item ids",
        examples=[["MLA1535410113", "MLA1462872331", "MLA2348170914", "MLA1562798377"]],
    )


class JobEnqueueResponse(BaseModel):
    job_id: str = Field(
        ...,
        description="Job identifier",
        examples=["b98ff942-9665-47ba-827e-72c2403d6ee2"],
    )
    status: JobStatus = Field(..., description="Current job status", examples=[JobStatus.pending])
    message: str = Field(
        ...,
        description="Human-readable message",
        examples=["Request enqueued successfully"],
    )


class JobSummaryResponse(BaseModel):
    id: str = Field(
        ...,
        description="Job identifier",
        examples=["b98ff942-9665-47ba-827e-72c2403d6ee2"],
    )
    status: JobStatus = Field(..., description="Current job status", examples=[JobStatus.completed])
    detail: str | None = Field(
        default=None,
        description="Summary or error message",
        examples=["Completed successfully"],
    )
    started_at: str | None = Field(
        default=None,
        description="ISO start timestamp",
        examples=["2025-12-03T19:22:29.373778+00:00"],
    )
    finished_at: str | None = Field(
        default=None,
        description="ISO finish timestamp",
        examples=["2025-12-03T19:22:30.301326+00:00"],
    )
    duration_seconds: float | None = Field(
        default=None, description="Total duration in seconds", examples=[0.93]
    )
    total_tasks: int | None = Field(
        default=None, description="Total items processed", examples=[4]
    )


class JobDetailResponse(BaseModel):
    id: str = Field(
        ...,
        description="Job identifier",
        examples=["b98ff942-9665-47ba-827e-72c2403d6ee2"],
    )
    status: JobStatus = Field(..., description="Current job status", examples=[JobStatus.completed])
    detail: str | None = Field(
        default=None,
        description="Summary or error message",
        examples=["Completed successfully"],
    )
    result: object | None = Field(
        default=None,
        description="Job payload result (list of item descriptions/errors)",
    )
    started_at: str | None = Field(
        default=None,
        description="ISO start timestamp",
        examples=["2025-12-03T19:22:29.373778+00:00"],
    )
    finished_at: str | None = Field(
        default=None,
        description="ISO finish timestamp",
        examples=["2025-12-03T19:22:30.301326+00:00"],
    )
    duration_seconds: float | None = Field(
        default=None, description="Total duration in seconds", examples=[0.93]
    )
    total_tasks: int | None = Field(
        default=None, description="Total items processed", examples=[4]
    )
