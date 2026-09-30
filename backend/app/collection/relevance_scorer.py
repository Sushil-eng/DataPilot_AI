"""
Source Relevance Scorer — Phase 4, Prompt 1

Estimates how relevant a discovered source is to the user's research request.

The score is between 0.0 and 1.0 and represents source relevance only —
it does NOT claim to be a factual-confidence or data-quality metric.

Scoring factors:
  1. URL relevance — do keywords appear in the URL path?
  2. Title relevance — do keywords appear in the page title?
  3. Query keyword overlap — word-level overlap with the search query
  4. Source type — search results from major engines score slightly higher
  5. Requested fields — do field-related terms appear in the source metadata?
"""

import logging
import re
from urllib.parse import urlparse

from .source_models import SourceCandidate, SourceType

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────

def score_source(
    source: SourceCandidate,
    query: str,
    goal: str,
    filters: dict,
    required_fields: list[dict],
) -> float:
    """
    Compute a relevance score for a single source candidate.

    Returns a float in [0.0, 1.0].
    """
    # Extract keyword set from all available context
    keywords = _extract_keywords(query, goal, filters, required_fields)

    if not keywords:
        # No keywords to compare — rely on existing score
        return source.relevance_score

    scores: list[tuple[float, float]] = []  # (score, weight)

    # 1. URL relevance (weight: 0.20)
    url_score = _url_keyword_score(source.url, keywords)
    scores.append((url_score, 0.20))

    # 2. Title relevance (weight: 0.30)
    title_score = _text_keyword_score(source.title, keywords)
    scores.append((title_score, 0.30))

    # 3. Snippet / metadata relevance (weight: 0.25)
    snippet = source.metadata.get("snippet", "")
    snippet_score = _text_keyword_score(snippet, keywords)
    scores.append((snippet_score, 0.25))

    # 4. Source type bonus (weight: 0.10)
    type_score = _source_type_score(source.source_type)
    scores.append((type_score, 0.10))

    # 5. Position bonus from search engine (weight: 0.15)
    position = source.metadata.get("position", 50)
    position_score = max(0.3, 1.0 - (position - 1) * 0.05)
    scores.append((position_score, 0.15))

    # Weighted average
    total_weight = sum(w for _, w in scores)
    if total_weight == 0:
        return 0.5

    weighted_sum = sum(s * w for s, w in scores)
    final_score = weighted_sum / total_weight

    return round(min(1.0, max(0.0, final_score)), 3)


def score_sources(
    sources: list[SourceCandidate],
    query: str,
    goal: str,
    filters: dict,
    required_fields: list[dict],
) -> list[SourceCandidate]:
    """
    Score all sources and sort by relevance (highest first).
    Modifies the relevance_score on each source in-place.
    """
    for source in sources:
        source.relevance_score = score_source(
            source, query, goal, filters, required_fields
        )

    # Sort by score descending
    sources.sort(key=lambda s: s.relevance_score, reverse=True)
    return sources


# ──────────────────────────────────────────────
# Private scoring helpers
# ──────────────────────────────────────────────

def _extract_keywords(
    query: str,
    goal: str,
    filters: dict,
    required_fields: list[dict],
) -> set[str]:
    """
    Build a keyword set from all available context.
    Filters out very short or common stop words.
    """
    STOP_WORDS = {
        "a", "an", "the", "in", "on", "at", "to", "for", "of",
        "and", "or", "is", "are", "was", "were", "be", "been",
        "with", "from", "by", "as", "it", "its", "that", "this",
        "find", "get", "show", "list", "search", "all", "any",
        "has", "have", "not", "but", "if", "each", "every",
    }

    raw_text = f"{query} {goal}"

    # Add filter values
    for value in filters.values():
        raw_text += f" {value}"

    # Add field names
    for field in required_fields:
        name = field.get("name", "").replace("_", " ")
        raw_text += f" {name}"

    # Tokenise and filter
    words = re.findall(r'[a-zA-Z0-9₹$€£]+', raw_text.lower())
    keywords = {w for w in words if len(w) > 2 and w not in STOP_WORDS}

    return keywords


def _url_keyword_score(url: str, keywords: set[str]) -> float:
    """Score based on keyword presence in the URL path and domain."""
    parsed = urlparse(url.lower())
    url_text = f"{parsed.netloc} {parsed.path}".replace("/", " ").replace("-", " ").replace("_", " ")
    url_words = set(re.findall(r'[a-zA-Z0-9]+', url_text))

    if not keywords:
        return 0.5

    overlap = keywords & url_words
    return min(1.0, len(overlap) / max(3, len(keywords) * 0.4))


def _text_keyword_score(text: str, keywords: set[str]) -> float:
    """Score based on keyword presence in a text string."""
    if not text or not keywords:
        return 0.3

    text_lower = text.lower()
    text_words = set(re.findall(r'[a-zA-Z0-9₹$€£]+', text_lower))

    overlap = keywords & text_words
    return min(1.0, len(overlap) / max(3, len(keywords) * 0.3))


def _source_type_score(source_type: SourceType) -> float:
    """Slight bonus for certain source types."""
    TYPE_SCORES = {
        SourceType.SEARCH_RESULT: 0.8,
        SourceType.WEBSITE: 0.7,
        SourceType.API: 0.9,
        SourceType.DOCUMENT: 0.6,
        SourceType.OTHER: 0.5,
    }
    return TYPE_SCORES.get(source_type, 0.5)
