from fastapi import APIRouter, HTTPException, Query, BackgroundTasks, Depends
from typing import Optional
import logging
from app.schemas import TaskCreate, TaskUpdate
from app.services import task_service
from app.auth.dependencies import get_optional_user, get_current_user
from app.ai.orchestrator import (
    WorkflowOrchestrator,
    OrchestratorError,
    TaskNotFoundError,
    TaskStateError,
)
from app.ai.llm_service import (
    LLMConfigError,
    LLMAPIError,
    LLMParsingError,
    LLMValidationError,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["tasks"])


def success_response(data: dict):
    return {"success": True, "data": data}


def error_response(message: str, status_code: int = 400):
    raise HTTPException(
        status_code=status_code,
        detail={"success": False, "error": {"message": message}}
    )


@router.post("/tasks")
async def create_task(
    task_in: TaskCreate,
    current_user: Optional[dict] = Depends(get_optional_user)
):
    user_id = current_user["id"] if current_user else None
    result = await task_service.create_task(
        prompt=task_in.prompt,
        record_limit=task_in.record_limit,
        user_id=user_id
    )
    return success_response(result)


@router.get("/tasks")
async def list_tasks(
    status: Optional[str] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    current_user: Optional[dict] = Depends(get_optional_user)
):
    user_id = current_user["id"] if current_user else None
    result = await task_service.list_tasks(
        status=status, search=search, page=page, limit=limit, user_id=user_id
    )
    return success_response(result)


@router.get("/tasks/{task_id}")
async def get_task(
    task_id: str,
    current_user: Optional[dict] = Depends(get_optional_user)
):
    user_id = current_user["id"] if current_user else None
    task = await task_service.get_task(task_id, user_id=user_id)
    if not task:
        error_response("Task not found", 404)
    return success_response(task)


@router.patch("/tasks/{task_id}")
async def update_task(task_id: str, task_update: TaskUpdate):
    update_data = task_update.model_dump(exclude_unset=True)
    result = await task_service.update_task(task_id, update_data)
    if not result:
        error_response("Task not found or no valid fields to update", 404)
    return success_response(result)


@router.delete("/tasks/{task_id}")
async def delete_task(task_id: str):
    result = await task_service.delete_task(task_id)
    if not result:
        error_response("Task not found", 404)
    return success_response(result)


# ──────────────────────────────────────────────
# Phase 3 — Prompt 3: AI Planning endpoint
# ──────────────────────────────────────────────

@router.post("/tasks/{task_id}/plan")
async def plan_task(task_id: str):
    """
    Run the full AI planning pipeline for a task.

    1. Load task
    2. Send prompt to AI analyzer
    3. Generate requirements
    4. Generate dynamic schema
    5. Generate workflow
    6. Validate everything
    7. Store results in MongoDB
    8. Return the complete plan

    The task status transitions: pending → planning → planned
    """
    try:
        orchestrator = WorkflowOrchestrator()
        plan = await orchestrator.plan(task_id)

        return {
            "success": True,
            "data": plan.to_dict(),
        }

    except TaskNotFoundError as exc:
        logger.error("Task not found: %s", exc)
        raise HTTPException(status_code=404, detail=str(exc))

    except TaskStateError as exc:
        logger.error("Task state error: %s", exc)
        raise HTTPException(status_code=409, detail=str(exc))

    except LLMConfigError as exc:
        logger.error("LLM config error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))

    except (LLMAPIError, LLMParsingError, LLMValidationError) as exc:
        logger.error("LLM error during planning: %s", exc)
        raise HTTPException(status_code=502, detail=str(exc))

    except OrchestratorError as exc:
        logger.error("Orchestrator error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))

    except Exception as exc:
        logger.exception("Unexpected error in /api/tasks/%s/plan", task_id)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {type(exc).__name__}",
        )


# ──────────────────────────────────────────────
# Phase 4 — Prompt 3: Processing Pipeline Endpoint
# ──────────────────────────────────────────────

@router.post("/tasks/{task_id}/process")
async def process_task(task_id: str, body: Optional[dict] = None):
    """
    Run Data Cleaning, Normalization, Validation, and Deduplication pipeline.

    1. Load task and validate AI plan / schema exists
    2. Load raw extracted records from MongoDB or body
    3. Run DataProcessingPipeline (Clean → Normalize → Validate → Deduplicate → Capped Record Limit)
    4. Return ProcessingResult with statistics and final clean unique records
    """
    from bson import ObjectId
    from app.database.connection import get_db
    from app.collection.pipeline import DataProcessingPipeline

    db = get_db()
    if not ObjectId.is_valid(task_id):
        raise HTTPException(status_code=404, detail=f"Invalid task ID: '{task_id}'")

    task = await db.tasks.find_one({"_id": ObjectId(task_id)})
    if not task:
        raise HTTPException(status_code=404, detail=f"Task not found: '{task_id}'")

    # Resolve dataset schema
    dataset = await db.datasets.find_one({"task_id": task_id})
    schema = None
    if dataset and "dynamic_schema" in dataset and isinstance(dataset["dynamic_schema"], dict):
        schema = dataset["dynamic_schema"]
    elif dataset and "schema" in dataset:
        schema = {"fields": dataset["schema"]}
    elif "ai_requirements" in task and isinstance(task["ai_requirements"], dict):
        schema = task["ai_requirements"]
    elif "ai_plan" in task and "dataset_schema" in task["ai_plan"]:
        schema = task["ai_plan"]["dataset_schema"]

    if not schema:
        raise HTTPException(
            status_code=409,
            detail=f"Task '{task_id}' has no dataset schema. Run POST /api/tasks/{task_id}/plan first."
        )

    # Collect raw extracted records
    raw_records = []
    if body and "records" in body and isinstance(body["records"], list):
        raw_records = body["records"]
    else:
        # Load from db.sources
        sources_cursor = db.sources.find({"task_id": task_id, "status": "extracted"})
        sources = await sources_cursor.to_list(length=200)
        for src in sources:
            recs = src.get("extracted_records", [])
            if recs:
                raw_records.extend(recs)

    record_limit = task.get("record_limit") or (
        task.get("ai_requirements", {}).get("record_limit", 50) if isinstance(task.get("ai_requirements"), dict) else 50
    )

    try:
        pipeline = DataProcessingPipeline()
        result = pipeline.process(
            raw_records=raw_records,
            dataset_schema=schema,
            record_limit=record_limit,
            task_id=task_id,
        )

        return {
            "success": True,
            "data": result.to_dict(),
        }

    except Exception as exc:
        logger.exception("Unexpected error in /api/tasks/%s/process", task_id)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error during data processing: {type(exc).__name__}",
        )


