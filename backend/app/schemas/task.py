from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Literal

StatusType = Literal["pending", "planning", "planned", "running", "completed", "failed"]

class TaskBase(BaseModel):
    prompt: str = Field(..., min_length=1)
    record_limit: Optional[int] = Field(default=50, gt=0)

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    prompt: Optional[str] = Field(default=None, min_length=1)
    status: Optional[StatusType] = None
    progress: Optional[int] = Field(default=None, ge=0, le=100)
    record_count: Optional[int] = Field(default=None, ge=0)

class Task(TaskBase):
    id: str = Field(alias="_id")
    user_id: str = "default_user"
    status: str
    progress: int = 0
    record_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"populate_by_name": True}
