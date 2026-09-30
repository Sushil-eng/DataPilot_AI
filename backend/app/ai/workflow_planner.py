"""
Workflow Planner — Phase 3, Prompt 3

Takes AI requirements + dynamic schema and generates a structured,
validated workflow plan that Phase 4 will execute.

This module ONLY creates the plan. It does NOT perform any real
web searches, scraping, or data collection.
"""

import logging
from typing import Optional

from .schemas import AIAnalysisResult, DynamicSchema, DataField

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# Tool type definitions (Phase 4 will implement these)
# ──────────────────────────────────────────────

VALID_TOOL_TYPES = frozenset({
    "search",
    "extract",
    "transform",
    "validate",
    "deduplicate",
    "store",
})


# ──────────────────────────────────────────────
# Planned workflow step
# ──────────────────────────────────────────────

class PlannedStep:
    """A single step in the workflow plan."""

    def __init__(
        self,
        step_id: str,
        name: str,
        description: str,
        tool: str,
        depends_on: Optional[str] = None,
    ):
        self.id = step_id
        self.name = name
        self.description = description
        self.tool = tool if tool in VALID_TOOL_TYPES else "search"
        self.status = "pending"
        self.depends_on = depends_on
        self.result = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "tool": self.tool,
            "status": self.status,
            "depends_on": self.depends_on,
            "result": self.result,
        }


# ──────────────────────────────────────────────
# Workflow Planner
# ──────────────────────────────────────────────

class WorkflowPlanner:
    """
    Generates a structured data-collection workflow from AI requirements.

    The planner adapts its steps based on the intent, filters, fields,
    and record limit — the same planner handles jobs, companies,
    products, market research, etc.
    """

    def generate(
        self,
        requirements: AIAnalysisResult,
        schema: DynamicSchema,
    ) -> dict:
        """
        Build a complete workflow plan.

        Returns a dict ready to be stored in MongoDB:
        {
            "workflow_type": "data_collection",
            "goal": "...",
            "intent": "...",
            "record_limit": N,
            "steps": [ ... ],
            "total_steps": N,
        }
        """
        steps = self._build_steps(requirements, schema)

        workflow = {
            "workflow_type": "data_collection",
            "goal": requirements.goal,
            "intent": requirements.intent,
            "record_limit": requirements.record_limit,
            "steps": [s.to_dict() for s in steps],
            "total_steps": len(steps),
        }

        logger.info(
            "WorkflowPlanner generated %d steps for intent=%s",
            len(steps),
            requirements.intent,
        )
        return workflow

    # ──────────────────────────────────────────
    # Step generation
    # ──────────────────────────────────────────

    def _build_steps(
        self,
        req: AIAnalysisResult,
        schema: DynamicSchema,
    ) -> list[PlannedStep]:
        """Build the ordered list of workflow steps."""

        field_names = [f.name for f in schema.fields]
        field_list_str = ", ".join(field_names[:8])
        if len(field_names) > 8:
            field_list_str += f" (+{len(field_names) - 8} more)"

        filter_desc = self._describe_filters(req.filters)

        steps: list[PlannedStep] = []

        # ── Step 1: Source Discovery ──
        steps.append(PlannedStep(
            step_id="step_1",
            name="source_discovery",
            description=(
                f"Identify permitted data sources suitable for "
                f"{req.intent.replace('_', ' ')}. "
                f"Target: {req.record_limit} records."
            ),
            tool="search",
        ))

        # ── Step 2: Data Search ──
        steps.append(PlannedStep(
            step_id="step_2",
            name="data_search",
            description=(
                f"Search identified sources for records matching: "
                f"{req.goal}"
                + (f" Filters: {filter_desc}" if filter_desc else "")
            ),
            tool="search",
            depends_on="step_1",
        ))

        # ── Step 3: Data Extraction ──
        steps.append(PlannedStep(
            step_id="step_3",
            name="data_extraction",
            description=(
                f"Extract required fields from raw results: "
                f"{field_list_str}"
            ),
            tool="extract",
            depends_on="step_2",
        ))

        # ── Step 4: Data Transformation / Normalisation ──
        steps.append(PlannedStep(
            step_id="step_4",
            name="data_normalisation",
            description=(
                "Normalise extracted data: standardise formats, "
                "clean whitespace, convert types to match the dataset schema."
            ),
            tool="transform",
            depends_on="step_3",
        ))

        # ── Step 5: Filter Application ──
        if req.filters:
            steps.append(PlannedStep(
                step_id=f"step_{len(steps) + 1}",
                name="filter_application",
                description=(
                    f"Apply user-specified filters: {filter_desc}. "
                    "Remove records that do not match constraints."
                ),
                tool="transform",
                depends_on=steps[-1].id,
            ))

        # ── Step 6: Validation ──
        required_fields = [f.name for f in schema.fields if f.required]
        steps.append(PlannedStep(
            step_id=f"step_{len(steps) + 1}",
            name="data_validation",
            description=(
                f"Validate that all required fields are present and "
                f"correctly typed. Required: "
                f"{', '.join(required_fields[:6])}"
                + (f" (+{len(required_fields) - 6} more)"
                   if len(required_fields) > 6 else "")
            ),
            tool="validate",
            depends_on=steps[-1].id,
        ))

        # ── Step 7: Deduplication ──
        steps.append(PlannedStep(
            step_id=f"step_{len(steps) + 1}",
            name="deduplication",
            description=(
                "Detect and remove duplicate records based on key "
                "identifying fields."
            ),
            tool="deduplicate",
            depends_on=steps[-1].id,
        ))

        # ── Step 8: Source Attachment ──
        steps.append(PlannedStep(
            step_id=f"step_{len(steps) + 1}",
            name="source_attachment",
            description=(
                "Attach source URL and collection timestamp to every "
                "record for provenance tracking."
            ),
            tool="transform",
            depends_on=steps[-1].id,
        ))

        # ── Step 9: Dataset Preparation & Storage ──
        steps.append(PlannedStep(
            step_id=f"step_{len(steps) + 1}",
            name="dataset_storage",
            description=(
                f"Compile final dataset (up to {req.record_limit} records) "
                f"and store in MongoDB."
            ),
            tool="store",
            depends_on=steps[-1].id,
        ))

        return steps

    @staticmethod
    def _describe_filters(filters: dict) -> str:
        """Build a human-readable filter description."""
        if not filters:
            return ""
        parts = [f"{k}={v}" for k, v in filters.items()]
        return ", ".join(parts)


