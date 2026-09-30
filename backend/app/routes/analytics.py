"""
Analytics Routes — Phase 5, Prompt 1
Real analytics endpoints using MongoDB data.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import logging

from app.analytics.analytics_service import AnalyticsService

logger = logging.getLogger(__name__)
router = APIRouter(tags=["analytics"])

_service = AnalyticsService()


def success_response(data):
    return {"success": True, "data": data}


@router.get("/analytics/overview")
async def get_analytics_overview():
    """
    Platform-wide overview statistics.
    Returns counts of tasks, records, sources, datasets from MongoDB.
    """
    try:
        stats = await _service.get_overview()
        return success_response(stats.model_dump())
    except Exception as exc:
        logger.exception("Failed to load analytics overview")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/analytics/activity")
async def get_analytics_activity(days: int = Query(7, ge=1, le=90)):
    """
    Activity timeline — records and tasks created over the last N days.
    """
    try:
        activity = await _service.get_activity(days=days)
        return success_response(activity.model_dump())
    except Exception as exc:
        logger.exception("Failed to load analytics activity")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/analytics/datasets/{dataset_id}")
async def get_dataset_analytics(dataset_id: str):
    """
    Comprehensive analytics for a specific dataset.
    Field statistics are computed dynamically from the dataset schema.
    """
    try:
        analytics = await _service.get_dataset_analytics(dataset_id)
        if not analytics:
            raise HTTPException(status_code=404, detail=f"Dataset not found: {dataset_id}")
        return success_response(analytics.model_dump())
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to load dataset analytics for %s", dataset_id)
        raise HTTPException(status_code=500, detail=str(exc))
