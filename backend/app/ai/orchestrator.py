"""
Workflow Orchestrator — Phase 3, Prompt 3

The single entry point that ties together the entire planning pipeline:

    User Prompt
         ↓
    AI Analyzer  (LLMService)
         ↓
    Research Requirements  (AIAnalysisResult)
         ↓
    Dynamic Schema  (build_dynamic_schema)
         ↓
    Workflow Planner  (WorkflowPlanner)
         ↓
    Workflow Validator  (WorkflowValidator)
         ↓
    MongoDB  (save requirements, schema, workflow, update task)

This orchestrator does NOT perform real data collection.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from bson import ObjectId

from ..database.connection import get_db
from .llm_service import LLMService
from .schemas import (
    AIAnalysisResult,
    DynamicSchema,
    build_dynamic_schema,
)
from .workflow_planner import (
    WorkflowPlanner,
    WorkflowValidator,
    WorkflowValidationError,
)

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# Custom exceptions
# ──────────────────────────────────────────────

class OrchestratorError(Exception):
    """Base exception for orchestrator failures."""
    pass


class TaskNotFoundError(OrchestratorError):
    pass


class TaskStateError(OrchestratorError):
    """Raised when a task is in an invalid state for planning."""
    pass


# ──────────────────────────────────────────────
# Plan result (returned to the route)
# ──────────────────────────────────────────────

class PlanResult:
    """Container for the complete plan returned to the API."""

    def __init__(
        self,
        task_id: str,
        requirements: AIAnalysisResult,
        schema: DynamicSchema,
        workflow: dict,
    ):
        self.task_id = task_id
        self.requirements = requirements
        self.schema = schema
        self.workflow = workflow

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "requirements": self.requirements.model_dump(),
            "schema": self.schema.model_dump(),
            "workflow": self.workflow,
        }


# ──────────────────────────────────────────────
# Workflow Orchestrator
# ──────────────────────────────────────────────

class WorkflowOrchestrator:
    """
    Orchestrates the full planning pipeline for a task.

    Usage:
        orchestrator = WorkflowOrchestrator()
        plan = await orchestrator.plan(task_id)
    """

    def __init__(self):
        self.llm_service = LLMService()
        self.planner = WorkflowPlanner()
        self.validator = WorkflowValidator()

    async def plan(self, task_id: str) -> PlanResult:
        """
        Run the full planning pipeline for a task.

        1. Load task from MongoDB
        2. Update status → "planning"
        3. Send prompt to AI analyzer
        4. Build dynamic schema
        5. Generate workflow plan
        6. Validate the plan
        7. Store everything in MongoDB
        8. Update status → "planned"
        9. Return the complete plan
        """
        db = get_db()
        now = datetime.now(timezone.utc)

        # ── 1. Load task ──
        task = await self._load_task(db, task_id)
        prompt = task["prompt"]
        record_limit = task.get("record_limit", 50)

        logger.info("Orchestrator: planning task %s — prompt: %s", task_id, prompt[:80])

        # ── 2. Update status → planning ──
        await self._update_task_status(db, task_id, "planning", now)

        try:
            # ── 3. AI analysis ──
            requirements: AIAnalysisResult = await self.llm_service.analyze(prompt)

            # Preserve task record_limit if set on the task document
            if record_limit and record_limit > 0:
                requirements.record_limit = record_limit

            # ── 4. Dynamic schema ──
            schema: DynamicSchema = build_dynamic_schema(requirements)

            # ── 5. Generate workflow ──
            workflow: dict = self.planner.generate(requirements, schema)

            # ── 6. Validate ──
            self.validator.validate(workflow, schema)

            # ── 7. Store in MongoDB ──
            await self._save_plan(db, task_id, requirements, schema, workflow, now)

            # ── 8. Update status → planned ──
            await self._update_task_status(db, task_id, "planned", now)

            logger.info("Orchestrator: task %s planned successfully", task_id)

            # ── 9. Return ──
            return PlanResult(
                task_id=task_id,
                requirements=requirements,
                schema=schema,
                workflow=workflow,
            )

        except WorkflowValidationError as exc:
            await self._update_task_status(db, task_id, "failed", now)
            raise OrchestratorError(f"Workflow validation failed: {exc}")
        except Exception:
            await self._update_task_status(db, task_id, "failed", now)
            raise

    # ──────────────────────────────────────────
    # Private helpers
    # ──────────────────────────────────────────

    async def _load_task(self, db, task_id: str) -> dict:
        """Load and validate the task document."""
        if not ObjectId.is_valid(task_id):
            raise TaskNotFoundError(f"Invalid task ID: {task_id}")

        task = await db.tasks.find_one({"_id": ObjectId(task_id)})
        if not task:
            raise TaskNotFoundError(f"Task not found: {task_id}")

        status = task.get("status", "")
        if status not in ("pending", "failed"):
            raise TaskStateError(
                f"Task '{task_id}' is in state '{status}'. "
                f"Only 'pending' or 'failed' tasks can be planned."
            )

        return task

    async def _update_task_status(
        self, db, task_id: str, status: str, now: datetime
    ) -> None:
        """Update task and its workflow status."""
        await db.tasks.update_one(
            {"_id": ObjectId(task_id)},
            {"$set": {"status": status, "updated_at": now}},
        )
        await db.workflows.update_many(
            {"task_id": task_id},
            {"$set": {"status": status, "updated_at": now}},
        )
        logger.debug("Task %s → status=%s", task_id, status)

    async def _save_plan(
        self,
        db,
        task_id: str,
        requirements: AIAnalysisResult,
        schema: DynamicSchema,
        workflow: dict,
        now: datetime,
    ) -> None:
        """Persist the complete plan into MongoDB."""

        req_dict = requirements.model_dump()
        schema_dict = schema.model_dump()

        # ── Save AI requirements on the task ──
        await db.tasks.update_one(
            {"_id": ObjectId(task_id)},
            {
                "$set": {
                    "ai_requirements": req_dict,
                    "record_limit": requirements.record_limit,
                    "updated_at": now,
                }
            },
        )

        # ── Update the workflow with planned steps ──
        workflow_doc = await db.workflows.find_one({"task_id": task_id})
        if workflow_doc:
            await db.workflows.update_one(
                {"task_id": task_id},
                {
                    "$set": {
                        "workflow_type": workflow.get("workflow_type"),
                        "goal": workflow.get("goal"),
                        "intent": workflow.get("intent"),
                        "record_limit": workflow.get("record_limit"),
                        "steps": workflow.get("steps", []),
                        "total_steps": workflow.get("total_steps", 0),
                        "progress": 0,
                        "updated_at": now,
                    }
                },
            )
        else:
            await db.workflows.insert_one(
                {
                    "task_id": task_id,
                    "status": "planned",
                    "workflow_type": workflow.get("workflow_type"),
                    "goal": workflow.get("goal"),
                    "intent": workflow.get("intent"),
                    "record_limit": workflow.get("record_limit"),
                    "steps": workflow.get("steps", []),
                    "total_steps": workflow.get("total_steps", 0),
                    "progress": 0,
                    "created_at": now,
                    "updated_at": now,
                }
            )

        # ── Update the dataset with the dynamic schema ──
        dataset = await db.datasets.find_one({"task_id": task_id})
        # Convert DataField objects to simple {name, type} for the dataset schema
        dataset_schema_fields = [
            {"name": f.name, "type": f.type}
            for f in schema.fields
        ]
        dataset_update = {
            "name": f"{requirements.intent.replace('_', ' ').title()} Dataset",
            "description": requirements.goal,
            "schema": dataset_schema_fields,
            "dynamic_schema": schema_dict,
            "updated_at": now,
        }

        if dataset:
            await db.datasets.update_one(
                {"task_id": task_id},
                {"$set": dataset_update},
            )
        else:
            dataset_update.update(
                {
                    "task_id": task_id,
                    "record_count": 0,
                    "created_at": now,
                }
            )
            await db.datasets.insert_one(dataset_update)

        logger.info("Plan saved for task %s", task_id)
