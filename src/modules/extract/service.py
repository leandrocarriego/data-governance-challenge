import logging
import time
from datetime import datetime, timezone

from src.modules.extract.schemas import (
    ItemDescriptionsRequest,
    JobDetailResponse,
    JobSummaryResponse,
)
from src.services.jobs import Job, job_manager, JobStatus
from src.services.mercadolibre import MeliExtractService, MeliExtractError


logger = logging.getLogger(__name__)


class ExtractService:
    """Orchestrates extraction jobs for MercadoLibre item descriptions."""

    job_manager = job_manager

    def __init__(self, meli_service: MeliExtractService) -> None:
        self.meli_service = meli_service

    def extract(self, job: Job, payload: ItemDescriptionsRequest) -> None:
        """Create or reuse a job and enqueue the background task."""

        started = datetime.now(timezone.utc).isoformat()

        self.job_manager.update_status(
            job.id,
            JobStatus.running,
            detail="Processing descriptions",
            started_at=started,
            total_tasks=len(payload.item_ids),
        )

        start_time = time.perf_counter()

        results: list[dict] = []
        for item_id in payload.item_ids:
            try:
                description = self.meli_service.extract_item_description(item_id)
                results.append(
                    {
                        "id": item_id,
                        "description": description.get("plain_text")
                        or description.get("text", ""),
                    }
                )

            except MeliExtractError as e:
                results.append({"id": item_id, "error": str(e)})

        duration_seconds = time.perf_counter() - start_time
        finished = datetime.now(timezone.utc).isoformat()
        errors_count = len([r for r in results if "error" in r])
        success_count = len(results) - errors_count
        detail = f"Completed successfully. processed={len(results)} success={success_count} errors={errors_count}"

        self.job_manager.update_status(
            job.id,
            JobStatus.completed,
            detail=detail,
            result=results,
            finished_at=finished,
            duration_seconds=duration_seconds,
        )

    def list_extractions(self) -> list[JobSummaryResponse]:
        """Return audit-friendly list of extraction jobs."""

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
            for job in self.job_manager.list()
        ]

    def get_extraction(self, job_id: str) -> JobDetailResponse | None:
        """Retrieve a single extraction job with full details."""

        job = self.job_manager.get(job_id)

        if not job:
            return None

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
