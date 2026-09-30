"""
Search Providers — Phase 4, Prompt 1

Pluggable search-provider abstraction.

Configured via environment variables:
    SEARCH_PROVIDER   — "serper" | "mock"  (default: "mock")
    SEARCH_API_KEY    — API key for the chosen provider
    SEARCH_ENGINE     — Search engine flavour (e.g. "google")

Adding a new provider:
    1. Subclass SearchProvider
    2. Register it in PROVIDER_REGISTRY
"""

import logging
import random
import hashlib
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Optional

import httpx

from ..config import get_settings
from .source_models import SourceCandidate, SourceType, SourceStatus

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# Abstract base class
# ──────────────────────────────────────────────

class SearchProvider(ABC):
    """
    Interface for any search provider.

    Subclasses must implement ``search()`` which takes a query string
    and a result limit, returning a list of SourceCandidate objects.
    """

    @abstractmethod
    async def search(self, query: str, limit: int = 10) -> list[SourceCandidate]:
        """Execute a search and return candidate sources."""
        ...


# ──────────────────────────────────────────────
# Serper (Google Search API) provider
# ──────────────────────────────────────────────

class SerperSearchProvider(SearchProvider):
    """
    Real search provider using Serper.dev (Google Search API).

    Requires:
        SEARCH_API_KEY — Serper API key
    """

    API_URL = "https://google.serper.dev/search"

    def __init__(self, api_key: str, engine: str = "google"):
        self.api_key = api_key
        self.engine = engine

    async def search(self, query: str, limit: int = 10) -> list[SourceCandidate]:
        """Call Serper API and convert results to SourceCandidate objects."""
        headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json",
        }
        payload = {
            "q": query,
            "num": min(limit, 100),  # Serper caps at 100
        }

        logger.info("SerperSearch: query=%r  limit=%d", query, limit)

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.post(
                    self.API_URL,
                    headers=headers,
                    json=payload,
                )

            if response.status_code != 200:
                logger.error(
                    "Serper API error status=%s body=%s",
                    response.status_code,
                    response.text[:500],
                )
                if response.status_code in (401, 403):
                    raise SearchProviderBlockedError(
                        f"Serper API access forbidden/unauthorized (status {response.status_code})"
                    )
                elif response.status_code == 429:
                    raise SearchProviderRateLimitError(
                        "Serper API rate limit reached (status 429)"
                    )
                raise SearchProviderError(
                    f"Serper API returned status {response.status_code}"
                )

            data = response.json()
            candidates: list[SourceCandidate] = []

            # Parse organic results
            organic = data.get("organic", [])
            for idx, result in enumerate(organic[:limit]):
                url = result.get("link", "")
                title = result.get("title", "Untitled")
                snippet = result.get("snippet", "")

                if not url:
                    continue

                # Position-based relevance: first result = highest relevance
                position_score = max(0.5, 1.0 - (idx * 0.04))

                candidates.append(SourceCandidate(
                    url=url,
                    title=title,
                    source_type=SourceType.SEARCH_RESULT,
                    relevance_score=round(position_score, 3),
                    discovered_at=datetime.now(timezone.utc),
                    status=SourceStatus.DISCOVERED,
                    metadata={
                        "snippet": snippet,
                        "position": idx + 1,
                        "search_engine": self.engine,
                        "search_query": query,
                    },
                ))

            logger.info("SerperSearch: got %d candidates", len(candidates))
            return candidates

        except httpx.TimeoutException:
            raise SearchProviderError("Serper API timed out after 15s")
        except httpx.RequestError as exc:
            raise SearchProviderError(f"Network error calling Serper API: {exc}")


# ──────────────────────────────────────────────
# Mock search provider (development / demo)
# ──────────────────────────────────────────────

