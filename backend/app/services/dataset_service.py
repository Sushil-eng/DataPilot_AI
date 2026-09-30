"""
Dataset Service
Handles all dataset and dataset record business logic.
Route → Service → Database
"""
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from bson import ObjectId
from app.database.connection import get_db
from app.schemas import VALID_SCHEMA_TYPES


def format_dataset(ds: dict) -> dict:
    """Normalize a dataset document for API responses."""
    ds["id"] = str(ds.pop("_id"))
    return ds


def format_record(rec: dict) -> dict:
    """Normalize a record document for API responses."""
    rec["id"] = str(rec.pop("_id"))
    return rec


# ==================================================
# DATASET CRUD
# ==================================================

async def create_dataset(
    task_id: Optional[str],
    name: str,
    description: str = "",
    schema_fields: Optional[List[dict]] = None
) -> dict:
    """Create a new dataset with optional schema definition."""
    db = get_db()
    now = datetime.now(timezone.utc)

    schema_list = []
    if schema_fields:
        for f in schema_fields:
            f_name = f.get("name") if isinstance(f, dict) else f.name
            f_type = f.get("type") if isinstance(f, dict) else f.type
            if f_type.lower() not in VALID_SCHEMA_TYPES:
                raise ValueError(
                    f"Invalid schema field type '{f_type}'. "
                    f"Supported types: {sorted(VALID_SCHEMA_TYPES)}"
                )
            schema_list.append({"name": f_name, "type": f_type.lower()})

    dataset_data = {
        "task_id": task_id,
        "name": name,
        "description": description,
        "schema": schema_list,
        "record_count": 0,
        "created_at": now,
        "updated_at": now
    }

    res = await db.datasets.insert_one(dataset_data)
    dataset_data["_id"] = res.inserted_id
    return format_dataset(dataset_data)


async def get_dataset(dataset_id: str, user_id: Optional[str] = None) -> Optional[dict]:
    """Get a single dataset by ID with ownership check."""
    if not ObjectId.is_valid(dataset_id):
        return None

    db = get_db()
    dataset = await db.datasets.find_one({"_id": ObjectId(dataset_id)})
    if not dataset:
        return None

    if user_id and dataset.get("user_id") and dataset.get("user_id") != "default_user":
        if dataset.get("user_id") != user_id:
            return None

    return format_dataset(dataset)


async def list_datasets(
    task_id: Optional[str] = None,
    search: Optional[str] = None,
    page: int = 1,
    limit: int = 10,
    user_id: Optional[str] = None
) -> dict:
    """List datasets with optional user ownership filter and pagination."""
    db = get_db()
    query = {}

    if user_id:
        query["$or"] = [{"user_id": user_id}, {"user_id": "default_user"}]
    if task_id:
        query["task_id"] = task_id
    if search:
        search_query = [
            {"name": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}}
        ]
        if "$or" in query:
            query["$and"] = [{"$or": query.pop("$or")}, {"$or": search_query}]
        else:
            query["$or"] = search_query

    skip = (page - 1) * limit
    cursor = db.datasets.find(query).sort("created_at", -1).skip(skip).limit(limit)
    datasets = await cursor.to_list(length=limit)

    total = await db.datasets.count_documents(query)

    formatted_items = [format_dataset(ds) for ds in datasets]

    return {
        "items": formatted_items,
        "page": page,
        "limit": limit,
        "total": total
    }


async def update_dataset(dataset_id: str, update_data: dict, user_id: Optional[str] = None) -> Optional[dict]:
    """Update a dataset's fields with ownership check."""
    if not ObjectId.is_valid(dataset_id):
        return None

    db = get_db()
    dataset = await db.datasets.find_one({"_id": ObjectId(dataset_id)})
    if not dataset:
        return None

    if user_id and dataset.get("user_id") and dataset.get("user_id") != "default_user":
        if dataset.get("user_id") != user_id:
            return None

    # Handle schema_fields → schema conversion
    if "schema_fields" in update_data or "schema" in update_data:
        fields = update_data.get("schema_fields") or update_data.get("schema") or []
        schema_list = []
        for f in fields:
            name = f.get("name") if isinstance(f, dict) else f.name
            ftype = f.get("type") if isinstance(f, dict) else f.type
            if ftype.lower() not in VALID_SCHEMA_TYPES:
                raise ValueError(
                    f"Invalid schema field type '{ftype}'. "
                    f"Supported types: {sorted(VALID_SCHEMA_TYPES)}"
                )
            schema_list.append({"name": name, "type": ftype.lower()})
        update_data.pop("schema_fields", None)
        update_data["schema"] = schema_list

    now = datetime.now(timezone.utc)
    update_data["updated_at"] = now

    await db.datasets.update_one(
        {"_id": ObjectId(dataset_id)},
        {"$set": update_data}
    )

    updated_dataset = await db.datasets.find_one({"_id": ObjectId(dataset_id)})
    return format_dataset(updated_dataset)


