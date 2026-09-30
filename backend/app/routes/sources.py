from fastapi import APIRouter, HTTPException
from typing import Any
import logging

from app.schemas import SourceCreate
from app.services import source_service
from app.collection.source_models import DiscoverRequest
from app.collection.source_discovery import (
    SourceDiscoveryService,
    TaskNotFoundError,
    NoPlanError,
    NoDatasetError,
    EmptyResultsError,
    SourceDiscoveryError,
)
from app.collection.search_providers import (
    SearchProviderError,
    SearchProviderConfigError,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["sources"])


def success_response(data: Any):
    return {"success": True, "data": data}


def error_response(message: str, status_code: int = 400):
    raise HTTPException(
        status_code=status_code,
        detail={"success": False, "error": {"message": message}}
    )


@router.get("/sources/{dataset_id}")
async def get_sources_by_dataset(dataset_id: str):
    result = await source_service.get_sources(dataset_id)
    if result is None:
        error_response("Invalid dataset ID", 400)
    return success_response(result)


@router.post("/sources")
async def create_source(source_in: SourceCreate):
    result = await source_service.create_source(
        dataset_id=source_in.dataset_id,
        url=source_in.url,
        title=source_in.title,
        source_type=source_in.source_type
    )
    if result is None:
        error_response("Dataset not found", 404)
    return success_response(result)


# ──────────────────────────────────────────────
# Phase 4 — Source Discovery endpoint
# ──────────────────────────────────────────────

@router.post("/tasks/{task_id}/sources/discover")
async def discover_sources(task_id: str, body: DiscoverRequest):
    """
    Discover candidate sources for a planned task.

    Pipeline:
      1. Load task and validate AI plan exists
      2. Build search queries from requirements
      3. Execute searches via configured provider
      4. Score, deduplicate, and persist sources
      5. Return discovered sources

    Requires the task to be in 'planned' status (POST /api/tasks/{task_id}/plan).
    """
    try:
        service = SourceDiscoveryService()
        response = await service.discover_for_task(
            task_id=task_id,
            limit=body.limit,
        )

        return {
            "success": True,
            "data": {
                "task_id": response.task_id,
                "source_count": response.source_count,
                "sources": response.sources,
            },
        }

    except TaskNotFoundError as exc:
        logger.error("Task not found: %s", exc)
        raise HTTPException(status_code=404, detail=str(exc))

    except NoPlanError as exc:
        logger.error("No AI plan: %s", exc)
        raise HTTPException(status_code=409, detail=str(exc))

    except NoDatasetError as exc:
        logger.error("No dataset: %s", exc)
        raise HTTPException(status_code=404, detail=str(exc))

    except EmptyResultsError as exc:
        logger.warning("Empty search results: %s", exc)
        raise HTTPException(status_code=404, detail=str(exc))

    except SearchProviderConfigError as exc:
        logger.error("Search provider config error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))

    except SearchProviderError as exc:
        logger.error("Search provider error: %s", exc)
        raise HTTPException(status_code=502, detail=str(exc))

    except SourceDiscoveryError as exc:
        logger.error("Source discovery error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))

    except Exception as exc:
        logger.exception(
            "Unexpected error in /api/tasks/%s/sources/discover", task_id
        )
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {type(exc).__name__}",
        )


# ──────────────────────────────────────────────
# Phase 4 — Data Extraction endpoint (Prompt 2)
# ──────────────────────────────────────────────

@router.post("/tasks/{task_id}/sources/{source_id}/extract")
async def extract_source(task_id: str, source_id: str):
    """
    Extract structured records from a discovered source.

    Pipeline:
      1. Load task and validate AI plan exists
      2. Load source candidate
      3. Load dynamic dataset schema
      4. Fetch source content (HTTP or Browser)
      5. Extract structured records using dynamic schema
      6. Return extracted records and update source status in MongoDB

    Status transitions: discovered → fetching → fetched → extracting → extracted (or failed)
    """
    try:
        from app.collection.data_extraction_service import (
            DataExtractionService,
            TaskNotFoundError as ExtTaskNotFoundError,
            SourceNotFoundError as ExtSourceNotFoundError,
            NoPlanError as ExtNoPlanError,
            SchemaNotFoundError as ExtSchemaNotFoundError,
            ExtractionServiceError,
        )

        service = DataExtractionService()
        result = await service.extract_for_source(task_id=task_id, source_id=source_id)

        return {
            "success": True,
            "data": result,
        }

    except ExtTaskNotFoundError as exc:
        logger.error("Task not found: %s", exc)
        raise HTTPException(status_code=404, detail=str(exc))

    except ExtSourceNotFoundError as exc:
        logger.error("Source not found: %s", exc)
        raise HTTPException(status_code=404, detail=str(exc))

    except (ExtNoPlanError, ExtSchemaNotFoundError) as exc:
        logger.error("Planning / schema error: %s", exc)
        raise HTTPException(status_code=409, detail=str(exc))

    except ExtractionServiceError as exc:
        logger.error("Extraction service error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))

    except Exception as exc:
        logger.exception(
            "Unexpected error in /api/tasks/%s/sources/%s/extract", task_id, source_id
        )
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {type(exc).__name__}",
        )
