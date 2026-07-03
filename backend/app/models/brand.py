import uuid

from sqlalchemy import String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Brand(Base):
    """Top-level brand entity.

    Phase 1 (Brand inputs) fields: vision, goal, moat. Later phases attach
    related tables (personas, voice, competitors, pillars) via this brand id.
    """

    __tablename__ = "brands"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)

    # Phase 1 — Brand inputs
    vision: Mapped[str | None] = mapped_column(Text, nullable=True)
    goal: Mapped[str | None] = mapped_column(Text, nullable=True)
    moat: Mapped[str | None] = mapped_column(Text, nullable=True)
