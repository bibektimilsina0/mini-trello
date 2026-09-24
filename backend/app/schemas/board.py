import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class BoardCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)


class BoardUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=200)


class BoardOut(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    title: str
    created_by: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True