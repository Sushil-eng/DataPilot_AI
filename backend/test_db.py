import asyncio
from datetime import datetime, timezone
import logging

from app.database.connection import connect_to_mongo, close_mongo_connection, get_db
from app.schemas import Task, Dataset, DatasetSchemaField, DatasetRecord, Source

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_tests():
    await connect_to_mongo()
    db = get_db()
    
    try:
        # Clear collections for clean test
        await db.tasks.delete_many({})
        await db.datasets.delete_many({})
        await db.dataset_records.delete_many({})
        await db.sources.delete_many({})
        
        logger.info("=== Testing Task ===")
        task_data = {
            "prompt": "Find 50 AI startups in India",
            "user_id": "user123",
            "status": "pending",
            "progress": 0,
            "record_count": 0,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        
        res = await db.tasks.insert_one(task_data)
        task_id = str(res.inserted_id)
        
        task_out = Task(**{**task_data, "_id": str(res.inserted_id)})
        logger.info(f"Task created: {task_out.prompt}")
        
        logger.info("=== Testing Dataset (Dynamic Schema) ===")
        schema_fields = [
            DatasetSchemaField(name="company_name", type="string"),
            DatasetSchemaField(name="location", type="string"),
            DatasetSchemaField(name="website", type="url"),
        ]
        
        dataset_data = {
            "task_id": task_id,
            "name": "AI Startup Research",
            "description": "Structured information about AI startups",
            "schema": [f.model_dump() for f in schema_fields],
            "record_count": 1,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        
        res2 = await db.datasets.insert_one(dataset_data)
        dataset_id = str(res2.inserted_id)
        
        dataset_out = Dataset(**{**dataset_data, "_id": str(res2.inserted_id)})
        logger.info(f"Dataset created: {dataset_out.name}")
        
        logger.info("=== Testing Dataset Records (Dynamic) ===")
        # Company Record
        rec1 = DatasetRecord(
            dataset_id=dataset_id,
            data={
                "company_name": "Example AI",
                "location": "Mumbai",
                "website": "https://example.com"
            },
            created_at=datetime.now(timezone.utc)
        )
        await db.dataset_records.insert_one(rec1.model_dump())
        logger.info(f"Company Record inserted: {rec1.data}")
        
        # Product Record
        rec2 = DatasetRecord(
            dataset_id=dataset_id,
            data={
                "product": "Example Product",
                "price": 5000,
                "category": "Electronics"
            },
            created_at=datetime.now(timezone.utc)
        )
        await db.dataset_records.insert_one(rec2.model_dump())
        logger.info(f"Product Record inserted: {rec2.data}")
        
        # Job Record
        rec3 = DatasetRecord(
            dataset_id=dataset_id,
            data={
                "job_title": "Python Developer",
                "company": "Example Corp",
                "location": "Mumbai"
            },
            created_at=datetime.now(timezone.utc)
        )
        await db.dataset_records.insert_one(rec3.model_dump())
        logger.info(f"Job Record inserted: {rec3.data}")

        logger.info("=== Testing Source ===")
        source_data = {
            "dataset_id": dataset_id,
            "url": "https://example.com",
            "title": "Example Source",
            "source_type": "website",
            "collected_at": datetime.now(timezone.utc)
        }
        res3 = await db.sources.insert_one(source_data)
        source_out = Source(**{**source_data, "_id": str(res3.inserted_id)})
        logger.info(f"Source created: {source_out.title}")
        
        logger.info("ALL TESTS PASSED!")
        
    finally:
        await close_mongo_connection()

if __name__ == "__main__":
    asyncio.run(run_tests())
