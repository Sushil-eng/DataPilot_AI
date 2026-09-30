"""
Data Extractor Engine — Phase 4, Prompt 2

Generic, schema-driven data extraction engine.

Discovered Sources → Fetch Source Content → Extract Information → Dynamic Schema Mapping → Raw Structured Records

Key Principles:
1. Dynamic & Domain-Agnostic: Driven entirely by AI-generated dataset schema (jobs, companies, products, leads, real estate, etc.).
2. Multi-Record Support: Single page can yield 1 or many records (`records: [...]`).
3. Deterministic + AI Extraction: Attempts JSON-LD / HTML structure first, falls back to LLM extraction or Mock extraction.
4. Source Provenance: Preserves source_url, source_title, extracted_at, source_id on every record.
5. Strict Validation & Non-Fabrication: Rejects invalid JSON, sets missing fields to null, calculates extraction confidence.
"""

import json
import logging
import re
import random
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup

from ..config import get_settings
from ..ai.llm_service import LLMService, LLMError
from .extraction_models import ExtractedRecord, ExtractionResult

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# Dedicated Extraction Prompt (Section 9)
# ──────────────────────────────────────────────

EXTRACTION_SYSTEM_PROMPT = """You are a precision structured data extraction engine for DataPilot AI.

CRITICAL INSTRUCTIONS:
1. Extract structured records from the provided source web content.
2. Use ONLY information explicitly present in the supplied source text. Do NOT invent, assume, or hallucinate facts or missing values.
3. Strict Schema Mapping: Return ONLY the fields defined in the requested target schema.
4. Missing Values: If a schema field is not mentioned or unavailable in the source text, set its value to null.
5. Multiple Records: If the page contains multiple items (e.g. a list of products, jobs, companies, directory listings), return ALL valid items up to the requested limit as separate records in the array.
6. Truthfulness: Do NOT infer unsupported facts. Preserve original text values faithfully.

Return ONLY a valid JSON object with the key "records" containing an array of record objects:
{
  "records": [
    {
      "field_name_1": "value_1",
      "field_name_2": null
    }
  ]
}
"""


def build_extraction_user_prompt(
    source_text: str,
    source_url: str,
    source_title: str,
    schema_fields: List[Dict[str, Any]],
    research_requirements: Optional[str] = None,
    record_limit: int = 10,
) -> str:
    schema_desc = json.dumps(schema_fields, indent=2)
    truncated_text = source_text[:12000] if len(source_text) > 12000 else source_text

    prompt_parts = [
        f"SOURCE URL: {source_url}",
        f"SOURCE TITLE: {source_title or 'Untitled'}",
    ]
    if research_requirements:
        prompt_parts.append(f"RESEARCH GOAL / REQUIREMENTS: {research_requirements}")

    prompt_parts.extend([
        f"MAX RECORD LIMIT: {record_limit}",
        f"TARGET DATASET SCHEMA (Extract ONLY these fields):\n{schema_desc}",
        f"\nSOURCE CONTENT:\n{truncated_text}",
    ])

    return "\n\n".join(prompt_parts)


# ──────────────────────────────────────────────
# Confidence Scoring Helper (Section 12)
# ──────────────────────────────────────────────

def calculate_confidence(record_data: Dict[str, Any], schema_fields: List[Dict[str, Any]]) -> float:
    """
    Calculate extraction confidence score (0.0 to 1.0).
    Based on field completeness ratio and required field fulfillment.
    Represent extraction quality, NOT factual truth.
    """
    if not schema_fields:
        return 0.8

    total_fields = len(schema_fields)
    populated_count = 0
    required_fields = [f for f in schema_fields if f.get("required", False)]
    total_required = len(required_fields)
    populated_required = 0

    for f in schema_fields:
        name = f.get("name")
        val = record_data.get(name)
        is_populated = val is not None and val != "" and val != [] and val != {}
        if is_populated:
            populated_count += 1
            if f.get("required", False):
                populated_required += 1

    field_ratio = populated_count / total_fields if total_fields > 0 else 1.0
    req_ratio = populated_required / total_required if total_required > 0 else 1.0

    score = 0.6 * req_ratio + 0.4 * field_ratio
    return round(max(0.1, min(1.0, score)), 2)


