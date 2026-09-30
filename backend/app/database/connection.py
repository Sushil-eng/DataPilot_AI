import logging
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import get_settings

logger = logging.getLogger(__name__)

class Database:
    client: AsyncIOMotorClient = None
    db = None

db_instance = Database()

import asyncio

async def connect_to_mongo():
    settings = get_settings()
    logger.info("Connecting to MongoDB...")

    primary_uri = settings.mongodb_uri
    if "mongodb+srv://" in primary_uri:
        try:
            import certifi
            client = AsyncIOMotorClient(
                primary_uri,
                tlsCAFile=certifi.where(),
                tlsAllowInvalidCertificates=True,
                serverSelectionTimeoutMS=2000
            )
            await client.admin.command('ping')
            db_instance.client = client
            db_instance.db = client[settings.database_name]
            logger.info("Connected to MongoDB Atlas")
            asyncio.create_task(create_indexes())
            return
        except Exception as e:
            logger.warning(f"MongoDB Atlas connection failed ({e}). Falling back to local MongoDB...")

    local_client = AsyncIOMotorClient("mongodb://localhost:27017", serverSelectionTimeoutMS=2000)
    db_instance.client = local_client
    db_instance.db = local_client[settings.database_name]
    logger.info("Connected to local MongoDB")
    asyncio.create_task(create_indexes())






async def close_mongo_connection():
    logger.info("Closing MongoDB connection...")
    if db_instance.client:
        db_instance.client.close()
    logger.info("MongoDB connection closed")

def get_db():
    return db_instance.db

async def create_indexes():
    db = db_instance.db
    if db is None:
        return
    try:
        # Tasks
        await db.tasks.create_index("user_id")
        await db.tasks.create_index("status")
        await db.tasks.create_index("created_at")
        
        # Workflows
        await db.workflows.create_index("task_id")
        
        # Datasets
        await db.datasets.create_index("task_id")
        
        # Sources
        await db.sources.create_index("dataset_id")
        await db.sources.create_index("task_id")
        await db.sources.create_index([("task_id", 1), ("status", 1)])
        logger.info("Indexes created successfully")
    except Exception as e:
        logger.warning(f"Could not create indexes: {e}")

