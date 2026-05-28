"""Telnet asyncio server — department store inventory terminal aesthetic.

Implements just enough of RFC 854 (Telnet) to:
- Suppress Go-Ahead (RFC 858) for smooth streaming
- Control echo (RFC 857) to hide passwords
- Handle CR+LF and CR+NUL line endings per spec

All inventory operations use a direct SQLAlchemy session.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import func, select
from sqlalchemy.orm import Session as DBSession, sessionmaker

from tangible.db import get_engine

if TYPE_CHECKING:
    from tangible.config import Settings

log = logging.getLogger(__name__)

# Telnet IAC commands
IAC = bytes([255])
WILL = bytes([251])
WONT = bytes([252])
DO = bytes([253])
DONT = bytes([254])
ECHO = bytes([1])
SGA = bytes([3])   # Suppress Go-Ahead

_MAX_LINE = 512
_LOGIN_ATTEMPTS = 3


async def create_telnet_server(settings: "Settings") -> asyncio.Server:
    handler = _make_handler(settings)
    return await asyncio.start_server(
        handler,
        host=settings.telnet_bind,
        port=settings.telnet_port,
    )


def _make_handler(settings: "Settings"):
    async def handle(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        peer = writer.get_extra_info("peername")
        ip = str(peer[0]) if peer else "unknown"
        session = TelnetSession(reader, writer, ip, settings)
        try:
            await session.run()
        except (ConnectionResetError, BrokenPipeError, asyncio.IncompleteReadError):
            pass
        except Exception:
            log.exception("Telnet session error from %s", ip)
        finally:
            try:
                writer.close()
            except Exception:
                pass

    return handle


class TelnetSession:
    def __init__(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        ip: str,
        settings: "Settings",
    ) -> None:
        self.reader = reader
        self.writer = writer
        self.ip = ip
        self.settings = settings
        self.username: str | None = None
        self._echo_on = True

    # ------------------------------------------------------------------
    # Entry point
    # ------------------------------------------------------------------

    async def run(self) -> None:
        from tangible.retro.ban_service import is_banned

        # Negotiate: WILL SGA, WILL ECHO
        self._write_raw(IAC + WILL + SGA + IAC + WILL + ECHO)
        await self.writer.drain()

        engine = get_engine()
        Session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

        with Session() as db:
            ban = is_banned(db, self.ip, "telnet")
        if ban is True:
            await self._writeln("*** ACCESS DENIED — CONTACT ADMINISTRATOR ***")
            await self._writeln("")
            await self.writer.drain()
            return
        if ban is not False:
            wait = max(0, int((ban - datetime.utcnow()).total_seconds()))
            await self._writeln(f"*** ACCESS TEMPORARILY BLOCKED — TRY AGAIN IN {wait} SECONDS ***")
            await self.writer.drain()
            return

        authenticated = await self._login()
        if not authenticated:
            return

        await self._main_loop()

    # ------------------------------------------------------------------
    # Login
    # ------------------------------------------------------------------

    async def _login(self) -> bool:
        from tangible.retro.terminal import login_screen
        from tangible.retro.auth import authenticate
        from tangible.retro.ban_service import record_attempt

        engine = get_engine()
        Session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

        await self._write(login_screen())

        for attempt in range(_LOGIN_ATTEMPTS):
            await self._write("\r\n   LOGIN:    ")
            username = await self._readline()
            if not username:
                continue

            await self._write("   PASSWORD: ")
            self._echo_off()
            password = await self._readline()
            self._echo_on_again()
            await self._write("\r\n")

            with Session() as db:
                from tangible.retro.ban_service import is_banned
                ban = is_banned(db, self.ip, "telnet")
                if ban is True or ban is not False:
                    await self._writeln("*** ACCESS BLOCKED — CONTACT ADMINISTRATOR ***")
                    return False

                user = authenticate(db, username, password)
                if user:
                    record_attempt(db, self.ip, "telnet", success=True)
                    self.username = username
                    return True
                else:
                    ban_result = record_attempt(db, self.ip, "telnet", success=False)
                    remaining = _LOGIN_ATTEMPTS - attempt - 1
                    if ban_result is not None:
                        # Just got banned
                        if ban_result is True:
                            await self._writeln("\r\n   *** TOO MANY FAILURES — ACCESS PERMANENTLY BLOCKED ***")
                        else:
                            wait = max(0, int((ban_result - datetime.utcnow()).total_seconds()))
                            await self._writeln(f"\r\n   *** TOO MANY FAILURES — BLOCKED FOR {wait} SECONDS ***")
                        return False
                    if remaining > 0:
                        await self._writeln(f"\r\n   INVALID LOGIN. {remaining} ATTEMPT(S) REMAINING.")
                    else:
                        await self._writeln("\r\n   TOO MANY INVALID ATTEMPTS. DISCONNECTING.")

        return False

    # ------------------------------------------------------------------
    # Main menu loop
    # ------------------------------------------------------------------

    async def _main_loop(self) -> None:
        from tangible.retro.terminal import main_menu_screen

        while True:
            await self._write(main_menu_screen(self.username or ""))
            choice = (await self._readline()).strip()

            if choice == "1":
                await self._browse_collections()
            elif choice == "2":
                await self._search_items()
            elif choice == "3":
                await self._item_lookup()
            elif choice == "4":
                await self._add_item()
            elif choice == "5":
                await self._edit_item_lookup()
            elif choice == "6":
                await self._list_collections()
            elif choice == "7":
                await self._writeln("\r\n   SIGNING OUT. THANK YOU.\r\n")
                return
            else:
                await self._writeln("\r\n   INVALID SELECTION. PLEASE TRY AGAIN.")

    # ------------------------------------------------------------------
    # Browse collections
    # ------------------------------------------------------------------

    async def _browse_collections(self) -> None:
        engine = get_engine()
        Session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

        with Session() as db:
            from tangible.models.collection import Collection
            from tangible.models.user import User
            user = db.scalar(select(User).where(User.username == self.username))
            if user is None:
                await self._writeln("   ERROR: User not found.")
                return
            colls = db.scalars(
                select(Collection).where(
                    (Collection.owner_id == user.id) |
                    Collection.memberships.any(user_id=user.id)
                ).order_by(Collection.name)
            ).all()

        if not colls:
            await self._writeln("\r\n   NO COLLECTIONS FOUND.\r\n")
            await self._pause()
            return

        while True:
            from tangible.retro.terminal import clear_screen, box_top, box_bottom, box_row, hr, table_header, table_row as trow, table_footer, WIDTH
            lines = [clear_screen(), box_top("SELECT COLLECTION", WIDTH)]
            lines.append(box_bottom(WIDTH))
            lines.append("")
            for i, c in enumerate(colls, 1):
                lines.append(f"   {i:2}. {c.name[:50]}")
            lines.append("")
            lines.append(hr())
            lines.append("   ENTER NUMBER OR [B]ack: ")
            await self._write("\r\n".join(lines))
            sel = (await self._readline()).strip().upper()
            if sel == "B":
                return
            try:
                idx = int(sel) - 1
                if 0 <= idx < len(colls):
                    await self._browse_items(colls[idx].id, colls[idx].name)
            except ValueError:
                pass

    async def _browse_items(self, collection_id: str, coll_name: str) -> None:
        engine = get_engine()
        Session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
        page = 0

        while True:
            from tangible.retro.terminal import (
                clear_screen, box_top, box_bottom, hr, table_header, table_row as trow,
                table_footer, paginate, pagination_prompt, WIDTH
            )
            with Session() as db:
                from tangible.models.item import Item
                all_items = db.scalars(
                    select(Item).where(
                        Item.collection_id == collection_id,
                        Item.archived_at.is_(None)
                    ).order_by(Item.title)
                ).all()

            page_items, total_pages = paginate(list(all_items), page, 20)
            cols = [("  #", 3), ("TITLE", 38), ("COND", 8), ("QTY", 4)]

            lines = [
                clear_screen(),
                box_top(f"INVENTORY: {coll_name[:30]}", WIDTH),
                box_bottom(WIDTH),
                "",
                table_header(*cols),
            ]
            for i, item in enumerate(page_items, page * 20 + 1):
                lines.append(trow(
                    (str(i), 3),
                    (item.title[:38] if item.title else "", 38),
                    ((item.condition or "")[:8], 8),
                    (str(item.quantity or 1), 4),
                ))
            lines.append(table_footer(*cols))
            lines.append("")
            lines.append(hr())
            lines.append(f"   PAGE {page + 1}/{total_pages}  " + pagination_prompt(page, total_pages))
            await self._write("\r\n".join(lines))

            sel = (await self._readline()).strip().upper()
            if sel == "B":
                return
            elif sel == "N" and page < total_pages - 1:
                page += 1
            elif sel == "P" and page > 0:
                page -= 1
            else:
                # Try numeric selection
                try:
                    idx = int(sel) - 1 - (page * 20)
                    if 0 <= idx < len(page_items):
                        await self._item_detail(page_items[idx].id)
                except ValueError:
                    pass

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    async def _search_items(self) -> None:
        await self._write("\r\n\r\n   SEARCH: ")
        query = (await self._readline()).strip()
        if not query:
            return

        engine = get_engine()
        Session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
        page = 0

        while True:
            from tangible.retro.terminal import (
                clear_screen, box_top, box_bottom, hr, table_header, table_row as trow,
                table_footer, paginate, pagination_prompt, WIDTH
            )
            with Session() as db:
                from tangible.models.item import Item
                from tangible.models.collection import Collection
                from tangible.models.user import User
                user = db.scalar(select(User).where(User.username == self.username))
                if user is None:
                    return
                coll_ids = [c.id for c in db.scalars(
                    select(Collection).where(
                        (Collection.owner_id == user.id) |
                        Collection.memberships.any(user_id=user.id)
                    )
                ).all()]
                like = f"%{query}%"
                all_items = db.scalars(
                    select(Item).where(
                        Item.collection_id.in_(coll_ids),
                        Item.archived_at.is_(None),
                        Item.title.ilike(like) | Item.subtitle.ilike(like) | Item.notes.ilike(like),
                    ).order_by(Item.title)
                ).all()

            page_items, total_pages = paginate(list(all_items), page, 20)
            cols = [("  #", 3), ("TITLE", 34), ("COLLECTION", 20), ("COND", 8)]

            lines = [
                clear_screen(),
                box_top(f'SEARCH: "{query[:30]}"', WIDTH),
                box_bottom(WIDTH),
                f"   FOUND {len(all_items)} RESULT(S)",
                "",
                table_header(*cols),
            ]
            for i, item in enumerate(page_items, page * 20 + 1):
                coll_name = (item.collection.name[:20] if item.collection else "")
                lines.append(trow(
                    (str(i), 3),
                    (item.title[:34] if item.title else "", 34),
                    (coll_name, 20),
                    ((item.condition or "")[:8], 8),
                ))
            lines.append(table_footer(*cols))
            lines.append("")
            lines.append(hr())
            lines.append(f"   PAGE {page + 1}/{total_pages}  " + pagination_prompt(page, total_pages))
            await self._write("\r\n".join(lines))

            sel = (await self._readline()).strip().upper()
            if sel == "B":
                return
            elif sel == "N" and page < total_pages - 1:
                page += 1
            elif sel == "P" and page > 0:
                page -= 1
            else:
                try:
                    idx = int(sel) - 1 - (page * 20)
                    if 0 <= idx < len(page_items):
                        await self._item_detail(page_items[idx].id)
                except ValueError:
                    pass

    # ------------------------------------------------------------------
    # Item lookup by ID/barcode
    # ------------------------------------------------------------------

    async def _item_lookup(self) -> None:
        await self._write("\r\n\r\n   ITEM ID OR BARCODE: ")
        val = (await self._readline()).strip()
        if not val:
            return

        engine = get_engine()
        Session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
        with Session() as db:
            from tangible.models.item import Item
            # Try by ID first
            item = db.get(Item, val)
            if item is None:
                # Try by barcode in identifiers JSON
                from sqlalchemy import cast, String
                item = db.scalar(
                    select(Item).where(
                        Item.identifiers.cast(String).ilike(f'%{val}%')
                    )
                )
            item_id = item.id if item else None

        if item_id:
            await self._item_detail(item_id)
        else:
            await self._writeln(f"\r\n   ITEM NOT FOUND: {val}")
            await self._pause()

    # ------------------------------------------------------------------
    # Item detail screen
    # ------------------------------------------------------------------

    async def _item_detail(self, item_id: str) -> None:
        engine = get_engine()
        Session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

        while True:
            from tangible.retro.terminal import clear_screen, box_top, box_bottom, box_row, hr, bold, WIDTH

            with Session() as db:
                from tangible.models.item import Item
                item = db.get(Item, item_id)
                if item is None:
                    await self._writeln("   ITEM NOT FOUND.")
                    return

                cat_name = item.category.name if item.category else ""
                loc_name = item.location.name if item.location else ""
                tags = ", ".join(t.name for t in item.tags) if item.tags else ""

            lines = [
                clear_screen(),
                box_top("ITEM DETAIL", WIDTH),
                box_bottom(WIDTH),
                "",
                f"   TITLE:        {(item.title or '')[:55]}",
                f"   SUBTITLE:     {(item.subtitle or '')[:55]}",
                f"   CONDITION:    {(item.condition or '')[:20]}",
                f"   QUANTITY:     {item.quantity or 1}",
                f"   CATEGORY:     {cat_name[:30]}",
                f"   LOCATION:     {loc_name[:30]}",
                f"   TAGS:         {tags[:40]}",
                f"   PRICE PAID:   {item.purchase_price or ''}",
                f"   CURRENT VAL:  {item.current_value or ''}",
                f"   ACQUIRED:     {item.acquired_at.date() if item.acquired_at else ''}",
                f"   WANTED:       {'YES' if item.wanted else 'NO'}",
            ]
            if item.notes:
                lines.append("")
                lines.append("   NOTES:")
                for ln in item.notes[:200].split("\n")[:5]:
                    lines.append(f"   {ln[:74]}")
            lines += [
                "",
                hr(),
                "   [E]dit  [A]rchive  [B]ack  ENTER SELECTION: ",
            ]
            await self._write("\r\n".join(lines))

            sel = (await self._readline()).strip().upper()
            if sel == "B":
                return
            elif sel == "E":
                await self._edit_item(item_id)
            elif sel == "A":
                await self._archive_item(item_id)

    # ------------------------------------------------------------------
    # Add item
    # ------------------------------------------------------------------

    async def _add_item(self) -> None:
        from tangible.retro.terminal import clear_screen, box_top, box_bottom, hr, WIDTH
        from tangible.models.item import Item
        from tangible.models.collection import Collection
        from tangible.models.user import User
        from tangible.models.base import ulid_str

        engine = get_engine()
        Session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

        with Session() as db:
            user = db.scalar(select(User).where(User.username == self.username))
            if user is None:
                return
            colls = db.scalars(
                select(Collection).where(
                    (Collection.owner_id == user.id) |
                    Collection.memberships.any(user_id=user.id)
                ).order_by(Collection.name)
            ).all()
            coll_list = list(colls)

        # Choose collection
        lines = [
            clear_screen(),
            box_top("ADD NEW ITEM", WIDTH),
            box_bottom(WIDTH),
            "",
        ]
        for i, c in enumerate(coll_list, 1):
            lines.append(f"   {i:2}. {c.name[:50]}")
        lines += ["", hr(), "   SELECT COLLECTION (or [B]ack): "]
        await self._write("\r\n".join(lines))
        sel = (await self._readline()).strip().upper()
        if sel == "B":
            return
        try:
            coll_idx = int(sel) - 1
            if not (0 <= coll_idx < len(coll_list)):
                return
        except ValueError:
            return
        chosen_coll = coll_list[coll_idx]

        # Gather fields
        fields: dict[str, str] = {}
        prompts = [
            ("title", "TITLE"),
            ("subtitle", "SUBTITLE (enter=skip)"),
            ("condition", "CONDITION (enter=skip)"),
            ("quantity", "QUANTITY (enter=1)"),
            ("notes", "NOTES (enter=skip)"),
        ]
        await self._write("\r\n")
        for key, label in prompts:
            await self._write(f"   {label}: ")
            val = (await self._readline()).strip()
            fields[key] = val

        # Confirm
        await self._write(
            f"\r\n   TITLE: {fields['title']}\r\n"
            f"   COLLECTION: {chosen_coll.name}\r\n"
            f"\r\n   CONFIRM? (Y/N): "
        )
        confirm = (await self._readline()).strip().upper()
        if confirm != "Y":
            await self._writeln("   CANCELLED.")
            await self._pause()
            return

        if not fields["title"]:
            await self._writeln("   ERROR: TITLE IS REQUIRED.")
            await self._pause()
            return

        with Session() as db:
            item = Item(
                id=ulid_str(),
                title=fields["title"],
                subtitle=fields["subtitle"] or None,
                notes=fields["notes"] or None,
                condition=fields["condition"] or None,
                quantity=int(fields["quantity"] or "1") if fields["quantity"].isdigit() else 1,
                collection_id=chosen_coll.id,
            )
            db.add(item)
            db.commit()
            item_id = item.id

        await self._writeln(f"\r\n   ITEM CREATED: {item_id}")
        await self._pause()
        await self._item_detail(item_id)

    # ------------------------------------------------------------------
    # Edit item lookup
    # ------------------------------------------------------------------

    async def _edit_item_lookup(self) -> None:
        await self._write("\r\n\r\n   ENTER ITEM ID: ")
        item_id = (await self._readline()).strip()
        if not item_id:
            return

        engine = get_engine()
        Session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
        with Session() as db:
            from tangible.models.item import Item
            item = db.get(Item, item_id)
            exists = item is not None

        if exists:
            await self._edit_item(item_id)
        else:
            await self._writeln("   ITEM NOT FOUND.")
            await self._pause()

    async def _edit_item(self, item_id: str) -> None:
        from tangible.retro.terminal import clear_screen, box_top, box_bottom, hr, WIDTH
        from tangible.models.item import Item

        engine = get_engine()
        Session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

        with Session() as db:
            item = db.get(Item, item_id)
            if item is None:
                await self._writeln("   ITEM NOT FOUND.")
                return
            current = {
                "title": item.title or "",
                "subtitle": item.subtitle or "",
                "condition": item.condition or "",
                "quantity": str(item.quantity or 1),
                "notes": item.notes or "",
            }

        lines = [
            clear_screen(),
            box_top("EDIT ITEM", WIDTH),
            box_bottom(WIDTH),
            "",
            f"   EDITING: {current['title'][:55]}",
            "",
            "   For each field, enter new value or press ENTER to keep current.",
            "",
            hr(),
        ]
        await self._write("\r\n".join(lines) + "\r\n")

        updates: dict[str, str] = {}
        edit_prompts = [
            ("title", "TITLE"),
            ("subtitle", "SUBTITLE"),
            ("condition", "CONDITION"),
            ("quantity", "QUANTITY"),
            ("notes", "NOTES"),
        ]
        for key, label in edit_prompts:
            await self._write(f"   {label} [{current[key][:30]}]: ")
            val = (await self._readline()).strip()
            if val:
                updates[key] = val

        if not updates:
            await self._writeln("   NO CHANGES MADE.")
            await self._pause()
            return

        await self._write(f"\r\n   SAVE CHANGES? (Y/N): ")
        confirm = (await self._readline()).strip().upper()
        if confirm != "Y":
            await self._writeln("   CANCELLED.")
            await self._pause()
            return

        with Session() as db:
            item = db.get(Item, item_id)
            if item is None:
                return
            if "title" in updates:
                item.title = updates["title"]
            if "subtitle" in updates:
                item.subtitle = updates["subtitle"] or None
            if "condition" in updates:
                item.condition = updates["condition"] or None
            if "quantity" in updates:
                try:
                    item.quantity = int(updates["quantity"])
                except ValueError:
                    pass
            if "notes" in updates:
                item.notes = updates["notes"] or None
            db.commit()

        await self._writeln("   ITEM UPDATED.")
        await self._pause()

    # ------------------------------------------------------------------
    # Archive item
    # ------------------------------------------------------------------

    async def _archive_item(self, item_id: str) -> None:
        await self._write("\r\n   ARCHIVE THIS ITEM? (Y/N): ")
        confirm = (await self._readline()).strip().upper()
        if confirm != "Y":
            return

        engine = get_engine()
        Session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
        with Session() as db:
            from tangible.models.item import Item
            item = db.get(Item, item_id)
            if item:
                item.archived_at = datetime.utcnow()
                db.commit()
        await self._writeln("   ITEM ARCHIVED.")
        await self._pause()

    # ------------------------------------------------------------------
    # Collections list
    # ------------------------------------------------------------------

    async def _list_collections(self) -> None:
        engine = get_engine()
        Session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

        with Session() as db:
            from tangible.models.collection import Collection
            from tangible.models.item import Item
            from tangible.models.user import User
            user = db.scalar(select(User).where(User.username == self.username))
            if user is None:
                return
            colls = db.scalars(
                select(Collection).where(
                    (Collection.owner_id == user.id) |
                    Collection.memberships.any(user_id=user.id)
                ).order_by(Collection.name)
            ).all()
            coll_data = [
                (c.id, c.name, db.scalar(select(func.count(Item.id)).where(Item.collection_id == c.id)) or 0)
                for c in colls
            ]

        from tangible.retro.terminal import clear_screen, box_top, box_bottom, hr, table_header, table_row as trow, table_footer, WIDTH

        cols = [("  #", 3), ("COLLECTION NAME", 40), ("ITEMS", 5)]
        lines = [
            clear_screen(),
            box_top("COLLECTIONS", WIDTH),
            box_bottom(WIDTH),
            "",
            table_header(*cols),
        ]
        for i, (cid, name, count) in enumerate(coll_data, 1):
            lines.append(trow((str(i), 3), (name[:40], 40), (str(count), 5)))
        lines.append(table_footer(*cols))
        lines += ["", hr(), "   ENTER NUMBER TO BROWSE OR [B]ack: "]
        await self._write("\r\n".join(lines))

        sel = (await self._readline()).strip().upper()
        if sel == "B":
            return
        try:
            idx = int(sel) - 1
            if 0 <= idx < len(coll_data):
                await self._browse_items(coll_data[idx][0], coll_data[idx][1])
        except ValueError:
            pass

    # ------------------------------------------------------------------
    # Low-level I/O helpers
    # ------------------------------------------------------------------

    def _write_raw(self, data: bytes) -> None:
        self.writer.write(data)

    async def _write(self, text: str) -> None:
        self.writer.write(text.encode("utf-8", errors="replace"))
        await self.writer.drain()

    async def _writeln(self, text: str) -> None:
        await self._write(text + "\r\n")

    async def _pause(self) -> None:
        await self._write("\r\n   PRESS ENTER TO CONTINUE...")
        await self._readline()

    def _echo_off(self) -> None:
        self._echo_on = False
        # IAC WONT ECHO tells client not to echo (server won't echo either)
        self._write_raw(IAC + WONT + ECHO)

    def _echo_on_again(self) -> None:
        self._echo_on = True
        self._write_raw(IAC + WILL + ECHO)

    async def _readline(self) -> str:
        """Read one line, stripping IAC sequences and telnet CR handling."""
        buf = bytearray()
        while True:
            try:
                byte = await asyncio.wait_for(self.reader.read(1), timeout=300)
            except asyncio.TimeoutError:
                raise ConnectionResetError("Telnet session timeout")
            if not byte:
                raise ConnectionResetError("Client disconnected")

            b = byte[0]

            # Handle IAC (telnet command sequence — skip 2 more bytes)
            if b == 255:
                cmd = await self.reader.read(1)
                if cmd and cmd[0] in (251, 252, 253, 254):
                    await self.reader.read(1)  # skip option byte
                continue

            # Ctrl+C or Ctrl+D = disconnect/cancel
            if b in (3, 4, 26):
                raise ConnectionResetError("Client cancelled")

            # Backspace
            if b in (8, 127):
                if buf:
                    buf.pop()
                    if self._echo_on:
                        self.writer.write(b"\x08 \x08")
                continue

            # CR (telnet sends CR+NUL or CR+LF)
            if b == 13:
                next_byte = await self.reader.read(1)
                # swallow NUL or LF
                break

            # LF alone (some clients)
            if b == 10:
                break

            if len(buf) < _MAX_LINE:
                buf.append(b)
                if self._echo_on:
                    self.writer.write(bytes([b]))

        return buf.decode("utf-8", errors="replace")
