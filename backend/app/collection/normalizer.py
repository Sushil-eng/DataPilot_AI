"""
Data Normalizer Engine — Phase 4, Prompt 3

Schema-driven type conversion and normalization engine.

Supported dynamic field types:
  • string
  • number
  • boolean
  • date (ISO YYYY-MM-DD format)
  • url (normalises http/https, rejects unsafe protocols)
  • currency (structured {amount, currency} object, preserves original symbol/code)
  • array (splits delimited strings into clean list)

Domain-Agnostic: Driven strictly by AI-generated dataset schema definitions.
"""

import logging
import re
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from urllib.parse import urlparse, urlunparse, urlencode, parse_qs
from dateutil import parser as date_parser

logger = logging.getLogger(__name__)

# Currency symbol → Currency code map
CURRENCY_SYMBOLS = {
    "₹": "INR",
    "rs": "INR",
    "inr": "INR",
    "$": "USD",
    "usd": "USD",
    "€": "EUR",
    "eur": "EUR",
    "£": "GBP",
    "gbp": "GBP",
    "¥": "JPY",
    "jpy": "JPY",
    "a$": "AUD",
    "aud": "AUD",
    "c$": "CAD",
    "cad": "CAD",
}


class DataNormalizer:
    """
    Schema-driven Data Normalization Engine.
    Converts values into standardized types based on dataset schema definitions.
    """

    def normalize_records(
        self,
        records: List[Dict[str, Any]],
        dataset_schema: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Normalize a batch of records against the dataset schema."""
        schema_fields = self._extract_fields(dataset_schema)
        normalized_list: List[Dict[str, Any]] = []

        for idx, record in enumerate(records):
            try:
                norm_rec = self.normalize_single_record(record, schema_fields)
                normalized_list.append(norm_rec)
            except Exception as exc:
                logger.warning("Error normalizing record #%d: %s", idx, exc)
                normalized_list.append(record)

        return normalized_list

    def normalize_single_record(
        self,
        record: Dict[str, Any],
        schema_fields: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Normalize fields inside a single record dictionary."""
        normalized_rec = dict(record)
        raw_data = record.get("data", {})

        if isinstance(raw_data, dict):
            normalized_data = {}
            for field_def in schema_fields:
                fname = field_def.get("name")
                ftype = (field_def.get("type") or "string").lower().strip()
                val = raw_data.get(fname)

                normalized_data[fname] = self.normalize_value(val, ftype)

            # Preserve any remaining fields in data not defined in schema
            for k, v in raw_data.items():
                if k not in normalized_data:
                    normalized_data[k] = v

            normalized_rec["data"] = normalized_data

        return normalized_rec

    def normalize_value(self, val: Any, ftype: str) -> Any:
        """Normalize a single field value according to its schema field type."""
        if val is None:
            return None

        if ftype == "number":
            return self._normalize_number(val)
        elif ftype == "boolean":
            return self._normalize_boolean(val)
        elif ftype == "date":
            return self._normalize_date(val)
        elif ftype == "url":
            return self._normalize_url(val)
        elif ftype == "currency":
            return self._normalize_currency(val)
        elif ftype == "array":
            return self._normalize_array(val)
        else:
            # Default string type
            return self._normalize_string(val)

    def _normalize_string(self, val: Any) -> Optional[str]:
        if val is None:
            return None
        s = str(val).strip()
        return s if s else None

    def _normalize_number(self, val: Any) -> Optional[Any]:
        """
        Normalize numbers:
          "50" -> 50
          "50.0" -> 50.0
          "₹50,000" -> 50000
          "1,200 LPA" -> 1200
        """
        if val is None:
            return None

        if isinstance(val, (int, float)):
            return val

        s = str(val).strip()
        if not s:
            return None

        # Clean commas, currency symbols, and text suffix
        # Extract first contiguous number match
        match = re.search(r"[-+]?\d[\d,]*\.?\d*", s)
        if not match:
            return None

        clean_num_str = match.group(0).replace(",", "")
        try:
            if "." in clean_num_str:
                return float(clean_num_str)
            return int(clean_num_str)
        except ValueError:
            return None

    def _normalize_boolean(self, val: Any) -> Optional[bool]:
        """
        Normalize booleans:
          "yes", "true", "1", True -> True
          "no", "false", "0", False -> False
        """
        if val is None:
            return None

        if isinstance(val, bool):
            return val

        if isinstance(val, (int, float)):
            if val == 1:
                return True
            if val == 0:
                return False

        s = str(val).strip().lower()
        if s in ("true", "yes", "1", "y", "t"):
            return True
        elif s in ("false", "no", "0", "n", "f"):
            return False

        return None

    def _normalize_date(self, val: Any) -> Optional[str]:
        """
        Normalize date strings to ISO YYYY-MM-DD or YYYY format.
        If unparseable -> return None (Do NOT invent dates).
        """
        if val is None:
            return None

        s = str(val).strip()
        if not s:
            return None

        # Check if year only (e.g. 2023)
        if re.match(r"^(19|20)\d{2}$", s):
            return s

        try:
            parsed_dt = date_parser.parse(s, fuzzy=False)
            return parsed_dt.strftime("%Y-%m-%d")
        except Exception:
            try:
                # Fuzzy fallback date parser
                parsed_dt = date_parser.parse(s, fuzzy=True)
                return parsed_dt.strftime("%Y-%m-%d")
            except Exception:
                return None

    def _normalize_url(self, val: Any) -> Optional[str]:
        """
        Normalize URLs:
          - Ensure http:// or https:// scheme
          - Lowercase scheme and hostname
          - Remove trailing slash (except root '/')
          - Drop fragment (#...)
          - Reject dangerous protocols (javascript:, file:, data:)
        """
        if not val or not isinstance(val, str):
            return None

        url_str = val.strip()
        if not url_str:
            return None

        # Reject dangerous protocols
        url_lower = url_str.lower()
        if any(url_lower.startswith(proto) for proto in ("javascript:", "file:", "data:", "ftp:", "about:")):
            return None

        # Ensure scheme
        if not url_lower.startswith("http://") and not url_lower.startswith("https://"):
            url_str = "https://" + url_str

        try:
            parsed = urlparse(url_str)
            scheme = parsed.scheme.lower()
            if scheme not in ("http", "https"):
                return None

            netloc = parsed.netloc.lower()
            if not netloc or ("." not in netloc and netloc != "localhost"):
                return None

            path = "" if parsed.path in ("", "/") else parsed.path.rstrip("/")
            return urlunparse((scheme, netloc, path, parsed.params, parsed.query, ""))
        except Exception:
            return None

    def _normalize_currency(self, val: Any) -> Optional[Any]:
        """
        Normalize currency:
          "₹50,000" -> {"amount": 50000, "currency": "INR"}
          "$1,000" -> {"amount": 1000, "currency": "USD"}
          "50000 INR" -> {"amount": 50000, "currency": "INR"}

        Does NOT convert between currencies (no FX rate changes).
        """
        if val is None:
            return None

        if isinstance(val, dict) and "amount" in val:
            return val

        if isinstance(val, (int, float)):
            return {"amount": val, "currency": "INR"}

        s = str(val).strip()
        if not s:
            return None

        # Detect currency code/symbol
        detected_curr = "INR"
        s_lower = s.lower()
        for sym, code in CURRENCY_SYMBOLS.items():
            if sym in s_lower:
                detected_curr = code
                break

        # Extract numeric amount
        num_val = self._normalize_number(s)
        if num_val is None:
            return None

        return {
            "amount": num_val,
            "currency": detected_curr,
        }

    def _normalize_array(self, val: Any) -> Optional[List[Any]]:
        """
        Normalize array fields:
          "Python, Java, C++" -> ["Python", "Java", "C++"]
          "Commercial Construction | Civil Fitout" -> ["Commercial Construction", "Civil Fitout"]
        """
        if val is None:
            return None

        if isinstance(val, list):
            res = [self._normalize_string(x) for x in val if x is not None]
            return [x for x in res if x is not None] or None

        if isinstance(val, str):
            s = val.strip()
            if not s:
                return None

            # Split on comma, semicolon, or pipe
            delimiters = [",", ";", "|"]
            best_delim = None
            for d in delimiters:
                if d in s:
                    best_delim = d
                    break

            if best_delim:
                parts = [p.strip() for p in s.split(best_delim) if p.strip()]
                cleaned = [self._normalize_string(p) for p in parts if p.strip()]
                return [c for c in cleaned if c is not None] or None
            else:
                return [s]

        return [val]

    def _extract_fields(self, dataset_schema: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Normalize dataset schema into a list of field dictionaries."""
        if "fields" in dataset_schema and isinstance(dataset_schema["fields"], list):
            return [f if isinstance(f, dict) else f.model_dump() for f in dataset_schema["fields"]]
        elif "dynamic_schema" in dataset_schema and "fields" in dataset_schema["dynamic_schema"]:
            return self._extract_fields(dataset_schema["dynamic_schema"])
        return []