# ──────────────────────────────────────────────
# Workflow Validator
# ──────────────────────────────────────────────

class WorkflowValidationError(Exception):
    """Raised when a workflow plan fails validation."""
    pass


class WorkflowValidator:
    """
    Validates a generated workflow plan before it is saved.
    """

    def validate(
        self,
        workflow: dict,
        schema: DynamicSchema,
    ) -> None:
        """
        Run all validation checks. Raises WorkflowValidationError on failure.
        """
        self._check_has_steps(workflow)
        self._check_valid_tools(workflow)
        self._check_step_order(workflow)
        self._check_required_fields(schema)
        self._check_source_info(schema)
        self._check_record_limit(workflow)

        logger.info("Workflow validation passed (%d steps)", len(workflow.get("steps", [])))

    def _check_has_steps(self, workflow: dict) -> None:
        steps = workflow.get("steps", [])
        if not steps:
            raise WorkflowValidationError("Workflow must have at least one step.")

    def _check_valid_tools(self, workflow: dict) -> None:
        for step in workflow.get("steps", []):
            tool = step.get("tool", "")
            if tool not in VALID_TOOL_TYPES:
                raise WorkflowValidationError(
                    f"Step '{step.get('id')}' uses invalid tool '{tool}'. "
                    f"Valid tools: {', '.join(sorted(VALID_TOOL_TYPES))}"
                )

    def _check_step_order(self, workflow: dict) -> None:
        steps = workflow.get("steps", [])
        seen_ids = set()
        for step in steps:
            step_id = step.get("id", "")
            if not step_id:
                raise WorkflowValidationError("Every step must have an 'id'.")
            if step_id in seen_ids:
                raise WorkflowValidationError(f"Duplicate step ID: '{step_id}'.")
            # Check dependency exists (if specified)
            dep = step.get("depends_on")
            if dep and dep not in seen_ids:
                raise WorkflowValidationError(
                    f"Step '{step_id}' depends on '{dep}' which has not appeared yet."
                )
            seen_ids.add(step_id)

    def _check_required_fields(self, schema: DynamicSchema) -> None:
        if not schema.fields:
            raise WorkflowValidationError(
                "Dynamic schema has no fields defined."
            )

    def _check_source_info(self, schema: DynamicSchema) -> None:
        field_names = {f.name for f in schema.fields}
        if "source_url" not in field_names:
            raise WorkflowValidationError(
                "Schema must include a 'source_url' field for provenance."
            )

    def _check_record_limit(self, workflow: dict) -> None:
        limit = workflow.get("record_limit", 0)
        if not isinstance(limit, int) or limit < 1 or limit > 1000:
            raise WorkflowValidationError(
                f"Record limit must be between 1 and 1000, got {limit}."
            )
