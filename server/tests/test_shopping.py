from __future__ import annotations


def _signup_and_login(client, username: str, password: str = "hunter22-secure") -> None:
    client.post(
        "/api/auth/register",
        json={"username": username, "password": password, "email": f"{username}@x.io"},
    )
    r = client.post("/api/auth/login", json={"username": username, "password": password})
    assert r.status_code == 200, r.text


def _create_pantry_item(client) -> tuple[str, str]:
    cid = client.post("/api/collections", json={"name": "Pantry"}).json()["id"]
    r = client.post(
        "/api/items",
        json={"collection_id": cid, "category": "other.generic", "title": "Milk"},
    )
    assert r.status_code == 201, r.text
    return cid, r.json()["id"]


def test_shopping_feed_includes_depleted_items(client) -> None:
    _signup_and_login(client, "alice")
    cid, item_id = _create_pantry_item(client)
    client.patch(f"/api/items/{item_id}", json={"depleted": True, "quantity": 0})

    feed = client.get("/api/lists").json()
    assert any(e["linked_item_id"] == item_id and e["source"]["kind"] == "depleted_item" for e in feed)

    count = client.get("/api/lists/count").json()
    assert count["depleted_items"] >= 1
    assert count["total"] == count["depleted_items"] + count["ad_hoc"]
    assert cid in {e["collection_id"] for e in feed}


def test_shopping_ad_hoc_create_update_delete(client) -> None:
    _signup_and_login(client, "alice")
    cid, _ = _create_pantry_item(client)

    r = client.post(
        "/api/lists",
        json={"collection_id": cid, "name": "Bananas", "quantity": 6, "brand": "Chiquita"},
    )
    assert r.status_code == 201, r.text
    gid = r.json()["id"]
    assert r.json()["brand"] == "Chiquita"

    # Brand survives a round-trip through the feed.
    feed = client.get("/api/lists").json()
    entry = next(e for e in feed if e["id"] == gid)
    assert entry["brand"] == "Chiquita"

    r = client.patch(f"/api/lists/{gid}", json={"quantity": 8, "notes": "ripe"})
    assert r.status_code == 200
    assert r.json()["quantity"] == 8
    assert r.json()["notes"] == "ripe"
    assert r.json()["brand"] == "Chiquita"

    r = client.delete(f"/api/lists/{gid}")
    assert r.status_code == 204
    feed = client.get("/api/lists").json()
    assert all(e["id"] != gid for e in feed)


def test_shopping_purchase_restocks_linked_item(client) -> None:
    _signup_and_login(client, "alice")
    cid, item_id = _create_pantry_item(client)
    client.patch(f"/api/items/{item_id}", json={"depleted": True, "quantity": 0})

    r = client.post(
        "/api/lists",
        json={"collection_id": cid, "name": "Milk", "quantity": 2, "linked_item_id": item_id},
    )
    gid = r.json()["id"]

    # Linked-and-open ad-hoc entry should suppress the duplicate depleted-item row.
    feed = client.get("/api/lists").json()
    depleted_rows = [e for e in feed if e["source"]["kind"] == "depleted_item" and e["linked_item_id"] == item_id]
    assert depleted_rows == []

    r = client.post(f"/api/lists/{gid}/purchase", json={})
    assert r.status_code == 200, r.text
    assert r.json()["purchased_at"] is not None

    item = client.get(f"/api/items/{item_id}").json()
    assert item["depleted"] is False
    assert item["quantity"] == 2

    # Default: feed hides purchased entries.
    feed = client.get("/api/lists").json()
    assert all(e["id"] != gid for e in feed)

    feed = client.get("/api/lists", params={"include_purchased": True}).json()
    assert any(e["id"] == gid for e in feed)


def test_shopping_purchase_twice_rejected(client) -> None:
    _signup_and_login(client, "alice")
    cid, _ = _create_pantry_item(client)
    gid = client.post("/api/lists", json={"collection_id": cid, "name": "Eggs"}).json()["id"]
    assert client.post(f"/api/lists/{gid}/purchase", json={}).status_code == 200
    assert client.post(f"/api/lists/{gid}/purchase", json={}).status_code == 409


def test_shopping_audit_trail(client) -> None:
    _signup_and_login(client, "alice")
    cid, _ = _create_pantry_item(client)
    gid = client.post("/api/lists", json={"collection_id": cid, "name": "Bread"}).json()["id"]
    client.patch(f"/api/lists/{gid}", json={"quantity": 2})
    client.post(f"/api/lists/{gid}/purchase", json={})

    log = client.get("/api/audit", params={"collection_id": cid}).json()
    actions = {entry["action"] for entry in log}
    assert {"shopping.create", "shopping.update", "shopping.purchase"}.issubset(actions)


def test_shopping_purchase_creates_item_when_no_link(client) -> None:
    """Purchasing an ad-hoc shopping entry creates a pantry item.

    Previously the purchase route only restocked when ``linked_item_id`` was
    set, so brand-new ad-hoc items disappeared without a trace. Now an Item +
    ItemLot are created in the entry's collection, carrying name, quantity,
    notes, and brand.
    """
    _signup_and_login(client, "alice")
    cid, _ = _create_pantry_item(client)

    items_before = client.get("/api/items", params={"collection_id": cid}).json()
    titles_before = {it["title"] for it in items_before}

    r = client.post(
        "/api/lists",
        json={
            "collection_id": cid,
            "name": "Sour Cream",
            "quantity": 2,
            "brand": "Hannaford",
            "notes": "low fat",
            "category_slug": "other.generic",
        },
    )
    assert r.status_code == 201, r.text
    gid = r.json()["id"]
    assert client.post(f"/api/lists/{gid}/purchase", json={}).status_code == 200

    items_after = client.get("/api/items", params={"collection_id": cid}).json()
    new_items = [it for it in items_after if it["title"] not in titles_before]
    assert len(new_items) == 1
    new_item = new_items[0]
    assert new_item["title"] == "Sour Cream"
    assert new_item["quantity"] == 2
    assert new_item["notes"] == "low fat"
    assert new_item["depleted"] is False
    assert (new_item.get("attrs") or {}).get("brand") == "Hannaford"


def test_shopping_purchase_creates_item_without_category(client) -> None:
    """Purchasing an ad-hoc entry with no category_slug still creates an Item.

    Previously the item was silently dropped when neither the entry nor the
    collection had a resolvable category.  The purchased item should appear in
    the collection with category_id=None.
    """
    _signup_and_login(client, "alice")
    cid = client.post("/api/collections", json={"name": "Pantry"}).json()["id"]

    r = client.post(
        "/api/lists",
        json={"collection_id": cid, "name": "Butter", "quantity": 1},
    )
    assert r.status_code == 201, r.text
    gid = r.json()["id"]

    items_before = client.get("/api/items", params={"collection_id": cid}).json()
    assert client.post(f"/api/lists/{gid}/purchase", json={}).status_code == 200

    items_after = client.get("/api/items", params={"collection_id": cid}).json()
    new_items = [it for it in items_after if it["title"] not in {x["title"] for x in items_before}]
    assert len(new_items) == 1
    assert new_items[0]["title"] == "Butter"
    assert new_items[0]["category_id"] is None
