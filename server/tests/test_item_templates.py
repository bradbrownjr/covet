"""Item template + per-type custom field validation tests."""

from __future__ import annotations


def _register(client, username, password="hunter22-secure"):
    r = client.post(
        "/api/auth/register",
        json={"username": username, "password": password, "email": f"{username}@x.io"},
    )
    assert r.status_code == 201, r.text


def _login(client, username, password="hunter22-secure"):
    r = client.post("/api/auth/login", json={"username": username, "password": password})
    assert r.status_code == 200, r.text


BOOK_FIELDS = [
    {"key": "isbn", "label": "ISBN", "type": "text", "required": True},
    {"key": "pages", "label": "Pages", "type": "number"},
    {"key": "signed", "label": "Signed", "type": "boolean", "default": False},
    {
        "key": "shelf",
        "label": "Shelf",
        "type": "select",
        "options": ["A", "B", "C"],
    },
]


def test_template_crud_and_attr_validation(client) -> None:
    _register(client, "alice")
    _login(client, "alice")
    cid = client.post("/api/collections", json={"name": "Library"}).json()["id"]

    # Create template
    r = client.post(
        f"/api/collections/{cid}/templates",
        json={
            "name": "Hardcover Book",
            "category_slug": "books.print",
            "description": "Bound books with ISBN",
            "fields": BOOK_FIELDS,
        },
    )
    assert r.status_code == 201, r.text
    tmpl_id = r.json()["id"]
    assert r.json()["fields"][0]["key"] == "isbn"

    # List shows it
    r = client.get(f"/api/collections/{cid}/templates")
    assert r.status_code == 200
    assert any(t["id"] == tmpl_id for t in r.json())

    # Item creation without required attr → 422
    r = client.post(
        "/api/items",
        json={
            "collection_id": cid,
            "category": "books.print",
            "title": "Dune",
            "template_id": tmpl_id,
            "attrs": {},
        },
    )
    assert r.status_code == 422, r.text

    # With required attr present → 201; default applied; coercion runs
    r = client.post(
        "/api/items",
        json={
            "collection_id": cid,
            "category": "books.print",
            "title": "Dune",
            "template_id": tmpl_id,
            "attrs": {"isbn": "978-0441172719", "pages": "658"},
        },
    )
    assert r.status_code == 201, r.text
    item = r.json()
    assert item["template_id"] == tmpl_id
    assert item["attrs"]["pages"] == 658.0
    assert item["attrs"]["signed"] is False

    # Invalid select option rejected on update
    r = client.patch(
        f"/api/items/{item['id']}",
        json={"attrs": {"isbn": "978-0441172719", "shelf": "Z"}},
    )
    assert r.status_code == 422

def test_scaffold_templates_for_home_equipment_root(client) -> None:
    _register(client, "homeeq")
    _login(client, "homeeq")
    cid = client.post(
        "/api/collections",
        json={"name": "Home", "default_category_slug": "home_equipment"},
    ).json()["id"]

    templates = client.get(f"/api/collections/{cid}/templates").json()
    names = {t["name"] for t in templates}
    assert "Appliance" in names

    appliance = next(t for t in templates if t["name"] == "Appliance")
    keys = {f["key"] for f in appliance["fields"]}
    assert {"brand", "model", "serial_number", "service_interval_days"}.issubset(keys)


def test_scaffold_templates_for_fuel_chemicals_root(client) -> None:
    _register(client, "fuelcat")
    _login(client, "fuelcat")
    cid = client.post(
        "/api/collections",
        json={"name": "Fuel", "default_category_slug": "fuel_chemicals"},
    ).json()["id"]

    templates = client.get(f"/api/collections/{cid}/templates").json()
    names = {t["name"] for t in templates}
    assert {"Stored Fuel", "Lubricants & Fluids", "Chemicals & Cleaning"}.issubset(names)

    stored_fuel = next(t for t in templates if t["name"] == "Stored Fuel")
    keys = {f["key"] for f in stored_fuel["fields"]}
    assert {"fuel_type", "quantity_on_hand_gal", "treat_by_date"}.issubset(keys)


