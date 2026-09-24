import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.card import Card


def _position_between(before: float | None, after: float | None) -> float:
    if before is None and after is None:
        return 1.0
    if before is None:
        return after / 2
    if after is None:
        return before + 1.0
    return (before + after) / 2


async def _get_position(db: AsyncSession, card_id: uuid.UUID | None) -> float | None:
    if card_id is None:
        return None
    card = await db.get(Card, card_id)
    return card.position if card else None


async def create_card(
    db: AsyncSession,
    list_id: uuid.UUID,
    title: str,
    description: str | None,
    due_date,
    assignee_id: uuid.UUID | None,
    after_card_id: uuid.UUID | None,
) -> Card:
    after_pos = await _get_position(db, after_card_id)

    next_card = await db.scalar(
        select(Card)
        .where(Card.list_id == list_id, Card.position > (after_pos or 0))
        .order_by(Card.position.asc())
        .limit(1)
    )
    next_pos = next_card.position if next_card else None
    position = _position_between(after_pos, next_pos)

    card = Card(
        list_id=list_id,
        title=title,
        description=description,
        due_date=due_date,
        assignee_id=assignee_id,
        position=position,
    )
    db.add(card)
    await db.commit()
    await db.refresh(card)
    return card


async def update_card(db: AsyncSession, card: Card, **fields) -> Card:
    for key, value in fields.items():
        if value is not None:
            setattr(card, key, value)
    await db.commit()
    await db.refresh(card)
    return card


async def move_card(
    db: AsyncSession,
    card: Card,
    target_list_id: uuid.UUID,
    before_card_id: uuid.UUID | None,
    after_card_id: uuid.UUID | None,
) -> Card:
    before_pos = await _get_position(db, before_card_id)
    after_pos = await _get_position(db, after_card_id)

    card.list_id = target_list_id
    card.position = _position_between(after_pos, before_pos)
    await db.commit()
    await db.refresh(card)
    return card


async def delete_card(db: AsyncSession, card: Card) -> None:
    await db.delete(card)
    await db.commit()


async def list_cards_for_list(db: AsyncSession, list_id: uuid.UUID) -> list[Card]:
    result = await db.scalars(select(Card).where(Card.list_id == list_id).order_by(Card.position))
    return list(result)