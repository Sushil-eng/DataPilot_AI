"""
Data Cleaner Engine — Phase 4, Prompt 3

Cleans raw extracted records by stripping HTML artifacts, normalizing whitespace,
unescaping HTML entities, and handling empty string noise safely.

Domain-Agnostic: Operates dynamically on arbitrary field keys.
"""

import html
import logging
import re
from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class DataCleaner:
    """
    Generic Data Cleaning Engine.

    Responsibilities:
      • Strip HTML tags, scripts, styles, and tracking artifacts
      • Trim leading/trailing whitespace
      • Collapse repeated internal whitespace
      • Convert empty noise strings to null (None)
      • Preserve original punctuation and meaning
    """

    def __init__(self):
        # Regex for matching HTML tags
        self._html_tag_re = re.compile(r"<[^>]+>")
        # Regex for collapsing multiple whitespace characters
        self._ws_re = re.compile(r"\s+")

    def clean_records(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Clean a batch of raw extracted record dicts."""
        cleaned_list: List[Dict[str, Any]] = []

        for idx, record in enumerate(records):
            try:
                cleaned_rec = self.clean_single_record(record)
                cleaned_list.append(cleaned_rec)
            except Exception as exc:
                logger.warning("Error cleaning record #%d: %s. Preserving original.", idx, exc)
                cleaned_list.append(record)

        return cleaned_list

    def clean_single_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Clean a single record dictionary."""
        cleaned_record = dict(record)

        raw_data = record.get("data", {})
        if isinstance(raw_data, dict):
            cleaned_data = {}
            for k, v in raw_data.items():
                cleaned_data[k] = self._clean_field_value(v)
            cleaned_record["data"] = cleaned_data

        # Clean top-level text fields if present
        if "source_title" in cleaned_record and isinstance(cleaned_record["source_title"], str):
            cleaned_record["source_title"] = self._clean_string(cleaned_record["source_title"])

        return cleaned_record

    def _clean_field_value(self, val: Any) -> Any:
        """Recursively clean field values (strings, lists, dicts)."""
        if val is None:
            return None

        if isinstance(val, str):
            return self._clean_string(val)

        elif isinstance(val, list):
            cleaned_items = [self._clean_field_value(item) for item in val]
            # Remove None items from array if empty string produced None
            filtered = [item for item in cleaned_items if item is not None]
            return filtered if filtered else None

        elif isinstance(val, dict):
            return {k: self._clean_field_value(v) for k, v in val.items()}

        return val

    def _clean_string(self, text: str) -> Optional[str]:
        """
        Clean string value:
          1. Strip scripts/styles/HTML tags if present
          2. Unescape HTML entities
          3. Normalize whitespace
          4. Return None if empty
        """
        if not text or not isinstance(text, str):
            return None

        s = text.strip()
        if not s:
            return None

        # Check if text contains HTML markup
        if "<" in s and ">" in s:
            s = self._strip_html(s)

        # Unescape HTML entities (&amp;, &quot;, &#39;, &lt;, &gt;, etc.)
        s = html.unescape(s)

        # Collapse multiple whitespace characters into single space
        s = self._ws_re.sub(" ", s).strip()

        # Obvious empty strings become None
        if not s or s.lower() in ("null", "none", "n/a", "undefined"):
            return None

        return s

    def _strip_html(self, raw_html: str) -> str:
        """Strip scripts, styles, and HTML tags using BeautifulSoup with regex fallback."""
        try:
            soup = BeautifulSoup(raw_html, "html.parser")
            for element in soup(["script", "style", "head", "noscript", "svg"]):
                element.decompose()
            cleaned_text = soup.get_text(separator=" ", strip=True)
            return cleaned_text
        except Exception:
            # Fallback regex tag stripping
            no_tags = self._html_tag_re.sub(" ", raw_html)
            return no_tags
