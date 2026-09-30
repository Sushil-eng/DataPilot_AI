"""
Workflow Executor — Phase 4 Prompt 4 + Phase 5 Resilient AI Fallback & Real-time Progress Tracking
The central engine that executes AI-generated workflows from start to finish.
Loads task, workflow, requirements, and dynamic schema, manages step execution,
updates MongoDB status and progress dynamically, collects statistics, and handles fallback gracefully.
"""

import sys
import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional

if sys.platform == "win32":
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    except Exception:
        pass

from bson import ObjectId

from app.database.connection import get_db
from app.workflow.execution_models import (
    ExecutionContext,
    StepStatus,
    ExecutionStatistics,
)
from app.workflow.step_executor import StepExecutor, StepExecutionError, ALLOWED_TOOLS

logger = logging.getLogger(__name__)


class WorkflowExecutorError(Exception):
    """Exception raised when workflow execution fails validation or running."""
    pass


class WorkflowExecutor:
    """
    Main workflow execution engine for DataPilot AI.
    Executes AI-planned steps sequentially, maintaining execution context in memory.
    """

    def __init__(self):
        self.step_executor = StepExecutor()

    async def execute(self, task_id: str) -> Dict[str, Any]:
        """
        Execute the AI-generated workflow for a task.

        1. Load task, workflow, dataset schema
        2. Validate executability & idempotency
        3. Initialize ExecutionContext
        4. Loop through workflow steps and execute
        5. Update MongoDB progress & status at each milestone
        6. Return final status & summary
        """
        db = get_db()
        now = datetime.now(timezone.utc)

        logger.info("[Workflow] Starting task %s", task_id)

        # ── 1. Load task ──
        if not ObjectId.is_valid(task_id):
            raise WorkflowExecutorError(f"Invalid task ID: '{task_id}'")

        task = await db.tasks.find_one({"_id": ObjectId(task_id)})
        if not task:
            raise WorkflowExecutorError(f"Task not found: '{task_id}'")

        # Idempotency checks
        current_task_status = task.get("status", "")
        if current_task_status == "running":
            logger.info("[Workflow] Task %s is already running", task_id)
            return {
                "task_id": task_id,
                "status": "already_running",
                "message": "Task is already executing",
            }

        if current_task_status == "completed":
            logger.info("[Workflow] Task %s is already completed", task_id)
            return {
                "task_id": task_id,
                "status": "already_completed",
                "message": "Task execution is already completed",
            }

        if current_task_status not in ("planned", "pending"):
            raise WorkflowExecutorError(
                f"Task '{task_id}' is in status '{current_task_status}'. "
                f"Must be 'planned' to execute."
            )

        # ── 2. Load workflow ──
        workflow = await db.workflows.find_one({"task_id": task_id})
        if not workflow or not workflow.get("steps"):
            raise WorkflowExecutorError(
                f"Task '{task_id}' has no executable workflow steps. Run planning first."
            )

        steps = workflow.get("steps", [])

        # Validate workflow tool safety prior to execution
        for step in steps:
            tool = str(step.get("tool", "")).lower().strip()
            if tool and tool not in ("plan", "understand", "info") and tool not in ALLOWED_TOOLS:
                raise WorkflowExecutorError(
                    f"Workflow contains unsupported/forbidden tool type '{tool}' in step '{step.get('name')}'"
                )

        # ── 3. Load dataset & schema ──
        dataset = await db.datasets.find_one({"task_id": task_id})
        dataset_id = str(dataset["_id"]) if dataset else ""
        schema = None

        if dataset and "dynamic_schema" in dataset and isinstance(dataset["dynamic_schema"], dict):
            schema = dataset["dynamic_schema"]
        elif task.get("ai_requirements"):
            schema = task.get("ai_requirements")
        elif task.get("ai_plan", {}).get("dataset_schema"):
            schema = task.get("ai_plan", {}).get("dataset_schema")

        if not schema:
            raise WorkflowExecutorError(
                f"Task '{task_id}' is missing a dataset schema. Cannot execute workflow."
            )

        requirements = task.get("ai_requirements") or {}
        record_limit = task.get("record_limit") or requirements.get("record_limit", 50)

        # ── 4. Initialize ExecutionContext ──
        context = ExecutionContext(
            task_id=task_id,
            workflow_id=str(workflow["_id"]),
            dataset_id=dataset_id,
            requirements=requirements,
            schema=schema,
            record_limit=record_limit,
        )

        # ── 5. Set status → running (initial progress: 10%) ──
        await self._update_task_and_workflow_status(
            db, task_id, "running", progress=10, current_step="source_discovery", message="Initializing workflow execution..."
        )

        total_steps = len(steps)
        completed_steps = 0

        # ── 6. Step Execution Loop ──
        try:
            for idx, step in enumerate(steps):
                step_id = str(step.get("id", f"step_{idx+1}"))
                step_name = step.get("name", f"Step {idx+1}")
                tool = str(step.get("tool", "")).strip().lower()

                logger.info("[Workflow] Step %s started (%s)", step_name, tool)

                # Update step status → running
                step["status"] = StepStatus.RUNNING.value
                step["started_at"] = datetime.now(timezone.utc).isoformat()
                step["error"] = None

                # Calculate intermediate progress bounded up to 90%
                step_progress = int(10 + (idx / total_steps) * 80)
                await self._persist_workflow_step_update(
                    db, task_id, steps, step_progress, current_step=step_name, current_msg=f"Executing {step_name}..."
                )

                # Execute the step
                step_res = await self.step_executor.execute_step(step, context)

                # Check if step was skipped / fallback vs completed
                if step_res.get("status") in (StepStatus.SKIPPED.value, StepStatus.FALLBACK.value):
                    step["status"] = StepStatus.SKIPPED.value
                    step["message"] = step_res.get("message")
                else:
                    step["status"] = StepStatus.COMPLETED.value
                    step["message"] = step_res.get("message")

                step["completed_at"] = step_res.get("completed_at") or datetime.now(timezone.utc).isoformat()
                step["progress"] = 100
                step["result"] = step_res.get("result", {})

                completed_steps += 1
                new_progress = int(10 + (completed_steps / total_steps) * 85)
                # Keep strictly under 100% until final completion
                new_progress = min(new_progress, 95)

                await self._persist_workflow_step_update(
                    db, task_id, steps, new_progress, current_step=step_name, current_msg=f"Completed {step_name}"
                )

            # ── 7. Workflow Completed Successfully (100% Final Milestone) ──
            now_complete = datetime.now(timezone.utc)
            final_record_count = len(context.final_records)

            fallback_notice = context.fallback_reason if context.fallback_used else None

            await db.workflows.update_one(
                {"task_id": task_id},
                {
                    "$set": {
                        "status": "completed",
                        "progress": 100,
                        "steps": steps,
                        "fallback_used": context.fallback_used,
                        "fallback_notice": fallback_notice,
                        "current_step": "completed",
                        "current_message": "Task completed successfully",
                        "execution_stats": context.statistics.to_dict(),
                        "updated_at": now_complete,
                    }
                },
            )

            await db.tasks.update_one(
                {"_id": ObjectId(task_id)},
                {
                    "$set": {
                        "status": "completed",
                        "progress": 100,
                        "record_count": final_record_count,
                        "fallback_used": context.fallback_used,
                        "fallback_notice": fallback_notice,
                        "current_step": "completed",
                        "current_message": "Task completed successfully",
                        "updated_at": now_complete,
                    }
                },
            )

            # Also ensure linked dataset has completed status and fallback metadata
            if dataset_id and ObjectId.is_valid(dataset_id):
                await db.datasets.update_one(
                    {"_id": ObjectId(dataset_id)},
                    {
                        "$set": {
                            "status": "completed",
                            "record_count": final_record_count,
                            "fallback_used": context.fallback_used,
                            "fallback_notice": fallback_notice,
                            "updated_at": now_complete,
                        }
                    },
                )

            logger.info("[Workflow] Task %s completed successfully (records=%d, fallback=%s)", task_id, final_record_count, context.fallback_used)

            return {
                "task_id": task_id,
                "status": "completed",
                "progress": 100,
                "record_count": final_record_count,
                "fallback_used": context.fallback_used,
                "fallback_notice": fallback_notice,
                "execution_stats": context.statistics.to_dict(),
            }

        except Exception as exc:
            # Handle step failure
            error_message = str(exc)
            logger.error("[Workflow] Execution failed for task %s: %s", task_id, error_message)

            now_fail = datetime.now(timezone.utc)

            # Mark current running step as failed
            for step in steps:
                if step.get("status") == StepStatus.RUNNING.value:
                    step["status"] = StepStatus.FAILED.value
                    step["completed_at"] = now_fail.isoformat()
                    step["error"] = error_message

            # Safe error message (no secrets exposed)
            safe_error = error_message.split("\n")[0][:300]

            await db.workflows.update_one(
                {"task_id": task_id},
                {
                    "$set": {
                        "status": "failed",
                        "steps": steps,
                        "current_step": "failed",
                        "current_message": f"Execution failed: {safe_error}",
                        "execution_stats": context.statistics.to_dict(),
                        "updated_at": now_fail,
                    }
                },
            )

            await db.tasks.update_one(
                {"_id": ObjectId(task_id)},
                {
                    "$set": {
                        "status": "failed",
                        "error_message": safe_error,
                        "current_step": "failed",
                        "current_message": f"Execution failed: {safe_error}",
                        "updated_at": now_fail,
                    }
                },
            )

            return {
                "task_id": task_id,
                "status": "failed",
                "error": safe_error,
            }

    # ──────────────────────────────────────────
    # Internal Helpers
    # ──────────────────────────────────────────

    async def _update_task_and_workflow_status(
        self, db, task_id: str, status: str, progress: int, current_step: str = "", message: str = ""
    ) -> None:
        """Update both task and workflow status, progress, and current step in MongoDB."""
        now = datetime.now(timezone.utc)
        update_doc = {
            "status": status,
            "progress": progress,
            "current_step": current_step,
            "current_message": message,
            "updated_at": now,
        }
        await db.tasks.update_one({"_id": ObjectId(task_id)}, {"$set": update_doc})
        await db.workflows.update_one({"task_id": task_id}, {"$set": update_doc})

    async def _persist_workflow_step_update(
        self, db, task_id: str, steps: list, progress: int, current_step: str = "", current_msg: str = ""
    ) -> None:
        """Persist step status updates, progress, and current active message to MongoDB."""
        now = datetime.now(timezone.utc)
        wf_update = {
            "steps": steps,
            "progress": progress,
            "current_step": current_step,
            "current_message": current_msg,
            "updated_at": now,
        }
        await db.workflows.update_one({"task_id": task_id}, {"$set": wf_update})
        task_update = {
            "progress": progress,
            "current_step": current_step,
            "current_message": current_msg,
            "updated_at": now,
        }
        await db.tasks.update_one({"_id": ObjectId(task_id)}, {"$set": task_update})
