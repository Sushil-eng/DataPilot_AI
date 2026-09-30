from fastapi import APIRouter, HTTPException
from typing import Any
from app.schemas import WorkflowUpdate, WorkflowStepUpdate
from app.services import workflow_service

router = APIRouter(tags=["workflows"])


def success_response(data: Any):
    return {"success": True, "data": data}


def error_response(message: str, status_code: int = 400):
    raise HTTPException(
        status_code=status_code,
        detail={"success": False, "error": {"message": message}}
    )


@router.get("/workflows/{task_id}")
async def get_workflow(task_id: str):
    workflow = await workflow_service.get_workflow(task_id)
    if not workflow:
        error_response("Workflow not found for given task_id", 404)
    return success_response(workflow)


@router.patch("/workflows/{task_id}")
async def update_workflow(task_id: str, update_in: WorkflowUpdate):
    update_data = update_in.model_dump(exclude_unset=True)
    try:
        result = await workflow_service.update_workflow(task_id, update_data)
    except ValueError as e:
        error_response(str(e), 400)
    if not result:
        error_response("Workflow not found or no valid fields to update", 404)
    return success_response(result)


@router.get("/workflows/{task_id}/steps")
async def get_workflow_steps(task_id: str):
    result = await workflow_service.get_workflow_steps(task_id)
    if not result:
        error_response("Workflow not found", 404)
    return success_response(result)


@router.patch("/workflows/{task_id}/steps/{step_id}")
async def update_workflow_step(task_id: str, step_id: str, step_update: WorkflowStepUpdate):
    step_data = step_update.model_dump(exclude_unset=True)
    try:
        result = await workflow_service.update_workflow_step(task_id, step_id, step_data)
    except KeyError as e:
        error_response(str(e), 404)
    except ValueError as e:
        error_response(str(e), 400)
    if not result:
        error_response("Workflow not found", 404)
    return success_response(result)
