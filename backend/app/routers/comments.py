import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.card import Card
from app.models.comment import Comment
from app.models.user import User
from app.permissions import require_card_access
from app.schemas.comment import CommentCreate, CommentOut, CommentUpdate
from app.services import comment_service

router = APIRouter(tags=["comments"])


def _to_out(comment: Comment) -> CommentOut:
    return CommentOut(
        id=comment.id,
        card_id=comment.card_id,
        user_id=comment.user_id,
        author_name=comment.author.name,
        body=comment.body,
        created_at=comment.created_at,
    )


@router.post("/api/cards/{card_id}/comments", response_model=CommentOut, status_code=status.HTTP_201_CREATED)
async def create_comment(
    body: CommentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    card: Card = Depends(require_card_access),
):
    comment = await comment_service.create_comment(db, card.id, current_user.id, body.body)
    await db.refresh(comment, attribute_names=["author"])
    return _to_out(comment)


@router.get("/api/cards/{card_id}/comments", response_model=list[CommentOut])
async def list_comments(
    db: AsyncSession = Depends(get_db),
    card: Card = Depends(require_card_access),
):
    comments = await comment_service.list_comments_for_card(db, card.id)
    return [_to_out(c) for c in comments]


async def _get_comment_or_404(db: AsyncSession, comment_id: uuid.UUID) -> Comment:
    comment = await db.get(Comment, comment_id)
    if not comment:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Comment not found")
    return comment


@router.patch("/api/comments/{comment_id}", response_model=CommentOut)
async def update_comment(
    comment_id: uuid.UUID,
    body: CommentUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    comment = await _get_comment_or_404(db, comment_id)
    updated = await comment_service.update_comment(db, comment, current_user.id, body.body)
    await db.refresh(updated, attribute_names=["author"])
    return _to_out(updated)


@router.delete("/api/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    comment_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    comment = await _get_comment_or_404(db, comment_id)
    await comment_service.delete_comment(db, comment, current_user.id)