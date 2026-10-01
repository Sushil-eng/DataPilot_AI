from fastapi import APIRouter
from app.database.connection import db_instance

router = APIRouter(tags=["health"])

@router.get("/health")
async def check_health():
    is_connected = False
    if db_instance.client is not None and db_instance.db is not None:
        try:
            await db_instance.client.admin.command('ping')
            is_connected = True
        except Exception:
            is_connected = False

    status_str = "ok" if is_connected else "degraded"
    db_str = "connected" if is_connected else "disconnected"

    return {
        "status": status_str,
        "service": "DataPilot AI API",
        "database": db_str,
        "connection_type": db_instance.connection_type if is_connected else "none",
        "error": db_instance.error_message if not is_connected else None
    }
