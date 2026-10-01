import sys
import asyncio

# Ensure Windows event loop policy supports Playwright Chromium subprocesses
if sys.platform == "win32":
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    except Exception:
        pass

from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from .config import get_settings
from .routes import health, tasks, workflows, datasets, sources, ai, analytics
from .auth import routes as auth_routes
from .database.connection import connect_to_mongo, close_mongo_connection

logger = logging.getLogger("datapilot.main")
settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongo()
    yield
    await close_mongo_connection()

app = FastAPI(
    title="DataPilot AI API",
    description="Generic AI-Powered Data Intelligence Platform API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

cors_list = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]
if settings.frontend_url and settings.frontend_url.strip() not in cors_list:
    cors_list.append(settings.frontend_url.strip())

if not cors_list:
    cors_list = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"]
)

@app.get("/")
def root():
    return {
        "status": "ok",
        "service": "DataPilot AI Backend",
        "message": "Backend is running"
    }


# Custom Global Exception Handlers for Clean JSON Error Responses

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if isinstance(exc.detail, dict) and "success" in exc.detail:
        return JSONResponse(status_code=exc.status_code, content=exc.detail)
    elif isinstance(exc.detail, dict) and "message" in exc.detail:
        return JSONResponse(status_code=exc.status_code, content={"success": False, "error": exc.detail})
    else:
        return JSONResponse(
            status_code=exc.status_code,
            content={"success": False, "error": {"message": str(exc.detail)}}
        )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for err in exc.errors():
        loc = " -> ".join([str(l) for l in err.get("loc", [])])
        msg = err.get("msg", "Invalid field")
        errors.append(f"{loc}: {msg}")
    err_msg = "; ".join(errors) if errors else "Invalid request body or query parameter"
    return JSONResponse(
        status_code=400,
        content={"success": False, "error": {"message": err_msg}}
    )

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled Server Error on {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": {"message": "An internal server error occurred. Please try again."}}
    )

app.include_router(auth_routes.router, prefix="/api")
app.include_router(health.router, prefix="/api")
app.include_router(tasks.router, prefix="/api")
app.include_router(workflows.router, prefix="/api")
app.include_router(datasets.router, prefix="/api")
app.include_router(sources.router, prefix="/api")
app.include_router(ai.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")