def test_scaffold_templates_for_vehicles_root_include_maintenance_fields(client) -> None:
    _register(client, "vehicles")
    _login(client, "vehicles")
    cid = client.post(
        "/api/collections",
        json={"name": "Vehicles", "default_category_slug": "vehicles"},
    ).json()["id"]

    templates = client.get(f"/api/collections/{cid}/templates").json()
    names = {t["name"] for t in templates}
    assert {"Car / Truck / SUV", "Motorcycle / ATV / UTV", "Lawn & Garden Equipment"}.issubset(names)

    car = next(t for t in templates if t["name"] == "Car / Truck / SUV")
    keys = {f["key"] for f in car["fields"]}
    assert {
        "last_oil_change_date",
        "last_oil_change_miles",
        "oil_change_interval_miles",
        "registration_expiry_date",
        "insurance_expiry_date",
    }.issubset(keys)


def test_template_update_and_delete(client) -> None:
    _register(client, "carol")
    _login(client, "carol")
    cid = client.post("/api/collections", json={"name": "Tools"}).json()["id"]
    tmpl_id = client.post(
        f"/api/collections/{cid}/templates",
        json={"name": "Hand Tool", "category_slug": "tools.hand", "fields": []},
    ).json()["id"]

    r = client.patch(
        f"/api/templates/{tmpl_id}",
        json={
            "name": "Hand Tool v2",
            "fields": [
                {"key": "brand", "label": "Brand", "type": "text", "required": True}
            ],
        },
    )
    assert r.status_code == 200
    assert r.json()["name"] == "Hand Tool v2"

    # Now items missing 'brand' should fail
    r = client.post(
        "/api/items",
        json={
            "collection_id": cid,
            "category": "tools.hand",
            "title": "Hammer",
            "template_id": tmpl_id,
        },
    )
    assert r.status_code == 422

    r = client.delete(f"/api/templates/{tmpl_id}")
    assert r.status_code == 204
    r = client.get(f"/api/templates/{tmpl_id}")
    assert r.status_code == 404


def test_template_unknown_id_rejected(client) -> None:
    _register(client, "dave")
    _login(client, "dave")
    cid = client.post("/api/collections", json={"name": "Misc"}).json()["id"]

    r = client.post(
        "/api/items",
        json={
            "collection_id": cid,
            "category": "other.generic",
            "title": "X",
            "template_id": "01ZZZZZZZZZZZZZZZZZZZZZZZZ",
        },
    )
    assert r.status_code == 422


def test_template_other_collection_rejected(client) -> None:
    _register(client, "eve")
    _login(client, "eve")
    cid_a = client.post("/api/collections", json={"name": "A"}).json()["id"]
    cid_b = client.post("/api/collections", json={"name": "B"}).json()["id"]

    tmpl_b = client.post(
        f"/api/collections/{cid_b}/templates",
        json={"name": "T", "category_slug": "other.generic", "fields": []},
    ).json()["id"]

    r = client.post(
        "/api/items",
        json={
            "collection_id": cid_a,
            "category": "other.generic",
            "title": "X",
            "template_id": tmpl_b,
        },
    )
    assert r.status_code == 422


def test_viewer_cannot_create_template(client) -> None:
    _register(client, "owner1")
    _register(client, "viewer1")
    _login(client, "owner1")
    cid = client.post("/api/collections", json={"name": "Shared"}).json()["id"]
    client.post(
        f"/api/collections/{cid}/members",
        json={"user_identifier": "viewer1", "role": "viewer"},
    )
    client.post("/api/auth/logout")

    _login(client, "viewer1")
    r = client.post(
        f"/api/collections/{cid}/templates",
        json={"name": "T", "category_slug": "other.generic", "fields": []},
    )
    assert r.status_code == 403


def test_dynamic_select_field_options_and_validation(client) -> None:
    _register(client, "dyn")
    _login(client, "dyn")
    cid = client.post("/api/collections", json={"name": "Garage"}).json()["id"]

    tmpl = client.post(
        f"/api/collections/{cid}/templates",
        json={
            "name": "Tool",
            "category_slug": "tools.hand",
            "fields": [
                {
                    "key": "bin_location",
                    "label": "Bin location",
                    "type": "select",
                    "select_source": "dynamic",
                }
            ],
        },
    )
    assert tmpl.status_code == 201, tmpl.text
    tmpl_id = tmpl.json()["id"]

    first = client.post(
        "/api/items",
        json={
            "collection_id": cid,
            "category": "tools.hand",
            "title": "Socket set",
            "template_id": tmpl_id,
            "attrs": {"bin_location": "Shelf A"},
        },
    )
    assert first.status_code == 201, first.text

    second = client.post(
        "/api/items",
        json={
            "collection_id": cid,
            "category": "tools.hand",
            "title": "Pliers",
            "template_id": tmpl_id,
            "attrs": {"bin_location": "Drawer 2"},
        },
    )
    assert second.status_code == 201, second.text

    opts = client.get(
        f"/api/collections/{cid}/template-field-options/bin_location",
        params={"template_id": tmpl_id},
    )
    assert opts.status_code == 200, opts.text
    assert opts.json() == ["Drawer 2", "Shelf A"]


