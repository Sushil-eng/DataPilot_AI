"""
Task Service
Handles all task-related business logic.
Route → Service → Database
"""
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from bson import ObjectId
from app.database.connection import get_db
from app.schemas import DEFAULT_WORKFLOW_STEPS


async def create_task(prompt: str, record_limit: int = 50, user_id: Optional[str] = None) -> dict:
    """Create a new task with associated workflow and dataset."""
    db = get_db()
    now = datetime.now(timezone.utc)
    uid = user_id or "default_user"

    task_data = {
        "prompt": prompt,
        "record_limit": record_limit,
        "user_id": uid,
        "status": "pending",
        "progress": 0,
        "record_count": 0,
        "created_at": now,
        "updated_at": now
    }
    task_res = await db.tasks.insert_one(task_data)
    task_id = str(task_res.inserted_id)

    # Initialize workflow with default generic steps
    workflow_data = {
        "task_id": task_id,
        "user_id": uid,
        "status": "pending",
        "progress": 0,
        "steps": [dict(s) for s in DEFAULT_WORKFLOW_STEPS],
        "created_at": now,
        "updated_at": now
    }
    await db.workflows.insert_one(workflow_data)

    # Initialize empty dataset
    dataset_data = {
        "task_id": task_id,
        "user_id": uid,
        "name": "Untitled Dataset",
        "description": "Generated from: " + prompt[:50],
        "schema": [],
        "record_count": 0,
        "created_at": now,
        "updated_at": now
    }
    ds_res = await db.datasets.insert_one(dataset_data)
    dataset_id = str(ds_res.inserted_id)

    # Link dataset_id to task
    await db.tasks.update_one({"_id": task_res.inserted_id}, {"$set": {"dataset_id": dataset_id}})

    return {
        "id": task_id,
        "prompt": task_data["prompt"],
        "status": task_data["status"],
        "progress": task_data["progress"],
        "user_id": uid,
        "dataset_id": dataset_id
    }


async def get_task(task_id: str, user_id: Optional[str] = None) -> Optional[dict]:
    """Get a single task by ID with ownership check."""
    if not ObjectId.is_valid(task_id):
        return None

    db = get_db()
    task = await db.tasks.find_one({"_id": ObjectId(task_id)})
    if not task:
        return None

    # User ownership check
    if user_id and task.get("user_id") and task.get("user_id") != "default_user":
        if task.get("user_id") != user_id:
            return None

    task["_id"] = str(task["_id"])
    return task


async def list_tasks(
    status: Optional[str] = None,
    search: Optional[str] = None,
    page: int = 1,
    limit: int = 10,
    user_id: Optional[str] = None
) -> dict:
    """List tasks with optional user ownership filter."""
    db = get_db()
    query = {}

    if user_id:
        query["$or"] = [{"user_id": user_id}, {"user_id": "default_user"}]
    if status:
        query["status"] = status
    if search:
        query["prompt"] = {"$regex": search, "$options": "i"}

    skip = (page - 1) * limit
    cursor = db.tasks.find(query).sort("created_at", -1).skip(skip).limit(limit)
    tasks = await cursor.to_list(length=limit)

    total = await db.tasks.count_documents(query)

    formatted_tasks = []
    for t in tasks:
        t["_id"] = str(t["_id"])
        t["id"] = t["_id"]
        formatted_tasks.append(t)

    return {
        "items": formatted_tasks,
        "page": page,
        "limit": limit,
        "total": total
    }


async def update_task(task_id: str, update_data: dict) -> Optional[dict]:
    """Update a task's fields."""
    if not ObjectId.is_valid(task_id):
        return None

    db = get_db()

    # Filter out None values
    clean_data = {k: v for k, v in update_data.items() if v is not None}
    if not clean_data:
        return None

    clean_data["updated_at"] = datetime.now(timezone.utc)

    res = await db.tasks.update_one(
        {"_id": ObjectId(task_id)},
        {"$set": clean_data}
    )

    if res.matched_count == 0:
        return None

    return await get_task(task_id)


async def delete_task(task_id: str) -> Optional[dict]:
    """Delete a task and all related data (workflow, datasets, records, sources)."""
    if not ObjectId.is_valid(task_id):
        return None

    db = get_db()
    obj_id = ObjectId(task_id)

    task = await db.tasks.find_one({"_id": obj_id})
    if not task:
        return None

    # Cascade delete: workflows
    await db.workflows.delete_many({"task_id": task_id})

    # Cascade delete: dataset records and sources
    datasets = await db.datasets.find({"task_id": task_id}).to_list(length=None)
    for ds in datasets:
        ds_id = str(ds["_id"])
        await db.dataset_records.delete_many({"dataset_id": ds_id})
        await db.sources.delete_many({"dataset_id": ds_id})

    # Cascade delete: datasets
    await db.datasets.delete_many({"task_id": task_id})

    # Delete the task itself
    await db.tasks.delete_one({"_id": obj_id})

    return {"message": "Task deleted safely"}
