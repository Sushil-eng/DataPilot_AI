"""
Query Builder — Phase 4, Prompt 1

Dynamically generates search queries from the AI-produced research requirements.

This module is COMPLETELY generic — it does NOT contain any domain-specific
conditionals like `if intent == "jobs"`.  Instead, it assembles the query
from the structured fields that Phase 3 already extracted:
    • goal
    • intent
    • filters
    • required fields
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────

def build_search_queries(
    goal: str,
    intent: str,
    filters: dict,
    required_fields: list[dict],
    record_limit: int = 10,
    max_queries: int = 3,
) -> list[str]:
    """
    Generate one or more search queries from structured research requirements.

    Strategy:
      1. Primary query — derived from the goal + filters
      2. Field-enriched query — adds important field names for specificity
      3. Filter-focused query — foregrounds filter constraints

    Returns up to ``max_queries`` queries, deduplicated.
    """
    queries: list[str] = []

    # ── 1. Primary query from goal ──
    primary = _build_primary_query(goal, filters)
    if primary:
        queries.append(primary)

    # ── 2. Field-enriched variant ──
    field_query = _build_field_enriched_query(goal, required_fields, filters)
    if field_query and field_query not in queries:
        queries.append(field_query)

    # ── 3. Filter-focused variant ──
    filter_query = _build_filter_focused_query(goal, filters, intent)
    if filter_query and filter_query not in queries:
        queries.append(filter_query)

    # Trim to max
    queries = queries[:max_queries]

    # Fallback: if no queries were built, use the raw goal
    if not queries:
        queries = [goal.strip()]

    logger.info(
        "QueryBuilder: generated %d queries from goal=%r",
        len(queries),
        goal[:80],
    )
    return queries


# ──────────────────────────────────────────────
# Private helpers
# ──────────────────────────────────────────────

def _build_primary_query(goal: str, filters: dict) -> str:
    """
    Build the main search query from the research goal + key filter values.

    Example:
        goal="Find AI startups in India founded after 2022"
        filters={"country": "India", "founded_after": 2022}
        → "Find AI startups in India founded after 2022"
        (goal already contains filter info, so we avoid redundancy)
    """
    # Start with the goal text, which is the most information-dense summary
    parts = [goal.strip()]

    # Append filter values that are NOT already mentioned in the goal
    goal_lower = goal.lower()
    for key, value in filters.items():
        val_str = str(value).strip()
        # Only add if the value isn't already in the goal text
        if val_str.lower() not in goal_lower and len(val_str) < 50:
            # Convert snake_case key to readable form
            readable_key = key.replace("_", " ")
            parts.append(f"{readable_key} {val_str}")

    return " ".join(parts).strip()


def _build_field_enriched_query(
    goal: str,
    required_fields: list[dict],
    filters: dict,
) -> str:
    """
    Build a query that includes important field names.

    This helps search engines surface pages that contain the data
    the user is looking for (e.g., "salary", "website", "price").

    Example:
        goal="Find laptops under 50000 with 16GB RAM"
        fields=[{name: "price"}, {name: "ram"}, {name: "brand"}]
        → "laptops under 50000 16GB RAM price brand specifications"
    """
    # Extract meaningful required field names
    field_names = _extract_field_keywords(required_fields)

    if not field_names:
        return ""

    # Combine goal with top field keywords
    goal_lower = goal.lower()
    extra_terms = [
        name for name in field_names
        if name.lower() not in goal_lower
    ][:5]  # Limit to 5 extra terms

    if not extra_terms:
        return ""

    return f"{goal.strip()} {' '.join(extra_terms)}".strip()


def _build_filter_focused_query(
    goal: str,
    filters: dict,
    intent: str,
) -> str:
    """
    Build a query that foregrounds filter constraints.

    Example:
        intent="company_research"
        filters={"location": "Mumbai", "services": "construction"}
        → "construction companies Mumbai website services location"
    """
    if not filters:
        return ""

    # Build from intent keyword + filter values
    parts: list[str] = []

    # Add intent as a readable keyword (e.g., "company_research" → "company research")
    intent_words = intent.replace("_", " ").strip()
    parts.append(intent_words)

    # Add filter values
    goal_lower = goal.lower()
    for key, value in filters.items():
        val_str = str(value).strip()
        if val_str.lower() not in " ".join(parts).lower() and len(val_str) < 50:
            parts.append(val_str)

    # Add filter keys as context words
    for key in filters:
        readable = key.replace("_", " ")
        if readable.lower() not in " ".join(parts).lower():
            parts.append(readable)

    query = " ".join(parts).strip()

    # If it's essentially the same as the goal, skip it
    if _similarity_ratio(query.lower(), goal.lower()) > 0.8:
        return ""

    return query


def _extract_field_keywords(fields: list[dict]) -> list[str]:
    """
    Extract human-readable keywords from field definitions.

    Filters out generic infrastructure fields like 'source_url',
    'collected_at', 'confidence'.
    """
    SKIP_FIELDS = {
        "source_url", "collected_at", "confidence",
        "id", "_id", "created_at", "updated_at",
    }

    keywords: list[str] = []
    for field in fields:
        name = field.get("name", "")
        if name in SKIP_FIELDS:
            continue
        # Convert snake_case to readable
        readable = name.replace("_", " ").strip()
        if readable:
            keywords.append(readable)

    return keywords


def _similarity_ratio(a: str, b: str) -> float:
    """
    Quick set-based similarity ratio.
    Not a proper edit distance — just word overlap for dedup purposes.
    """
    words_a = set(a.split())
    words_b = set(b.split())
    if not words_a or not words_b:
        return 0.0
    intersection = words_a & words_b
    union = words_a | words_b
    return len(intersection) / len(union)