def test_scaffold_templates_for_batteries_root(client) -> None:
    _register(client, "batteries")
    _login(client, "batteries")
    cid = client.post(
        "/api/collections",
        json={"name": "Batteries", "default_category_slug": "batteries"},
    ).json()["id"]

    templates = client.get(f"/api/collections/{cid}/templates").json()
    names = {t["name"] for t in templates}
    assert {"Rechargeable Battery", "Disposable Battery", "Smoke Detector Battery Program"}.issubset(names)

    rechargeable = next(t for t in templates if t["name"] == "Rechargeable Battery")
    keys = {f["key"] for f in rechargeable["fields"]}
    assert {"chemistry", "form_factor", "capacity_mah", "voltage", "quantity"}.issubset(keys)

    smoke_detector = next(t for t in templates if t["name"] == "Smoke Detector Battery Program")
    keys = {f["key"] for f in smoke_detector["fields"]}
    assert {"detector_type", "install_date", "replacement_due_date", "test_interval_months"}.issubset(keys)


def test_scaffold_templates_for_clothing_root(client) -> None:
    _register(client, "clothing")
    _login(client, "clothing")
    cid = client.post(
        "/api/collections",
        json={"name": "Wardrobe", "default_category_slug": "clothing"},
    ).json()["id"]

    templates = client.get(f"/api/collections/{cid}/templates").json()
    names = {t["name"] for t in templates}
    assert {"Clothing Item", "Footwear", "Accessories"}.issubset(names)

    clothing_item = next(t for t in templates if t["name"] == "Clothing Item")
    keys = {f["key"] for f in clothing_item["fields"]}
    assert {"type", "brand", "size", "color", "material", "condition", "season", "occasion"}.issubset(keys)

    footwear = next(t for t in templates if t["name"] == "Footwear")
    keys = {f["key"] for f in footwear["fields"]}
    assert {"type", "brand", "size", "size_system", "sole_type", "insole_last_replaced"}.issubset(keys)


def test_scaffold_templates_for_art_decor_root(client) -> None:
    _register(client, "artcol")
    _login(client, "artcol")
    cid = client.post(
        "/api/collections",
        json={"name": "Art Collection", "default_category_slug": "art_decor"},
    ).json()["id"]

    templates = client.get(f"/api/collections/{cid}/templates").json()
    names = {t["name"] for t in templates}
    assert {"Artwork", "Framed Print / Poster", "Decorative Object"}.issubset(names)

    artwork = next(t for t in templates if t["name"] == "Artwork")
    keys = {f["key"] for f in artwork["fields"]}
    assert {"artist", "title", "medium", "year_created", "estimated_value", "insured_value", "last_appraisal_date"}.issubset(keys)

    decorative_obj = next(t for t in templates if t["name"] == "Decorative Object")
    keys = {f["key"] for f in decorative_obj["fields"]}
    assert {"type", "material", "origin", "era", "condition"}.issubset(keys)


def test_static_select_field_options_endpoint_returns_declared_values(client) -> None:
    _register(client, "stat")
    _login(client, "stat")
    cid = client.post("/api/collections", json={"name": "Library"}).json()["id"]

    tmpl = client.post(
        f"/api/collections/{cid}/templates",
        json={
            "name": "Book",
            "category_slug": "books.print",
            "fields": [
                {
                    "key": "shelf",
                    "label": "Shelf",
                    "type": "select",
                    "options": ["A", "B", "C"],
                    "select_source": "static",
                }
            ],
        },
    )
    assert tmpl.status_code == 201, tmpl.text
    tmpl_id = tmpl.json()["id"]

    opts = client.get(
        f"/api/collections/{cid}/template-field-options/shelf",
        params={"template_id": tmpl_id},
    )
    assert opts.status_code == 200, opts.text
    assert opts.json() == ["A", "B", "C"]


