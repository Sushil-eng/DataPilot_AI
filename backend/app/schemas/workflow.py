from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional, Any

VALID_WORKFLOW_STATUSES = {"pending", "planning", "planned", "running", "completed", "failed"}

DEFAULT_WORKFLOW_STEPS = [
    {"id": "step_1", "name": "Understanding request", "status": "pending", "result": None},
    {"id": "step_2", "name": "Creating collection plan", "status": "pending", "result": None},
    {"id": "step_3", "name": "Finding sources", "status": "pending", "result": None},
    {"id": "step_4", "name": "Extracting information", "status": "pending", "result": None},
    {"id": "step_5", "name": "Cleaning and validating data", "status": "pending", "result": None},
    {"id": "step_6", "name": "Removing duplicates", "status": "pending", "result": None},
    {"id": "step_7", "name": "Preparing dataset", "status": "pending", "result": None},
]

class WorkflowStep(BaseModel):
    id: str
    name: str
    status: str
    result: Optional[dict] = None

class WorkflowStepUpdate(BaseModel):
    status: Optional[str] = None
    result: Optional[dict] = None

class WorkflowBase(BaseModel):
    task_id: str

class WorkflowCreate(WorkflowBase):
    pass

class WorkflowUpdate(BaseModel):
    status: Optional[str] = None
    progress: Optional[int] = None

class Workflow(WorkflowBase):
    id: str = Field(alias="_id")
    status: str
    progress: int
    steps: List[WorkflowStep] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"populate_by_name": True}

