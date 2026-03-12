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
        list_price=price,
        listed_at=datetime.now(UTC) - timedelta(days=days_ago),
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
    session.add(
        make_card(
            player_name="Mike Trout",
            year=2011,
            brand="Topps",
            set="Update Series",
            card_number="175",
        )
    )
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


def test_search_query_without_card_number(session: Session) -> None:
    card = make_card(card_number="")
    assert card.search_query == "1989 Upper Deck Base Set Ken Griffey Jr."


# ---------------------------------------------------------------------------
# Card.estimated_value
# ---------------------------------------------------------------------------


def test_estimated_value_no_records(session: Session) -> None:
    card = make_card()
    session.add(card)
    session.commit()
    session.refresh(card)

    assert card.estimated_value is None


def test_estimated_value_mean(session: Session) -> None:
    """Mean of [10, 20, 30] is 20."""
    card = make_card()
    session.add(card)
    session.commit()
    session.refresh(card)

    for price in [10.0, 20.0, 30.0]:
        session.add(make_price(card.id, price))  # type: ignore[arg-type]
    session.commit()
    session.refresh(card)

    assert card.estimated_value == 20.0


def test_estimated_value_includes_all_records(session: Session) -> None:
    """Mean includes all records — [10, 20, 30, 40] = 25."""
    card = make_card()
    session.add(card)
    session.commit()
    session.refresh(card)

    for price in [10.0, 20.0, 30.0, 40.0]:
        session.add(make_price(card.id, price))  # type: ignore[arg-type]
    session.commit()
    session.refresh(card)

    assert card.estimated_value == 25.0


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
    assert record.list_price == 125.50
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

    assert len(card.listing_records) == 2