async def delete_dataset(dataset_id: str, user_id: Optional[str] = None) -> Optional[dict]:
    """Delete a dataset and its associated records and sources with ownership check."""
    if not ObjectId.is_valid(dataset_id):
        return None

    db = get_db()
    dataset = await db.datasets.find_one({"_id": ObjectId(dataset_id)})
    if not dataset:
        return None

    if user_id and dataset.get("user_id") and dataset.get("user_id") != "default_user":
        if dataset.get("user_id") != user_id:
            return None

    # Cascade delete records and sources
    await db.dataset_records.delete_many({"dataset_id": dataset_id})
    await db.sources.delete_many({"dataset_id": dataset_id})
    await db.datasets.delete_one({"_id": ObjectId(dataset_id)})

    return {"message": "Dataset deleted successfully"}


# ==================================================
# DATASET RECORDS CRUD & EXPORT
# ==================================================

async def list_records(
    dataset_id: str,
    page: int = 1,
    limit: int = 10,
    search: Optional[str] = None,
    sort_by: Optional[str] = None,
    order: str = "desc",
    user_id: Optional[str] = None
) -> Optional[dict]:
    """List records for a dataset with search, sort, and ownership check."""
    if not ObjectId.is_valid(dataset_id):
        return None

    db = get_db()
    dataset = await db.datasets.find_one({"_id": ObjectId(dataset_id)})
    if not dataset:
        return None

    if user_id and dataset.get("user_id") and dataset.get("user_id") != "default_user":
        if dataset.get("user_id") != user_id:
            return None

    query: Dict[str, Any] = {"dataset_id": dataset_id}

    if search and search.strip():
        regex = {"$regex": search.strip(), "$options": "i"}
        data_keys = set()
        for field in dataset.get("schema", []):
            if isinstance(field, dict) and field.get("name"):
                data_keys.add(field.get("name"))

        sample_rec = await db.dataset_records.find_one({"dataset_id": dataset_id})
        if sample_rec and isinstance(sample_rec.get("data"), dict):
            for k, val in sample_rec["data"].items():
                if isinstance(val, str):
                    data_keys.add(k)

        if data_keys:
            query["$or"] = [{f"data.{k}": regex} for k in data_keys]

    skip = (page - 1) * limit
    sort_direction = 1 if order.lower() == "asc" else -1

    if sort_by:
        sort_field = f"data.{sort_by}"
    else:
        sort_field = "created_at"

    cursor = db.dataset_records.find(query).sort(sort_field, sort_direction).skip(skip).limit(limit)
    records = await cursor.to_list(length=limit)

    total = await db.dataset_records.count_documents(query)

    formatted_items = [format_record(r) for r in records]

    return {
        "items": formatted_items,
        "page": page,
        "limit": limit,
        "total": total
    }


async def export_dataset(dataset_id: str, export_format: str = "csv", user_id: Optional[str] = None) -> Optional[tuple]:
    """
    Export all records of a dataset as CSV or JSON.
    Includes ownership check to prevent unauthorized exports.
    """
    import io
    import csv
    import json

    if not ObjectId.is_valid(dataset_id):
        return None

    db = get_db()
    dataset = await db.datasets.find_one({"_id": ObjectId(dataset_id)})
    if not dataset:
        return None

    if user_id and dataset.get("user_id") and dataset.get("user_id") != "default_user":
        if dataset.get("user_id") != user_id:
            return None

    dataset_name = dataset.get("name", "dataset").strip()
    sanitized_name = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in dataset_name).lower()

    # Get all records for dataset
    cursor = db.dataset_records.find({"dataset_id": dataset_id}).sort("created_at", -1)
    records = await cursor.to_list(length=None)

    clean_records = []
    for r in records:
        rec_data = r.get("data", {})
        if not isinstance(rec_data, dict):
            rec_data = {"value": rec_data}

        # Build public record object
        clean_rec = dict(rec_data)

        # Retain metadata fields if present
        if "source_url" in r:
            clean_rec["source_url"] = r["source_url"]
        if "collected_at" in r:
            clean_rec["collected_at"] = str(r["collected_at"])
        if "confidence" in r:
            clean_rec["confidence"] = r["confidence"]

        clean_records.append(clean_rec)

    if export_format.lower() == "json":
        json_content = json.dumps(clean_records, indent=2, default=str)
        filename = f"{sanitized_name}_export.json"
        return json_content.encode("utf-8"), filename, "application/json"

    # CSV Format
    schema_fields = dataset.get("schema", [])
    field_names = [f.get("name") for f in schema_fields if isinstance(f, dict) and f.get("name")]

    # Discover extra keys across all clean records
    extra_keys = []
    for rec in clean_records:
        for k in rec.keys():
            if k not in field_names and k not in extra_keys:
                extra_keys.append(k)

    all_headers = field_names + extra_keys
    if not all_headers:
        all_headers = ["data"]

    output = io.StringIO()
    writer = csv.DictWriter(
        output, 
        fieldnames=all_headers, 
        extrasaction="ignore",
        quoting=csv.QUOTE_ALL,
        lineterminator="\r\n"
    )
    writer.writeheader()

    for rec in clean_records:
        row = {}
        for k in all_headers:
            val = rec.get(k)
            if isinstance(val, (dict, list)):
                row[k] = json.dumps(val, ensure_ascii=False)
            elif val is None:
                row[k] = ""
            else:
                # Clean embedded newlines inside cell string values to preserve 1 record per CSV line
                row[k] = str(val).replace("\r\n", " ").replace("\n", " ").replace("\r", " ").strip()
        writer.writerow(row)

    csv_content = output.getvalue()
    filename = f"{sanitized_name}_export.csv"
    return csv_content.encode("utf-8-sig"), filename, "text/csv; charset=utf-8"