# ──────────────────────────────────────────────
# Dynamic Mock Record Generator (Section 17)
# ──────────────────────────────────────────────

class DynamicMockGenerator:
    """
    Generates realistic, domain-aware mock records strictly adhering to the dynamic schema.
    Used when EXTRACTION_MODE=mock for hackathon development.
    """

    @classmethod
    def generate_mock_records(
        cls,
        schema_fields: List[Dict[str, Any]],
        source_url: str,
        source_title: str,
        record_limit: int = 5,
    ) -> List[Dict[str, Any]]:
        num_records = min(max(2, random.randint(3, 5)), record_limit)
        records = []

        field_names = [f.get("name", "").lower() for f in schema_fields]
        domain_type = cls._detect_domain_type(field_names)

        for i in range(num_records):
            record_data = {}
            for field in schema_fields:
                name = field.get("name")
                ftype = field.get("type", "string").lower()
                req = field.get("required", False)

                # Occasionally set optional fields to None (15% chance)
                if not req and random.random() < 0.15:
                    record_data[name] = None
                    continue

                record_data[name] = cls._generate_field_value(name, ftype, domain_type, index=i)

            # Ensure source_url field if present
            if "source_url" in field_names and not record_data.get("source_url"):
                record_data["source_url"] = source_url

            records.append(record_data)

        return records

    @classmethod
    def _detect_domain_type(cls, field_names: List[str]) -> str:
        s = " ".join(field_names)
        if any(k in s for k in ("job", "salary", "experience", "role", "designation")):
            return "job"
        elif any(k in s for k in ("startup", "company", "funding", "founded", "investors", "headquarters")):
            return "company"
        elif any(k in s for k in ("laptop", "price", "ram", "storage", "processor", "specs", "brand", "model", "product")):
            return "product"
        elif any(k in s for k in ("real_estate", "property", "bhk", "sqft", "rent", "address")):
            return "property"
        elif any(k in s for k in ("construction", "contractor", "services", "projects")):
            return "services"
        return "general"

    @classmethod
    def _generate_field_value(cls, name: str, ftype: str, domain: str, index: int) -> Any:
        name_lower = name.lower()

        # Specific domain matchers
        if domain == "job":
            if "title" in name_lower or "role" in name_lower:
                return ["Senior Python Engineer", "Lead AI/ML Architect", "Backend Developer", "Full Stack Engineer", "Data Scientist"][index % 5]
            if "company" in name_lower:
                return ["TechSolutions Pvt Ltd", "Nexus AI Corp", "DataPulse Systems", "InnoWave Labs", "CyberCloud India"][index % 5]
            if "location" in name_lower:
                return ["Mumbai, Maharashtra", "Bengaluru, Karnataka", "Remote (India)", "Pune, Maharashtra", "Gurugram, Haryana"][index % 5]
            if "salary" in name_lower:
                return ["₹18,000,000 - ₹24,000,000 P.A.", "₹1,500,000 - ₹2,200,000 LPA", "₹2,500,000 LPA", "₹1,200,000 LPA", "₹3,000,000 LPA"][index % 5]

        elif domain == "company":
            if "company" in name_lower or "name" in name_lower or "startup" in name_lower:
                return ["Aura AI Systems", "NeuroCode Analytics", "KubeScale Robotics", "Veda Data Labs", "Zenith FinTech"][index % 5]
            if "location" in name_lower or "headquarters" in name_lower or "city" in name_lower:
                return ["Bengaluru, India", "Mumbai, India", "Hyderabad, India", "Pune, India", "Delhi NCR, India"][index % 5]
            if "founded" in name_lower or "year" in name_lower:
                return 2023 if ftype == "number" else "2023"
            if "funding" in name_lower:
                return "$2.5M Seed" if ftype == "string" else 2500000

        elif domain == "product":
            if "product" in name_lower or "laptop" in name_lower or "name" in name_lower:
                return ["ProBook Ultra 15", "ZenBook AI 14", "IdeaPad Slim 5", "TUF Gaming A15", "Swift Go 14"][index % 5]
            if "brand" in name_lower:
                return ["HP", "ASUS", "Lenovo", "Dell", "Acer"][index % 5]
            if "price" in name_lower:
                return 48990 if ftype == "number" else "₹48,990"
            if "ram" in name_lower:
                return "16GB LPDDR5"
            if "storage" in name_lower:
                return "512GB NVMe SSD"

        elif domain == "services":
            if "company" in name_lower or "name" in name_lower:
                return ["Apex Infrastructure Ltd", "BuildCraft Builders", "Mumbai Construction Corp", "Skyline Structures", "Prime Infra Solutions"][index % 5]
            if "location" in name_lower:
                return ["Mumbai, Maharashtra", "Navi Mumbai", "Thane, Maharashtra", "Andheri East, Mumbai", "Bandra, Mumbai"][index % 5]
            if "services" in name_lower:
                return ["Commercial Construction, Turnkey Projects, Civil Engineering", "Residential High-Rises, Structural Audits", "Interior Architecture, Commercial Fitouts"][index % 3]

        # Generic field matchers by name
        if "website" in name_lower or "url" in name_lower or ftype == "url":
            return f"https://example.com/item-{index + 1}"
        if "email" in name_lower:
            return f"contact{index + 1}@example.com"
        if "phone" in name_lower:
            return f"+91 98200 9180{index}"

        # Generic fallbacks by type
        if ftype == "number":
            return random.randint(10, 500)
        elif ftype == "boolean":
            return True
        elif ftype == "array":
            return ["Item 1", "Item 2"]
        elif ftype == "currency":
            return f"₹{random.randint(1, 50) * 1000}"
        elif ftype == "date":
            return "2024-01-15"

        return f"Sample {name.replace('_', ' ').title()} {index + 1}"


