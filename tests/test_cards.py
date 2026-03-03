"""Tests for card CRUD routes."""

from fastapi.testclient import TestClient

GRIFFEY = {
    "year": "1989",
    "player_name": "Ken Griffey Jr.",
    "brand": "Upper Deck",
    "set": "Base Set",
    "card_number": "1",
    "variation": "Rookie",
}

TROUT = {
    "year": "2011",
    "player_name": "Mike Trout",
    "brand": "Topps",
    "set": "Update Series",
    "card_number": "175",
    "variation": "",
}


def post_card(client: TestClient, data: dict[str, str]) -> None:
    resp = client.post("/cards", data=data)
    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# GET /
# ---------------------------------------------------------------------------


def test_index_empty(client: TestClient) -> None:
    resp = client.get("/")
    assert resp.status_code == 200
    assert "No cards yet" in resp.text


def test_index_shows_cards(client: TestClient) -> None:
    post_card(client, GRIFFEY)
    resp = client.get("/")
    assert "Ken Griffey Jr." in resp.text
    assert "Upper Deck" in resp.text


# ---------------------------------------------------------------------------
# POST /cards
# ---------------------------------------------------------------------------


def test_create_card_returns_row(client: TestClient) -> None:
    resp = client.post("/cards", data=GRIFFEY)
    assert resp.status_code == 200
    assert "Ken Griffey Jr." in resp.text
    assert "1989" in resp.text
    assert "Upper Deck" in resp.text


def test_create_card_without_variation(client: TestClient) -> None:
    resp = client.post("/cards", data=TROUT)
    assert resp.status_code == 200
    assert "Mike Trout" in resp.text


def test_create_card_without_card_number(client: TestClient) -> None:
    data = {k: v for k, v in GRIFFEY.items() if k != "card_number"}
    resp = client.post("/cards", data=data)
    assert resp.status_code == 200
    assert "Ken Griffey Jr." in resp.text


def test_create_card_missing_required_field(client: TestClient) -> None:
    resp = client.post("/cards", data={"player_name": "Oops"})
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# DELETE /cards/{id}
# ---------------------------------------------------------------------------


def test_delete_card_returns_empty(client: TestClient) -> None:
    post_card(client, GRIFFEY)
    # Grab the id from the index page
    index = client.get("/")
    assert "Ken Griffey Jr." in index.text

    # Parse out the card id from the delete button href
    import re

    match = re.search(r'hx-delete="/cards/(\d+)"', index.text)
    assert match, "Could not find delete button in page"
    card_id = match.group(1)

    resp = client.delete(f"/cards/{card_id}")
    assert resp.status_code == 200
    assert resp.text == ""


def test_delete_card_removes_from_list(client: TestClient) -> None:
    post_card(client, GRIFFEY)
    index = client.get("/")

    import re

    match = re.search(r'hx-delete="/cards/(\d+)"', index.text)
    assert match
    card_id = match.group(1)

    client.delete(f"/cards/{card_id}")
    resp = client.get("/")
    assert "No cards yet" in resp.text


def test_delete_nonexistent_card(client: TestClient) -> None:
    resp = client.delete("/cards/99999")
    assert resp.status_code == 200
    assert resp.text == ""


# ---------------------------------------------------------------------------
# GET /cards/search
# ---------------------------------------------------------------------------


def test_search_no_query_returns_all(client: TestClient) -> None:
    post_card(client, GRIFFEY)
    post_card(client, TROUT)
    resp = client.get("/cards/search")
    assert resp.status_code == 200
    assert "Ken Griffey Jr." in resp.text
    assert "Mike Trout" in resp.text


def test_search_filters_by_player_name(client: TestClient) -> None:
    post_card(client, GRIFFEY)
    post_card(client, TROUT)
    resp = client.get("/cards/search?q=griffey")
    assert "Ken Griffey Jr." in resp.text
    assert "Mike Trout" not in resp.text


def test_search_filters_by_brand(client: TestClient) -> None:
    post_card(client, GRIFFEY)
    post_card(client, TROUT)
    resp = client.get("/cards/search?q=topps")
    assert "Mike Trout" in resp.text
    assert "Ken Griffey Jr." not in resp.text


def test_search_no_results(client: TestClient) -> None:
    post_card(client, GRIFFEY)
    resp = client.get("/cards/search?q=nobody")
    assert "No cards yet" in resp.text
