import logging
import time
from datetime import datetime, timezone
from fastapi import BackgroundTasks

from src.modules.enrichment.schemas import (
    EnrichedProduct,
    EnrichmentRequest,
    JobDetailResponse,
    JobEnqueueResponse,
    JobSummaryResponse,
)
from src.modules.enrichment.db.repository import EnrichedProductsRepository
from src.services.llm.base import LLMService
from src.services.llm.gemini import GeminiRateLimitError
from src.services.mercadolibre import MeliExtractError, MeliExtractService
from src.services.jobs import Job, job_manager, JobStatus


logger = logging.getLogger(__name__)


class EnrichmentService:
    """Orchestrates enrichment jobs for MercadoLibre item descriptions."""

    job_manager = job_manager

    def __init__(
        self,
        llm_client: LLMService,
        meli_service: MeliExtractService,
        products_repo: EnrichedProductsRepository | None = None,
    ) -> None:
        self.llm_client = llm_client
        self.meli_service = meli_service
        self.products_repo = products_repo or EnrichedProductsRepository()

    def _build_prompt(self, item: dict, tone: str, max_words: int) -> str:
        """Build a concise prompt for the LLM."""

        attrs = item.get("attributes", [])
        brand = next(
            (a.get("value_name") for a in attrs if a.get("id") == "BRAND"), None
        )
        model = next(
            (a.get("value_name") for a in attrs if a.get("id") == "MODEL"), None
        )
        color = next(
            (
                a.get("value_name")
                for a in attrs
                if a.get("id") in {"COLOR", "MAIN_COLOR"}
            ),
            None,
        )
        spec_line = ", ".join(
            filter(None, [f"brand: {brand}", f"model: {model}", f"color: {color}"])
        )
        source_desc = item.get("description", "")[:400]
        return (
            "Generate a concise, factual product description for an e-commerce listing. "
            f"Tone: {tone}. Limit to {max_words} words. Avoid exaggeration. "
            "Respond strictly in Spanish. "
            f"Specs: {spec_line}. "
            f"Source description (trimmed): {source_desc}"
        )

    def enrich(self, job: Job, payload: EnrichmentRequest) -> None:
        """Enqueue an enrichment job and schedule processing."""

        try:
            self._check_models(payload.model)

            started = datetime.now(timezone.utc).isoformat()

            job_manager.update_status(
                job.id,
                JobStatus.running,
                detail="Processing",
                started_at=started,
                total_tasks=len(payload.item_ids),
            )

            start_time = time.perf_counter()

            enriched, errors = self._enrich_from_ids(
                item_ids=payload.item_ids,
                tone=payload.tone,
                max_words=payload.max_words,
            )

            duration_seconds = time.perf_counter() - start_time

            if not enriched:
                job_manager.update_status(
                    job.id,
                    JobStatus.failed,
                    detail="No items enriched",
                    result={"errors": errors},
                    finished_at=datetime.now(timezone.utc).isoformat(),
                    duration_seconds=duration_seconds,
                )
                return

            finished = datetime.now(timezone.utc).isoformat()

            job_manager.update_status(
                job.id,
                JobStatus.completed,
                result=enriched,
                finished_at=finished,
                duration_seconds=duration_seconds,
            )

        except GeminiRateLimitError as e:
            duration_seconds = time.perf_counter() - start_time

            job_manager.update_status(
                job.id,
                JobStatus.failed,
                detail=f"Gemini quota exceeded. Retry after {getattr(e, 'retry_after_seconds', 'unknown')}s",
                finished_at=datetime.now(timezone.utc).isoformat(),
                duration_seconds=duration_seconds,
                result={"errors": [{"message": str(e)}]},
            )

            logger.error(
                "Enrichment job %s failed (rate limit) in %.3fs: %s",
                job.id,
                duration_seconds,
                e,
            )

        except ValueError as e:
            job_manager.update_status(
                job.id,
                JobStatus.failed,
                detail=str(e),
                finished_at=datetime.now(timezone.utc).isoformat(),
                duration_seconds=0.0,
            )
            logger.error("Enrichment job %s failed: %s", job.id, e)
        except Exception as e:
            duration_seconds = time.perf_counter() - start_time

            job_manager.update_status(
                job.id,
                JobStatus.failed,
                detail=str(e),
                finished_at=datetime.now(timezone.utc).isoformat(),
                duration_seconds=duration_seconds,
            )

            logger.error(
                "Enrichment job %s failed in %.3fs: %s",
                job.id,
                duration_seconds,
                e,
            )

    def _check_models(self, model_name: str) -> None:
        available_models = self.list_models()
        normalized = model_name
        prefixed = f"models/{normalized}" if not normalized.startswith("models/") else normalized

        if normalized not in available_models and prefixed not in available_models:
            logger.warning("Model '%s' not available", model_name)
            raise ValueError(f"Model '{model_name}' not available", available_models)

    def list_models(self) -> list[str]:
        """List available LLM models."""

        return self.llm_client.list_models()
    
    def _enrich_from_ids(
        self, item_ids: list[str], tone: str = "", max_words: int = 60
    ) -> tuple[list[dict], list[dict]]:
        """Fetch descriptions from MELI and enrich them with the LLM."""

        items: list[dict] = []
        errors: list[dict] = []

        for item_id in item_ids:
            item: dict = {"id": item_id, "description": ""}

            try:
                description = self.meli_service.extract_item_description(item_id)
                item["description"] = description.get("plain_text") or description.get("text") or ""

                logger.info("Fetched description for item %s", item_id)

            except MeliExtractError as e:
                errors.append({"id": item_id, "error": str(e)})
                logger.warning("No description found for item %s: %s", item_id, e)
                continue

            items.append(item)

        enriched: list[dict] = []
        for item in items:
            prompt = self._build_prompt(item, tone=tone, max_words=max_words)

            enriched_description = self.llm_client.generate(prompt)

            logger.info("Enriched item %s", item.get("id", ""))

            enriched.append(
                {
                    "item_id": item.get("id", ""),
                    "original_description": item.get("description", ""),
                    "enriched_description": enriched_description,
                    "created_at": datetime.utcnow().isoformat(),
                }
            )

        if enriched:
            self.products_repo.insert_many(enriched)
            logger.info("Persisted %d enriched items to database", len(enriched))

        return enriched, errors

    def load_last_enriched(self) -> list[dict]:
        """Return all enriched items from the repository."""
        
        items = self.products_repo.list()

        return [item.model_dump() for item in items]

    def list_enrichments(self) -> list[JobSummaryResponse]:
        """Return job summaries for enrichment jobs."""

        return [
            JobSummaryResponse(
                id=j.id,
                status=j.status,
                detail=j.detail,
                started_at=j.started_at,
                finished_at=j.finished_at,
                duration_seconds=j.duration_seconds,
                total_tasks=j.total_tasks,
            )
            for j in job_manager.list()
        ]

    def get_enrichment(self, job_id: str) -> JobDetailResponse | None:
        """Return a full job detail by id."""

        job = job_manager.get(job_id)

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

    
