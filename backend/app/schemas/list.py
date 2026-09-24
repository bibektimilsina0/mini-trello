import uuid

from pydantic import BaseModel, Field


class ListCreate(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    # Position of the list this new one goes AFTER — omit to add at the end.
    after_list_id: uuid.UUID | None = None


class ListUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=100)


class ListReorder(BaseModel):
    before_list_id: uuid.UUID | None = None
    after_list_id: uuid.UUID | None = None


class ListOut(BaseModel):
    id: uuid.UUID
    board_id: uuid.UUID
    title: str
    position: float

    class Config:
        from_attributes = True