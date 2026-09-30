"""
Source Service
Handles all source-related business logic.
Route → Service → Database
"""
from datetime import datetime, timezone
from typing import Optional, List
from bson import ObjectId
from app.database.connection import get_db


def format_source(src: dict) -> dict:
    """Normalize a source document for API responses."""
    src["id"] = str(src.pop("_id"))
    return src


async def create_source(
    dataset_id: str,
    url: str,
    title: str,
    source_type: str
) -> Optional[dict]:
    """Create a new source linked to a dataset."""
    if not ObjectId.is_valid(dataset_id):
        return None

    db = get_db()
    dataset = await db.datasets.find_one({"_id": ObjectId(dataset_id)})
    if not dataset:
        return None

    now = datetime.now(timezone.utc)
    source_data = {
        "dataset_id": dataset_id,
        "url": url,
        "title": title,
        "source_type": source_type,
        "collected_at": now
    }

    res = await db.sources.insert_one(source_data)
    source_data["_id"] = res.inserted_id
    return format_source(source_data)


async def get_sources(dataset_id: str) -> Optional[dict]:
    """Get all sources for a dataset."""
    if not ObjectId.is_valid(dataset_id):
        return None

    db = get_db()
    cursor = db.sources.find({"dataset_id": dataset_id}).sort("collected_at", -1)
    sources = await cursor.to_list(length=None)

    formatted_items = [format_source(s) for s in sources]
    return {
        "items": formatted_items,
        "count": len(formatted_items)
    }


async def delete_source(source_id: str) -> Optional[dict]:
    """Delete a specific source."""
    if not ObjectId.is_valid(source_id):
        return None

    db = get_db()
    source = await db.sources.find_one({"_id": ObjectId(source_id)})
    if not source:
        return None

    await db.sources.delete_one({"_id": ObjectId(source_id)})
    return {"message": "Source deleted successfully"}
