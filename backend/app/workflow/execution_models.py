"""
Workflow Execution Models — Phase 4 Prompt 4
Defines execution status, statistics, and execution context.
"""

from enum import Enum
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field


class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    FALLBACK = "fallback"


class WorkflowStepState(BaseModel):
    id: str
    name: str
    tool: str
    status: StepStatus = StepStatus.PENDING
    progress: float = 0.0
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None
    message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()


class ExecutionStatistics(BaseModel):
    sources_discovered: int = 0
    sources_processed: int = 0
    sources_failed: int = 0
    raw_records: int = 0
    cleaned_records: int = 0
    valid_records: int = 0
    invalid_records: int = 0
    duplicates_removed: int = 0
    final_records: int = 0

    def to_dict(self) -> Dict[str, int]:
        return self.model_dump()


class ExecutionContext:
    """
    In-memory state container maintained during a single workflow execution run.
    Passes output between workflow steps without unnecessarily reloading from DB.
    """

    def __init__(
        self,
        task_id: str,
        workflow_id: str,
        dataset_id: str,
        requirements: Dict[str, Any],
        schema: Dict[str, Any],
        record_limit: int = 50,
    ):
        self.task_id = task_id
        self.workflow_id = workflow_id
        self.dataset_id = dataset_id
        self.requirements = requirements
        self.schema = schema
        self.record_limit = record_limit

        self.sources: List[Dict[str, Any]] = []
        self.raw_records: List[Dict[str, Any]] = []
        self.processed_records: List[Dict[str, Any]] = []
        self.valid_records: List[Dict[str, Any]] = []
        self.final_records: List[Dict[str, Any]] = []

        self.search_fallback: bool = False
        self.fallback_used: bool = False
        self.fallback_reason: Optional[str] = None

        self.statistics = ExecutionStatistics()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "workflow_id": self.workflow_id,
            "dataset_id": self.dataset_id,
            "record_limit": self.record_limit,
            "sources": self.sources,
            "raw_records": self.raw_records,
            "processed_records": self.processed_records,
            "valid_records": self.valid_records,
            "final_records": self.final_records,
            "search_fallback": self.search_fallback,
            "fallback_used": self.fallback_used,
            "fallback_reason": self.fallback_reason,
            "statistics": self.statistics.to_dict(),
        }
