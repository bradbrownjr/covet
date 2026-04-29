"""Tag and ItemTag models."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from covet.db import Base
from covet.models.base import TimestampMixin, ULIDPrimaryKey

if TYPE_CHECKING:
    from covet.models.item import Item


class Tag(ULIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "tags"
    __table_args__ = (UniqueConstraint("owner_id", "name", name="uq_tag_owner_name"),)

    owner_id: Mapped[str] = mapped_column(
        String(26), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    color: Mapped[str | None] = mapped_column(String(16), nullable=True)


class ItemTag(Base):
    __tablename__ = "item_tags"

    item_id: Mapped[str] = mapped_column(
        String(26), ForeignKey("items.id", ondelete="CASCADE"), primary_key=True
    )
    tag_id: Mapped[str] = mapped_column(
        String(26), ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True
    )

    item: Mapped[Item] = relationship(back_populates="tags")
    tag: Mapped[Tag] = relationship()
