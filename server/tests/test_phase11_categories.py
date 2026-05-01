"""Phase 11 category seed tests."""


PHASE11_HOME_EQUIPMENT_SLUGS = {
    "home_equipment",
    "home_equipment.appliance",
    "home_equipment.generator",
    "home_equipment.hvac",
    "home_equipment.water_heater",
    "home_equipment.refrigerator",
    "home_equipment.water_filtration",
    "home_equipment.sump_pump",
}


def _signup_and_login(client, username: str, password: str = "hunter22-secure") -> None:
    client.post(
        "/api/auth/register",
        json={"username": username, "password": password, "email": f"{username}@x.io"},
    )
    r = client.post("/api/auth/login", json={"username": username, "password": password})
    assert r.status_code == 200, r.text


def test_phase11_home_equipment_categories_available(client) -> None:
    _signup_and_login(client, "phase11")

    r = client.get("/api/categories")
    assert r.status_code == 200, r.text

    slugs = {row["slug"] for row in r.json()}
    assert PHASE11_HOME_EQUIPMENT_SLUGS.issubset(slugs)
