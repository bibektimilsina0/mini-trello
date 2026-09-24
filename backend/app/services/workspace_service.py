import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMember, WorkspaceRole


async def create_workspace(db: AsyncSession, owner: User, name: str) -> Workspace:
    workspace = Workspace(name=name, owner_id=owner.id)
    db.add(workspace)
    await db.flush()  # get workspace.id before adding the membership row

    membership = WorkspaceMember(workspace_id=workspace.id, user_id=owner.id, role=WorkspaceRole.owner)
    db.add(membership)

    await db.commit()
    await db.refresh(workspace)
    return workspace


async def list_user_workspaces(db: AsyncSession, user: User) -> list[Workspace]:
    result = await db.scalars(
        select(Workspace)
        .join(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
        .where(WorkspaceMember.user_id == user.id)
    )
    return list(result)


async def update_workspace(db: AsyncSession, workspace_id: uuid.UUID, name: str) -> Workspace:
    workspace = await db.get(Workspace, workspace_id)
    if not workspace:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Workspace not found")
    workspace.name = name
    await db.commit()
    await db.refresh(workspace)
    return workspace


async def invite_member(db: AsyncSession, workspace_id: uuid.UUID, email: str, role: WorkspaceRole) -> WorkspaceMember:
    user = await db.scalar(select(User).where(User.email == email))
    if not user:
        # Simplification for now: the invited person must already have an
        # account. A real invite flow would create a pending invite + email
        # a signup link instead — worth adding once you're past the MVP.
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No account found with that email")

    existing = await db.scalar(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id, WorkspaceMember.user_id == user.id
        )
    )
    if existing:
        raise HTTPException(status.HTTP_409_CONFLICT, "User is already a member")

    membership = WorkspaceMember(workspace_id=workspace_id, user_id=user.id, role=role)
    db.add(membership)
    await db.commit()
    await db.refresh(membership)
    return membership


async def remove_member(db: AsyncSession, workspace_id: uuid.UUID, user_id: uuid.UUID) -> None:
    membership = await db.scalar(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id, WorkspaceMember.user_id == user_id
        )
    )
    if not membership:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Member not found")
    if membership.role == WorkspaceRole.owner:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Cannot remove the workspace owner")

    await db.delete(membership)
    await db.commit()