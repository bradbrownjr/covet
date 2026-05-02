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


def test_grocery_feed_includes_depleted_items(client) -> None:
    _signup_and_login(client, "alice")
    cid, item_id = _create_pantry_item(client)
    client.patch(f"/api/items/{item_id}", json={"depleted": True, "quantity": 0})

    feed = client.get("/api/grocery").json()
    assert any(e["linked_item_id"] == item_id and e["source"]["kind"] == "depleted_item" for e in feed)

    count = client.get("/api/grocery/count").json()
    assert count["depleted_items"] >= 1
    assert count["total"] == count["depleted_items"] + count["ad_hoc"]
    assert cid in {e["collection_id"] for e in feed}


def test_grocery_ad_hoc_create_update_delete(client) -> None:
    _signup_and_login(client, "alice")
    cid, _ = _create_pantry_item(client)

    r = client.post("/api/grocery", json={"collection_id": cid, "name": "Bananas", "quantity": 6})
    assert r.status_code == 201, r.text
    gid = r.json()["id"]

    r = client.patch(f"/api/grocery/{gid}", json={"quantity": 8, "notes": "ripe"})
    assert r.status_code == 200
    assert r.json()["quantity"] == 8
    assert r.json()["notes"] == "ripe"

    r = client.delete(f"/api/grocery/{gid}")
    assert r.status_code == 204
    feed = client.get("/api/grocery").json()
    assert all(e["id"] != gid for e in feed)


def test_grocery_purchase_restocks_linked_item(client) -> None:
    _signup_and_login(client, "alice")
    cid, item_id = _create_pantry_item(client)
    client.patch(f"/api/items/{item_id}", json={"depleted": True, "quantity": 0})

    r = client.post(
        "/api/grocery",
        json={"collection_id": cid, "name": "Milk", "quantity": 2, "linked_item_id": item_id},
    )
    gid = r.json()["id"]

    # Linked-and-open ad-hoc entry should suppress the duplicate depleted-item row.
    feed = client.get("/api/grocery").json()
    depleted_rows = [e for e in feed if e["source"]["kind"] == "depleted_item" and e["linked_item_id"] == item_id]
    assert depleted_rows == []

    r = client.post(f"/api/grocery/{gid}/purchase", json={})
    assert r.status_code == 200, r.text
    assert r.json()["purchased_at"] is not None

    item = client.get(f"/api/items/{item_id}").json()
    assert item["depleted"] is False
    assert item["quantity"] == 2

    # Default: feed hides purchased entries.
    feed = client.get("/api/grocery").json()
    assert all(e["id"] != gid for e in feed)

    feed = client.get("/api/grocery", params={"include_purchased": True}).json()
    assert any(e["id"] == gid for e in feed)


def test_grocery_purchase_twice_rejected(client) -> None:
    _signup_and_login(client, "alice")
    cid, _ = _create_pantry_item(client)
    gid = client.post("/api/grocery", json={"collection_id": cid, "name": "Eggs"}).json()["id"]
    assert client.post(f"/api/grocery/{gid}/purchase", json={}).status_code == 200
    assert client.post(f"/api/grocery/{gid}/purchase", json={}).status_code == 409


def test_grocery_audit_trail(client) -> None:
    _signup_and_login(client, "alice")
    cid, _ = _create_pantry_item(client)
    gid = client.post("/api/grocery", json={"collection_id": cid, "name": "Bread"}).json()["id"]
    client.patch(f"/api/grocery/{gid}", json={"quantity": 2})
    client.post(f"/api/grocery/{gid}/purchase", json={})

    log = client.get("/api/audit", params={"collection_id": cid}).json()
    actions = {entry["action"] for entry in log}
    assert {"grocery.create", "grocery.update", "grocery.purchase"}.issubset(actions)
