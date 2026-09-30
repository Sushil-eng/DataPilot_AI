"""
Data Validator Engine — Phase 4, Prompt 3

Schema validation engine enforcing required fields, valid data types, URL safety,
and data integrity without hallucinating missing values.

Domain-Agnostic: Driven strictly by dynamic dataset schema definitions.
"""

import logging
import re
from typing import Dict, Any, List, Tuple, Optional
from urllib.parse import urlparse

from .processing_models import ValidationStatus, ValidationErrorItem, ValidationResult

logger = logging.getLogger(__name__)


class DataValidator:
    """
    Schema-driven Data Validation Engine.

    Rules:
      1. Mandatory check for required fields (required=True)
      2. Missing optional fields (required=False) are permitted as None
      3. Type safety checks for URLs, numbers, dates, booleans, arrays
      4. Preserves extraction confidence score
      5. Never invents or hallucinates missing data
    """

    def validate_records(
        self,
        records: List[Dict[str, Any]],
        dataset_schema: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[ValidationErrorItem]]:
        """
        Validate a batch of records against the dynamic schema.

        Returns:
            (valid_records, invalid_records, all_validation_errors)
        """
        schema_fields = self._extract_fields(dataset_schema)

        valid_records: List[Dict[str, Any]] = []
        invalid_records: List[Dict[str, Any]] = []
        all_errors: List[ValidationErrorItem] = []

        for idx, record in enumerate(records):
            val_result = self.validate_single_record(record, schema_fields, record_index=idx)
            rec_copy = dict(record)

            if val_result.valid:
                rec_copy["validation_status"] = ValidationStatus.VALID.value
                rec_copy["validation_errors"] = []
                valid_records.append(rec_copy)
            else:
                rec_copy["validation_status"] = ValidationStatus.INVALID.value
                rec_copy["validation_errors"] = [e.message for e in val_result.errors]
                invalid_records.append(rec_copy)

            all_errors.extend(val_result.errors)

        return valid_records, invalid_records, all_errors

    def validate_single_record(
        self,
        record: Dict[str, Any],
        schema_fields: List[Dict[str, Any]],
        record_index: int = 0,
    ) -> ValidationResult:
        """Validate a single record against schema fields."""
        errors: List[ValidationErrorItem] = []
        warnings: List[str] = []

        raw_data = record.get("data") if ("data" in record and isinstance(record.get("data"), dict) and record.get("data")) else record
        if not isinstance(raw_data, dict):
            errors.append(
                ValidationErrorItem(
                    record_index=record_index,
                    field="data",
                    message="Record 'data' object is missing or not a valid dictionary",
                )
            )
            return ValidationResult(valid=False, errors=errors, warnings=warnings)

        for field_def in schema_fields:
            fname = field_def.get("name")
            ftype = (field_def.get("type") or "string").lower().strip()
            is_required = field_def.get("required", False)

            val = raw_data.get(fname)
            is_missing = val is None or val == "" or val == [] or val == {}

            # 1. Required Field Check
            if is_required and is_missing:
                errors.append(
                    ValidationErrorItem(
                        record_index=record_index,
                        field=fname,
                        message=f"Required field '{fname}' is missing or null",
                    )
                )
                continue

            # 2. Type Validation (if value is populated)
            if not is_missing:
                type_err = self._validate_field_type(fname, val, ftype, record_index)
                if type_err:
                    if is_required:
                        errors.append(type_err)
                    else:
                        warnings.append(type_err.message)

        is_valid = len(errors) == 0
        return ValidationResult(valid=is_valid, errors=errors, warnings=warnings)

    def _validate_field_type(
        self,
        field_name: str,
        val: Any,
        ftype: str,
        record_index: int,
    ) -> Optional[ValidationErrorItem]:
        """Validate value format according to schema field type."""
        if ftype == "url":
            if not isinstance(val, str):
                return ValidationErrorItem(
                    record_index=record_index,
                    field=field_name,
                    message=f"Field '{field_name}' must be a string URL",
                )
            parsed = urlparse(val)
            if parsed.scheme not in ("http", "https", "ai-fallback") or not (parsed.netloc or parsed.path):
                return ValidationErrorItem(
                    record_index=record_index,
                    field=field_name,
                    message=f"Field '{field_name}' URL '{val[:50]}' is not a valid web address",
                )

        elif ftype == "number":
            if not isinstance(val, (int, float)):
                return ValidationErrorItem(
                    record_index=record_index,
                    field=field_name,
                    message=f"Field '{field_name}' must be numeric (int/float), got {type(val).__name__}",
                )

        elif ftype == "boolean":
            if not isinstance(val, bool):
                return ValidationErrorItem(
                    record_index=record_index,
                    field=field_name,
                    message=f"Field '{field_name}' must be boolean, got {type(val).__name__}",
                )

        elif ftype == "date":
            if isinstance(val, str):
                if not re.match(r"^\d{4}(-\d{2}-\d{2})?$", val):
                    return ValidationErrorItem(
                        record_index=record_index,
                        field=field_name,
                        message=f"Field '{field_name}' date '{val}' must be in YYYY-MM-DD or YYYY format",
                    )

        elif ftype == "currency":
            if isinstance(val, dict):
                if "amount" not in val:
                    return ValidationErrorItem(
                        record_index=record_index,
                        field=field_name,
                        message=f"Currency field '{field_name}' missing 'amount' key",
                    )
            elif not isinstance(val, (int, float)):
                return ValidationErrorItem(
                    record_index=record_index,
                    field=field_name,
                    message=f"Currency field '{field_name}' must be a structured object or number",
                )

        elif ftype == "array":
            if not isinstance(val, list):
                return ValidationErrorItem(
                    record_index=record_index,
                    field=field_name,
                    message=f"Field '{field_name}' must be a list",
                )

        return None

    def _extract_fields(self, dataset_schema: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Normalize dataset schema into a list of field dictionaries."""
        if "fields" in dataset_schema and isinstance(dataset_schema["fields"], list):
            return [f if isinstance(f, dict) else f.model_dump() for f in dataset_schema["fields"]]
        elif "dynamic_schema" in dataset_schema and "fields" in dataset_schema["dynamic_schema"]:
            return self._extract_fields(dataset_schema["dynamic_schema"])
        return []
