import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class CommentCreate(BaseModel):
    body: str = Field(min_length=1, max_length=2000)


class CommentUpdate(BaseModel):
    body: str = Field(min_length=1, max_length=2000)


class CommentOut(BaseModel):
    id: uuid.UUID
    card_id: uuid.UUID
    user_id: uuid.UUID
    author_name: str
    body: str
    created_at: datetime

    class Config:
        from_attributes = True