"""Raw HTTP/1.0 asyncio server serving an HTML 1.0 interface.

Protocol notes:
- Speaks HTTP/1.0 only (no persistent connections, no chunked encoding)
- Authenticates via HTTP Basic Auth (RFC 7235) on every request
- Serves plain HTTP (not HTTPS) — LAN use only
- All writes go directly to the SQLAlchemy session; no internal API round-trips

Security note: HTTP Basic Auth transmits credentials as base64 (not encrypted).
Only use on a trusted LAN. Never expose this port to the internet.
"""

from __future__ import annotations

import asyncio
import base64
import logging
import urllib.parse
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import func, select
from sqlalchemy.orm import Session as DBSession

from tangible.db import get_engine
from sqlalchemy.orm import sessionmaker

if TYPE_CHECKING:
    from tangible.config import Settings

log = logging.getLogger(__name__)

# Maximum bytes to read from a single request (prevents slow-loris / OOM)
_MAX_REQUEST_BYTES = 256 * 1024  # 256 KB


# ---------------------------------------------------------------------------
# Server factory
# ---------------------------------------------------------------------------

async def create_http_server(settings: "Settings") -> asyncio.Server:
    handler = _make_handler(settings)
    return await asyncio.start_server(
        handler,
        host=settings.retro_http_bind,
        port=settings.retro_http_port,
    )


