import logging
import asyncio
import certifi
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import get_settings

logger = logging.getLogger("datapilot.database")

class Database:
    client: Optional[AsyncIOMotorClient] = None
    db = None
    status: str = "disconnected"
    connection_type: str = "none"
    error_message: Optional[str] = None

db_instance = Database()

def log_safe_env_config(uri: str, db_name: str):
    """
    Log safe diagnostic information regarding MongoDB environment configuration
    without exposing any secrets or passwords.
    """
    has_uri = bool(uri and uri.strip())
    has_user = False
    has_pass = False

    if has_uri and "://" in uri and "@" in uri:
        try:
            creds_part = uri.split("://")[1].split("@")[0]
            if ":" in creds_part:
                user, passwd = creds_part.split(":", 1)
                has_user = bool(user and user.strip())
                has_pass = bool(passwd and passwd.strip())
        except Exception:
            pass

    logger.info(f"MongoDB URI configured: {'YES' if has_uri else 'NO'}")
    logger.info(f"MongoDB username configured: {'YES' if has_user else 'NO'}")
    logger.info(f"MongoDB password configured: {'YES' if has_pass else 'NO'}")
    logger.info(f"MongoDB database configured: {'YES' if db_name else 'NO'}")

async def connect_to_mongo():
    settings = get_settings()
    logger.info("Initializing MongoDB connection...")
    
    primary_uri = settings.mongodb_uri
    log_safe_env_config(primary_uri, settings.database_name)

    if "mongodb+srv://" in primary_uri or "mongodb://" in primary_uri:
        is_atlas = "mongodb+srv://" in primary_uri
        conn_label = "MongoDB Atlas" if is_atlas else "configured Primary MongoDB"
        logger.info(f"Attempting connection to {conn_label}...")

        try:
            client = AsyncIOMotorClient(
                primary_uri,
                tlsCAFile=certifi.where(),
                serverSelectionTimeoutMS=10000
            )
            # Send ping command to verify active connection
            await client.admin.command('ping')
            db_instance.client = client
            db_instance.db = client[settings.database_name]
            db_instance.status = "connected"
            db_instance.connection_type = "atlas" if is_atlas else "primary"
            db_instance.error_message = None
            logger.info(f"Connected successfully to {conn_label}")
            asyncio.create_task(create_indexes())
            return
        except Exception as e:
            db_instance.status = "disconnected"
            db_instance.error_message = str(e)
            logger.error(f"{conn_label} connection failed: {e}")
            if not settings.mongodb_fallback_local:
                logger.critical("MONGODB_FALLBACK_LOCAL=false. Raising startup error.")
                raise RuntimeError(f"Failed to connect to primary MongoDB database: {e}") from e

    if settings.mongodb_fallback_local:
        logger.warning("MONGODB_FALLBACK_LOCAL=true. Falling back to local MongoDB (mongodb://localhost:27017)...")
        try:
            local_client = AsyncIOMotorClient("mongodb://localhost:27017", serverSelectionTimeoutMS=3000)
            await local_client.admin.command('ping')
            db_instance.client = local_client
            db_instance.db = local_client[settings.database_name]
            db_instance.status = "connected"
            db_instance.connection_type = "local_fallback"
            db_instance.error_message = None
            logger.info("Connected to local fallback MongoDB successfully")
            asyncio.create_task(create_indexes())
            return
        except Exception as local_err:
            db_instance.status = "disconnected"
            db_instance.error_message = str(local_err)
            logger.error(f"Local fallback MongoDB connection failed: {local_err}")
            raise RuntimeError(f"Failed to connect to both primary MongoDB and local fallback: {local_err}") from local_err

async def close_mongo_connection():
    logger.info("Closing MongoDB connection...")
    if db_instance.client:
        db_instance.client.close()
    db_instance.status = "disconnected"
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