class MockSearchProvider(SearchProvider):
    """
    Development-mode search provider that returns realistic fake sources
    derived from the query itself.

    The generated URLs and titles vary based on the query content so that
    different research domains produce visibly different mock results.
    """

    # Domain-neutral template pools keyed by broad category signals.
    # The system does NOT do `if intent == "jobs"` — instead it pattern-matches
    # keywords in the *generated query string* to pick plausible domains.
    _DOMAIN_POOLS: dict[str, list[dict]] = {
        "job": [
            {"domain": "linkedin.com/jobs", "title_tpl": "{query} - LinkedIn Jobs"},
            {"domain": "indeed.com", "title_tpl": "{query} | Indeed"},
            {"domain": "naukri.com", "title_tpl": "{query} Jobs - Naukri.com"},
            {"domain": "glassdoor.com/Job", "title_tpl": "{query} – Glassdoor"},
            {"domain": "wellfound.com/jobs", "title_tpl": "{query} Careers - Wellfound"},
            {"domain": "remote.co/remote-jobs", "title_tpl": "Remote {query} Openings"},
            {"domain": "simplyhired.com", "title_tpl": "{query} - SimplyHired"},
            {"domain": "ziprecruiter.com", "title_tpl": "{query} - ZipRecruiter"},
        ],
        "startup": [
            {"domain": "crunchbase.com/discover", "title_tpl": "{query} - Crunchbase"},
            {"domain": "tracxn.com/explore", "title_tpl": "{query} – Tracxn"},
            {"domain": "f6s.com/companies", "title_tpl": "{query} Startups - F6S"},
            {"domain": "ycombinator.com/companies", "title_tpl": "{query} – Y Combinator"},
            {"domain": "wellfound.com/startups", "title_tpl": "{query} - Wellfound"},
            {"domain": "startupindia.gov.in", "title_tpl": "{query} - Startup India"},
            {"domain": "inc42.com/startups", "title_tpl": "{query} - Inc42"},
        ],
        "company": [
            {"domain": "linkedin.com/company", "title_tpl": "{query} Companies - LinkedIn"},
            {"domain": "zaubacorp.com", "title_tpl": "{query} - Zauba Corp"},
            {"domain": "crunchbase.com/organization", "title_tpl": "{query} - Crunchbase"},
            {"domain": "dnb.com/business-directory", "title_tpl": "{query} - D&B"},
            {"domain": "yellowpages.com", "title_tpl": "{query} - Yellow Pages"},
            {"domain": "justdial.com", "title_tpl": "{query} - Justdial"},
            {"domain": "indiamart.com", "title_tpl": "{query} Suppliers - IndiaMART"},
            {"domain": "glassdoor.com/Reviews", "title_tpl": "{query} Reviews - Glassdoor"},
        ],
        "product": [
            {"domain": "amazon.in/s", "title_tpl": "{query} - Amazon.in"},
            {"domain": "flipkart.com/search", "title_tpl": "{query} - Flipkart"},
            {"domain": "smartprix.com", "title_tpl": "{query} Prices - Smartprix"},
            {"domain": "91mobiles.com", "title_tpl": "{query} Specs - 91mobiles"},
            {"domain": "gadgets360.com", "title_tpl": "{query} - NDTV Gadgets"},
            {"domain": "pricebefore.com", "title_tpl": "{query} Price Comparison"},
            {"domain": "croma.com/searchB", "title_tpl": "{query} - Croma"},
        ],
        "real_estate": [
            {"domain": "99acres.com", "title_tpl": "{query} - 99acres"},
            {"domain": "magicbricks.com", "title_tpl": "{query} - Magicbricks"},
            {"domain": "housing.com", "title_tpl": "{query} - Housing.com"},
            {"domain": "nobroker.in", "title_tpl": "{query} - NoBroker"},
            {"domain": "squareyards.com", "title_tpl": "{query} - Square Yards"},
            {"domain": "commonfloor.com", "title_tpl": "{query} - CommonFloor"},
        ],
        "general": [
            {"domain": "google.com/search", "title_tpl": "{query} - Google Search"},
            {"domain": "bing.com/search", "title_tpl": "{query} - Bing"},
            {"domain": "duckduckgo.com", "title_tpl": "{query} - DuckDuckGo"},
            {"domain": "en.wikipedia.org/wiki", "title_tpl": "{query} - Wikipedia"},
            {"domain": "reddit.com/search", "title_tpl": "{query} : Reddit"},
            {"domain": "quora.com/search", "title_tpl": "{query} - Quora"},
            {"domain": "medium.com/search", "title_tpl": "Articles about {query} - Medium"},
        ],
    }

    # Keywords that map to each pool
    _CATEGORY_KEYWORDS: dict[str, list[str]] = {
        "job": ["job", "jobs", "hiring", "career", "developer", "engineer", "vacancy", "openings", "recruitment"],
        "startup": ["startup", "startups", "founded", "founding", "venture", "seed", "unicorn"],
        "company": ["company", "companies", "firm", "firms", "agency", "agencies", "services", "contractor", "construction"],
        "product": ["product", "laptop", "phone", "gadget", "buy", "price", "ram", "specifications", "specs", "under"],
        "real_estate": ["real estate", "property", "apartment", "flat", "house", "rent", "bhk", "sq ft"],
    }

    async def search(self, query: str, limit: int = 10) -> list[SourceCandidate]:
        """Generate realistic mock sources based on query keywords."""
        logger.info("MockSearch: query=%r  limit=%d", query, limit)

        category = self._detect_category(query)
        pool = self._DOMAIN_POOLS.get(category, self._DOMAIN_POOLS["general"])

        # Merge general pool for variety if needed
        if category != "general":
            pool = pool + self._DOMAIN_POOLS["general"][:2]

        candidates: list[SourceCandidate] = []
        query_slug = query.lower().replace(" ", "-")[:60]

        for idx in range(min(limit, len(pool))):
            entry = pool[idx % len(pool)]
            # Deterministic but varied URL based on query hash
            query_hash = hashlib.md5(f"{query}{idx}".encode()).hexdigest()[:8]
            url = f"https://{entry['domain']}/{query_slug}-{query_hash}"
            title = entry["title_tpl"].format(query=query[:80])

            position_score = max(0.5, 1.0 - (idx * 0.04))

            candidates.append(SourceCandidate(
                url=url,
                title=title,
                source_type=SourceType.SEARCH_RESULT,
                relevance_score=round(position_score, 3),
                discovered_at=datetime.now(timezone.utc),
                status=SourceStatus.DISCOVERED,
                metadata={
                    "snippet": f"Mock result for: {query[:100]}",
                    "position": idx + 1,
                    "search_engine": "mock",
                    "search_query": query,
                    "mock": True,
                },
            ))

        # If we need more results than the pool size, generate extras
        while len(candidates) < limit:
            idx = len(candidates)
            query_hash = hashlib.md5(f"{query}{idx}extra".encode()).hexdigest()[:8]
            url = f"https://example.com/results/{query_slug}-{query_hash}"
            title = f"{query[:80]} — Result {idx + 1}"
            position_score = max(0.3, 1.0 - (idx * 0.04))

            candidates.append(SourceCandidate(
                url=url,
                title=title,
                source_type=SourceType.WEBSITE,
                relevance_score=round(position_score, 3),
                discovered_at=datetime.now(timezone.utc),
                status=SourceStatus.DISCOVERED,
                metadata={
                    "snippet": f"Mock result for: {query[:100]}",
                    "position": idx + 1,
                    "search_engine": "mock",
                    "search_query": query,
                    "mock": True,
                },
            ))

        logger.info("MockSearch: generated %d candidates (category=%s)", len(candidates), category)
        return candidates[:limit]

    def _detect_category(self, query: str) -> str:
        """
        Detect the broad category from query keywords.
        This is NOT intent classification — it only picks a mock-data pool.
        """
        query_lower = query.lower()
        scores: dict[str, int] = {}

        for category, keywords in self._CATEGORY_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in query_lower)
            if score > 0:
                scores[category] = score

        if not scores:
            return "general"

        return max(scores, key=scores.get)


