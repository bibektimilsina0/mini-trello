import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.board import Board
from app.models.list import List
from app.permissions import require_board_access, require_list_access
from app.schemas.list import ListCreate, ListOut, ListReorder, ListUpdate
from app.services import list_service

router = APIRouter(tags=["lists"])


@router.post("/api/boards/{board_id}/lists", response_model=ListOut, status_code=status.HTTP_201_CREATED)
async def create_list(
    body: ListCreate,
    db: AsyncSession = Depends(get_db),
    board: Board = Depends(require_board_access),
):
    new_list = await list_service.create_list(db, board.id, body.title, body.after_list_id)
    return ListOut.model_validate(new_list)


@router.patch("/api/lists/{list_id}", response_model=ListOut)
async def update_list(
    body: ListUpdate,
    db: AsyncSession = Depends(get_db),
    list_obj: List = Depends(require_list_access),
):
    updated = await list_service.update_list(db, list_obj, body.title)
    return ListOut.model_validate(updated)


@router.patch("/api/lists/{list_id}/reorder", response_model=ListOut)
async def reorder_list(
    body: ListReorder,
    db: AsyncSession = Depends(get_db),
    list_obj: List = Depends(require_list_access),
):
    reordered = await list_service.reorder_list(db, list_obj, body.before_list_id, body.after_list_id)
    return ListOut.model_validate(reordered)


@router.delete("/api/lists/{list_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_list(
    db: AsyncSession = Depends(get_db),
    list_obj: List = Depends(require_list_access),
):
    await list_service.delete_list(db, list_obj)