import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field


class CardCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    due_date: date | None = None
    assignee_id: uuid.UUID | None = None
    after_card_id: uuid.UUID | None = None  # same "insert after X" pattern as ListCreate


class CardUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    due_date: date | None = None
    assignee_id: uuid.UUID | None = None


class CardMove(BaseModel):
    """Moving a card can change both its list AND its position within
    that list in one action — this is what fires on every drag-and-drop."""
    target_list_id: uuid.UUID
    before_card_id: uuid.UUID | None = None
    after_card_id: uuid.UUID | None = None


class CardOut(BaseModel):
    id: uuid.UUID
    list_id: uuid.UUID
    title: str
    description: str | None
    position: float
    due_date: date | None
    assignee_id: uuid.UUID | None
    created_at: datetime

    class Config:
        from_attributes = True