# ──────────────────────────────────────────────
# Exa (Metaphor) provider
# ──────────────────────────────────────────────

class ExaSearchProvider(SearchProvider):
    """
    Search provider using Exa API (https://api.exa.ai).
    Provides rich neural search results with full text, highlights, and summaries.
    """

    API_URL = "https://api.exa.ai/search"

    def __init__(self, api_key: str):
        self.api_key = api_key

    async def search(self, query: str, limit: int = 10) -> list[SourceCandidate]:
        """Call Exa Search API and convert results to SourceCandidate with rich contents."""
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
        }
        payload = {
            "query": query,
            "numResults": min(limit, 25),
            "useAutoprompt": True,
            "contents": {
                "text": True,
                "highlights": True,
                "summary": True,
            },
        }

        logger.info("ExaSearch: query=%r  limit=%d", query, limit)

        try:
            async with httpx.AsyncClient(timeout=20) as client:
                response = await client.post(
                    self.API_URL,
                    headers=headers,
                    json=payload,
                )

            if response.status_code != 200:
                logger.error(
                    "Exa API error status=%s body=%s",
                    response.status_code,
                    response.text[:500],
                )
                if response.status_code in (401, 403):
                    raise SearchProviderBlockedError(
                        f"Exa API access forbidden/unauthorized (status {response.status_code})"
                    )
                elif response.status_code == 429:
                    raise SearchProviderRateLimitError(
                        "Exa API rate limit reached (status 429)"
                    )
                raise SearchProviderError(
                    f"Exa API returned status {response.status_code}"
                )

            data = response.json()
            results = data.get("results", [])
            candidates: list[SourceCandidate] = []

            for idx, item in enumerate(results[:limit]):
                url = item.get("url", "")
                title = item.get("title", "Untitled")
                text = item.get("text", "")
                highlights = item.get("highlights", [])
                summary = item.get("summary", "")
                snippet = " ".join(highlights) if highlights else (summary or text[:300])

                if not url:
                    continue

                score = item.get("score")
                position_score = float(score) if isinstance(score, (int, float)) and score > 0 else max(0.5, 1.0 - (idx * 0.04))

                pub_date = item.get("publishedDate") or item.get("published_date") or ""
                author = item.get("author") or ""

                candidates.append(SourceCandidate(
                    url=url,
                    title=title,
                    source_type=SourceType.SEARCH_RESULT,
                    relevance_score=round(min(1.0, position_score), 3),
                    discovered_at=datetime.now(timezone.utc),
                    status=SourceStatus.DISCOVERED,
                    metadata={
                        "snippet": snippet,
                        "text": text,
                        "highlights": highlights,
                        "summary": summary,
                        "published_date": pub_date,
                        "author": author,
                        "position": idx + 1,
                        "search_engine": "exa",
                        "search_query": query,
                    },
                ))

            logger.info("ExaSearch: got %d candidates", len(candidates))
            return candidates

        except httpx.TimeoutException:
            raise SearchProviderError("Exa API timed out after 20s")
        except httpx.RequestError as exc:
            raise SearchProviderError(f"Network error calling Exa API: {exc}")


