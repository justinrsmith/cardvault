from collections.abc import Generator
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from cardvault.database import get_session
from cardvault.main import app


@pytest.fixture(autouse=True)
def mock_scraper() -> Generator[tuple[AsyncMock, AsyncMock]]:
    """Block real eBay network calls in every test.

    Yields (cards_mock, prices_mock) so individual tests can reconfigure
    return_value or side_effect as needed.
    """
    with (
        patch(
            "cardvault.routers.cards.fetch_active_listings",
            new_callable=AsyncMock,
        ) as cards_mock,
        patch(
            "cardvault.routers.prices.fetch_active_listings",
            new_callable=AsyncMock,
        ) as prices_mock,
    ):
        cards_mock.return_value = []
        prices_mock.return_value = []
        yield cards_mock, prices_mock


@pytest.fixture(name="engine")
def engine_fixture() -> Generator[object]:
    """Shared in-memory SQLite engine — one per test, all requests see the same data."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    yield engine


@pytest.fixture(name="session")
def session_fixture(engine: object) -> Generator[Session]:
    """Single session for direct model tests."""
    from sqlalchemy import Engine

    assert isinstance(engine, Engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(engine: object) -> Generator[TestClient]:
    """TestClient where each request gets a fresh session from the shared engine.
    This mirrors how the real app works and avoids identity-map stale-read issues."""
    from sqlalchemy import Engine

    assert isinstance(engine, Engine)

    def override_get_session() -> Generator[Session]:
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()
