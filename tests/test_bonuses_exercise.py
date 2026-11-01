"""Checks for the bonuses exercise (see BONUSES_TASK.md).

Run only these:  .venv/bin/python -m pytest tests/test_bonuses_exercise.py -v
Uses the `client` fixture from tests/conftest.py (fresh in-memory database per test).
"""
import time
from datetime import datetime

import pytest

PROMO = {"name": "WELCOME100", "terms": "Wagering x35", "offer": "100% up to $100"}


def create(client, **fields):
    body = {
        "name": "Welcome Bonus",
        "description": "100% on first deposit",
        "minDeposit": 20,
        "amount": 100,
        "promo": PROMO,
    } | fields
    res = client.post("/bonuses", json=body)
    assert res.status_code == 201, res.text
    return res.json()


def ts(value: str) -> datetime:
    # Compare moments, not text: SQLite drops the timezone, so "…Z" and "…" can both appear.
    return datetime.fromisoformat(value).replace(tzinfo=None)


# --- Level 1: CRUD (your current code should already pass these) -------------


def test_create_returns_201_with_nested_promo(client):
    bonus = create(client)
    assert bonus["id"] == 1
    assert bonus["name"] == "Welcome Bonus"
    assert bonus["minDeposit"] == 20
    assert bonus["promo"]["id"] == 1
    assert bonus["promo"]["name"] == "WELCOME100"


def test_description_is_optional(client):
    body = {"name": "No description", "minDeposit": 0, "amount": 5, "promo": PROMO}
    res = client.post("/bonuses", json=body)
    assert res.status_code == 201
    assert res.json()["description"] == ""


def test_get_bonus_by_id(client):
    create(client)
    res = client.get("/bonuses/1")
    assert res.status_code == 200
    assert res.json()["name"] == "Welcome Bonus"


def test_get_missing_bonus_returns_404_with_message(client):
    res = client.get("/bonuses/999")
    assert res.status_code == 404
    assert res.json() == {"detail": "Bonus not found"}


def test_patch_changes_only_sent_fields(client):
    create(client)
    body = client.patch("/bonuses/1", json={"amount": 150}).json()
    assert body["amount"] == 150
    assert body["name"] == "Welcome Bonus"
    assert body["minDeposit"] == 20


def test_patch_is_saved(client):
    create(client)
    client.patch("/bonuses/1", json={"name": "Big Welcome"})
    assert client.get("/bonuses/1").json()["name"] == "Big Welcome"


def test_patch_missing_bonus_returns_404(client):
    assert client.patch("/bonuses/42", json={"amount": 1}).status_code == 404


def test_delete_returns_204_with_empty_body(client):
    create(client)
    res = client.delete("/bonuses/1")
    assert res.status_code == 204
    assert res.content == b""
    assert client.get("/bonuses/1").status_code == 404


# --- Level 2: validation -------------------------------------------------------


@pytest.mark.parametrize(
    "fields",
    [
        {"name": ""},                                         # empty
        {"name": "   "},                                      # only spaces
        {"name": "x" * 121},                                  # longer than 120
        {"amount": "lots"},                                   # not a number
        {"amount": -1},                                       # negative
        {"minDeposit": -5},                                   # negative
        {"promo": None},                                      # promo missing
        {"promo": PROMO | {"name": "  "}},                    # blank promo name
        {"promo": {"name": "X", "terms": "T"}},               # promo offer missing
    ],
)
def test_create_rejects_invalid_body(client, fields):
    body = {"name": "B", "minDeposit": 0, "amount": 1, "promo": PROMO} | fields
    body = {k: v for k, v in body.items() if v is not None}
    assert client.post("/bonuses", json=body).status_code == 422


def test_names_are_trimmed(client):
    bonus = create(client, name="  Reload Bonus  ", promo=PROMO | {"name": "  FRIDAY50 "})
    assert bonus["name"] == "Reload Bonus"
    assert bonus["promo"]["name"] == "FRIDAY50"


