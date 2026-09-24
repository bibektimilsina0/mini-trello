import uuid

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.board import Board
from app.models.list import List as ListModel
from app.models.user import User
from app.models.workspace import WorkspaceMember, WorkspaceRole
from app.models.card import Card


async def _check_membership(db: AsyncSession, workspace_id: uuid.UUID, user_id: uuid.UUID) -> WorkspaceMember:
    member = await db.scalar(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user_id,
        )
    )
    if not member:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not a member of this workspace")
    return member


async def require_workspace_member(
    workspace_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WorkspaceMember:
    return await _check_membership(db, workspace_id, current_user.id)


async def require_workspace_owner(
    member: WorkspaceMember = Depends(require_workspace_member),
) -> WorkspaceMember:
    if member.role != WorkspaceRole.owner:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only the workspace owner can do this")
    return member


async def require_board_access(
    board_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Board:
    board = await db.get(Board, board_id)
    if not board:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Board not found")
    await _check_membership(db, board.workspace_id, current_user.id)
    return board


async def require_list_access(
    list_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ListModel:
    """One level deeper than require_board_access: fetch the list, walk up
    to its board, then its workspace, and check membership there. Same
    pattern you'll reuse for require_card_access next."""
    list_obj = await db.get(ListModel, list_id)
    if not list_obj:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "List not found")

    board = await db.get(Board, list_obj.board_id)
    if not board:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Board not found")

    await _check_membership(db, board.workspace_id, current_user.id)
    return list_obj


async def require_card_access(
    card_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Card:
    """Four hops deep: Card -> List -> Board -> Workspace membership."""
    card = await db.get(Card, card_id)
    if not card:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Card not found")

    list_obj = await db.get(ListModel, card.list_id)
    if not list_obj:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "List not found")

    board = await db.get(Board, list_obj.board_id)
    if not board:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Board not found")

    await _check_membership(db, board.workspace_id, current_user.id)
    return card