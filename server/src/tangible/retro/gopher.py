"""Gopher (RFC 1436) asyncio server.

Serves public collections (is_public=True) as a read-only Gopher menu tree.
No authentication — Gopher has no native auth mechanism.

Item types used:
  0  plain text document (item detail)
  1  directory / submenu
  g  GIF image
  i  informational line (no link)

LAN use only — plain TCP on port 70 (configurable).
"""

from __future__ import annotations

import asyncio
import logging
import os
import urllib.parse
from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.orm import Session as DBSession, sessionmaker

from tangible.db import get_engine

if TYPE_CHECKING:
    from tangible.config import Settings

log = logging.getLogger(__name__)

_MAX_SELECTOR_BYTES = 4096


async def create_gopher_server(settings: "Settings") -> asyncio.Server:
    handler = _make_handler(settings)
    return await asyncio.start_server(
        handler,
        host=settings.retro_gopher_bind,
        port=settings.retro_gopher_port,
    )


def _make_handler(settings: "Settings"):
    async def handle(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        peer = writer.get_extra_info("peername")
        ip = str(peer[0]) if peer else "unknown"
        try:
            raw = await asyncio.wait_for(reader.read(_MAX_SELECTOR_BYTES), timeout=10)
            selector = raw.decode("ascii", errors="replace").rstrip("\r\n")
            await _dispatch(writer, selector, settings)
        except asyncio.TimeoutError:
            pass
        except Exception:
            log.exception("Gopher handler error from %s", ip)
        finally:
            try:
                writer.close()
            except Exception:
                pass

    return handle


# ---------------------------------------------------------------------------
# Gopher line helpers
# ---------------------------------------------------------------------------

def _item(item_type: str, display: str, selector: str, host: str, port: int) -> str:
    return f"{item_type}{display}\t{selector}\t{host}\t{port}\r\n"


def _info(text: str) -> str:
    return f"i{text}\t\t\t\r\n"


def _end() -> str:
    return ".\r\n"


def _not_found(host: str, port: int) -> str:
    return (
        _info("Resource not found.")
        + _item("1", "Return to root", "/", host, port)
        + _end()
    )


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------

async def _dispatch(
    writer: asyncio.StreamWriter,
    selector: str,
    settings: "Settings",
) -> None:
    host = settings.retro_gopher_host
    port = settings.retro_gopher_port
    engine = get_engine()
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

    selector = selector.strip()
    if selector == "" or selector == "/":
        with Session() as db:
            content = _menu_root(db, host, port)
        _send(writer, content)

    elif selector.startswith("/collections/"):
        parts = selector.split("/")
        coll_id = parts[2] if len(parts) > 2 else ""
        with Session() as db:
            content = _menu_collection(db, coll_id, host, port)
        _send(writer, content)

    elif selector.startswith("/items/") and selector.endswith("/photo.gif"):
        parts = selector.split("/")
        item_id = parts[2] if len(parts) > 2 else ""
        with Session() as db:
            data = _serve_photo(db, item_id, settings)
        if data:
            writer.write(data)
        else:
            _send(writer, _not_found(host, port))

    elif selector.startswith("/items/"):
        parts = selector.split("/")
        item_id = parts[2] if len(parts) > 2 else ""
        with Session() as db:
            content = _doc_item(db, item_id, host, port)
        _send(writer, content)

    else:
        _send(writer, _not_found(host, port))


def _send(writer: asyncio.StreamWriter, content: str) -> None:
    writer.write(content.encode("utf-8", errors="replace"))


# ---------------------------------------------------------------------------
# Menu: root
# ---------------------------------------------------------------------------

def _menu_root(db: DBSession, host: str, port: int) -> str:
    from tangible.models.collection import Collection

    colls = db.scalars(
        select(Collection).where(Collection.is_public == True).order_by(Collection.name)  # noqa: E712
    ).all()

    lines = [
        _info("=" * 67),
        _info("  TANGIBLE INVENTORY MANAGEMENT SYSTEM"),
        _info("  Public Collection Browser (Gopher)"),
        _info("=" * 67),
        _info(""),
    ]

    if colls:
        lines.append(_info("Public Collections:"))
        for c in colls:
            desc = f" — {c.description[:40]}" if c.description else ""
            lines.append(_item("1", f"{c.name[:50]}{desc}", f"/collections/{c.id}", host, port))
    else:
        lines.append(_info("No public collections available."))

    lines.append(_info(""))
    lines.append(_info("Connect to the modern web interface for full access."))
    lines.append(_end())
    return "".join(lines)


# ---------------------------------------------------------------------------
# Menu: collection items
# ---------------------------------------------------------------------------

def _menu_collection(db: DBSession, collection_id: str, host: str, port: int) -> str:
    from tangible.models.collection import Collection
    from tangible.models.item import Item

    coll = db.get(Collection, collection_id)
    if coll is None or not coll.is_public:
        return _not_found(host, port)

    items = db.scalars(
        select(Item).where(
            Item.collection_id == collection_id,
            Item.archived_at.is_(None),
        ).order_by(Item.title)
    ).all()

    lines = [
        _info("=" * 67),
        _info(f"  {coll.name[:60]}"),
    ]
    if coll.description:
        lines.append(_info(f"  {coll.description[:60]}"))
    lines.append(_info("=" * 67))
    lines.append(_info(""))

    for item in items:
        cond = f" [{item.condition}]" if item.condition else ""
        display = f"{(item.title or 'Untitled')[:50]}{cond}"
        lines.append(_item("0", display, f"/items/{item.id}", host, port))

        # Offer GIF if the item has a photo
        from tangible.models.photo import Photo
        photo = db.scalar(select(Photo).where(Photo.item_id == item.id).order_by(Photo.sort_order))
        if photo:
            lines.append(_item("g", f"  [photo] {(item.title or '')[:40]}", f"/items/{item.id}/photo.gif", host, port))

    lines.append(_info(""))
    lines.append(_item("1", "Back to root", "/", host, port))
    lines.append(_end())
    return "".join(lines)


# ---------------------------------------------------------------------------
# Document: item detail
# ---------------------------------------------------------------------------

def _doc_item(db: DBSession, item_id: str, host: str, port: int) -> str:
    from tangible.models.item import Item

    item = db.get(Item, item_id)
    if item is None:
        return "Item not found.\r\n.\r\n"

    coll = item.collection
    if coll is None or not coll.is_public:
        return "Item not available.\r\n.\r\n"

    cat_name = item.category.name if item.category else ""
    loc_name = item.location.name if item.location else ""
    tags = ", ".join(t.name for t in item.tags) if item.tags else ""

    lines = [
        "=" * 67,
        f"  {item.title or 'Untitled'}",
        "=" * 67,
        "",
    ]
    if item.subtitle:
        lines.append(f"  Subtitle:      {item.subtitle}")
    if item.condition:
        lines.append(f"  Condition:     {item.condition}")
    lines.append(f"  Quantity:      {item.quantity or 1}")
    if cat_name:
        lines.append(f"  Category:      {cat_name}")
    if loc_name:
        lines.append(f"  Location:      {loc_name}")
    if tags:
        lines.append(f"  Tags:          {tags}")
    if item.purchase_price:
        lines.append(f"  Purchase Price:{item.purchase_price}")
    if item.current_value:
        lines.append(f"  Current Value: {item.current_value}")
    if item.acquired_at:
        lines.append(f"  Acquired:      {item.acquired_at.date()}")
    if item.notes:
        lines.append("")
        lines.append("  Notes:")
        for ln in item.notes.splitlines()[:10]:
            lines.append(f"  {ln[:65]}")
    lines.append("")
    lines.append(f"  Collection: {coll.name}")
    lines.append("=" * 67)
    lines.append("")

    return "\r\n".join(lines) + "\r\n.\r\n"


# ---------------------------------------------------------------------------
# Photo serving
# ---------------------------------------------------------------------------

def _serve_photo(db: DBSession, item_id: str, settings: "Settings") -> bytes | None:
    from tangible.models.photo import Photo
    from tangible.models.item import Item
    from tangible.models.collection import Collection
    from tangible.retro.html_gen import photo_to_gif

    item = db.get(Item, item_id)
    if item is None:
        return None
    coll = item.collection
    if coll is None or not coll.is_public:
        return None

    photo = db.scalar(
        select(Photo).where(Photo.item_id == item_id, Photo.is_primary == True)  # noqa: E712
        .order_by(Photo.sort_order)
    )
    if photo is None:
        photo = db.scalar(select(Photo).where(Photo.item_id == item_id).order_by(Photo.sort_order))
    if photo is None:
        return None

    photo_path = os.path.join(str(settings.photos_dir), photo.storage_key)
    if not os.path.isfile(photo_path):
        return None

    return photo_to_gif(photo_path)