def test_patch_rejects_blank_name_and_keeps_old_value(client):
    create(client)
    assert client.patch("/bonuses/1", json={"name": "  "}).status_code == 422
    assert client.get("/bonuses/1").json()["name"] == "Welcome Bonus"


def test_non_integer_id_returns_422(client):
    assert client.get("/bonuses/abc").status_code == 422


# --- Level 3: timestamps -------------------------------------------------------


def test_response_has_exactly_these_fields(client):
    bonus = create(client)
    assert set(bonus) == {
        "id", "name", "description", "minDeposit", "amount", "promo", "createdAt", "updatedAt",
    }


def test_timestamps_are_set_on_create(client):
    bonus = create(client)
    assert ts(bonus["createdAt"]) == ts(bonus["updatedAt"])


def test_timestamps_cannot_be_set_by_client(client):
    bonus = create(client, createdAt="2000-01-01T00:00:00")
    assert ts(bonus["createdAt"]).year != 2000


def test_patch_moves_updated_at_but_not_created_at(client):
    before = create(client)
    time.sleep(0.01)  # make sure the clock has moved on
    after = client.patch("/bonuses/1", json={"amount": 200}).json()
    assert ts(after["createdAt"]) == ts(before["createdAt"])
    assert ts(after["updatedAt"]) > ts(before["updatedAt"])


def test_patching_only_the_promo_also_moves_updated_at(client):
    before = create(client)
    time.sleep(0.01)
    after = client.patch("/bonuses/1", json={"promo": PROMO | {"offer": "50% up to $50"}}).json()
    assert after["promo"]["offer"] == "50% up to $50"
    assert ts(after["updatedAt"]) > ts(before["updatedAt"])


# --- Level 4: search, filter, sort, pagination ---------------------------------


def names(client, **params):
    res = client.get("/bonuses", params=params)
    assert res.status_code == 200, res.text
    return [b["name"] for b in res.json()]


def test_default_order_is_oldest_first(client):
    create(client, name="A")
    create(client, name="B")
    assert names(client) == ["A", "B"]


def test_search_q_matches_name_description_or_promo_case_insensitive(client):
    create(client, name="Friday Reload", description="weekly")
    create(client, name="Spins", description="free spins on FRIDAY")
    create(client, name="VIP", description="big", promo=PROMO | {"name": "FRIDAYVIP"})
    create(client, name="Welcome", description="first deposit")
    assert names(client, q="friday") == ["Friday Reload", "Spins", "VIP"]


def test_filter_max_deposit(client):
    create(client, name="cheap", minDeposit=10)
    create(client, name="exact", minDeposit=50)
    create(client, name="pricey", minDeposit=500)
    assert names(client, maxDeposit=50) == ["cheap", "exact"]


def test_sort_by_amount_highest_first(client):
    create(client, name="small", amount=10)
    create(client, name="big", amount=1000)
    create(client, name="mid", amount=100)
    create(client, name="mid too", amount=100)  # ties keep oldest first
    assert names(client, sort="amount") == ["big", "mid", "mid too", "small"]


def test_filters_combine(client):
    create(client, name="Reload cheap", minDeposit=10, amount=50)
    create(client, name="Reload big", minDeposit=20, amount=500)
    create(client, name="Reload pricey", minDeposit=900, amount=5000)
    create(client, name="Other", minDeposit=10, amount=999)
    assert names(client, q="reload", maxDeposit=100, sort="amount") == [
        "Reload big", "Reload cheap",
    ]


def test_limit_and_offset(client):
    for i in range(1, 6):
        create(client, name=f"bonus {i}")
    assert names(client, limit=2, offset=1) == ["bonus 2", "bonus 3"]


def test_default_limit_is_20(client):
    for i in range(25):
        create(client, name=f"b{i}")
    assert len(names(client)) == 20


@pytest.mark.parametrize(
    "params",
    [{"limit": 0}, {"limit": 101}, {"offset": -1}, {"sort": "name"}, {"maxDeposit": -1}],
)
def test_bad_query_params_return_422(client, params):
    assert client.get("/bonuses", params=params).status_code == 422