# ──────────────────────────────────────────────
# Phase 4 — Prompt 4: Workflow Execution Endpoint
# ──────────────────────────────────────────────

async def _run_workflow_in_background(task_id: str):
    """Background runner for workflow execution."""
    from app.workflow.executor import WorkflowExecutor
    try:
        executor = WorkflowExecutor()
        await executor.execute(task_id)
    except Exception as exc:
        logger.exception("Background workflow execution failed for task %s", task_id)


@router.post("/tasks/{task_id}/execute")
async def execute_task(task_id: str, background_tasks: BackgroundTasks):
    """
    Start the AI Workflow Execution Engine for a planned task.

    1. Load task from MongoDB
    2. Verify task status & idempotency (running / completed)
    3. Verify task has AI-generated workflow & valid dynamic schema
    4. Start WorkflowExecutor in background via BackgroundTasks
    5. Return immediate execution status
    """
    from bson import ObjectId
    from app.database.connection import get_db
    from app.workflow.step_executor import ALLOWED_TOOLS

    db = get_db()
    if not ObjectId.is_valid(task_id):
        raise HTTPException(status_code=404, detail=f"Invalid task ID: '{task_id}'")

    task = await db.tasks.find_one({"_id": ObjectId(task_id)})
    if not task:
        raise HTTPException(status_code=404, detail=f"Task not found: '{task_id}'")

    current_status = task.get("status", "")

    # Idempotency handling
    if current_status == "running":
        return {
            "success": True,
            "data": {
                "task_id": task_id,
                "status": "already_running",
                "message": "Workflow execution is already running",
            }
        }

    if current_status == "completed":
        return {
            "success": True,
            "data": {
                "task_id": task_id,
                "status": "already_completed",
                "message": "Workflow execution is already completed",
            }
        }

    if current_status not in ("planned", "pending"):
        raise HTTPException(
            status_code=409,
            detail=f"Task '{task_id}' is in status '{current_status}'. Run planning endpoint first."
        )

    # Load & validate workflow
    workflow = await db.workflows.find_one({"task_id": task_id})
    if not workflow or not workflow.get("steps"):
        raise HTTPException(
            status_code=409,
            detail=f"Task '{task_id}' has no AI-generated workflow. Run POST /api/tasks/{task_id}/plan first."
        )

    # Security tool validation
    steps = workflow.get("steps", [])
    for step in steps:
        tool = str(step.get("tool", "")).lower().strip()
        if tool and tool not in ("plan", "understand", "info") and tool not in ALLOWED_TOOLS:
            raise HTTPException(
                status_code=400,
                detail=f"Workflow contains unauthorized tool type '{tool}' in step '{step.get('name')}'"
            )

    # Check schema existence
    dataset = await db.datasets.find_one({"task_id": task_id})
    has_schema = False
    if dataset and ("dynamic_schema" in dataset or "schema" in dataset):
        has_schema = True
    elif task.get("ai_requirements") or task.get("ai_plan", {}).get("dataset_schema"):
        has_schema = True

    if not has_schema:
        raise HTTPException(
            status_code=409,
            detail=f"Task '{task_id}' is missing a dataset schema. Run POST /api/tasks/{task_id}/plan first."
        )

    # Schedule background execution
    background_tasks.add_task(_run_workflow_in_background, task_id)

    return {
        "success": True,
        "data": {
            "task_id": task_id,
            "status": "running",
            "message": "Workflow execution started",
        }
    }