async def create_record(dataset_id: str, record_data: dict) -> Optional[dict]:
    """Create a new record in a dataset. Supports flexible JSON payloads."""
    if not ObjectId.is_valid(dataset_id):
        return None

    db = get_db()
    dataset = await db.datasets.find_one({"_id": ObjectId(dataset_id)})
    if not dataset:
        return None

    # Support both direct object {"company": "ABC"} and wrapped {"data": {"company": "ABC"}}
    if "data" in record_data and isinstance(record_data["data"], dict) and len(record_data) == 1:
        data_payload = record_data["data"]
    else:
        data_payload = record_data

    now = datetime.now(timezone.utc)
    rec_document = {
        "dataset_id": dataset_id,
        "data": data_payload,
        "created_at": now,
        "updated_at": now
    }

    res = await db.dataset_records.insert_one(rec_document)
    rec_document["_id"] = res.inserted_id

    # Increment record_count on dataset and task
    await db.datasets.update_one(
        {"_id": ObjectId(dataset_id)},
        {"$inc": {"record_count": 1}, "$set": {"updated_at": now}}
    )

    task_id = dataset.get("task_id")
    if task_id and ObjectId.is_valid(task_id):
        await db.tasks.update_one(
            {"_id": ObjectId(task_id)},
            {"$inc": {"record_count": 1}, "$set": {"updated_at": now}}
        )

    return format_record(rec_document)


async def update_record(dataset_id: str, record_id: str, update_data: dict) -> Optional[dict]:
    """Patch an existing record's data fields."""
    if not ObjectId.is_valid(dataset_id) or not ObjectId.is_valid(record_id):
        return None

    db = get_db()
    record = await db.dataset_records.find_one(
        {"_id": ObjectId(record_id), "dataset_id": dataset_id}
    )
    if not record:
        return None

    # Support wrapped {"data": {...}} or direct object
    if "data" in update_data and isinstance(update_data["data"], dict):
        patch_data = update_data["data"]
    else:
        patch_data = update_data

    current_data = record.get("data", {})
    current_data.update(patch_data)

    now = datetime.now(timezone.utc)
    await db.dataset_records.update_one(
        {"_id": ObjectId(record_id)},
        {"$set": {"data": current_data, "updated_at": now}}
    )

    updated_record = await db.dataset_records.find_one({"_id": ObjectId(record_id)})
    return format_record(updated_record)


async def delete_record(dataset_id: str, record_id: str) -> Optional[dict]:
    """Delete a specific record and decrement counts."""
    if not ObjectId.is_valid(dataset_id) or not ObjectId.is_valid(record_id):
        return None

    db = get_db()
    record = await db.dataset_records.find_one(
        {"_id": ObjectId(record_id), "dataset_id": dataset_id}
    )
    if not record:
        return None

    await db.dataset_records.delete_one({"_id": ObjectId(record_id)})

    now = datetime.now(timezone.utc)
    # Decrement dataset record count
    await db.datasets.update_one(
        {"_id": ObjectId(dataset_id)},
        {"$inc": {"record_count": -1}, "$set": {"updated_at": now}}
    )

    # Decrement task record count
    dataset = await db.datasets.find_one({"_id": ObjectId(dataset_id)})
    if dataset:
        task_id = dataset.get("task_id")
        if task_id and ObjectId.is_valid(task_id):
            await db.tasks.update_one(
                {"_id": ObjectId(task_id)},
                {"$inc": {"record_count": -1}, "$set": {"updated_at": now}}
            )

    return {"message": "Record deleted successfully"}
