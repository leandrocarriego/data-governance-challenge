import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Header
from fastapi.exceptions import RequestValidationError

from src.modules.extract.dependencies import get_extract_service
from src.modules.extract.schemas import (
    ItemDescriptionsRequest,
    JobEnqueueResponse,
    JobDetailResponse,
    JobSummaryResponse,
)
from src.modules.extract.service import ExtractService
from src.services.mercadolibre import MeliExtractError
from src.services.jobs import job_manager


router = APIRouter(prefix="/extract", tags=["extract"])
logger = logging.getLogger(__name__)


@router.post("/items/descriptions", response_model=JobEnqueueResponse)
def extract_items_descriptions(
    payload: ItemDescriptionsRequest,
    background_tasks: BackgroundTasks,
    idempotency_key: str | None = Header(
        default=None, convert_underscores=False, alias="Idempotency-Key"
    ),
    extract_service: ExtractService = Depends(get_extract_service),
) -> JobEnqueueResponse:
    """Enqueue an extraction job for item descriptions."""

    try:
        job, created = job_manager.create(key=idempotency_key)

        if not created:
            return JobEnqueueResponse(
                job_id=job.id, status=job.status, message="Request already enqueued."
            )
        
        background_tasks.add_task(extract_service.extract, job, payload)
        
        return JobEnqueueResponse(
            job_id=job.id, status=job.status, message="Request enqueued successfully."
        )
    
    except MeliExtractError as e:
        logger.error("MELI error enqueuing extract job: %s", e)
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.exception("Unexpected error enqueuing extract job")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/jobs", response_model=list[JobSummaryResponse])
def list_extract_jobs(
    service: ExtractService = Depends(get_extract_service),
) -> list[JobSummaryResponse]:
    """List extraction jobs with audit fields."""

    try:
        return service.list_extractions()
    
    except Exception as e:
        logger.exception("Failed to list extract jobs")
        raise HTTPException(status_code=500, detail="Failed to list extract jobs") from e


@router.get("/jobs/{job_id}", response_model=JobDetailResponse)
def get_extract_job(
    job_id: str, service: ExtractService = Depends(get_extract_service)
) -> JobDetailResponse:
    """Retrieve a single extraction job by id."""

    try:
        job = service.get_extraction(job_id)

    except Exception as e:
        logger.exception("Failed to fetch extract job %s", job_id)
        raise HTTPException(status_code=500, detail="Failed to fetch job") from e

    if not job:
        logger.error("Extract job %s not found", job_id)
        raise HTTPException(status_code=404, detail="Job not found")

    return job
