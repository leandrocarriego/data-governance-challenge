from pydantic import BaseModel, Field


class EnrichmentRequest(BaseModel):
    """Payload to request enrichment of MercadoLibre items."""

    item_ids: list[str] = Field(
        ...,
        description="List of item ids to enrich",
        examples=[["MLA1535410113", "MLA1462872331", "MLA2348170914", "MLA1562798377"]],
    )
    tone: str = Field(default="helpful", description="Desired tone for the enriched description", examples=["helpful"])
    max_words: int = Field(default=60, ge=20, le=120, description="Maximum words for the description", examples=[60])
    model: str = Field(..., description="LLM model id", examples=["gemini-2.5-flash"])


class EnrichedProduct(BaseModel):
    """Stored enriched product."""

    id: int
    item_id: str = Field(..., description="MercadoLibre item id", examples=["MLA1535410113"])
    original_description: str = Field(..., description="Original description from MercadoLibre")
    enriched_description: str = Field(..., description="LLM-enriched description")
    created_at: str | None = Field(None, description="ISO timestamp of enrichment creation")


class EnrichedProductListResponse(BaseModel):
    """Paginated list of enriched products."""

    count: int = Field(..., description="Total items available")
    items: list[EnrichedProduct]


class JobEnqueueResponse(BaseModel):
    """Response after enqueuing a job."""

    job_id: str = Field(..., description="Job identifier")
    status: str = Field(..., description="Job status at enqueue time", examples=["pending"])
    message: str = Field(..., description="Human readable message", examples=["Request enqueued successfully"])


class JobSummaryResponse(BaseModel):
    """Summary view of a background job."""

    id: str = Field(..., description="Job identifier")
    status: str = Field(..., description="Job status", examples=["running", "completed", "failed"])
    detail: str | None = Field(None, description="Optional detail or progress note")
    started_at: str | None = Field(None, description="ISO time when the job started")
    finished_at: str | None = Field(None, description="ISO time when the job finished")
    duration_seconds: float | None = Field(None, description="Execution time in seconds")
    total_tasks: int | None = Field(None, description="Total tasks processed")


class JobDetailResponse(BaseModel):
    """Detailed job response including result payload."""

    id: str = Field(..., description="Job identifier")
    status: str = Field(..., description="Job status", examples=["completed"])
    detail: str | None = Field(None, description="Optional detail or failure reason")
    result: object | None = Field(None, description="Result payload (may be omitted)")
    started_at: str | None = Field(None, description="ISO time when the job started")
    finished_at: str | None = Field(None, description="ISO time when the job finished")
    duration_seconds: float | None = Field(None, description="Execution time in seconds")
    total_tasks: int | None = Field(None, description="Total tasks processed")