# ──────────────────────────────────────────────
# Exceptions
# ──────────────────────────────────────────────

class SearchProviderError(Exception):
    """Raised when a search provider fails."""
    pass


class SearchProviderBlockedError(SearchProviderError):
    """Raised when a search provider returns 401/403 or blocks access."""
    pass


class SearchProviderRateLimitError(SearchProviderError):
    """Raised when a search provider rate limits (429)."""
    pass


class SearchProviderConfigError(SearchProviderError):
    """Raised when search provider configuration is invalid."""
    pass


# ──────────────────────────────────────────────
# Factory
# ──────────────────────────────────────────────

PROVIDER_REGISTRY: dict[str, type] = {
    "serper": SerperSearchProvider,
    "exa": ExaSearchProvider,
    "mock": MockSearchProvider,
}


def create_search_provider() -> SearchProvider:
    """
    Create a search provider based on environment configuration.

    Reads:
        SEARCH_PROVIDER  — provider name (default: "mock")
        SEARCH_API_KEY   — API key (required for non-mock providers)
        SEARCH_ENGINE    — engine flavour (default: "google")
    """
    settings = get_settings()

    provider_name = settings.search_provider.strip().lower()
    api_key = settings.search_api_key.strip()
    engine = settings.search_engine.strip().lower()

    if provider_name not in PROVIDER_REGISTRY:
        raise SearchProviderConfigError(
            f"Unknown SEARCH_PROVIDER '{provider_name}'. "
            f"Supported: {', '.join(PROVIDER_REGISTRY.keys())}"
        )

    if provider_name == "mock":
        logger.info("Using MockSearchProvider (no API key required)")
        return MockSearchProvider()

    if not api_key:
        raise SearchProviderConfigError(
            f"SEARCH_API_KEY is required for provider '{provider_name}'. "
            "Set it in your .env file."
        )

    if provider_name == "serper":
        logger.info("Using SerperSearchProvider (engine=%s)", engine)
        return SerperSearchProvider(api_key=api_key, engine=engine)

    if provider_name == "exa":
        logger.info("Using ExaSearchProvider")
        return ExaSearchProvider(api_key=api_key)

    # Generic fallback — shouldn't reach here given the registry check
    raise SearchProviderConfigError(f"Provider '{provider_name}' is not implemented.")
