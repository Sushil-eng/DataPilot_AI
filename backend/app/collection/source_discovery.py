"""
Source Discovery Service — Phase 4, Prompt 1

The main orchestrator for the source discovery phase:

    AI Requirements (from Phase 3)
            ↓
    Query Builder
            ↓
    Search Provider
            ↓
    Relevance Scorer
            ↓
    Deduplication
            ↓
    Candidate Sources (persisted to MongoDB)

This service is completely generic — it works from the AI-generated
requirements, not from hardcoded domain logic.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from bson import ObjectId

from ..database.connection import get_db
from .source_models import (
    SourceCandidate,
    SourceStatus,
    DiscoverResponse,
    deduplicate_sources,
)
from .search_providers import (
    SearchProvider,
    SearchProviderError,
    create_search_provider,
)
from .query_builder import build_search_queries
from .relevance_scorer import score_sources

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# Custom exceptions
# ──────────────────────────────────────────────

class SourceDiscoveryError(Exception):
    """Base exception for source discovery failures."""
    pass


class TaskNotFoundError(SourceDiscoveryError):
    """Task does not exist."""
    pass


class NoPlanError(SourceDiscoveryError):
    """Task has no AI plan — planning must be completed first."""
    pass


class NoDatasetError(SourceDiscoveryError):
    """Task has no associated dataset."""
    pass


class EmptyResultsError(SourceDiscoveryError):
    """Search returned no results."""
    pass


# ──────────────────────────────────────────────
# Source Discovery Service
# ──────────────────────────────────────────────

class SourceDiscoveryService:
    """
    Discovers candidate sources for a planned research task.

    Usage:
        service = SourceDiscoveryService()
        response = await service.discover_for_task(task_id, limit=10)
    """

    def __init__(self, provider: Optional[SearchProvider] = None):
        """
        Initialise with an optional search provider.
        If none is given, one is created from environment configuration.
        """
        self.provider = provider or create_search_provider()

    async def discover_for_task(
        self,
        task_id: str,
        limit: int = 10,
    ) -> DiscoverResponse:
        """
        Full discovery pipeline for a task:

        1. Load task and validate it has a plan
        2. Load dataset
        3. Extract requirements from AI plan
        4. Build search queries
        5. Execute searches
        6. Score and deduplicate
        7. Save to MongoDB
        8. Return response
        """
        db = get_db()

        # ── 1. Load task ──
        task = await self._load_task(db, task_id)

        # ── 2. Extract AI requirements ──
        requirements = task.get("ai_requirements")
        if not requirements:
            raise NoPlanError(
                f"Task '{task_id}' has no AI plan. "
                "Run POST /api/tasks/{task_id}/plan first."
            )

        # ── 3. Load dataset ──
        dataset = await db.datasets.find_one({"task_id": task_id})
        if not dataset:
            raise NoDatasetError(f"No dataset found for task '{task_id}'.")
        dataset_id = str(dataset["_id"])

        # ── 4. Extract structured fields from requirements ──
        goal = requirements.get("goal", "")
        intent = requirements.get("intent", "general_research")
        filters = requirements.get("filters", {})
        fields = requirements.get("fields", [])
        record_limit = requirements.get("record_limit", limit)

        logger.info(
            "SourceDiscovery: task=%s  goal=%r  intent=%s  limit=%d",
            task_id, goal[:80], intent, limit,
        )

        # ── 5. Build search queries ──
        queries = build_search_queries(
            goal=goal,
            intent=intent,
            filters=filters,
            required_fields=fields,
            record_limit=limit,
        )

        # ── 6. Execute searches ──
        all_candidates: list[SourceCandidate] = []
        for query in queries:
            try:
                # Request more than needed per query to allow dedup
                per_query_limit = max(limit, limit // len(queries) + 5)
                results = await self.provider.search(query, limit=per_query_limit)
                all_candidates.extend(results)
            except SearchProviderError as exc:
                logger.warning(
                    "Search failed for query=%r: %s", query, exc
                )
                # Continue with other queries — don't fail completely
                continue

        if not all_candidates:
            logger.warning(
                "SourceDiscovery: No sources found for task %s (search provider unavailable/empty). "
                "Marking for AI knowledge fallback.",
                task_id,
            )
            await self._update_task_status(db, task_id, "sources_discovered")
            return DiscoverResponse(
                task_id=task_id,
                source_count=0,
                sources=[],
            )

        # ── 7. Deduplicate ──
        unique_candidates = deduplicate_sources(all_candidates)

        # ── 8. Score relevance ──
        primary_query = queries[0] if queries else goal
        scored_candidates = score_sources(
            sources=unique_candidates,
            query=primary_query,
            goal=goal,
            filters=filters,
            required_fields=fields,
        )

        # Trim to requested limit
        final_candidates = scored_candidates[:limit]

        # ── 9. Save to MongoDB ──
        saved_sources = await self._save_sources(
            db, task_id, dataset_id, final_candidates
        )

        # ── 10. Update task status ──
        await self._update_task_status(db, task_id, "sources_discovered")

        logger.info(
            "SourceDiscovery: task=%s — saved %d sources",
            task_id, len(saved_sources),
        )

        return DiscoverResponse(
            task_id=task_id,
            source_count=len(saved_sources),
            sources=saved_sources,
        )

    async def discover_sources(
        self,
        goal: str,
        intent: str,
        filters: dict,
        required_fields: list[dict],
        record_limit: int = 10,
        dataset_schema: Optional[dict] = None,
    ) -> list[SourceCandidate]:
        """
        Standalone discovery (not tied to a task).
        Useful for testing and direct API usage.
        """
        queries = build_search_queries(
            goal=goal,
            intent=intent,
            filters=filters,
            required_fields=required_fields,
            record_limit=record_limit,
        )

        all_candidates: list[SourceCandidate] = []
        for query in queries:
            try:
                results = await self.provider.search(query, limit=record_limit)
                all_candidates.extend(results)
            except SearchProviderError as exc:
                logger.warning("Search failed for query=%r: %s", query, exc)
                continue

        if not all_candidates:
            return []

        unique = deduplicate_sources(all_candidates)
        primary_query = queries[0] if queries else goal

        scored = score_sources(
            sources=unique,
            query=primary_query,
            goal=goal,
            filters=filters,
            required_fields=required_fields,
        )

        return scored[:record_limit]

    # ──────────────────────────────────────────
    # Private helpers
    # ──────────────────────────────────────────

    async def _load_task(self, db, task_id: str) -> dict:
        """Load and validate the task document."""
        if not ObjectId.is_valid(task_id):
            raise TaskNotFoundError(f"Invalid task ID: {task_id}")

        task = await db.tasks.find_one({"_id": ObjectId(task_id)})
        if not task:
            raise TaskNotFoundError(f"Task not found: {task_id}")

        status = task.get("status", "")
        if status not in ("planned", "running", "sources_discovered", "failed"):
            raise NoPlanError(
                f"Task '{task_id}' is in state '{status}'. "
                f"Source discovery requires status 'planned'. "
                f"Run POST /api/tasks/{{task_id}}/plan first."
            )

        return task

    async def _save_sources(
        self,
        db,
        task_id: str,
        dataset_id: str,
        candidates: list[SourceCandidate],
    ) -> list[dict]:
        """Persist discovered sources to MongoDB."""
        saved: list[dict] = []

        for candidate in candidates:
            doc = candidate.to_db_dict(task_id, dataset_id)
            result = await db.sources.insert_one(doc)
            doc["_id"] = str(result.inserted_id)
            doc["id"] = doc.pop("_id")
            # Serialise datetime for JSON response
            if "discovered_at" in doc:
                doc["discovered_at"] = doc["discovered_at"].isoformat()
            saved.append(doc)

        return saved

    async def _update_task_status(
        self, db, task_id: str, status: str
    ) -> None:
        """Update the task status after discovery."""
        now = datetime.now(timezone.utc)
        await db.tasks.update_one(
            {"_id": ObjectId(task_id)},
            {"$set": {"status": status, "updated_at": now}},
        )
        await db.workflows.update_many(
            {"task_id": task_id},
            {"$set": {"status": status, "updated_at": now}},
        )
        logger.debug("Task %s → status=%s", task_id, status)