def _make_handler(settings: "Settings"):
    from tangible.retro.ban_service import is_banned, record_attempt

    async def handle(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        peer = writer.get_extra_info("peername")
        ip = _extract_ip(peer)
        try:
            await _handle_request(reader, writer, ip, settings)
        except (ConnectionResetError, BrokenPipeError):
            pass
        except Exception:
            log.exception("Retro HTTP handler error from %s", ip)
        finally:
            try:
                writer.close()
            except Exception:
                pass

    return handle


# ---------------------------------------------------------------------------
# Request parsing
# ---------------------------------------------------------------------------

async def _handle_request(
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
    ip: str,
    settings: "Settings",
) -> None:
    from tangible.retro.ban_service import is_banned, record_attempt

    raw = await reader.read(_MAX_REQUEST_BYTES)
    if not raw:
        return

    try:
        header_part, _, body_part = raw.partition(b"\r\n\r\n")
        lines = header_part.decode("latin-1", errors="replace").splitlines()
        if not lines:
            _send(writer, _status(400), b"Bad Request")
            return

        request_line = lines[0]
        parts = request_line.split()
        if len(parts) < 2:
            _send(writer, _status(400), b"Bad Request")
            return

        method = parts[0].upper()
        raw_path = parts[1]

        # Parse headers into dict (lowercase keys)
        headers: dict[str, str] = {}
        for line in lines[1:]:
            if ":" in line:
                k, _, v = line.partition(":")
                headers[k.strip().lower()] = v.strip()

        # Respect X-Forwarded-For for reverse-proxy deployments
        if "x-forwarded-for" in headers:
            ip = headers["x-forwarded-for"].split(",")[0].strip()

        # Check ban status before processing credentials
        engine = get_engine()
        Session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
        with Session() as db:
            ban = is_banned(db, ip, "http")
            if ban is not True and ban is not False:
                # ban is a datetime (expiry)
                wait_secs = max(0, int((ban - datetime.utcnow()).total_seconds()))
                msg = f"Access temporarily blocked. Try again in {wait_secs} seconds.".encode()
                _send(writer, _status(403), msg)
                return
            if ban is True:
                _send(writer, _status(403), b"Access permanently blocked. Contact administrator.")
                return

        # Extract Basic Auth credentials
        auth_header = headers.get("authorization", "")
        username, password = _parse_basic_auth(auth_header)

        if username is None:
            _send_auth_challenge(writer)
            return

        # Validate credentials
        with Session() as db:
            from tangible.retro.auth import authenticate
            user = authenticate(db, username, password)
            if user is None:
                ban_result = record_attempt(db, ip, "http", success=False)
                if ban_result is not None:
                    # Newly banned
                    _send(writer, _status(403), b"Too many failed attempts. Access blocked.")
                else:
                    _send_auth_challenge(writer)
                return
            record_attempt(db, ip, "http", success=True)

        # Dispatch to page handler
        parsed = urllib.parse.urlparse(raw_path)
        path = urllib.parse.unquote(parsed.path)
        query = urllib.parse.parse_qs(parsed.query, keep_blank_values=True)

        # Parse POST body if applicable
        post_data: dict[str, list[str]] = {}
        if method == "POST" and body_part:
            try:
                post_data = urllib.parse.parse_qs(body_part.decode("utf-8", errors="replace"))
            except Exception:
                pass

        await _dispatch(writer, method, path, query, post_data, username, settings)

    except Exception:
        log.exception("Error parsing retro HTTP request from %s", ip)
        try:
            _send(writer, _status(500), b"Internal Server Error")
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

async def _dispatch(
    writer: asyncio.StreamWriter,
    method: str,
    path: str,
    query: dict[str, list[str]],
    post_data: dict[str, list[str]],
    username: str,
    settings: "Settings",
) -> None:
    engine = get_engine()
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

    def q(key: str, default: str = "") -> str:
        return query.get(key, [default])[0]

    def p(key: str, default: str = "") -> str:
        return post_data.get(key, [default])[0]

    # Static dispatch table (ordered most-specific first)
    if path == "/" or path == "":
        with Session() as db:
            body = _page_home(db, username)
        _send_html(writer, body)

    elif path == "/collections":
        with Session() as db:
            body = _page_collections(db, username)
        _send_html(writer, body)

    elif path.startswith("/collections/"):
        coll_id = path.split("/")[2] if len(path.split("/")) > 2 else ""
        page_num = int(q("page", "0"))
        search = q("q")
        with Session() as db:
            body = _page_collection(db, username, coll_id, page_num, search)
        _send_html(writer, body)

    elif path == "/search":
        search = q("q")
        coll_id = q("collection_id")
        page_num = int(q("page", "0"))
        with Session() as db:
            body = _page_search(db, username, search, coll_id, page_num)
        _send_html(writer, body)

    elif path.startswith("/items/") and path.endswith("/photo.gif"):
        parts = path.split("/")
        item_id = parts[2] if len(parts) > 2 else ""
        with Session() as db:
            data = _serve_photo(db, item_id, "gif", settings)
        if data:
            _send(writer, _status(200, "image/gif"), data)
        else:
            _send(writer, _status(404), b"Photo not found")

    elif path.startswith("/items/") and path.endswith("/photo.jpg"):
        parts = path.split("/")
        item_id = parts[2] if len(parts) > 2 else ""
        with Session() as db:
            data = _serve_photo(db, item_id, "jpeg", settings)
        if data:
            _send(writer, _status(200, "image/jpeg"), data)
        else:
            _send(writer, _status(404), b"Photo not found")

    elif path.startswith("/items/new"):
        coll_id = q("collection_id")
        if method == "POST":
            with Session() as db:
                result = _action_create_item(db, username, p, settings)
            if isinstance(result, str) and result.startswith("REDIRECT:"):
                _send_redirect(writer, result[9:])
            else:
                _send_html(writer, result)
        else:
            with Session() as db:
                body = _page_new_item(db, username, coll_id)
            _send_html(writer, body)

    elif path.startswith("/items/") and path.endswith("/edit"):
        item_id = path.split("/")[2]
        if method == "POST":
            with Session() as db:
                result = _action_edit_item(db, username, item_id, p)
            if isinstance(result, str) and result.startswith("REDIRECT:"):
                _send_redirect(writer, result[9:])
            else:
                _send_html(writer, result)
        else:
            with Session() as db:
                body = _page_edit_item(db, username, item_id)
            _send_html(writer, body)

    elif path.startswith("/items/"):
        item_id = path.split("/")[2] if len(path.split("/")) > 2 else ""
        with Session() as db:
            body = _page_item(db, username, item_id)
        _send_html(writer, body)

    elif path == "/logout":
        # Send 401 so the browser forgets stored Basic Auth credentials
        _send_auth_challenge(writer, force_logout=True)

    else:
        from tangible.retro.html_gen import error_page
        _send_html(writer, error_page("Not Found", "The requested page was not found."), status=404)


# ---------------------------------------------------------------------------
# Page handlers
# ---------------------------------------------------------------------------

def _page_home(db: DBSession, username: str) -> bytes:
    from tangible.retro.html_gen import page, table_start, table_row, table_end
    from tangible.models.collection import Collection
    from tangible.models.user import User

    user = db.scalar(select(User).where(User.username == username))
    if user is None:
        from tangible.retro.html_gen import error_page
        return error_page("Error", "User not found")

    colls = db.scalars(
        select(Collection).where(
            (Collection.owner_id == user.id) |
            Collection.memberships.any(user_id=user.id)
        )
    ).all()

    body = "<P>Welcome to <B>Tangible IMS</B> &mdash; Your Personal Inventory System.</P>\n"
    body += "<P>Select a collection below or use the navigation links above.</P>\n<HR>\n"

    if colls:
        body += table_start(["Collection", "Description"])
        for c in colls:
            link = f'<A HREF="/collections/{c.id}">{c.name}</A>'
            body += table_row([link, c.description or ""])
        body += table_end()
    else:
        body += "<P>No collections found. <A HREF=\"/items/new\">Add your first item</A>.</P>\n"

    return page("Home", body, nav_user=username)


def _page_collections(db: DBSession, username: str) -> bytes:
    from tangible.retro.html_gen import page, table_start, table_row, table_end
    from tangible.models.collection import Collection
    from tangible.models.user import User
    from tangible.models.item import Item

    user = db.scalar(select(User).where(User.username == username))
    if user is None:
        from tangible.retro.html_gen import error_page
        return error_page("Error", "User not found")

    colls = db.scalars(
        select(Collection).where(
            (Collection.owner_id == user.id) |
            Collection.memberships.any(user_id=user.id)
        ).order_by(Collection.name)
    ).all()

    body = table_start(["Collection", "Description", "Items"])
    for c in colls:
        count = db.scalar(select(func.count(Item.id)).where(Item.collection_id == c.id)) or 0
        link = f'<A HREF="/collections/{c.id}">{c.name}</A>'
        body += table_row([link, c.description or "", str(count)])
    body += table_end()
    body += f'\n<P><A HREF="/items/new">[ + Add Item ]</A></P>\n'

    return page("Collections", body, nav_user=username)


_ITEMS_PER_PAGE = 25


def _page_collection(
    db: DBSession, username: str, collection_id: str, page_num: int, search: str
) -> bytes:
    from tangible.retro.html_gen import (
        page, table_start, table_row, table_end, pagination_links, form_start, form_end,
        input_text, input_hidden, input_submit
    )
    from tangible.models.collection import Collection
    from tangible.models.item import Item
    from tangible.models.user import User

    user = db.scalar(select(User).where(User.username == username))
    coll = db.get(Collection, collection_id)
    if coll is None:
        from tangible.retro.html_gen import error_page
        return error_page("Not Found", "Collection not found")

    stmt = select(Item).where(Item.collection_id == collection_id, Item.archived_at.is_(None))
    if search:
        like = f"%{search}%"
        stmt = stmt.where(Item.title.ilike(like) | Item.subtitle.ilike(like) | Item.notes.ilike(like))
    stmt = stmt.order_by(Item.title)

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    items = db.scalars(stmt.offset(page_num * _ITEMS_PER_PAGE).limit(_ITEMS_PER_PAGE)).all()

    body = f"<H3>{coll.name}</H3>\n"
    if coll.description:
        body += f"<P>{coll.description}</P>\n"

    # Search form
    body += form_start(f"/collections/{collection_id}", "GET")
    body += input_hidden("collection_id", collection_id)
    body += input_text("q", "Search", value=search, size=30)
    body += input_submit("Search")
    body += form_end()
    body += f'<P><A HREF="/items/new?collection_id={collection_id}">[ + Add Item ]</A></P>\n'
    body += "<HR>\n"

    if items:
        body += table_start(["Title", "Category", "Condition", "Qty"])
        for item in items:
            link = f'<A HREF="/items/{item.id}">{item.title}</A>'
            cat = item.category.name if item.category else ""
            body += table_row([link, cat, item.condition or "", str(item.quantity or 1)])
        body += table_end()
        body += pagination_links(f"/collections/{collection_id}", page_num, total, _ITEMS_PER_PAGE)
    else:
        body += "<P>No items found.</P>\n"

    return page(coll.name, body, nav_user=username)


def _page_item(db: DBSession, username: str, item_id: str) -> bytes:
    from tangible.retro.html_gen import page, table_start, table_row, table_end
    from tangible.models.item import Item
    from tangible.models.photo import Photo

    item = db.get(Item, item_id)
    if item is None:
        from tangible.retro.html_gen import error_page
        return error_page("Not Found", "Item not found")

    # Primary photo
    photo = db.scalar(
        select(Photo).where(Photo.item_id == item_id, Photo.is_primary == True)  # noqa: E712
        .order_by(Photo.sort_order)
    )
    if photo is None:
        photo = db.scalar(select(Photo).where(Photo.item_id == item_id).order_by(Photo.sort_order))

    body = ""
    if photo:
        body += f'<P><IMG SRC="/items/{item_id}/photo.gif" ALT="Item photo"></P>\n'

    body += table_start(["Field", "Value"])
    fields = [
        ("Title", item.title or ""),
        ("Subtitle", item.subtitle or ""),
        ("Notes", item.notes or ""),
        ("Condition", item.condition or ""),
        ("Quantity", str(item.quantity or 1)),
        ("Category", item.category.name if item.category else ""),
        ("Location", item.location.name if item.location else ""),
        ("Purchase Price", str(item.purchase_price or "")),
        ("Current Value", str(item.current_value or "")),
        ("Acquired", str(item.acquired_at.date()) if item.acquired_at else ""),
        ("Wanted", "Yes" if item.wanted else "No"),
        ("Archived", "Yes" if item.archived_at else "No"),
    ]
    for label, value in fields:
        if value:
            body += table_row([f"<B>{label}</B>", value])
    body += table_end()

    back_url = f"/collections/{item.collection_id}" if item.collection_id else "/collections"
    body += (
        f'\n<P>'
        f'<A HREF="/items/{item_id}/edit">[Edit]</A> &nbsp; '
        f'<A HREF="{back_url}">[Back to Collection]</A>'
        f'</P>\n'
    )

    return page(item.title or "Item", body, nav_user=username)


def _page_search(
    db: DBSession, username: str, search: str, collection_id: str, page_num: int
) -> bytes:
    from tangible.retro.html_gen import (
        page, table_start, table_row, table_end, pagination_links,
        form_start, form_end, input_text, input_submit
    )
    from tangible.models.item import Item
    from tangible.models.collection import Collection
    from tangible.models.user import User

    user = db.scalar(select(User).where(User.username == username))
    if user is None:
        from tangible.retro.html_gen import error_page
        return error_page("Error", "User not found")

    # Build search form
    body = form_start("/search", "GET")
    body += input_text("q", "Search", value=search, size=40)
    body += input_submit("Search")
    body += form_end()

    if not search:
        return page("Search", body, nav_user=username)

    # Get collections the user can access
    user_colls = db.scalars(
        select(Collection).where(
            (Collection.owner_id == user.id) |
            Collection.memberships.any(user_id=user.id)
        )
    ).all()
    coll_ids = [c.id for c in user_colls]

    stmt = select(Item).where(
        Item.collection_id.in_(coll_ids),
        Item.archived_at.is_(None),
        Item.title.ilike(f"%{search}%") | Item.subtitle.ilike(f"%{search}%") | Item.notes.ilike(f"%{search}%"),
    ).order_by(Item.title)

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    items = db.scalars(stmt.offset(page_num * _ITEMS_PER_PAGE).limit(_ITEMS_PER_PAGE)).all()

    body += f"<P>Found <B>{total}</B> result(s) for &quot;{search}&quot;.</P>\n"

    if items:
        body += table_start(["Title", "Collection", "Condition"])
        for item in items:
            link = f'<A HREF="/items/{item.id}">{item.title}</A>'
            coll_name = item.collection.name if item.collection else ""
            body += table_row([link, coll_name, item.condition or ""])
        body += table_end()
        body += pagination_links(f"/search?q={urllib.parse.quote(search)}", page_num, total, _ITEMS_PER_PAGE)

    return page("Search Results", body, nav_user=username)


def _page_new_item(db: DBSession, username: str, collection_id: str) -> bytes:
    from tangible.retro.html_gen import (
        page, form_start, form_end, input_text, input_textarea, input_hidden,
        input_submit, select_field
    )
    from tangible.models.collection import Collection
    from tangible.models.category import Category
    from tangible.models.user import User

    user = db.scalar(select(User).where(User.username == username))
    if user is None:
        from tangible.retro.html_gen import error_page
        return error_page("Error", "User not found")

    colls = db.scalars(
        select(Collection).where(
            (Collection.owner_id == user.id) |
            Collection.memberships.any(user_id=user.id)
        ).order_by(Collection.name)
    ).all()
    coll_options = [("", "-- Select --")] + [(c.id, c.name) for c in colls]

    cats = db.scalars(select(Category).where(Category.is_active == True).order_by(Category.name)).all()  # noqa: E712
    cat_options = [("", "-- None --")] + [(str(c.id), c.name) for c in cats]

    body = form_start("/items/new", "POST")
    body += input_hidden("collection_id", collection_id)
    body += input_text("title", "Title *", size=50)
    body += input_text("subtitle", "Subtitle", size=50)
    body += input_textarea("notes", "Notes")
    body += input_text("condition", "Condition (e.g. Mint, Good, Fair)", size=20)
    body += input_text("quantity", "Quantity", value="1", size=5)
    body += select_field("collection_id_sel", "Collection", coll_options, selected=collection_id)
    body += select_field("category_id", "Category", cat_options)
    body += input_submit("Add Item")
    body += form_end()

    return page("Add New Item", body, nav_user=username)


def _action_create_item(
    db: DBSession, username: str, p, settings: "Settings"
) -> bytes | str:
    from tangible.models.item import Item
    from tangible.models.user import User

    user = db.scalar(select(User).where(User.username == username))
    if user is None:
        from tangible.retro.html_gen import error_page
        return error_page("Error", "User not found")

    title = p("title").strip()
    if not title:
        from tangible.retro.html_gen import error_page
        return error_page("Validation Error", "Title is required.")

    coll_id = p("collection_id_sel") or p("collection_id") or None
    cat_id = p("category_id") or None

    from tangible.models.base import ulid_str
    item = Item(
        id=ulid_str(),
        title=title,
        subtitle=p("subtitle").strip() or None,
        notes=p("notes").strip() or None,
        condition=p("condition").strip() or None,
        quantity=int(p("quantity") or "1"),
        collection_id=coll_id,
        category_id=cat_id,
    )
    db.add(item)
    db.commit()
    return f"REDIRECT:/items/{item.id}"


def _page_edit_item(db: DBSession, username: str, item_id: str) -> bytes:
    from tangible.retro.html_gen import (
        page, form_start, form_end, input_text, input_textarea,
        input_hidden, input_submit, select_field
    )
    from tangible.models.item import Item
    from tangible.models.category import Category

    item = db.get(Item, item_id)
    if item is None:
        from tangible.retro.html_gen import error_page
        return error_page("Not Found", "Item not found")

    cats = db.scalars(select(Category).where(Category.is_active == True).order_by(Category.name)).all()  # noqa: E712
    cat_options = [("", "-- None --")] + [(str(c.id), c.name) for c in cats]

    body = form_start(f"/items/{item_id}/edit", "POST")
    body += input_hidden("item_id", item_id)
    body += input_text("title", "Title *", value=item.title or "", size=50)
    body += input_text("subtitle", "Subtitle", value=item.subtitle or "", size=50)
    body += input_textarea("notes", "Notes", value=item.notes or "")
    body += input_text("condition", "Condition", value=item.condition or "", size=20)
    body += input_text("quantity", "Quantity", value=str(item.quantity or 1), size=5)
    body += select_field("category_id", "Category", cat_options, selected=str(item.category_id or ""))
    body += input_submit("Save Changes")
    body += form_end()
    body += f'<P><A HREF="/items/{item_id}">[Cancel]</A></P>\n'

    return page(f"Edit: {item.title}", body, nav_user=username)


def _action_edit_item(
    db: DBSession, username: str, item_id: str, p
) -> bytes | str:
    from tangible.models.item import Item

    item = db.get(Item, item_id)
    if item is None:
        from tangible.retro.html_gen import error_page
        return error_page("Not Found", "Item not found")

    title = p("title").strip()
    if not title:
        from tangible.retro.html_gen import error_page
        return error_page("Validation Error", "Title is required.")

    item.title = title
    item.subtitle = p("subtitle").strip() or None
    item.notes = p("notes").strip() or None
    item.condition = p("condition").strip() or None
    try:
        item.quantity = int(p("quantity") or "1")
    except ValueError:
        pass
    cat_id = p("category_id") or None
    item.category_id = cat_id
    db.commit()
    return f"REDIRECT:/items/{item_id}"


def _serve_photo(db: DBSession, item_id: str, fmt: str, settings: "Settings") -> bytes | None:
    from tangible.models.photo import Photo
    from tangible.retro.html_gen import photo_to_gif, photo_to_jpeg
    import os

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

    if fmt == "gif":
        return photo_to_gif(photo_path)
    return photo_to_jpeg(photo_path)


# ---------------------------------------------------------------------------
# HTTP response helpers
# ---------------------------------------------------------------------------

def _status(code: int, content_type: str = "text/html") -> str:
    phrases = {200: "OK", 301: "Moved Permanently", 302: "Found", 400: "Bad Request",
               401: "Unauthorized", 403: "Forbidden", 404: "Not Found", 500: "Internal Server Error"}
    phrase = phrases.get(code, "Unknown")
    return (
        f"HTTP/1.0 {code} {phrase}\r\n"
        f"Content-Type: {content_type}\r\n"
        "Connection: close\r\n"
    )


def _send(writer: asyncio.StreamWriter, header: str, body: bytes) -> None:
    data = (header + f"Content-Length: {len(body)}\r\n\r\n").encode("latin-1") + body
    writer.write(data)


def _send_html(writer: asyncio.StreamWriter, body: bytes, status: int = 200) -> None:
    _send(writer, _status(status), body)


def _send_redirect(writer: asyncio.StreamWriter, location: str) -> None:
    from tangible.retro.html_gen import redirect_response
    header = (
        f"HTTP/1.0 302 Found\r\n"
        f"Location: {location}\r\n"
        "Connection: close\r\n"
    )
    body = redirect_response(location)
    data = (header + f"Content-Length: {len(body)}\r\n\r\n").encode("latin-1") + body
    writer.write(data)


def _send_auth_challenge(writer: asyncio.StreamWriter, force_logout: bool = False) -> None:
    if force_logout:
        msg = b"You have been logged out. Close this browser window to complete logout."
    else:
        msg = b"Authentication required."
    header = (
        "HTTP/1.0 401 Unauthorized\r\n"
        'WWW-Authenticate: Basic realm="Tangible IMS"\r\n'
        "Content-Type: text/plain\r\n"
        "Connection: close\r\n"
    )
    data = (header + f"Content-Length: {len(msg)}\r\n\r\n").encode("latin-1") + msg
    writer.write(data)


def _parse_basic_auth(auth_header: str) -> tuple[str | None, str]:
    """Parse 'Basic <base64>' → (username, password) or (None, '')."""
    if not auth_header.lower().startswith("basic "):
        return None, ""
    try:
        decoded = base64.b64decode(auth_header[6:]).decode("utf-8", errors="replace")
        username, _, password = decoded.partition(":")
        return username, password
    except Exception:
        return None, ""


def _extract_ip(peer) -> str:  # type: ignore[no-untyped-def]
    if peer and isinstance(peer, tuple):
        return str(peer[0])
    return "unknown"
