import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.card import Card
from app.models.list import List
from app.permissions import require_card_access, require_list_access
from app.schemas.card import CardCreate, CardMove, CardOut, CardUpdate
from app.services import card_service

router = APIRouter(tags=["cards"])


@router.post("/api/lists/{list_id}/cards", response_model=CardOut, status_code=status.HTTP_201_CREATED)
async def create_card(
    body: CardCreate,
    db: AsyncSession = Depends(get_db),
    list_obj: List = Depends(require_list_access),
):
    card = await card_service.create_card(
        db, list_obj.id, body.title, body.description, body.due_date, body.assignee_id, body.after_card_id
    )
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
    return CardOut.model_validate(updated)


@router.patch("/api/cards/{card_id}/move", response_model=CardOut)
async def move_card(
    body: CardMove,
    db: AsyncSession = Depends(get_db),
    card: Card = Depends(require_card_access),
):
    moved = await card_service.move_card(db, card, body.target_list_id, body.before_card_id, body.after_card_id)
    return CardOut.model_validate(moved)


@router.delete("/api/cards/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_card(
    db: AsyncSession = Depends(get_db),
    card: Card = Depends(require_card_access),
):
    await card_service.delete_card(db, card)