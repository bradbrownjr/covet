"""Maintenance task schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class MaintenanceTaskBase(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    notes: str | None = None
    interval_days: int | None = Field(default=None, ge=1, le=36500)
    last_completed_at: datetime | None = None
    next_due_at: datetime | None = None


class MaintenanceTaskCreate(MaintenanceTaskBase):
    pass


class MaintenanceTaskUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    notes: str | None = None
    interval_days: int | None = Field(default=None, ge=1, le=36500)
    last_completed_at: datetime | None = None
    next_due_at: datetime | None = None


class MaintenanceTaskRead(MaintenanceTaskBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    item_id: str
    created_at: datetime
    updated_at: datetime
