"""Tests for Card and PriceRecord models."""

from datetime import UTC, datetime, timedelta

from sqlmodel import Session, select

from cardvault.models import Card, PriceRecord


def make_card(**kwargs: object) -> Card:
    defaults: dict[str, object] = {
        "player_name": "Ken Griffey Jr.",
        "year": 1989,
        "brand": "Upper Deck",
        "set": "Base Set",
        "card_number": "1",
        "variation": "",
    }
    defaults.update(kwargs)
    return Card(**defaults)  # type: ignore[arg-type]


def make_price(card_id: int, price: float, days_ago: int = 0) -> PriceRecord:
    return PriceRecord(
        card_id=card_id,
        sale_price=price,
        sold_at=datetime.now(UTC) - timedelta(days=days_ago),
    )


# ---------------------------------------------------------------------------
# Card persistence
# ---------------------------------------------------------------------------


def test_card_create_and_retrieve(session: Session) -> None:
    card = make_card()
    session.add(card)
    session.commit()
    session.refresh(card)

    result = session.get(Card, card.id)
    assert result is not None
    assert result.player_name == "Ken Griffey Jr."
    assert result.year == 1989


def test_card_defaults(session: Session) -> None:
    card = make_card()
    session.add(card)
    session.commit()
    session.refresh(card)

    assert card.variation == ""
    assert card.notes == ""
    assert isinstance(card.created_at, datetime)


def test_multiple_cards(session: Session) -> None:
    session.add(make_card(player_name="Ken Griffey Jr."))
    session.add(make_card(player_name="Mike Trout", year=2011, brand="Topps", card_number="175"))
    session.commit()

    results = session.exec(select(Card)).all()
    assert len(results) == 2


# ---------------------------------------------------------------------------
# Card.search_query
# ---------------------------------------------------------------------------


def test_search_query_without_variation(session: Session) -> None:
    card = make_card(variation="")
    assert card.search_query == "1989 Upper Deck Base Set Ken Griffey Jr. 1"


def test_search_query_with_variation(session: Session) -> None:
    card = make_card(variation="Rookie")
    assert card.search_query == "1989 Upper Deck Base Set Ken Griffey Jr. 1 Rookie"


# ---------------------------------------------------------------------------
# Card.estimated_value
# ---------------------------------------------------------------------------


def test_estimated_value_no_records(session: Session) -> None:
    card = make_card()
    session.add(card)
    session.commit()
    session.refresh(card)

    assert card.estimated_value is None


def test_estimated_value_odd_count(session: Session) -> None:
    """Median of [10, 20, 30] is 20."""
    card = make_card()
    session.add(card)
    session.commit()
    session.refresh(card)

    for price in [10.0, 20.0, 30.0]:
        session.add(make_price(card.id, price))  # type: ignore[arg-type]
    session.commit()
    session.refresh(card)

    assert card.estimated_value == 20.0


def test_estimated_value_even_count(session: Session) -> None:
    """Median of [10, 20, 30, 40] is 25."""
    card = make_card()
    session.add(card)
    session.commit()
    session.refresh(card)

    for price in [10.0, 20.0, 30.0, 40.0]:
        session.add(make_price(card.id, price))  # type: ignore[arg-type]
    session.commit()
    session.refresh(card)

    assert card.estimated_value == 25.0


def test_estimated_value_uses_only_5_most_recent(session: Session) -> None:
    """6 records: 5 recent ones at $10-$50, one old outlier at $1000.
    The $1000 record should be excluded so median stays reasonable."""
    card = make_card()
    session.add(card)
    session.commit()
    session.refresh(card)

    # Old outlier
    session.add(make_price(card.id, 1000.0, days_ago=30))  # type: ignore[arg-type]
    # 5 recent prices
    for i, price in enumerate([10.0, 20.0, 30.0, 40.0, 50.0], start=1):
        session.add(make_price(card.id, price, days_ago=i))  # type: ignore[arg-type]
    session.commit()
    session.refresh(card)

    # Median of [10, 20, 30, 40, 50] = 30
    assert card.estimated_value == 30.0


# ---------------------------------------------------------------------------
# PriceRecord persistence
# ---------------------------------------------------------------------------


def test_price_record_persists(session: Session) -> None:
    card = make_card()
    session.add(card)
    session.commit()
    session.refresh(card)

    record = make_price(card.id, 125.50)  # type: ignore[arg-type]
    session.add(record)
    session.commit()
    session.refresh(record)

    assert record.id is not None
    assert record.sale_price == 125.50
    assert record.card_id == card.id


def test_price_record_relationship(session: Session) -> None:
    card = make_card()
    session.add(card)
    session.commit()
    session.refresh(card)

    session.add(make_price(card.id, 50.0))  # type: ignore[arg-type]
    session.add(make_price(card.id, 75.0))  # type: ignore[arg-type]
    session.commit()
    session.refresh(card)

    assert len(card.price_records) == 2
