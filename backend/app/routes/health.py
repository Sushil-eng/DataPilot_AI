from fastapi import APIRouter

router = APIRouter(tags=["health"])

@router.get("/health")
def check_health():
    return {
        "success": True,
        "data": {
            "status": "ok",
            "service": "DataPilot AI API"
        }
    }
