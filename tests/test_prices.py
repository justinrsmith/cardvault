"""Tests for POST /cards/{id}/refresh."""

import re
from datetime import UTC, datetime
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from cardvault.models import PriceRecord

GRIFFEY = {
    "year": "1989",
    "player_name": "Ken Griffey Jr.",
    "brand": "Upper Deck",
    "set": "Base Set",
    "card_number": "1",
    "variation": "Rookie",
}

MOCK_RESULTS = [
    {
        "sale_price": 125.0,
        "sold_at": datetime(2024, 11, 15, tzinfo=UTC),
        "source_url": "https://www.ebay.com/itm/1",
    },
    {
        "sale_price": 150.0,
        "sold_at": datetime(2024, 10, 1, tzinfo=UTC),
        "source_url": "https://www.ebay.com/itm/2",
    },
    {
        "sale_price": 100.0,
        "sold_at": datetime(2024, 9, 5, tzinfo=UTC),
        "source_url": "https://www.ebay.com/itm/3",
    },
]


def _create_card(client: TestClient) -> int:
    resp = client.post("/cards", data=GRIFFEY)
    assert resp.status_code == 200
    match = re.search(r'id="price-cell-(\d+)"', resp.text)
    assert match, f"price-cell id not found in response: {resp.text[:500]}"
    return int(match.group(1))


# ---------------------------------------------------------------------------
# POST /cards/{id}/refresh
# ---------------------------------------------------------------------------


def test_refresh_creates_price_records(
    client: TestClient,
    session: Session,
    mock_scraper: tuple[AsyncMock, AsyncMock],
) -> None:
    _, prices_mock = mock_scraper
    prices_mock.return_value = MOCK_RESULTS

    card_id = _create_card(client)
    resp = client.post(f"/cards/{card_id}/refresh")

    assert resp.status_code == 200
    records = session.exec(select(PriceRecord).where(PriceRecord.card_id == card_id)).all()
    assert len(records) == 3
    # mean of [100, 125, 150] = 125.00
    assert "$125.00" in resp.text


def test_refresh_shows_sale_count(
    client: TestClient,
    mock_scraper: tuple[AsyncMock, AsyncMock],
) -> None:
    _, prices_mock = mock_scraper
    prices_mock.return_value = MOCK_RESULTS

    card_id = _create_card(client)
    resp = client.post(f"/cards/{card_id}/refresh")

    assert "3 sales" in resp.text


def test_refresh_nonexistent_card(client: TestClient) -> None:
    resp = client.post("/cards/99999/refresh")
    assert resp.status_code == 404


def test_refresh_scraper_failure_returns_ok(
    client: TestClient,
    mock_scraper: tuple[AsyncMock, AsyncMock],
) -> None:
    _, prices_mock = mock_scraper
    prices_mock.side_effect = Exception("Network error")

    card_id = _create_card(client)
    resp = client.post(f"/cards/{card_id}/refresh")

    # Graceful degradation — still returns the partial, no 500
    assert resp.status_code == 200


def test_refresh_replaces_records(
    client: TestClient,
    session: Session,
    mock_scraper: tuple[AsyncMock, AsyncMock],
) -> None:
    """Refreshing twice should replace records, not accumulate."""
    _, prices_mock = mock_scraper
    prices_mock.return_value = MOCK_RESULTS

    card_id = _create_card(client)
    client.post(f"/cards/{card_id}/refresh")
    client.post(f"/cards/{card_id}/refresh")

    records = session.exec(select(PriceRecord).where(PriceRecord.card_id == card_id)).all()
    assert len(records) == 3


def test_create_card_fetches_prices_immediately(
    client: TestClient,
    session: Session,
    mock_scraper: tuple[AsyncMock, AsyncMock],
) -> None:
    """Prices should be scraped as soon as a card is added."""
    cards_mock, _ = mock_scraper
    cards_mock.return_value = MOCK_RESULTS[:1]  # one result

    resp = client.post("/cards", data=GRIFFEY)
    assert resp.status_code == 200

    match = re.search(r'id="price-cell-(\d+)"', resp.text)
    assert match
    card_id = int(match.group(1))

    records = session.exec(select(PriceRecord).where(PriceRecord.card_id == card_id)).all()
    assert len(records) == 1
    assert "$125.00" in resp.text
