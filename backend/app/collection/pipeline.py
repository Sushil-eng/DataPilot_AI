"""
Data Processing Pipeline — Phase 4, Prompt 3

Full processing pipeline combining:
  1. DataCleaner      (strips HTML, normalises whitespace)
  2. DataNormalizer   (converts types: numbers, dates, URLs, booleans, currencies, arrays)
  3. DataValidator    (enforces required fields, data types, URL safety)
  4. DataDeduplicator (removes exact and key duplicates)
  5. Record Limit     (slices final clean unique valid records to task record_limit)

Domain-Agnostic: Driven by dynamic dataset schema definitions.
"""

import logging
from typing import Dict, Any, List, Optional

from .cleaner import DataCleaner
from .normalizer import DataNormalizer
from .validator import DataValidator
from .deduplicator import DataDeduplicator
from .processing_models import ProcessingResult

logger = logging.getLogger(__name__)


class DataProcessingPipeline:
    """
    Main orchestrator for the Data Cleaning, Normalization, Validation,
    and Deduplication pipeline.

    Usage:
        pipeline = DataProcessingPipeline()
        result = pipeline.process(raw_records, dataset_schema, record_limit=50)
    """

    def __init__(
        self,
        cleaner: Optional[DataCleaner] = None,
        normalizer: Optional[DataNormalizer] = None,
        validator: Optional[DataValidator] = None,
        deduplicator: Optional[DataDeduplicator] = None,
    ):
        self.cleaner = cleaner or DataCleaner()
        self.normalizer = normalizer or DataNormalizer()
        self.validator = validator or DataValidator()
        self.deduplicator = deduplicator or DataDeduplicator()

    def process(
        self,
        raw_records: List[Dict[str, Any]],
        dataset_schema: Dict[str, Any],
        record_limit: Optional[int] = None,
        task_id: Optional[str] = None,
    ) -> ProcessingResult:
        """
        Execute full processing pipeline on a list of raw extracted records.
        """
        input_count = len(raw_records)
        if input_count == 0:
            return ProcessingResult(
                task_id=task_id,
                input_count=0,
                cleaned_count=0,
                valid_count=0,
                invalid_count=0,
                duplicates_removed=0,
                final_count=0,
                records=[],
                errors=[],
                warnings=[],
            )

        logger.info("Starting DataProcessingPipeline: input_count=%d task_id=%s", input_count, task_id)

        # ── Step 1. Cleaning Phase ──
        cleaned_records = self.cleaner.clean_records(raw_records)
        cleaned_count = len(cleaned_records)

        # ── Step 2. Normalization Phase ──
        normalized_records = self.normalizer.normalize_records(cleaned_records, dataset_schema)

        # ── Step 3. Validation Phase ──
        valid_records, invalid_records, validation_errors = self.validator.validate_records(
            normalized_records, dataset_schema
        )
        valid_count = len(valid_records)
        invalid_count = len(invalid_records)

        collected_errors = [e.to_dict() for e in validation_errors]

        # ── Step 4. Deduplication Phase ──
        dedup_result = self.deduplicator.deduplicate(valid_records, dataset_schema)
        dedup_records = dedup_result.records
        duplicates_removed = dedup_result.duplicates_removed

        collected_warnings = []
        if dedup_result.duplicate_candidates > 0:
            collected_warnings.append(
                f"Flagged {dedup_result.duplicate_candidates} potential fuzzy duplicate candidate(s)"
            )

        # ── Step 5. Apply Final Record Limit (Section 17) ──
        limit = record_limit or dataset_schema.get("record_limit")
        if limit and limit > 0 and len(dedup_records) > limit:
            logger.info("Applying final record_limit=%d (capping from %d)", limit, len(dedup_records))
            final_records = dedup_records[:limit]
        else:
            final_records = dedup_records

        final_count = len(final_records)

        logger.info(
            "DataProcessingPipeline complete: input=%d cleaned=%d valid=%d invalid=%d dedup_removed=%d final=%d",
            input_count, cleaned_count, valid_count, invalid_count, duplicates_removed, final_count
        )

        return ProcessingResult(
            task_id=task_id,
            input_count=input_count,
            cleaned_count=cleaned_count,
            valid_count=valid_count,
            invalid_count=invalid_count,
            duplicates_removed=duplicates_removed,
            final_count=final_count,
            records=final_records,
            errors=collected_errors,
            warnings=collected_warnings,
        )