# ──────────────────────────────────────────────
# DataExtractor Engine
# ──────────────────────────────────────────────

class DataExtractor:
    """
    Main dynamic extraction service.

    Pipeline:
      1. Deterministic JSON-LD / HTML extraction (if valid structured data exists)
      2. LLM AI Extraction (using Phase 3 LLM Service abstraction)
      3. Mock Extraction Mode (if EXTRACTION_MODE=mock)
      4. Schema validation, confidence scoring, provenance & record limit trimming
    """

    def __init__(self, llm_service: Optional[LLMService] = None):
        settings = get_settings()
        self.mode = getattr(settings, "extraction_mode", "mock").strip().lower()
        self.llm_service = llm_service

    async def extract(
        self,
        source_content: Dict[str, Any],
        dataset_schema: Dict[str, Any],
        research_requirements: Optional[Any] = None,
        source_id: Optional[str] = None,
        record_limit: Optional[int] = None,
    ) -> ExtractionResult:
        """
        Extract structured records from source content using the provided dataset schema.
        """
        url = source_content.get("url", "")
        title = source_content.get("title", "")
        html = source_content.get("html", "")
        text = source_content.get("text", "")
        fetch_error = source_content.get("error")

        schema_fields = self._extract_schema_fields(dataset_schema)
        limit = record_limit or dataset_schema.get("record_limit", 10)

        # 0. Check if fetch failed
        if fetch_error and not html and not text and self.mode != "mock":
            return ExtractionResult(
                source_id=source_id,
                source_url=url,
                source_title=title,
                records=[],
                total_records=0,
                status="failed",
                error_message=f"Fetch failed: {fetch_error}",
            )

        # 1. Mock Extraction Mode (Section 17)
        if self.mode == "mock":
            logger.info("Extracting records in MOCK mode for url=%s", url)
            mock_records_raw = DynamicMockGenerator.generate_mock_records(
                schema_fields=schema_fields,
                source_url=url,
                source_title=title,
                record_limit=limit,
            )
            extracted_records = self._format_records(
                raw_records=mock_records_raw,
                schema_fields=schema_fields,
                source_url=url,
                source_title=title,
                source_id=source_id,
            )
            return ExtractionResult(
                source_id=source_id,
                source_url=url,
                source_title=title,
                records=extracted_records[:limit],
                total_records=len(extracted_records[:limit]),
                status="extracted",
            )

        # 2. Deterministic HTML / JSON-LD Extraction (Section 6)
        deterministic_records = self._extract_json_ld(html, schema_fields, url, title)
        if deterministic_records and len(deterministic_records) >= 1:
            logger.info("Found %d records via JSON-LD for url=%s", len(deterministic_records), url)
            formatted = self._format_records(
                raw_records=deterministic_records,
                schema_fields=schema_fields,
                source_url=url,
                source_title=title,
                source_id=source_id,
            )
            return ExtractionResult(
                source_id=source_id,
                source_url=url,
                source_title=title,
                records=formatted[:limit],
                total_records=len(formatted[:limit]),
                status="extracted",
            )

        # 3. LLM AI Extraction (Section 7, 8, 9)
        try:
            if not self.llm_service:
                self.llm_service = LLMService()

            req_str = str(research_requirements) if research_requirements else ""
            user_prompt = build_extraction_user_prompt(
                source_text=text or title or url,
                source_url=url,
                source_title=title,
                schema_fields=schema_fields,
                research_requirements=req_str,
                record_limit=limit,
            )

            raw_llm_json = await self._call_llm_for_extraction(user_prompt)
            parsed_records = self._parse_and_validate_llm_json(raw_llm_json, schema_fields)

            formatted = self._format_records(
                raw_records=parsed_records,
                schema_fields=schema_fields,
                source_url=url,
                source_title=title,
                source_id=source_id,
            )

            return ExtractionResult(
                source_id=source_id,
                source_url=url,
                source_title=title,
                records=formatted[:limit],
                total_records=len(formatted[:limit]),
                status="extracted" if formatted else "empty",
                error_message=None if formatted else "No records found matching schema in source content.",
            )

        except Exception as exc:
            logger.warning("LLM extraction failed for url=%s: %s", url, exc)
            return ExtractionResult(
                source_id=source_id,
                source_url=url,
                source_title=title,
                records=[],
                total_records=0,
                status="failed",
                error_message=f"Extraction error: {type(exc).__name__} - {str(exc)[:200]}",
            )

    # ──────────────────────────────────────────
    # Helper Methods
    # ──────────────────────────────────────────

    def _extract_schema_fields(self, dataset_schema: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Normalize dataset schema input to a clean list of field dicts."""
        if "fields" in dataset_schema and isinstance(dataset_schema["fields"], list):
            fields = dataset_schema["fields"]
            res = []
            for f in fields:
                if isinstance(f, dict):
                    res.append(f)
                elif hasattr(f, "model_dump"):
                    res.append(f.model_dump())
            return res
        elif "dynamic_schema" in dataset_schema and "fields" in dataset_schema["dynamic_schema"]:
            return self._extract_schema_fields(dataset_schema["dynamic_schema"])
        return []

    def _extract_json_ld(
        self,
        html: str,
        schema_fields: List[Dict[str, Any]],
        url: str,
        title: str,
    ) -> List[Dict[str, Any]]:
        """Extract structured records from application/ld+json script tags in HTML."""
        if not html:
            return []

        try:
            soup = BeautifulSoup(html, "html.parser")
            script_tags = soup.find_all("script", type="application/ld+json")
            if not script_tags:
                return []

            extracted = []
            expected_names = [f.get("name") for f in schema_fields if f.get("name")]

            for tag in script_tags:
                if not tag.string:
                    continue
                try:
                    data = json.loads(tag.string.strip())
                    items = data if isinstance(data, list) else [data]
                    if isinstance(data, dict) and "@graph" in data:
                        items = data["@graph"]

                    for item in items:
                        if not isinstance(item, dict):
                            continue

                        # Check if JSON-LD object shares keys with requested dataset schema
                        record_dict = {}
                        matches = 0
                        for name in expected_names:
                            # Direct key or camelCase match
                            camel_name = re.sub(r'_([a-z])', lambda m: m.group(1).upper(), name)
                            val = item.get(name) or item.get(camel_name) or item.get(name.replace("_", ""))
                            if val is not None:
                                record_dict[name] = val
                                matches += 1
                            else:
                                record_dict[name] = None

                        if matches >= max(1, len(expected_names) // 3):
                            extracted.append(record_dict)

                except json.JSONDecodeError:
                    continue

            return extracted

        except Exception as exc:
            logger.debug("JSON-LD parse error: %s", exc)
            return []

    async def _call_llm_for_extraction(self, user_prompt: str) -> str:
        """Call LLM API using custom extraction prompt."""
        headers = {
            "Authorization": f"Bearer {self.llm_service.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.llm_service.model,
            "messages": [
                {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.1,
            "max_tokens": 2048,
            "response_format": {"type": "json_object"},
        }

        import httpx
        async with httpx.AsyncClient(timeout=self.llm_service.timeout) as client:
            response = await client.post(self.llm_service.api_url, headers=headers, json=payload)

        if response.status_code != 200:
            raise LLMError(f"LLM API returned {response.status_code}: {response.text[:200]}")

        data = response.json()
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        return content

    def _parse_and_validate_llm_json(
        self,
        raw_json_str: str,
        schema_fields: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Safe parsing & schema alignment of raw LLM JSON output."""
        text = raw_json_str.strip()
        if text.startswith("```"):
            first_nl = text.index("\n")
            text = text[first_nl + 1:]
            if text.endswith("```"):
                text = text[:-3].strip()

        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            # Fallback repair: search for json object using regex
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                try:
                    parsed = json.loads(match.group(0))
                except json.JSONDecodeError:
                    return []
            else:
                return []

        raw_records = []
        if isinstance(parsed, dict):
            raw_records = parsed.get("records", [parsed])
        elif isinstance(parsed, list):
            raw_records = parsed

        if not isinstance(raw_records, list):
            return []

        aligned_records = []
        expected_names = [f.get("name") for f in schema_fields if f.get("name")]

        for rec in raw_records:
            if not isinstance(rec, dict):
                continue
            aligned_rec = {}
            for name in expected_names:
                aligned_rec[name] = rec.get(name, None)
            aligned_records.append(aligned_rec)

        return aligned_records

    def _format_records(
        self,
        raw_records: List[Dict[str, Any]],
        schema_fields: List[Dict[str, Any]],
        source_url: str,
        source_title: str,
        source_id: Optional[str],
    ) -> List[ExtractedRecord]:
        """Convert raw dict records to ExtractedRecord objects with confidence & provenance."""
        formatted = []
        now = datetime.now(timezone.utc)

        for raw_data in raw_records:
            # Ensure source_url field is filled if schema contains it
            if "source_url" in raw_data and not raw_data["source_url"]:
                raw_data["source_url"] = source_url

            conf = calculate_confidence(raw_data, schema_fields)

            rec = ExtractedRecord(
                data=raw_data,
                source_url=source_url,
                source_title=source_title,
                source_id=source_id,
                extracted_at=now,
                confidence=conf,
            )
            formatted.append(rec)

        return formatted
