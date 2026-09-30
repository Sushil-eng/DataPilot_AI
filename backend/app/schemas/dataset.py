from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import List, Dict, Any, Optional

VALID_SCHEMA_TYPES = {"string", "number", "boolean", "date", "url", "currency", "array"}

class DatasetSchemaField(BaseModel):
    name: str
    type: str

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        v_lower = v.lower()
        if v_lower not in VALID_SCHEMA_TYPES:
            raise ValueError(f"Invalid type '{v}'. Supported types: {', '.join(sorted(VALID_SCHEMA_TYPES))}")
        return v_lower

class DatasetBase(BaseModel):
    task_id: Optional[str] = None
    name: str
    description: Optional[str] = ""
    schema_fields: List[DatasetSchemaField] = Field(default_factory=list, alias="schema")

class DatasetCreate(DatasetBase):
    pass

class DatasetUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    schema_fields: Optional[List[DatasetSchemaField]] = Field(default=None, alias="schema")

class Dataset(DatasetBase):
    id: str = Field(alias="_id")
    record_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"populate_by_name": True}

class DatasetRecord(BaseModel):
    dataset_id: str
    data: Dict[str, Any]
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"extra": "allow"}

