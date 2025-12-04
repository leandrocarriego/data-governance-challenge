import logging

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Query

from src.modules.enrichment.schemas import (
    EnrichmentRequest,
    EnrichedProduct,
    EnrichedProductListResponse,
    JobDetailResponse,
    JobEnqueueResponse,
    JobSummaryResponse,
)
from src.modules.enrichment.dependencies import get_products_repo
from src.modules.enrichment.service import EnrichmentService
from src.modules.enrichment.db import EnrichedProductsRepository
from src.services.jobs import job_manager
from src.services.llm.schemas import LLMConfig
from src.services.llm.gemini import GeminiService
from src.services.mercadolibre import MeliExtractService
from src.settings import settings


router = APIRouter(prefix="/enrichment", tags=["enrichment"])
logger = logging.getLogger(__name__)


def build_service(model: str, repository: EnrichedProductsRepository | None = None) -> EnrichmentService:
    """Factory that wires Gemini + MELI + repo into an EnrichmentService."""
    config = LLMConfig(api_key=settings.gemini_api_key, model=model)
    client = GeminiService(config=config)

    return EnrichmentService(llm_client=client, meli_service=MeliExtractService(), products_repo=repository)


@router.post("/run", response_model=JobEnqueueResponse)
def run_enrichment(
    payload: EnrichmentRequest,
    background_tasks: BackgroundTasks,
    idempotency_key: str | None = Header(default=None, convert_underscores=False, alias="Idempotency-Key"),
    products_repository: EnrichedProductsRepository = Depends(get_products_repo),
) -> JobEnqueueResponse:
    """Enqueue an enrichment job."""

    try:
        enrichment_service = build_service(payload.model, products_repository)
        enrichment_service._check_models(payload.model)

        job, created = job_manager.create(key=idempotency_key)
        if not created:
            return JobEnqueueResponse(
                job_id=job.id, status=job.status, message="Request already enqueued."
            )

        background_tasks.add_task(enrichment_service.enrich, job, payload)

        return JobEnqueueResponse(
            job_id=job.id, status=job.status, message="Request enqueued successfully"
        )
    
    except ValueError as e:
        message, *rest = e.args
        available = rest[0] if rest else []
        logger.error("Validation error enqueuing enrichment job: %s", e)
        raise HTTPException(
            status_code=400,
            detail={"message": message, "available_models": available},
        ) from e
    except Exception as e:
        logger.exception("Unexpected error enqueuing enrichment job")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/models")
def list_llm_models() -> dict[str, list[str]]:
    """List available LLM models for enrichment."""

    service = build_service(settings.gemini_model)

    try:
        return {"models": service.list_models()}
    
    except Exception as e:
        logger.exception("Failed to list LLM models")
        raise HTTPException(status_code=500, detail=f"Failed to list LLM models: {e}") from e


@router.get("/jobs", response_model=list[JobSummaryResponse])
def list_jobs() -> list[JobSummaryResponse]:
    """List enrichment jobs audit fields."""

    try:
        return [
            JobSummaryResponse(
                id=job.id,
                status=job.status,
                detail=job.detail,
                started_at=job.started_at,
                finished_at=job.finished_at,
                duration_seconds=job.duration_seconds,
                total_tasks=job.total_tasks,
            )
            for job in job_manager.list()
        ]
    
    except Exception as e:
        logger.exception("Failed to list enrichment jobs")
        raise HTTPException(status_code=500, detail="Failed to list enrichment jobs") from e


@router.get("/jobs/{job_id}", response_model=JobDetailResponse)
def get_job(job_id: str) -> JobDetailResponse:
    """Retrieve a single enrichment job by id."""
    
    try:
        job = job_manager.get(job_id)

        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return JobDetailResponse(
            id=job.id,
            status=job.status,
            detail=job.detail,
            result=job.result,
            started_at=job.started_at,
            finished_at=job.finished_at,
            duration_seconds=job.duration_seconds,
            total_tasks=job.total_tasks,
        )

    except Exception as e:
        logger.exception("Failed to get enrichment job %s", job_id)
        raise HTTPException(status_code=500, detail="Failed to fetch job") from e


@router.get("/enriched", response_model=EnrichedProductListResponse)
def list_enriched_products(
    q: str | None = Query(None, description="Full-text search in original/enriched description"),
    created_from: str | None = Query(None, description="Filter by created_at >= ISO date"),
    created_to: str | None = Query(None, description="Filter by created_at <= ISO date"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    products_repository: EnrichedProductsRepository = Depends(get_products_repo),
) -> EnrichedProductListResponse:
    """Search enriched products with filters and pagination."""

    try:
        items, total = products_repository.search(q=q, created_from=created_from, created_to=created_to, limit=limit, offset=offset)
        
        return EnrichedProductListResponse(count=total, items=items)
    
    except Exception as e:
        logger.exception("Failed to fetch enriched products")
        raise HTTPException(status_code=500, detail="Failed to fetch enriched products") from e


@router.get("/enriched/{item_id}", response_model=EnrichedProduct)
def get_enriched_product(item_id: str, products_repository: EnrichedProductsRepository = Depends(get_products_repo)) -> EnrichedProduct:
    """Get a single enriched product by item_id."""

    try:
        item = products_repository.get(item_id)

        if not item:
            raise HTTPException(status_code=404, detail=f"Enriched product {item_id} not found")
        
        return item

    except Exception as e:
        logger.exception("Failed to fetch enriched product %s", item_id)
        raise HTTPException(status_code=500, detail="Failed to fetch enriched product") from e
