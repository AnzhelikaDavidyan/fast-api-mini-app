PAYLOAD = {
    "name": "Welcome Bonus",
    "description": "100% on your first deposit",
    "minDeposit": 20,
    "amount": 100,
    "promo": {
        "name": "WELCOME100",
        "terms": "Wagering x35, valid 7 days",
        "offer": "100% up to $100",
    },
}


def create(client, **overrides):
    return client.post("/bonuses", json={**PAYLOAD, **overrides})


def test_create_bonus_returns_201_with_nested_promo(client):
    res = create(client)
    assert res.status_code == 201
    body = res.json()
    assert body["id"] == 1
    assert body["name"] == "Welcome Bonus"
    assert body["minDeposit"] == 20
    assert body["amount"] == 100
    assert body["promo"] == {
        "id": 1,
        "name": "WELCOME100",
        "terms": "Wagering x35, valid 7 days",
        "offer": "100% up to $100",
    }


def test_list_bonuses_returns_all(client):
    create(client)
    create(client, name="Reload Bonus")
    res = client.get("/bonuses")
    assert res.status_code == 200
    assert [b["name"] for b in res.json()] == ["Welcome Bonus", "Reload Bonus"]


def test_get_bonus_by_id_and_404(client):
    create(client)
    assert client.get("/bonuses/1").json()["name"] == "Welcome Bonus"
    assert client.get("/bonuses/999").status_code == 404


def test_patch_updates_only_sent_fields_and_keeps_promo_id(client):
    create(client)
    res = client.patch("/bonuses/1", json={"amount": 150})
    assert res.status_code == 200
    body = res.json()
    assert body["amount"] == 150
    assert body["name"] == "Welcome Bonus"
    assert body["promo"]["id"] == 1


def test_patch_replaces_promo_content(client):
    create(client)
    res = client.patch("/bonuses/1", json={"promo": {"name": "NEW", "terms": "T", "offer": "O"}})
    assert res.json()["promo"] == {"id": 1, "name": "NEW", "terms": "T", "offer": "O"}


def test_patch_missing_bonus_returns_404(client):
    assert client.patch("/bonuses/42", json={"amount": 1}).status_code == 404


def test_delete_bonus(client):
    create(client)
    assert client.delete("/bonuses/1").status_code == 204
    assert client.get("/bonuses/1").status_code == 404
    assert client.delete("/bonuses/1").status_code == 404


def test_create_rejects_invalid_payload(client):
    res = create(client, minDeposit=-5)
    assert res.status_code == 422
