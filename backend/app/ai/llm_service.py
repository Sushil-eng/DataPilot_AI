"""
LLM Service — the core AI layer for DataPilot AI.

Responsibilities:
  1. Receive a user prompt
  2. Send structured instructions to the LLM via an API
  3. Parse the JSON response
  4. Validate it against the Pydantic schema
  5. Return clean, structured data

The provider, API key, and model are all configurable through
environment variables so nothing is hardcoded.
"""

import json
import logging
import httpx
from typing import Optional

from ..config import get_settings
from .prompts import SYSTEM_PROMPT, build_user_prompt
from .schemas import AIAnalysisResult

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# Custom exceptions
# ──────────────────────────────────────────────

class LLMError(Exception):
    """Base exception for LLM-related failures."""
    pass


class LLMConfigError(LLMError):
    """Raised when LLM configuration is missing or invalid."""
    pass


class LLMAPIError(LLMError):
    """Raised when the LLM API returns an error."""
    pass


class LLMParsingError(LLMError):
    """Raised when the LLM response cannot be parsed as valid JSON."""
    pass


class LLMValidationError(LLMError):
    """Raised when the parsed JSON does not match the expected schema."""
    pass


# ──────────────────────────────────────────────
# Provider → base-URL mapping
# ──────────────────────────────────────────────

PROVIDER_URLS = {
    "groq": "https://api.groq.com/openai/v1/chat/completions",
    "openai": "https://api.openai.com/v1/chat/completions",
    "openrouter": "https://openrouter.ai/api/v1/chat/completions",
}


# ──────────────────────────────────────────────
# LLMService
# ──────────────────────────────────────────────

class LLMService:
    """
    Stateless service that turns a natural-language prompt into a
    validated AIAnalysisResult.
    """

    def __init__(self):
        settings = get_settings()

        self.provider: str = getattr(settings, "llm_provider", "").strip().lower()
        self.api_key: str = getattr(settings, "llm_api_key", "").strip()
        self.model: str = getattr(settings, "llm_model", "").strip()
        self.timeout: int = int(getattr(settings, "llm_timeout", 30))

        # ── validate config ──
        if not self.api_key:
            raise LLMConfigError(
                "LLM_API_KEY is not set. Add it to your .env file."
            )
        if not self.provider:
            raise LLMConfigError(
                "LLM_PROVIDER is not set. Add it to your .env file. "
                f"Supported providers: {', '.join(PROVIDER_URLS.keys())}"
            )
        if not self.model:
            raise LLMConfigError(
                "LLM_MODEL is not set. Add it to your .env file."
            )

        self.api_url: str = PROVIDER_URLS.get(self.provider, "")
        if not self.api_url:
            raise LLMConfigError(
                f"Unsupported LLM_PROVIDER '{self.provider}'. "
                f"Supported: {', '.join(PROVIDER_URLS.keys())}"
            )

        logger.info(
            "LLMService initialised  provider=%s  model=%s",
            self.provider,
            self.model,
        )

    # ──────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────

    async def analyze(self, user_prompt: str) -> AIAnalysisResult:
        """
        End-to-end pipeline:
            user prompt → LLM call → parse JSON → validate → return
        """
        raw_response = await self._call_llm(user_prompt)
        parsed_json = self._parse_json(raw_response)
        validated = self._validate(parsed_json)
        return validated

    # ──────────────────────────────────────────
    # Private helpers
    # ──────────────────────────────────────────

    async def _call_llm(self, user_prompt: str) -> str:
        """Send the prompt to the LLM API and return the raw text response."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": build_user_prompt(user_prompt)},
            ],
            "temperature": 0.1,          # low temperature → deterministic output
            "max_tokens": 2048,
            "response_format": {"type": "json_object"},   # force JSON mode where supported
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.api_url,
                    headers=headers,
                    json=payload,
                )

            if response.status_code != 200:
                error_body = response.text
                logger.error(
                    "LLM API error  status=%s  body=%s",
                    response.status_code,
                    error_body[:500],
                )
                raise LLMAPIError(
                    f"LLM API returned status {response.status_code}: {error_body[:300]}"
                )

            data = response.json()
            content: Optional[str] = (
                data.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
            )

            if not content or not content.strip():
                raise LLMAPIError("LLM returned an empty response.")

            logger.debug("LLM raw response (first 500 chars): %s", content[:500])
            return content.strip()

        except httpx.TimeoutException:
            raise LLMAPIError(
                f"LLM API timed out after {self.timeout}s. "
                "Try increasing LLM_TIMEOUT in your .env file."
            )
        except httpx.RequestError as exc:
            raise LLMAPIError(f"Network error while calling LLM API: {exc}")

    def _parse_json(self, raw: str) -> dict:
        """
        Parse the raw LLM text into a Python dict.
        Handles edge cases where the model wraps JSON in markdown fences.
        """
        text = raw.strip()

        # Strip markdown code fences if present
        if text.startswith("```"):
            # Remove opening fence (```json or ```)
            first_newline = text.index("\n")
            text = text[first_newline + 1:]
            # Remove closing fence
            if text.endswith("```"):
                text = text[: -3].strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            logger.error("JSON parse failed: %s — raw: %s", exc, text[:500])
            raise LLMParsingError(
                f"LLM response is not valid JSON: {exc}"
            )

    def _validate(self, data: dict) -> AIAnalysisResult:
        """Validate the parsed dict against the Pydantic schema."""
        try:
            return AIAnalysisResult(**data)
        except Exception as exc:
            logger.error("Schema validation failed: %s — data: %s", exc, data)
            raise LLMValidationError(
                f"LLM response does not match the expected schema: {exc}"
            )
