"""Shopping list schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ShoppingSource(BaseModel):
    """Sub-schema describing where a grocery feed entry comes from."""

    model_config = ConfigDict(from_attributes=True)

    kind: str  # "ad_hoc" | "depleted_item"
    item_id: str | None = None  # populated for "depleted_item" or when ad-hoc has linked_item


class ShoppingItemRead(BaseModel):
    """A user-created grocery list entry."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    collection_id: str
    name: str
    quantity: int
    unit: str | None = None
    notes: str | None = None
    category_slug: str | None = None
    linked_item_id: str | None = None
    purchased_at: datetime | None = None
    purchased_by_user_id: str | None = None
    created_by_user_id: str | None = None
    created_at: datetime
    updated_at: datetime


class ShoppingFeedEntry(BaseModel):
    """A single row in the unified grocery feed.

    Either an ad-hoc grocery_item or a depleted Item shown as a virtual
    grocery entry.
    """

    model_config = ConfigDict(from_attributes=True)

    id: str  # grocery_item.id OR item.id (with prefix)
    source: ShoppingSource
    collection_id: str
    name: str
    subtitle: str | None = None
    quantity: int = 1
    unit: str | None = None
    notes: str | None = None
    category_slug: str | None = None
    linked_item_id: str | None = None
    purchased_at: datetime | None = None
    created_at: datetime


class ShoppingItemCreate(BaseModel):
    collection_id: str
    name: str = Field(min_length=1, max_length=255)
    quantity: int = Field(default=1, ge=1)
    unit: str | None = Field(default=None, max_length=32)
    notes: str | None = None
    category_slug: str | None = Field(default=None, max_length=120)
    linked_item_id: str | None = None


class ShoppingItemUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    quantity: int | None = Field(default=None, ge=1)
    unit: str | None = Field(default=None, max_length=32)
    notes: str | None = None
    category_slug: str | None = Field(default=None, max_length=120)
    linked_item_id: str | None = None


class ShoppingPurchaseRequest(BaseModel):
    """Optional metadata for the purchase event."""

    purchased_at: datetime | None = None
    use_by_date: str | None = None


# ---------------------------------------------------------------------------
# Store / aisle schemas
# ---------------------------------------------------------------------------


class ShoppingAisleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    store_id: str
    name: str
    position: int
    category_slugs: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class ShoppingAisleCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    position: int = Field(default=0, ge=0)
    category_slugs: list[str] = Field(default_factory=list)


class ShoppingAisleUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    position: int | None = Field(default=None, ge=0)
    category_slugs: list[str] | None = None


class ShoppingStoreRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    owner_user_id: str
    name: str
    aisles: list[ShoppingAisleRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class ShoppingStoreCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class ShoppingStoreUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)


class ShoppingCount(BaseModel):
    """Lightweight count for nav badge."""

    total: int
    ad_hoc: int
    depleted_items: int
