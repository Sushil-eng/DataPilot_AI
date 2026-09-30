"""
Source Models — Phase 4, Prompt 1

Pydantic models for source candidates discovered by the Source Discovery Engine.

These models are domain-agnostic: they represent any web source that may contain
data relevant to the user's research request (jobs, companies, products, etc.).
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, field_validator
from urllib.parse import urlparse, urlunparse, urlencode, parse_qs


# ──────────────────────────────────────────────
# Source type enumeration
# ──────────────────────────────────────────────

class SourceType(str, Enum):
    """Supported source types — kept generic, not tied to any domain."""
    WEBSITE = "website"
    SEARCH_RESULT = "search_result"
    API = "api"
    DOCUMENT = "document"
    OTHER = "other"


class SourceStatus(str, Enum):
    """Lifecycle status of a discovered source."""
    DISCOVERED = "discovered"
    FETCHING = "fetching"
    FETCHED = "fetched"
    EXTRACTING = "extracting"
    EXTRACTED = "extracted"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    FAILED = "failed"
    SKIPPED = "skipped"


# ──────────────────────────────────────────────
# Source candidate model
# ──────────────────────────────────────────────

class SourceCandidate(BaseModel):
    """
    A single candidate source discovered by the Source Discovery Engine.

    This model is returned from the discovery phase and persisted to MongoDB.
    It does NOT contain extracted data — only metadata about where data may
    be found.
    """
    url: str = Field(
        ...,
        description="The URL of the discovered source"
    )
    title: str = Field(
        ...,
        description="Title or heading of the source page"
    )
    source_type: SourceType = Field(
        default=SourceType.SEARCH_RESULT,
        description="Classification of the source"
    )
    relevance_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Estimated relevance of this source to the research query (0.0–1.0)"
    )
    discovered_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when this source was discovered"
    )
    status: SourceStatus = Field(
        default=SourceStatus.DISCOVERED,
        description="Current lifecycle status"
    )
    metadata: dict = Field(
        default_factory=dict,
        description="Arbitrary metadata: snippet, search engine rank, etc."
    )

    @field_validator("url", mode="before")
    @classmethod
    def validate_url(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("URL cannot be empty")
        parsed = urlparse(v)
        if parsed.scheme not in ("http", "https", ""):
            raise ValueError(f"Unsupported URL scheme: {parsed.scheme}")
        return v

    def to_db_dict(self, task_id: str, dataset_id: str) -> dict:
        """Convert to a MongoDB document dict."""
        return {
            "task_id": task_id,
            "dataset_id": dataset_id,
            "url": self.url,
            "title": self.title,
            "source_type": self.source_type.value,
            "relevance_score": self.relevance_score,
            "discovered_at": self.discovered_at,
            "status": self.status.value,
            "metadata": self.metadata,
        }


# ──────────────────────────────────────────────
# Discovery request / response wrappers
# ──────────────────────────────────────────────

class DiscoverRequest(BaseModel):
    """Request body for POST /api/tasks/{task_id}/sources/discover"""
    limit: int = Field(
        default=10,
        ge=1,
        le=200,
        description="Maximum number of sources to discover"
    )


class DiscoverResponse(BaseModel):
    """Response body for the discovery endpoint."""
    task_id: str
    source_count: int
    sources: list[dict]


# ──────────────────────────────────────────────
# URL normalisation utilities
# ──────────────────────────────────────────────

def normalise_url(url: str) -> str:
    """
    Normalise a URL for deduplication purposes.

    Rules:
      - Strip whitespace
      - Remove trailing slashes (path only)
      - Remove URL fragments (#...)
      - Normalise scheme to https where http is used
      - Sort query parameters for consistent comparison
      - Lowercase the hostname

    Does NOT aggressively modify paths or remove query params
    to avoid breaking functional URLs.
    """
    url = url.strip()
    if not url:
        return url

    parsed = urlparse(url)

    # Normalise scheme: prefer https for comparison
    scheme = parsed.scheme.lower() if parsed.scheme else "https"
    if scheme == "http":
        scheme = "https"

    # Lowercase the hostname
    netloc = parsed.netloc.lower() if parsed.netloc else ""

    # Remove trailing slash from the path (but keep "/" alone)
    path = parsed.path.rstrip("/") if parsed.path != "/" else parsed.path

    # Sort query parameters for stable comparison
    query_params = parse_qs(parsed.query, keep_blank_values=True)
    sorted_query = urlencode(
        sorted(
            ((k, v[0]) for k, v in query_params.items()),
            key=lambda x: x[0],
        )
    ) if query_params else ""

    # Drop fragment entirely
    return urlunparse((scheme, netloc, path, parsed.params, sorted_query, ""))


def deduplicate_sources(sources: list[SourceCandidate]) -> list[SourceCandidate]:
    """
    Remove duplicate sources based on normalised URL.
    Keeps the first occurrence (highest relevance if pre-sorted).
    """
    seen: set[str] = set()
    unique: list[SourceCandidate] = []

    for source in sources:
        norm = normalise_url(source.url)
        if norm not in seen:
            seen.add(norm)
            unique.append(source)

    return unique
