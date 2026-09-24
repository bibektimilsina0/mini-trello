import uuid

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.workspace import WorkspaceMember, WorkspaceRole


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