from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class SourceBase(BaseModel):
    dataset_id: str
    url: str
    title: str
    source_type: str

class SourceCreate(SourceBase):
    pass

class Source(SourceBase):
    id: str = Field(alias="_id")
    collected_at: datetime

    model_config = {"populate_by_name": True}

