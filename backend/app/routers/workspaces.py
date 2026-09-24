import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.workspace import WorkspaceMember
from app.permissions import require_workspace_member, require_workspace_owner
from app.schemas.workspace import MemberInvite, MemberOut, WorkspaceCreate, WorkspaceOut, WorkspaceUpdate
from app.services import workspace_service

router = APIRouter(prefix="/api/workspaces", tags=["workspaces"])


@router.post("", response_model=WorkspaceOut, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    body: WorkspaceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    workspace = await workspace_service.create_workspace(db, current_user, body.name)
    return WorkspaceOut.model_validate(workspace)


@router.get("", response_model=list[WorkspaceOut])
async def list_my_workspaces(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    workspaces = await workspace_service.list_user_workspaces(db, current_user)
    return [WorkspaceOut.model_validate(w) for w in workspaces]


@router.patch("/{workspace_id}", response_model=WorkspaceOut)
async def update_workspace(
    workspace_id: uuid.UUID,
    body: WorkspaceUpdate,
    db: AsyncSession = Depends(get_db),
    _owner: WorkspaceMember = Depends(require_workspace_owner),
):
    workspace = await workspace_service.update_workspace(db, workspace_id, body.name)
    return WorkspaceOut.model_validate(workspace)


@router.get("/{workspace_id}/members", response_model=list[MemberOut])
async def list_members(
    workspace_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _member: WorkspaceMember = Depends(require_workspace_member),
):
    rows = await db.execute(
        select(WorkspaceMember, User)
        .join(User, User.id == WorkspaceMember.user_id)
        .where(WorkspaceMember.workspace_id == workspace_id)
    )
    return [
        MemberOut(user_id=user.id, email=user.email, name=user.name, role=member.role)
        for member, user in rows.all()
    ]


@router.post("/{workspace_id}/members", response_model=MemberOut, status_code=status.HTTP_201_CREATED)
async def invite_member(
    workspace_id: uuid.UUID,
    body: MemberInvite,
    db: AsyncSession = Depends(get_db),
    _owner: WorkspaceMember = Depends(require_workspace_owner),
):
    membership = await workspace_service.invite_member(db, workspace_id, body.email, body.role)
    user = await db.get(User, membership.user_id)
    return MemberOut(user_id=user.id, email=user.email, name=user.name, role=membership.role)


@router.delete("/{workspace_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _owner: WorkspaceMember = Depends(require_workspace_owner),
):
    await workspace_service.remove_member(db, workspace_id, user_id)