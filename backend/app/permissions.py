import uuid

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.workspace import WorkspaceMember, WorkspaceRole
from app.models.board import Board


async def require_workspace_member(
    workspace_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WorkspaceMember:
    """Any board/list/card route under a workspace depends on this — proves
    the current user is actually a member before letting them read/write
    anything inside it."""
    member = await db.scalar(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == current_user.id,
        )
    )
    if not member:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not a member of this workspace")
    return member


async def require_workspace_owner(
    member: WorkspaceMember = Depends(require_workspace_member),
) -> WorkspaceMember:
    """Stricter check for owner-only actions (invite/remove members, delete
    workspace). Chains off require_workspace_member — no duplicate query."""
    if member.role != WorkspaceRole.owner:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only the workspace owner can do this")
    return member

async def require_board_access(
    board_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Board:
    """Boards don't have their own membership table — access to a board is
    just membership in its parent workspace. So this looks up the board,
    then delegates to the same workspace-membership check."""
    board = await db.get(Board, board_id)
    if not board:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Board not found")

    member = await db.scalar(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == board.workspace_id,
            WorkspaceMember.user_id == current_user.id,
        )
    )
    if not member:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not a member of this board's workspace")

    return board