"""
Collection Module — Phase 4

Generic data-collection and processing components:
  • source_models          — Pydantic models for source candidates
  • source_discovery       — Source discovery engine
  • search_providers        — Pluggable search provider abstraction
  • query_builder           — Dynamic query generation from AI requirements
  • fetcher                 — SourceFetcher, HTTPFetcher, BrowserFetcher
  • extraction_models       — ExtractedRecord, ExtractionResult
  • extractor               — DataExtractor engine (JSON-LD, LLM, Mock)
  • data_extraction_service — Service layer for task/source extraction endpoints
  • cleaner                 — DataCleaner (HTML stripping & whitespace normalization)
  • normalizer              — DataNormalizer (schema-driven type conversion)
  • validator               — DataValidator (required fields & type safety)
  • deduplicator            — DataDeduplicator (exact & identity key deduplication)
  • pipeline                — DataProcessingPipeline (full pipeline execution)
  • processing_models       — ProcessingResult, ValidationResult, DeduplicationResult
"""

from .source_models import SourceCandidate, SourceStatus
from .fetcher import SourceFetcher, HTTPFetcher, BrowserFetcher
from .extraction_models import ExtractedRecord, ExtractionResult
from .extractor import DataExtractor, DynamicMockGenerator
from .data_extraction_service import (
    DataExtractionService,
    ExtractionServiceError,
    TaskNotFoundError as ExtractionTaskNotFoundError,
    SourceNotFoundError,
    NoPlanError as ExtractionNoPlanError,
    SchemaNotFoundError,
)
from .cleaner import DataCleaner
from .normalizer import DataNormalizer
from .validator import DataValidator
from .deduplicator import DataDeduplicator
from .pipeline import DataProcessingPipeline
from .processing_models import (
    ProcessingResult,
    ValidationResult,
    DeduplicationResult,
    ValidationStatus,
    ValidationErrorItem,
)

__all__ = [
    "SourceCandidate",
    "SourceStatus",
    "SourceFetcher",
    "HTTPFetcher",
    "BrowserFetcher",
    "ExtractedRecord",
    "ExtractionResult",
    "DataExtractor",
    "DynamicMockGenerator",
    "DataExtractionService",
    "ExtractionServiceError",
    "ExtractionTaskNotFoundError",
    "SourceNotFoundError",
    "ExtractionNoPlanError",
    "SchemaNotFoundError",
    "DataCleaner",
    "DataNormalizer",
    "DataValidator",
    "DataDeduplicator",
    "DataProcessingPipeline",
    "ProcessingResult",
    "ValidationResult",
    "DeduplicationResult",
    "ValidationStatus",
    "ValidationErrorItem",
]
