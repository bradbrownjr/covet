"""Importer framework.

An importer reads a single source file (CLZ XML, CSV, JSON backup) and yields
:class:`ImportItem` records that the API/CLI then persists into a target
collection. Importers are pure parsers; they do **no** database I/O, which
makes them trivially testable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import IO, Any, Protocol


@dataclass
class ImportItem:
    """One item discovered by an importer.

    ``type`` matches :class:`covet.models.item.ItemType` values
    (``movie``, ``music``, ``book``, ``comic``, ``game``, ``other``).
    ``identifiers`` is a free-form dict (e.g. ``{"barcode": "...", "isbn": "..."}``).
    ``attrs`` holds any extra type-specific fields not modelled in the items
    table — these survive the round-trip via the JSON ``attrs`` column.
    """

    type: str
    title: str
    subtitle: str | None = None
    notes: str | None = None
    condition: str | None = None
    quantity: int = 1
    purchase_price: float | None = None
    current_value: float | None = None
    currency: str | None = None
    location: str | None = None
    identifiers: dict[str, Any] = field(default_factory=dict)
    attrs: dict[str, Any] = field(default_factory=dict)


@dataclass
class ImportResult:
    items: list[ImportItem] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.items)


class Importer(Protocol):
    """A pure parser from a binary stream to an :class:`ImportResult`."""

    name: str

    def parse(self, source: IO[bytes]) -> ImportResult: ...


__all__ = ["ImportItem", "ImportResult", "Importer"]
