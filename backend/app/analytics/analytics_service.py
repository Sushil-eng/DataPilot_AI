"""
Analytics Service — Phase 5, Prompt 1
Calculates real statistics from MongoDB collections.

All analytics are GENERIC and schema-driven:
  - No hardcoded field names like salary, location, company
  - Field statistics are computed dynamically from dataset schema + records
  - Works for any domain: jobs, companies, products, startups, etc.
"""

import logging
from collections import Counter
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse

from bson import ObjectId

from app.database.connection import get_db
from app.analytics.analytics_models import (
    OverviewStats,
    ActivityPoint,
    ActivityData,
    FieldStatistic,
    SourceStatistic,
    DatasetAnalytics,
)

logger = logging.getLogger(__name__)

# Field types that should get numeric statistics
NUMERIC_TYPES = {"number", "currency", "integer", "float"}
# Field types that should get date statistics
DATE_TYPES = {"date", "datetime"}
# Field types that should get URL / source statistics
URL_TYPES = {"url", "link"}
# Everything else gets categorical / string statistics
STRING_TYPES = {"string", "text", "array", "boolean"}


class AnalyticsService:
    """Calculates real analytics from MongoDB data."""

    # ──────────────────────────────────────────
    # Platform Overview
    # ──────────────────────────────────────────

    async def get_overview(self) -> OverviewStats:
        """Calculate platform-wide overview statistics from MongoDB."""
        db = get_db()

        # Task counts by status
        total_tasks = await db.tasks.count_documents({})
        active_tasks = await db.tasks.count_documents(
            {"status": {"$in": ["pending", "planning", "planned", "running"]}}
        )
        completed_tasks = await db.tasks.count_documents({"status": "completed"})
        failed_tasks = await db.tasks.count_documents({"status": "failed"})

        # Total records across all datasets
        total_records = 0
        pipeline = [
            {"$group": {"_id": None, "total": {"$sum": "$record_count"}}}
        ]
        async for doc in db.datasets.aggregate(pipeline):
            total_records = doc.get("total", 0)

        # If dataset record_count is 0, count from dataset_records collection
        if total_records == 0:
            total_records = await db.dataset_records.count_documents({})

        # Total sources
        total_sources = await db.sources.count_documents({})

        # Total datasets
        total_datasets = await db.datasets.count_documents({})

        return OverviewStats(
            active_tasks=active_tasks,
            completed_tasks=completed_tasks,
            failed_tasks=failed_tasks,
            total_tasks=total_tasks,
            total_records=total_records,
            total_sources=total_sources,
            total_datasets=total_datasets,
        )

    # ──────────────────────────────────────────
    # Activity Timeline
    # ──────────────────────────────────────────

    async def get_activity(self, days: int = 7) -> ActivityData:
        """
        Get records collected over the last N days.
        Uses dataset_records.created_at for real timeline data.
        Falls back to task.created_at if no records exist.
        """
        db = get_db()
        now = datetime.now(timezone.utc)
        start_date = now - timedelta(days=days)

        # Initialize all days with zero
        date_map: Dict[str, Dict[str, int]] = {}
        for i in range(days):
            d = (start_date + timedelta(days=i + 1)).strftime("%Y-%m-%d")
            date_map[d] = {"records": 0, "tasks": 0}

        # Count records by day from dataset_records
        records_pipeline = [
            {"$match": {"created_at": {"$gte": start_date}}},
            {
                "$group": {
                    "_id": {
                        "$dateToString": {
                            "format": "%Y-%m-%d",
                            "date": "$created_at",
                        }
                    },
                    "count": {"$sum": 1},
                }
            },
            {"$sort": {"_id": 1}},
        ]

        try:
            async for doc in db.dataset_records.aggregate(records_pipeline):
                day = doc["_id"]
                if day in date_map:
                    date_map[day]["records"] = doc["count"]
        except Exception as e:
            logger.warning("Activity records aggregation failed: %s", e)

        # Count tasks by day
        tasks_pipeline = [
            {"$match": {"created_at": {"$gte": start_date}}},
            {
                "$group": {
                    "_id": {
                        "$dateToString": {
                            "format": "%Y-%m-%d",
                            "date": "$created_at",
                        }
                    },
                    "count": {"$sum": 1},
                }
            },
            {"$sort": {"_id": 1}},
        ]

        try:
            async for doc in db.tasks.aggregate(tasks_pipeline):
                day = doc["_id"]
                if day in date_map:
                    date_map[day]["tasks"] = doc["count"]
        except Exception as e:
            logger.warning("Activity tasks aggregation failed: %s", e)

        # Build sorted response
        data_points = []
        for date_str in sorted(date_map.keys()):
            data_points.append(
                ActivityPoint(
                    date=date_str,
                    records=date_map[date_str]["records"],
                    tasks=date_map[date_str]["tasks"],
                )
            )

        return ActivityData(data=data_points)

    # ──────────────────────────────────────────
    # Dataset Analytics
    # ──────────────────────────────────────────

    async def get_dataset_analytics(self, dataset_id: str) -> Optional[DatasetAnalytics]:
        """
        Calculate comprehensive analytics for a specific dataset.
        All field statistics are generated dynamically from the schema.
        """
        db = get_db()

        # Load dataset document
        if not ObjectId.is_valid(dataset_id):
            return None
        dataset = await db.datasets.find_one({"_id": ObjectId(dataset_id)})
        if not dataset:
            return None

        task_id = dataset.get("task_id", "")

        # Load schema fields
        schema_fields = dataset.get("schema", [])
        dynamic_schema = dataset.get("dynamic_schema", {})
        if dynamic_schema and "fields" in dynamic_schema:
            schema_fields = dynamic_schema["fields"]

        # Build field type map from schema
        field_type_map: Dict[str, str] = {}
        for f in schema_fields:
            if isinstance(f, dict):
                field_type_map[f.get("name", "")] = f.get("type", "string")

        # Load all records for this dataset (analytics computed server-side)
        records_cursor = db.dataset_records.find(
            {"dataset_id": dataset_id},
            {"data": 1, "source_url": 1, "confidence": 1, "_id": 0},
        )
        records = await records_cursor.to_list(length=5000)

        record_count = len(records)

        # Source count from sources collection
        source_count = await db.sources.count_documents({"dataset_id": dataset_id})
        if source_count == 0 and task_id:
            source_count = await db.sources.count_documents({"task_id": task_id})

        # Get execution stats from workflow
        valid_records = record_count
        invalid_records = 0
        duplicates_removed = 0
        if task_id:
            workflow = await db.workflows.find_one({"task_id": task_id})
            if workflow:
                exec_stats = workflow.get("execution_stats", {})
                if exec_stats:
                    valid_records = exec_stats.get("valid_records", record_count)
                    invalid_records = exec_stats.get("invalid_records", 0)
                    duplicates_removed = exec_stats.get("duplicates_removed", 0)
                    if exec_stats.get("sources_processed", 0) > source_count:
                        source_count = exec_stats["sources_processed"]

        # Calculate field statistics dynamically
        field_statistics = self._calculate_field_statistics(
            records, field_type_map
        )

        # Calculate source statistics from source_url
        source_statistics = self._calculate_source_statistics(records)

        return DatasetAnalytics(
            dataset_id=dataset_id,
            dataset_name=dataset.get("name", ""),
            description=dataset.get("description", ""),
            record_count=record_count,
            field_count=len(field_type_map),
            source_count=source_count,
            valid_records=valid_records,
            invalid_records=invalid_records,
            duplicates_removed=duplicates_removed,
            field_statistics=field_statistics,
            source_statistics=source_statistics,
        )

    # ──────────────────────────────────────────
    # Private: Field Statistics Calculator
    # ──────────────────────────────────────────

    def _calculate_field_statistics(
        self,
        records: List[Dict[str, Any]],
        field_type_map: Dict[str, str],
    ) -> List[FieldStatistic]:
        """
        Generate statistics for each field based on its schema type.
        Completely generic — no hardcoded field name assumptions.
        """
        stats: List[FieldStatistic] = []

        for field_name, field_type in field_type_map.items():
            # Skip internal/metadata fields from the analysis output
            if field_name in ("_source_url", "_confidence", "_collected_at"):
                continue

            values = []
            null_count = 0

            for rec in records:
                data = rec.get("data", {})
                if not isinstance(data, dict):
                    continue
                val = data.get(field_name)
                if val is None or val == "" or val == []:
                    null_count += 1
                else:
                    values.append(val)

            total = len(records)
            non_null = len(values)

            field_stat = FieldStatistic(
                field_name=field_name,
                field_type=field_type,
                total_values=total,
                non_null_count=non_null,
                null_count=null_count,
            )

            lower_type = field_type.lower()

            if lower_type in NUMERIC_TYPES:
                field_stat = self._calc_numeric_stats(field_stat, values, lower_type)
            elif lower_type in DATE_TYPES:
                field_stat = self._calc_date_stats(field_stat, values)
            elif lower_type in URL_TYPES:
                field_stat = self._calc_url_stats(field_stat, values)
            else:
                field_stat = self._calc_categorical_stats(field_stat, values)

            stats.append(field_stat)

        return stats

    def _calc_numeric_stats(
        self, stat: FieldStatistic, values: list, field_type: str
    ) -> FieldStatistic:
        """Calculate numeric statistics: min, max, average."""
        numeric_vals = []
        for v in values:
            n = self._extract_number(v, field_type)
            if n is not None:
                numeric_vals.append(n)

        if numeric_vals:
            stat.minimum = round(min(numeric_vals), 2)
            stat.maximum = round(max(numeric_vals), 2)
            stat.average = round(sum(numeric_vals) / len(numeric_vals), 2)
            stat.unique_count = len(set(numeric_vals))
            stat.chart_type = "numeric"
        else:
            stat.chart_type = "bar"

        return stat

    def _calc_date_stats(
        self, stat: FieldStatistic, values: list
    ) -> FieldStatistic:
        """Calculate date statistics: earliest, latest."""
        date_strs = [str(v) for v in values if v]
        if date_strs:
            sorted_dates = sorted(date_strs)
            stat.earliest = sorted_dates[0]
            stat.latest = sorted_dates[-1]
            stat.unique_count = len(set(date_strs))
            stat.chart_type = "timeline"
        return stat

    def _calc_url_stats(
        self, stat: FieldStatistic, values: list
    ) -> FieldStatistic:
        """Calculate URL/source statistics."""
        domains = []
        for v in values:
            try:
                parsed = urlparse(str(v))
                domain = parsed.netloc or parsed.path
                if domain:
                    domains.append(domain)
            except Exception:
                pass

        stat.source_count = len(set(domains))
        stat.unique_count = len(set(str(v) for v in values))

        if domains:
            counter = Counter(domains)
            stat.top_values = [
                {"value": k, "count": c}
                for k, c in counter.most_common(10)
            ]
            stat.chart_type = "bar"

        return stat

    def _calc_categorical_stats(
        self, stat: FieldStatistic, values: list
    ) -> FieldStatistic:
        """Calculate categorical/string statistics: unique count, top values."""
        str_values = []
        for v in values:
            if isinstance(v, list):
                str_values.extend(str(item) for item in v)
            elif isinstance(v, dict):
                str_values.append(str(v))
            else:
                str_values.append(str(v))

        stat.unique_count = len(set(str_values))

        if str_values:
            counter = Counter(str_values)
            stat.top_values = [
                {"value": k, "count": c}
                for k, c in counter.most_common(10)
            ]

        # Choose chart type based on unique count
        if stat.unique_count and stat.unique_count <= 15:
            stat.chart_type = "pie"
        elif stat.unique_count and stat.unique_count <= 50:
            stat.chart_type = "bar"
        else:
            stat.chart_type = None  # too many unique values for a chart

        return stat

    # ──────────────────────────────────────────
    # Private: Source Statistics
    # ──────────────────────────────────────────

    def _calculate_source_statistics(
        self, records: List[Dict[str, Any]]
    ) -> List[SourceStatistic]:
        """Calculate domain distribution from source_url fields."""
        domains: List[str] = []
        for rec in records:
            url = rec.get("source_url", "")
            if not url:
                data = rec.get("data", {})
                if isinstance(data, dict):
                    url = data.get("source_url", "")
            if url:
                try:
                    parsed = urlparse(str(url))
                    domain = parsed.netloc or parsed.path
                    if domain:
                        domains.append(domain)
                except Exception:
                    pass

        counter = Counter(domains)
        return [
            SourceStatistic(domain=domain, count=count)
            for domain, count in counter.most_common(20)
        ]

    # ──────────────────────────────────────────
    # Private: Numeric Extraction Helper
    # ──────────────────────────────────────────

    @staticmethod
    def _extract_number(value: Any, field_type: str) -> Optional[float]:
        """Extract a numeric value from various representations."""
        if isinstance(value, (int, float)):
            return float(value)

        if isinstance(value, dict):
            # Handle currency objects like {"amount": 48990, "currency": "INR"}
            if "amount" in value:
                try:
                    return float(value["amount"])
                except (ValueError, TypeError):
                    pass
            if "value" in value:
                try:
                    return float(value["value"])
                except (ValueError, TypeError):
                    pass
            return None

        if isinstance(value, str):
            # Strip currency symbols and commas
            cleaned = value.replace(",", "").replace("₹", "").replace("$", "").replace("€", "").strip()
            # Try to parse the first number-like substring
            parts = cleaned.split()
            for part in parts:
                try:
                    return float(part)
                except ValueError:
                    continue

        return None
