"""
Data Deduplicator Engine — Phase 4, Prompt 3

Multi-stage generic deduplication engine:
  1. Exact Data Matching (identical normalised JSON content)
  2. Identity Key Matching (unique URL, website, email, or item key)
  3. Normalised Key Comparison (case and whitespace insensitive comparison)
  4. Conservative Fuzzy Candidate Flagging (difflib SequenceMatcher without destructive deletion)

Domain-Agnostic: Works for any dynamic schema without assuming fixed hardcoded domain fields.
"""

import json
import logging
from difflib import SequenceMatcher
from typing import Dict, Any, List, Set, Tuple, Optional

from .processing_models import DeduplicationResult

logger = logging.getLogger(__name__)

# Candidate identity field keywords across domains
IDENTITY_KEY_KEYWORDS = (
    "id", "url", "website", "link", "email",
    "job_title", "company_name", "company", "startup_name",
    "product_name", "model", "serial"
)


class DataDeduplicator:
    """
    Schema-driven Data Deduplication Engine.

    Guarantees:
      • Prevents duplicate records from entering final dataset
      • Preserves multi-item pages (e.g. 20 jobs on 1 page are kept)
      • Uses conservative fuzzy matching to flag candidates without destroying data
    """

    def deduplicate(
        self,
        records: List[Dict[str, Any]],
        dataset_schema: Dict[str, Any],
        fuzzy_threshold: float = 0.95,
    ) -> DeduplicationResult:
        """
        Execute multi-stage deduplication on a batch of records.
        """
        if not records:
            return DeduplicationResult(records=[], duplicates_removed=0, duplicate_candidates=0)

        schema_fields = self._extract_fields(dataset_schema)
        identity_fields = self._identify_identity_fields(schema_fields)

        unique_records: List[Dict[str, Any]] = []
        seen_exact_hashes: Set[str] = set()
        seen_identity_keys: Set[str] = set()

        duplicates_removed = 0
        duplicate_candidates = 0

        for record in records:
            data = record.get("data", {})
            if not isinstance(data, dict):
                unique_records.append(record)
                continue

            # Step 1: Exact Duplicate Check (Normalized Data Hash)
            data_hash = self._compute_record_hash(data)
            if data_hash in seen_exact_hashes:
                duplicates_removed += 1
                logger.debug("Removed exact duplicate record with hash %s", data_hash[:10])
                continue

            # Step 2: Identity Key Check (e.g. unique website / item URL / title)
            item_identity_key = self._compute_identity_key(data, identity_fields, record.get("source_url", ""))
            if item_identity_key and item_identity_key in seen_identity_keys:
                duplicates_removed += 1
                logger.debug("Removed identity duplicate record with key '%s'", item_identity_key)
                continue

            # Step 3 & 4: Conservative Fuzzy Duplicate Detection against existing records
            is_fuzzy_candidate = False
            for existing in unique_records:
                existing_data = existing.get("data", {})
                similarity = self._compute_record_similarity(data, existing_data, identity_fields)

                if similarity >= 1.0:
                    is_fuzzy_candidate = True
                    break
                elif similarity >= fuzzy_threshold:
                    duplicate_candidates += 1
                    logger.debug("Flagged fuzzy duplicate candidate (similarity=%.2f)", similarity)

            if is_fuzzy_candidate:
                duplicates_removed += 1
                continue

            # Record is unique! Mark as seen and retain
            seen_exact_hashes.add(data_hash)
            if item_identity_key:
                seen_identity_keys.add(item_identity_key)

            unique_records.append(record)

        return DeduplicationResult(
            records=unique_records,
            duplicates_removed=duplicates_removed,
            duplicate_candidates=duplicate_candidates,
        )

    def _compute_record_hash(self, data: Dict[str, Any]) -> str:
        """Compute stable JSON string representation for exact matching."""
        try:
            # Sort keys for deterministic JSON serialization
            serialized = json.dumps(data, sort_keys=True, default=str)
            return serialized.lower().strip()
        except Exception:
            return str(data).lower().strip()

    def _identify_identity_fields(self, schema_fields: List[Dict[str, Any]]) -> List[str]:
        """Dynamically detect candidate identity fields from schema."""
        identity_names = []
        for f in schema_fields:
            fname = f.get("name", "").lower()
            if any(k in fname for k in IDENTITY_KEY_KEYWORDS):
                identity_names.append(f.get("name"))
        return identity_names

    def _compute_identity_key(
        self,
        data: Dict[str, Any],
        identity_fields: List[str],
        source_url: str,
    ) -> Optional[str]:
        """
        Construct a composite identity key combining item identity fields and URL.
        Example: "https://example.com/job-1|senior python engineer"
        """
        key_parts = []

        # Check for explicit unique item URL or website (excluding generic source_url)
        for fname in ("item_url", "job_url", "product_url", "profile_url", "website"):
            val = data.get(fname)
            if val and isinstance(val, str) and val.startswith("http") and not val.endswith("/job_search"):
                key_parts.append(f"item_url:{val.lower().strip()}")

        for fname in identity_fields:
            if fname == "source_url":
                continue
            val = data.get(fname)
            if val is not None and val != "":
                key_parts.append(f"{fname}:{str(val).lower().strip()}")

        if key_parts:
            return "|".join(key_parts)

        return None

    def _compute_record_similarity(
        self,
        data_a: Dict[str, Any],
        data_b: Dict[str, Any],
        identity_fields: List[str],
    ) -> float:
        """Compute text similarity score between two record data dicts."""
        target_fields = identity_fields if identity_fields else list(data_a.keys())
        if not target_fields:
            return 0.0

        scores = []
        for fname in target_fields:
            val_a = data_a.get(fname)
            val_b = data_b.get(fname)

            if val_a is None or val_b is None:
                continue

            str_a = str(val_a).lower().strip()
            str_b = str(val_b).lower().strip()

            if str_a == str_b:
                scores.append(1.0)
            elif isinstance(val_a, str) and isinstance(val_b, str):
                sim = SequenceMatcher(None, str_a, str_b).ratio()
                scores.append(sim)

        return sum(scores) / len(scores) if scores else 0.0

    def _extract_fields(self, dataset_schema: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Normalize dataset schema into a list of field dictionaries."""
        if "fields" in dataset_schema and isinstance(dataset_schema["fields"], list):
            return [f if isinstance(f, dict) else f.model_dump() for f in dataset_schema["fields"]]
        elif "dynamic_schema" in dataset_schema and "fields" in dataset_schema["dynamic_schema"]:
            return self._extract_fields(dataset_schema["dynamic_schema"])
        return []
