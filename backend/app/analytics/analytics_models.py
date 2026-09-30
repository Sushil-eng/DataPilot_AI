"""
Analytics Models — Phase 5, Prompt 1
Pydantic models for analytics API responses.
All models are generic — no domain-specific assumptions.
"""

from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field


class OverviewStats(BaseModel):
    """Platform-wide overview statistics."""
    active_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    total_tasks: int = 0
    total_records: int = 0
    total_sources: int = 0
    total_datasets: int = 0


class ActivityPoint(BaseModel):
    """A single data point for the activity timeline."""
    date: str
    records: int = 0
    tasks: int = 0


class ActivityData(BaseModel):
    """Activity data over time."""
    data: List[ActivityPoint] = []


class FieldStatistic(BaseModel):
    """
    Dynamic statistics for a single dataset field.
    The kind of stats returned depends on the field type.
    """
    field_name: str
    field_type: str = "string"
    total_values: int = 0
    non_null_count: int = 0
    null_count: int = 0

    # Numeric fields
    minimum: Optional[float] = None
    maximum: Optional[float] = None
    average: Optional[float] = None

    # String / categorical fields
    unique_count: Optional[int] = None
    top_values: Optional[List[Dict[str, Any]]] = None

    # Date fields
    earliest: Optional[str] = None
    latest: Optional[str] = None

    # URL fields
    source_count: Optional[int] = None

    # Chart type hint for frontend
    chart_type: Optional[str] = None  # "bar", "pie", "numeric", "timeline"


class SourceStatistic(BaseModel):
    """Statistics about a single source domain."""
    domain: str
    count: int = 0


class DatasetAnalytics(BaseModel):
    """Complete analytics for a single dataset."""
    dataset_id: str
    dataset_name: str = ""
    description: str = ""
    record_count: int = 0
    field_count: int = 0
    source_count: int = 0
    valid_records: int = 0
    invalid_records: int = 0
    duplicates_removed: int = 0
    field_statistics: List[FieldStatistic] = []
    source_statistics: List[SourceStatistic] = []
