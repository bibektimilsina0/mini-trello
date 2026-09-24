import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.list import List


def _position_between(before: float | None, after: float | None) -> float:
    if before is None and after is None:
        return 1.0
    if before is None:
        return after / 2
    if after is None:
        return before + 1.0
    return (before + after) / 2


async def _get_position_value(db: AsyncSession, list_id: uuid.UUID | None) -> float | None:
    if list_id is None:
        return None
    row = await db.get(List, list_id)
    return row.position if row else None


async def create_list(db: AsyncSession, board_id: uuid.UUID, title: str, after_list_id: uuid.UUID | None) -> List:
    after_pos = await _get_position_value(db, after_list_id)

    if after_pos is not None:
        # Find the list immediately after "after_list_id" to compute a midpoint.
        next_list = await db.scalar(
            select(List)
            .where(List.board_id == board_id, List.position > after_pos)
            .order_by(List.position.asc())
            .limit(1)
        )
        next_pos = next_list.position if next_list else None
    else:
        next_pos = None

    position = _position_between(after_pos, next_pos)

    new_list = List(board_id=board_id, title=title, position=position)
    db.add(new_list)
    await db.commit()
    await db.refresh(new_list)
    return new_list


async def reorder_list(db: AsyncSession, list_obj: List, before_id: uuid.UUID | None, after_id: uuid.UUID | None) -> List:
    before_pos = await _get_position_value(db, before_id)
    after_pos = await _get_position_value(db, after_id)

    list_obj.position = _position_between(after_pos, before_pos) if (before_pos or after_pos) else _position_between(None, None)
    # Note: before/after naming follows "before_list_id = the list now to the
    # LEFT of this one" — so the new position sits between after_pos (left)
    # and before_pos (right).
    list_obj.position = _position_between(after_pos, before_pos)

    await db.commit()
    await db.refresh(list_obj)
    return list_obj


async def update_list(db: AsyncSession, list_obj: List, title: str) -> List:
    list_obj.title = title
    await db.commit()
    await db.refresh(list_obj)
    return list_obj


async def delete_list(db: AsyncSession, list_obj: List) -> None:
    await db.delete(list_obj)
    await db.commit()