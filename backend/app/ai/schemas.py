"""
Pydantic models for AI request/response validation.

These schemas enforce structured output from the LLM,
preventing arbitrary raw text from entering the database.

Prompt 2 — Requirement Analyzer & Dynamic Dataset Schema Generator:
  • DataField: typed field definition (name, type, description, required)
  • DynamicSchema: auto-derived dataset schema
  • build_dynamic_schema(): constructs a DynamicSchema from AI output
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional


# ──────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────

VALID_FIELD_TYPES = frozenset({
    "string", "number", "boolean", "date",
    "url", "currency", "array",
})


# ──────────────────────────────────────────────
# Data field definition (dynamic schema)
# ──────────────────────────────────────────────

class DataField(BaseModel):
    """A single field in the dynamically generated dataset schema."""
    name: str = Field(
        ...,
        description="snake_case field name, e.g. 'company_name'"
    )
    type: str = Field(
        ...,
        description="One of: string, number, boolean, date, url, currency, array"
    )
    description: str = Field(
        ...,
        description="Human-readable description of this field"
    )
    required: bool = Field(
        default=True,
        description="Whether this field is mandatory"
    )

    @field_validator("type")
    @classmethod
    def normalise_type(cls, v: str) -> str:
        v = v.lower().strip()
        if v not in VALID_FIELD_TYPES:
            return "string"          # safe fallback
        return v

    @field_validator("name")
    @classmethod
    def normalise_name(cls, v: str) -> str:
        return v.strip().lower().replace(" ", "_").replace("-", "_")


# ──────────────────────────────────────────────
# Workflow step
# ──────────────────────────────────────────────

class WorkflowStep(BaseModel):
    """A single step in the AI-generated data-collection workflow."""
    step_number: int = Field(..., description="Sequential step number")
    action: str = Field(
        ...,
        description="Action to perform, e.g. 'search', 'extract', 'filter'"
    )
    description: str = Field(
        ...,
        description="Human-readable description of this step"
    )
    target: Optional[str] = Field(
        None,
        description="Target resource or data source for this step"
    )


# ──────────────────────────────────────────────
# AI Analysis Result (what the LLM must return)
# ──────────────────────────────────────────────

class AIAnalysisResult(BaseModel):
    """
    Structured output the LLM must produce.
    Every field is validated before it reaches the database.
    """
    intent: str = Field(
        ...,
        description=(
            "The type of research request, e.g. 'job_search', "
            "'company_research', 'product_search', 'market_research', "
            "'lead_generation', 'competitor_analysis', 'general_research'"
        ),
    )
    goal: str = Field(
        ...,
        description="A clear, one-sentence summary of what the user wants"
    )
    record_limit: int = Field(
        default=10,
        ge=1,
        le=1000,
        description="How many records the user wants"
    )
    filters: dict = Field(
        default_factory=dict,
        description="Key-value pairs of constraints, e.g. {'country': 'India', 'founded_after': 2022}"
    )
    fields: list[DataField] = Field(
        default_factory=list,
        description="Typed field definitions for the dataset schema"
    )
    workflow_steps: list[WorkflowStep] = Field(
        default_factory=list,
        description="Ordered steps for a future data-collection workflow"
    )
    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="How confident the AI is in its understanding (0-1)"
    )
    notes: Optional[str] = Field(
        None,
        description="Any additional observations or caveats"
    )


# ──────────────────────────────────────────────
# Dynamic schema (derived server-side)
# ──────────────────────────────────────────────

class DynamicSchema(BaseModel):
    """Auto-generated dataset schema derived from the AI analysis."""
    schema_name: str = Field(
        ..., description="Short snake_case identifier for this schema"
    )
    description: str = Field(
        ..., description="What this dataset contains"
    )
    fields: list[DataField] = Field(default_factory=list)
    total_fields: int = Field(default=0)
    required_count: int = Field(default=0)


# ──────────────────────────────────────────────
# API request / response wrappers
# ──────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    """Incoming request body for POST /api/ai/analyze."""
    prompt: str = Field(
        ...,
        min_length=3,
        max_length=2000,
        description="The user's natural-language data request"
    )


class AnalyzeResponseData(BaseModel):
    """Structured response payload with requirements + dynamic schema."""
    requirements: AIAnalysisResult
    dynamic_schema: DynamicSchema
    filters: dict


class AnalyzeResponse(BaseModel):
    """Standardised API response wrapper."""
    success: bool
    data: Optional[AnalyzeResponseData] = None
    error: Optional[str] = None


# ──────────────────────────────────────────────
# Utility: build a DynamicSchema from AI output
# ──────────────────────────────────────────────

def build_dynamic_schema(result: AIAnalysisResult) -> DynamicSchema:
    """
    Derive a DynamicSchema from the validated AIAnalysisResult.

    • Deduplicates fields by name (first occurrence wins).
    • Ensures source_url is present if not already included.
    """
    seen: set[str] = set()
    unique_fields: list[DataField] = []

    for field in result.fields:
        if field.name not in seen:
            seen.add(field.name)
            unique_fields.append(field)

    # Ensure source_url is always present
    if "source_url" not in seen:
        unique_fields.append(
            DataField(
                name="source_url",
                type="url",
                description="URL of the source where this record was found",
                required=True,
            )
        )

    schema_name = result.intent.replace(" ", "_").lower()

    return DynamicSchema(
        schema_name=schema_name,
        description=result.goal,
        fields=unique_fields,
        total_fields=len(unique_fields),
        required_count=sum(1 for f in unique_fields if f.required),
    )
