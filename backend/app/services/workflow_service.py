"""
Workflow Service
Handles all workflow-related business logic.
Route → Service → Database
"""
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from bson import ObjectId
from app.database.connection import get_db
from app.schemas import DEFAULT_WORKFLOW_STEPS, VALID_WORKFLOW_STATUSES


def format_workflow(wf: dict) -> dict:
    """Normalize a workflow document for API responses."""
    wf["id"] = str(wf.pop("_id"))
    if not wf.get("steps"):
        wf["steps"] = [dict(s) for s in DEFAULT_WORKFLOW_STEPS]
    return wf


async def create_workflow(task_id: str) -> dict:
    """Create a new workflow with default generic steps for a task."""
    db = get_db()
    now = datetime.now(timezone.utc)

    workflow_data = {
        "task_id": task_id,
        "status": "pending",
        "progress": 0,
        "steps": [dict(s) for s in DEFAULT_WORKFLOW_STEPS],
        "created_at": now,
        "updated_at": now
    }
    res = await db.workflows.insert_one(workflow_data)
    workflow_data["_id"] = res.inserted_id
    return format_workflow(workflow_data)


async def get_workflow(task_id: str) -> Optional[dict]:
    """Get workflow by task_id. Auto-creates if task exists but workflow doesn't."""
    db = get_db()
    workflow = await db.workflows.find_one({"task_id": task_id})

    if not workflow:
        # Check if the task exists — if so, create a default workflow
        if ObjectId.is_valid(task_id):
            task = await db.tasks.find_one({"_id": ObjectId(task_id)})
            if task:
                return await create_workflow(task_id)
        return None

    return format_workflow(workflow)


async def update_workflow(task_id: str, update_data: dict) -> Optional[dict]:
    """Update workflow status/progress and sync with the parent task."""
    db = get_db()
    workflow = await db.workflows.find_one({"task_id": task_id})
    if not workflow:
        return None

    # Filter out None values
    clean_data = {k: v for k, v in update_data.items() if v is not None}
    if not clean_data:
        return None

    # Validate status
    if "status" in clean_data and clean_data["status"] not in VALID_WORKFLOW_STATUSES:
        raise ValueError(
            f"Invalid status '{clean_data['status']}'. "
            f"Must be one of {sorted(VALID_WORKFLOW_STATUSES)}"
        )

    now = datetime.now(timezone.utc)
    clean_data["updated_at"] = now

    await db.workflows.update_one(
        {"task_id": task_id},
        {"$set": clean_data}
    )

    # Sync status/progress to tasks collection
    task_sync = {}
    if "status" in clean_data:
        task_sync["status"] = clean_data["status"]
    if "progress" in clean_data:
        task_sync["progress"] = clean_data["progress"]
    if task_sync and ObjectId.is_valid(task_id):
        task_sync["updated_at"] = now
        await db.tasks.update_one({"_id": ObjectId(task_id)}, {"$set": task_sync})

    updated_wf = await db.workflows.find_one({"task_id": task_id})
    return format_workflow(updated_wf)


async def get_workflow_steps(task_id: str) -> Optional[dict]:
    """Get the workflow steps for a given task."""
    db = get_db()
    workflow = await db.workflows.find_one({"task_id": task_id})

    if not workflow:
        # Auto-create if task exists
        if ObjectId.is_valid(task_id):
            task = await db.tasks.find_one({"_id": ObjectId(task_id)})
            if task:
                await create_workflow(task_id)
                return {"steps": [dict(s) for s in DEFAULT_WORKFLOW_STEPS]}
        return None

    steps = workflow.get("steps") or [dict(s) for s in DEFAULT_WORKFLOW_STEPS]
    return {"steps": steps}


async def update_workflow_step(task_id: str, step_id: str, step_data: dict) -> Optional[dict]:
    """Update a specific workflow step and recalculate workflow progress/status."""
    db = get_db()
    workflow = await db.workflows.find_one({"task_id": task_id})
    if not workflow:
        return None

    steps = workflow.get("steps") or [dict(s) for s in DEFAULT_WORKFLOW_STEPS]

    # Flexible step matching: by id, step_N format, or numeric index
    target_idx = None
    for idx, s in enumerate(steps):
        s_id = str(s.get("id", ""))
        if s_id == step_id or s_id == f"step_{step_id}" or str(idx + 1) == step_id:
            target_idx = idx
            break

    if target_idx is None:
        raise KeyError(f"Step '{step_id}' not found in workflow")

    # Validate step status
    if "status" in step_data and step_data["status"] not in VALID_WORKFLOW_STATUSES:
        raise ValueError(
            f"Invalid step status '{step_data['status']}'. "
            f"Must be one of {sorted(VALID_WORKFLOW_STATUSES)}"
        )

    # Apply updates to the step
    if "status" in step_data:
        steps[target_idx]["status"] = step_data["status"]
    if "result" in step_data:
        steps[target_idx]["result"] = step_data["result"]

    # Recalculate workflow progress and status
    total_steps = len(steps)
    completed_steps = sum(1 for s in steps if s.get("status") == "completed")
    has_failed = any(s.get("status") == "failed" for s in steps)
    has_running = any(s.get("status") == "running" for s in steps)

    new_progress = int((completed_steps / total_steps) * 100) if total_steps > 0 else 0

    if has_failed:
        new_wf_status = "failed"
    elif completed_steps == total_steps and total_steps > 0:
        new_wf_status = "completed"
    elif has_running or completed_steps > 0:
        new_wf_status = "running"
    else:
        new_wf_status = workflow.get("status", "pending")

    now = datetime.now(timezone.utc)
    await db.workflows.update_one(
        {"task_id": task_id},
        {"$set": {
            "steps": steps,
            "progress": new_progress,
            "status": new_wf_status,
            "updated_at": now
        }}
    )

    # Sync with task
    if ObjectId.is_valid(task_id):
        await db.tasks.update_one(
            {"_id": ObjectId(task_id)},
            {"$set": {"status": new_wf_status, "progress": new_progress, "updated_at": now}}
        )

    return steps[target_idx]
