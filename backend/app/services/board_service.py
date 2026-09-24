import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.board import Board


async def create_board(db: AsyncSession, workspace_id: uuid.UUID, title: str, creator_id: uuid.UUID) -> Board:
    board = Board(workspace_id=workspace_id, title=title, created_by=creator_id)
    db.add(board)
    await db.commit()
    await db.refresh(board)
    return board


async def list_boards_for_workspace(db: AsyncSession, workspace_id: uuid.UUID) -> list[Board]:
    result = await db.scalars(select(Board).where(Board.workspace_id == workspace_id))
    return list(result)


async def update_board(db: AsyncSession, board: Board, title: str) -> Board:
    board.title = title
    await db.commit()
    await db.refresh(board)
    return board


async def delete_board(db: AsyncSession, board: Board) -> None:
    await db.delete(board)
    await db.commit()