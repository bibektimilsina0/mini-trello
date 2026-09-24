import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.comment import Comment


async def create_comment(db: AsyncSession, card_id: uuid.UUID, user_id: uuid.UUID, body: str) -> Comment:
    comment = Comment(card_id=card_id, user_id=user_id, body=body)
    db.add(comment)
    await db.commit()
    await db.refresh(comment)
    return comment


async def list_comments_for_card(db: AsyncSession, card_id: uuid.UUID) -> list[Comment]:
    result = await db.scalars(
        select(Comment).where(Comment.card_id == card_id).order_by(Comment.created_at)
    )
    return list(result)


async def update_comment(db: AsyncSession, comment: Comment, current_user_id: uuid.UUID, body: str) -> Comment:
    if comment.user_id != current_user_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "You can only edit your own comments")
    comment.body = body
    await db.commit()
    await db.refresh(comment)
    return comment


async def delete_comment(db: AsyncSession, comment: Comment, current_user_id: uuid.UUID) -> None:
    if comment.user_id != current_user_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "You can only delete your own comments")
    await db.delete(comment)
    await db.commit()