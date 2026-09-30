from fastapi import APIRouter, HTTPException, Query, Request, Response, Depends
from typing import Optional, Any
from app.schemas import DatasetCreate, DatasetUpdate
from app.services import dataset_service
from app.auth.dependencies import get_optional_user, get_current_user

router = APIRouter(tags=["datasets"])


def success_response(data: Any):
    return {"success": True, "data": data}


def error_response(message: str, status_code: int = 400):
    raise HTTPException(
        status_code=status_code,
        detail={"success": False, "error": {"message": message}}
    )


# ==================================================
# DATASET EXPORT ENDPOINT
# ==================================================

@router.get("/datasets/{dataset_id}/export")
async def export_dataset(
    dataset_id: str,
    format: str = Query("csv", regex="^(csv|json)$"),
    current_user: Optional[dict] = Depends(get_optional_user)
):
    """
    Export dataset records as CSV or JSON file download.
    Enforces user ownership on dataset exports.
    """
    user_id = current_user["id"] if current_user else None
    res = await dataset_service.export_dataset(dataset_id, export_format=format, user_id=user_id)
    if res is None:
        error_response("Dataset not found or unauthorized", 404)

    content_bytes, filename, media_type = res
    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
        "Access-Control-Expose-Headers": "Content-Disposition"
    }

    return Response(
        content=content_bytes,
        media_type=media_type,
        headers=headers
    )


# ==================================================
# DATASET CRUD ENDPOINTS
# ==================================================

@router.get("/datasets")
async def list_datasets(
    task_id: Optional[str] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    current_user: Optional[dict] = Depends(get_optional_user)
):
    user_id = current_user["id"] if current_user else None
    result = await dataset_service.list_datasets(
        task_id=task_id, search=search, page=page, limit=limit, user_id=user_id
    )
    return success_response(result)


@router.post("/datasets")
async def create_dataset(dataset_in: DatasetCreate):
    schema_fields = None
    if dataset_in.schema_fields:
        schema_fields = [{"name": f.name, "type": f.type} for f in dataset_in.schema_fields]

    try:
        result = await dataset_service.create_dataset(
            task_id=dataset_in.task_id,
            name=dataset_in.name,
            description=dataset_in.description or "",
            schema_fields=schema_fields
        )
    except ValueError as e:
        error_response(str(e), 400)

    return success_response(result)


@router.get("/datasets/{dataset_id}")
async def get_dataset(
    dataset_id: str,
    current_user: Optional[dict] = Depends(get_optional_user)
):
    user_id = current_user["id"] if current_user else None
    dataset = await dataset_service.get_dataset(dataset_id, user_id=user_id)
    if not dataset:
        error_response("Dataset not found", 404)
    return success_response(dataset)


@router.patch("/datasets/{dataset_id}")
async def update_dataset(
    dataset_id: str,
    dataset_update: DatasetUpdate,
    current_user: Optional[dict] = Depends(get_optional_user)
):
    user_id = current_user["id"] if current_user else None
    update_data = dataset_update.model_dump(exclude_unset=True)
    try:
        result = await dataset_service.update_dataset(dataset_id, update_data, user_id=user_id)
    except ValueError as e:
        error_response(str(e), 400)
    if not result:
        error_response("Dataset not found", 404)
    return success_response(result)


@router.delete("/datasets/{dataset_id}")
async def delete_dataset(
    dataset_id: str,
    current_user: Optional[dict] = Depends(get_optional_user)
):
    user_id = current_user["id"] if current_user else None
    result = await dataset_service.delete_dataset(dataset_id, user_id=user_id)
    if not result:
        error_response("Dataset not found", 404)
    return success_response(result)


# ==================================================
# DATASET RECORDS ENDPOINTS
# ==================================================

@router.get("/datasets/{dataset_id}/records")
async def list_dataset_records(
    dataset_id: str,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=500),
    search: Optional[str] = None,
    sort_by: Optional[str] = None,
    order: str = Query("desc", regex="^(asc|desc)$"),
    current_user: Optional[dict] = Depends(get_optional_user)
):
    user_id = current_user["id"] if current_user else None
    result = await dataset_service.list_records(
        dataset_id,
        page=page,
        limit=limit,
        search=search,
        sort_by=sort_by,
        order=order,
        user_id=user_id
    )
    if result is None:
        error_response("Dataset not found", 404)
    return success_response(result)


@router.post("/datasets/{dataset_id}/records")
async def create_dataset_record(dataset_id: str, request: Request):
    try:
        body = await request.json()
    except Exception:
        error_response("Invalid JSON payload", 400)

    if not isinstance(body, dict):
        error_response("Record payload must be a JSON object", 400)

    result = await dataset_service.create_record(dataset_id, body)
    if result is None:
        error_response("Dataset not found", 404)
    return success_response(result)


@router.patch("/datasets/{dataset_id}/records/{record_id}")
async def update_dataset_record(dataset_id: str, record_id: str, request: Request):
    try:
        body = await request.json()
    except Exception:
        error_response("Invalid JSON payload", 400)

    if not isinstance(body, dict):
        error_response("Update payload must be a JSON object", 400)

    result = await dataset_service.update_record(dataset_id, record_id, body)
    if result is None:
        error_response("Record not found", 404)
    return success_response(result)


@router.delete("/datasets/{dataset_id}/records/{record_id}")
async def delete_dataset_record(dataset_id: str, record_id: str):
    result = await dataset_service.delete_record(dataset_id, record_id)
    if result is None:
        error_response("Record not found", 404)
    return success_response(result)
