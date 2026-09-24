import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.card import Card
from app.models.list import List
from app.permissions import require_card_access, require_list_access
from app.realtime.connection_manager import manager
from app.realtime.events import EventType, build_event
from app.schemas.card import CardCreate, CardMove, CardOut, CardUpdate
from app.services import card_service

router = APIRouter(tags=["cards"])


async def _board_id_for_list(db: AsyncSession, list_id: uuid.UUID) -> uuid.UUID:
    list_obj = await db.get(List, list_id)
    return list_obj.board_id


@router.post("/api/lists/{list_id}/cards", response_model=CardOut, status_code=status.HTTP_201_CREATED)
async def create_card(
    body: CardCreate,
    db: AsyncSession = Depends(get_db),
    list_obj: List = Depends(require_list_access),
):
    card = await card_service.create_card(
        db, list_obj.id, body.title, body.description, body.due_date, body.assignee_id, body.after_card_id
    )

    event = build_event(EventType.CARD_CREATED, CardOut.model_validate(card).model_dump(mode="json"))
    await manager.broadcast(str(list_obj.board_id), event)

    return CardOut.model_validate(card)


@router.get("/api/lists/{list_id}/cards", response_model=list[CardOut])
async def list_cards(
    db: AsyncSession = Depends(get_db),
    list_obj: List = Depends(require_list_access),
):
    cards = await card_service.list_cards_for_list(db, list_obj.id)
    return [CardOut.model_validate(c) for c in cards]


@router.patch("/api/cards/{card_id}", response_model=CardOut)
async def update_card(
    body: CardUpdate,
    db: AsyncSession = Depends(get_db),
    card: Card = Depends(require_card_access),
):
    updated = await card_service.update_card(db, card, **body.model_dump())

    board_id = await _board_id_for_list(db, updated.list_id)
    event = build_event(EventType.CARD_UPDATED, CardOut.model_validate(updated).model_dump(mode="json"))
    await manager.broadcast(str(board_id), event)

    return CardOut.model_validate(updated)


@router.patch("/api/cards/{card_id}/move", response_model=CardOut)
async def move_card(
    body: CardMove,
    db: AsyncSession = Depends(get_db),
    card: Card = Depends(require_card_access),
):
    moved = await card_service.move_card(db, card, body.target_list_id, body.before_card_id, body.after_card_id)

    board_id = await _board_id_for_list(db, moved.list_id)
    event = build_event(
        EventType.CARD_MOVED,
        {"card_id": str(moved.id), "list_id": str(moved.list_id), "position": moved.position},
    )
    await manager.broadcast(str(board_id), event)

    return CardOut.model_validate(moved)


@router.delete("/api/cards/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_card(
    db: AsyncSession = Depends(get_db),
    card: Card = Depends(require_card_access),
):
    board_id = await _board_id_for_list(db, card.list_id)
    card_id_str = str(card.id)

    await card_service.delete_card(db, card)

    event = build_event(EventType.CARD_DELETED, {"card_id": card_id_str})
    await manager.broadcast(str(board_id), event)

@router.patch("/api/cards/{card_id}/move", response_model=CardOut)
async def move_card(
    body: CardMove,
    db: AsyncSession = Depends(get_db),
    card: Card = Depends(require_card_access),
):
    moved = await card_service.move_card(db, card, body.target_list_id, body.before_card_id, body.after_card_id)

    # Find the board this card's (new) list belongs to, so we broadcast to
    # everyone currently viewing that board.
    list_obj = await db.get(List, moved.list_id)
    event = build_event(
        EventType.CARD_MOVED,
        {
            "card_id": str(moved.id),
            "list_id": str(moved.list_id),
            "position": moved.position,
        },
    )
    await manager.broadcast(str(list_obj.board_id), event)

    return CardOut.model_validate(moved)