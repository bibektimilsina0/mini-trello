import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class List(Base):
    __tablename__ = "lists"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    board_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("boards.id"), nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    position: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    board: Mapped["Board"] = relationship(back_populates="lists")
    cards: Mapped[list["Card"]] = relationship(back_populates="list", lazy="selectin", order_by="Card.position")