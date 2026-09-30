"""
Data Extraction Service — Phase 4, Prompt 2

Service layer connecting MongoDB task/source documents with SourceFetcher and DataExtractor.

Pipeline:
  1. Load Task & validate AI Plan / Schema
  2. Load Source Candidate
  3. Update Source Status: discovered → fetching
  4. Fetch Source Content (SourceFetcher)
  5. Update Source Status: fetching → fetched → extracting
  6. Extract Structured Records (DataExtractor)
  7. Validate & Score Records
  8. Update Source Status: extracting → extracted (or failed)
  9. Persist Raw Extracted Records & Return
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from bson import ObjectId

from ..database.connection import get_db
from .fetcher import SourceFetcher
from .extractor import DataExtractor
from .extraction_models import ExtractionResult

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# Custom Exceptions
# ──────────────────────────────────────────────

class ExtractionServiceError(Exception):
    """Base exception for data extraction failures."""
    pass


class TaskNotFoundError(ExtractionServiceError):
    """Task document does not exist."""
    pass


class SourceNotFoundError(ExtractionServiceError):
    """Source candidate document does not exist."""
    pass


class NoPlanError(ExtractionServiceError):
    """Task has no AI plan or requirements."""
    pass


class SchemaNotFoundError(ExtractionServiceError):
    """Task or dataset missing valid dynamic dataset schema."""
    pass


# ──────────────────────────────────────────────
# Data Extraction Service
# ──────────────────────────────────────────────

class DataExtractionService:
    """
    Orchestrates source fetching, extraction, status updates, and MongoDB updates.

    Usage:
        service = DataExtractionService()
        result_dict = await service.extract_for_source(task_id, source_id)
    """

    def __init__(
        self,
        fetcher: Optional[SourceFetcher] = None,
        extractor: Optional[DataExtractor] = None,
    ):
        self.fetcher = fetcher or SourceFetcher()
        self.extractor = extractor or DataExtractor()

    async def extract_for_source(
        self,
        task_id: str,
        source_id: str,
    ) -> Dict[str, Any]:
        """
        Execute full extraction pipeline for a single source.
        """
        db = get_db()

        # ── 1. Validate & Load Task ──
        if not ObjectId.is_valid(task_id):
            raise TaskNotFoundError(f"Invalid task ID: '{task_id}'")

        task = await db.tasks.find_one({"_id": ObjectId(task_id)})
        if not task:
            raise TaskNotFoundError(f"Task not found: '{task_id}'")

        ai_requirements = task.get("ai_requirements")
        ai_plan = task.get("ai_plan")
        if not ai_requirements and not ai_plan:
            raise NoPlanError(
                f"Task '{task_id}' has no AI plan. Run POST /api/tasks/{task_id}/plan first."
            )

        # ── 2. Load Source Document ──
        source_doc = await self._load_source(db, task_id, source_id)
        source_url = source_doc.get("url", "")
        source_title = source_doc.get("title", "")

        # ── 3. Resolve Dataset Schema ──
        dataset_schema = await self._resolve_dataset_schema(db, task, task_id)
        record_limit = (
            ai_requirements.get("record_limit")
            if isinstance(ai_requirements, dict)
            else 10
        )

        # ── 4. Update Status → fetching ──
        await self._update_source_status(db, source_doc["_id"], "fetching")

        # ── 5. Fetch Source Content ──
        logger.info("Fetching source url=%s for task=%s", source_url, task_id)
        try:
            fetch_result = await self.fetcher.fetch(source_url)
        except Exception as exc:
            err_msg = f"Fetch error: {type(exc).__name__}"
            await self._update_source_status(db, source_doc["_id"], "failed", error_message=err_msg)
            return ExtractionResult(
                source_id=source_id,
                source_url=source_url,
                source_title=source_title,
                records=[],
                total_records=0,
                status="failed",
                error_message=err_msg,
            ).to_dict()

        fetch_status = fetch_result.get("status", "failed")
        http_status = fetch_result.get("http_status") or fetch_result.get("status_code", 0)
        fetch_error = fetch_result.get("error") or None

        if fetch_status in ("blocked", "timeout", "failed", "browser_unavailable") or http_status in (401, 403, 407, 429, 451, 504):
            final_status = (
                "blocked" if (fetch_status == "blocked" or http_status in (401, 403, 407, 429, 451))
                else ("timeout" if (fetch_status == "timeout" or http_status == 504) else "failed")
            )
            error_msg = fetch_error or ("Source blocked automated access" if final_status == "blocked" else ("Fetch timeout" if final_status == "timeout" else "Fetch failed"))

            await db.sources.update_one(
                {"_id": source_doc["_id"]},
                {"$set": {
                    "status": final_status,
                    "http_status": http_status,
                    "error": error_msg,
                    "error_message": error_msg,
                    "updated_at": datetime.now(timezone.utc),
                }},
            )
            return ExtractionResult(
                source_id=source_id,
                source_url=source_url,
                source_title=source_title,
                records=[],
                total_records=0,
                status=final_status,
                error_message=error_msg,
            ).to_dict()

        # ── 6. Update Status → fetched, then extracting ──
        await self._update_source_status(db, source_doc["_id"], "fetched")
        await self._update_source_status(db, source_doc["_id"], "extracting")

        # ── 7. Perform Data Extraction ──
        logger.info("Extracting records from url=%s for task=%s", source_url, task_id)
        extraction_result = await self.extractor.extract(
            source_content=fetch_result,
            dataset_schema=dataset_schema,
            research_requirements=ai_requirements or ai_plan,
            source_id=source_id,
            record_limit=record_limit,
        )

        # ── 8. Persist Results & Update Status → extracted / failed ──
        final_status = extraction_result.status  # "extracted", "failed", "empty"
        source_status = "extracted" if (final_status == "extracted" and extraction_result.total_records > 0) else "failed"

        await self._save_extraction_results(
            db=db,
            source_obj_id=source_doc["_id"],
            status=source_status,
            extraction_result=extraction_result,
        )

        logger.info(
            "Source extraction completed: source_id=%s task_id=%s status=%s records=%d",
            source_id, task_id, source_status, extraction_result.total_records
        )

        return extraction_result.to_dict()

    # ──────────────────────────────────────────
    # Helper Methods
    # ──────────────────────────────────────────

    async def _load_source(self, db, task_id: str, source_id: str) -> dict:
        """Find source candidate in MongoDB by ID or task relationship."""
        doc = None
        if ObjectId.is_valid(source_id):
            doc = await db.sources.find_one({"_id": ObjectId(source_id)})

        if not doc:
            # Fallback search by url or string id
            doc = await db.sources.find_one({"task_id": task_id, "url": source_id})

        if not doc:
            raise SourceNotFoundError(f"Source '{source_id}' not found for task '{task_id}'")

        return doc

    async def _resolve_dataset_schema(self, db, task: dict, task_id: str) -> dict:
        """Extract or construct dataset schema from task / dataset collection."""
        # Check dataset collection first
        dataset = await db.datasets.find_one({"task_id": task_id})
        if dataset and "schema" in dataset and isinstance(dataset["schema"], dict):
            return dataset["schema"]

        # Check task ai_requirements
        ai_req = task.get("ai_requirements", {})
        if isinstance(ai_req, dict) and "fields" in ai_req:
            return ai_req

        # Check task ai_plan
        ai_plan = task.get("ai_plan", {})
        if isinstance(ai_plan, dict) and "dataset_schema" in ai_plan:
            return ai_plan["dataset_schema"]

        raise SchemaNotFoundError(f"No dynamic dataset schema found for task '{task_id}'")

    async def _update_source_status(
        self,
        db,
        source_obj_id: ObjectId,
        status: str,
        error_message: Optional[str] = None,
    ) -> None:
        """Update source document status in MongoDB."""
        now = datetime.now(timezone.utc)
        update_doc: Dict[str, Any] = {
            "status": status,
            "updated_at": now,
        }
        if error_message:
            update_doc["error_message"] = error_message

        await db.sources.update_one(
            {"_id": source_obj_id},
            {"$set": update_doc},
        )

    async def _save_extraction_results(
        self,
        db,
        source_obj_id: ObjectId,
        status: str,
        extraction_result: ExtractionResult,
    ) -> None:
        """Persist raw extracted records and extraction metadata to source document."""
        now = datetime.now(timezone.utc)
        records_dict_list = [r.to_dict() for r in extraction_result.records]

        update_doc = {
            "status": status,
            "extracted_records": records_dict_list,
            "record_count": extraction_result.total_records,
            "extracted_at": now,
            "updated_at": now,
            "error_message": extraction_result.error_message,
        }

        await db.sources.update_one(
            {"_id": source_obj_id},
            {"$set": update_doc},
        )
