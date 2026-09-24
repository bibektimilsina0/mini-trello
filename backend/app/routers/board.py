import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.board import Board
from app.models.user import User
from app.permissions import require_board_access, require_workspace_member
from app.schemas.board import BoardCreate, BoardOut, BoardUpdate
from app.services import board_service

router = APIRouter(tags=["boards"])


# Nested under workspace — creating/listing boards needs the workspace_id.
@router.post("/api/workspaces/{workspace_id}/boards", response_model=BoardOut, status_code=status.HTTP_201_CREATED)
async def create_board(
    workspace_id: uuid.UUID,
    body: BoardCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _member=Depends(require_workspace_member),
):
    board = await board_service.create_board(db, workspace_id, body.title, current_user.id)
    return BoardOut.model_validate(board)


@router.get("/api/workspaces/{workspace_id}/boards", response_model=list[BoardOut])
async def list_boards(
    workspace_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _member=Depends(require_workspace_member),
):
    boards = await board_service.list_boards_for_workspace(db, workspace_id)
    return [BoardOut.model_validate(b) for b in boards]


# Flat, board-scoped routes — once you have a board_id, you don't need the
# workspace_id in the URL anymore; require_board_access derives it internally.
@router.get("/api/boards/{board_id}", response_model=BoardOut)
async def get_board(board: Board = Depends(require_board_access)):
    return BoardOut.model_validate(board)


@router.patch("/api/boards/{board_id}", response_model=BoardOut)
async def update_board(
    body: BoardUpdate,
    db: AsyncSession = Depends(get_db),
    board: Board = Depends(require_board_access),
):
    updated = await board_service.update_board(db, board, body.title)
    return BoardOut.model_validate(updated)


@router.delete("/api/boards/{board_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_board(
    db: AsyncSession = Depends(get_db),
    board: Board = Depends(require_board_access),
):
    await board_service.delete_board(db, board)