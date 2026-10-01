from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    mongodb_username: str = ""
    mongodb_uri: str = "mongodb://localhost:27017"
    database_name: str = "datapilot"
    mongodb_fallback_local: bool = False
    frontend_url: str = "http://localhost:5173"


    # ── Search Provider (Phase 4) ──
    search_provider: str = "mock"
    search_api_key: str = ""
    search_engine: str = "google"

    # ── Data Extraction (Phase 4 Prompt 2) ──
    extraction_mode: str = "mock"  # mock or live
    fetcher_mode: str = "auto"      # http, browser, auto
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    fetch_timeout: int = 15
    browser_timeout: int = 20000

    # ── Workflow Execution (Phase 4 Prompt 4) ──
    workflow_max_retries: int = 2
    max_concurrent_sources: int = 5

    # ── Auth & Security (Phase 5 Prompt 3) ──
    jwt_secret_key: str = "datapilot_jwt_secret_key_change_in_prod_2026"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 10080
    cors_origins: str = "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173"

    class Config:
        env_file = ".env"
        extra = "allow"

@lru_cache()
def get_settings():
    return Settings()