def test_multi_value_field_coercion_and_order(client) -> None:
    _register(client, "mval")
    _login(client, "mval")
    cid = client.post("/api/collections", json={"name": "Movies"}).json()["id"]

    tmpl = client.post(
        f"/api/collections/{cid}/templates",
        json={
            "name": "Movie",
            "category_slug": "movies.dvd",
            "fields": [
                {
                    "key": "cast",
                    "label": "Cast",
                    "type": "multi_value",
                }
            ],
        },
    )
    assert tmpl.status_code == 201, tmpl.text
    tmpl_id = tmpl.json()["id"]

    # Array input preserves ordering.
    created = client.post(
        "/api/items",
        json={
            "collection_id": cid,
            "category": "movies.dvd",
            "title": "The Matrix",
            "template_id": tmpl_id,
            "attrs": {"cast": ["Keanu Reeves", "Carrie-Anne Moss", "Laurence Fishburne"]},
        },
    )
    assert created.status_code == 201, created.text
    item = created.json()
    assert item["attrs"]["cast"] == ["Keanu Reeves", "Carrie-Anne Moss", "Laurence Fishburne"]

    # Comma-delimited input is coerced to ordered list.
    patched = client.patch(
        f"/api/items/{item['id']}",
        json={"attrs": {"cast": "Hugo Weaving, Joe Pantoliano"}},
    )
    assert patched.status_code == 200, patched.text
    assert patched.json()["attrs"]["cast"] == ["Hugo Weaving", "Joe Pantoliano"]


def test_relation_field_scope_validation(client) -> None:
    _register(client, "reluser")
    _login(client, "reluser")
    cid_a = client.post("/api/collections", json={"name": "A"}).json()["id"]
    cid_b = client.post("/api/collections", json={"name": "B"}).json()["id"]

    item_a = client.post(
        "/api/items",
        json={"collection_id": cid_a, "category": "other.generic", "title": "Local target"},
    ).json()["id"]
    item_b = client.post(
        "/api/items",
        json={"collection_id": cid_b, "category": "other.generic", "title": "Remote target"},
    ).json()["id"]

    same_scope_tmpl = client.post(
        f"/api/collections/{cid_a}/templates",
        json={
            "name": "Accessory",
            "category_slug": "other.generic",
            "fields": [
                {
                    "key": "accessory_for",
                    "label": "Accessory for",
                    "type": "relation",
                    "relation_scope": "same_collection",
                }
            ],
        },
    )
    assert same_scope_tmpl.status_code == 201, same_scope_tmpl.text
    same_scope_tmpl_id = same_scope_tmpl.json()["id"]

    ok_same = client.post(
        "/api/items",
        json={
            "collection_id": cid_a,
            "category": "other.generic",
            "title": "Accessory cable",
            "template_id": same_scope_tmpl_id,
            "attrs": {"accessory_for": item_a},
        },
    )
    assert ok_same.status_code == 201, ok_same.text

    bad_same = client.post(
        "/api/items",
        json={
            "collection_id": cid_a,
            "category": "other.generic",
            "title": "Accessory cable 2",
            "template_id": same_scope_tmpl_id,
            "attrs": {"accessory_for": item_b},
        },
    )
    assert bad_same.status_code == 422

    any_scope_tmpl = client.post(
        f"/api/collections/{cid_a}/templates",
        json={
            "name": "Compatible battery",
            "category_slug": "other.generic",
            "fields": [
                {
                    "key": "compatible_with",
                    "label": "Compatible with",
                    "type": "relation",
                    "relation_scope": "any_collection",
                }
            ],
        },
    )
    assert any_scope_tmpl.status_code == 201, any_scope_tmpl.text
    any_scope_tmpl_id = any_scope_tmpl.json()["id"]

    ok_any = client.post(
        "/api/items",
        json={
            "collection_id": cid_a,
            "category": "other.generic",
            "title": "Battery",
            "template_id": any_scope_tmpl_id,
            "attrs": {"compatible_with": item_b},
        },
    )
    assert ok_any.status_code == 201, ok_any.text

    bad_unknown = client.post(
        "/api/items",
        json={
            "collection_id": cid_a,
            "category": "other.generic",
            "title": "Battery 2",
            "template_id": any_scope_tmpl_id,
            "attrs": {"compatible_with": "01ZZZZZZZZZZZZZZZZZZZZZZZZ"},
        },
    )
    assert bad_unknown.status_code == 422
