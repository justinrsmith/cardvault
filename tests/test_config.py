"""Tests for Settings config."""

import pytest

from cardvault.config import Settings


def test_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("EBAY_APP_ID", raising=False)
    monkeypatch.delenv("EBAY_CLIENT_SECRET", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("EBAY_RESULTS_COUNT", raising=False)
    s = Settings(_env_file=None)  # type: ignore[call-arg]
    assert s.database_url == "sqlite:///./cardvault.db"
    assert s.ebay_app_id == ""
    assert s.ebay_client_secret == ""
    assert s.ebay_results_count == 20


def test_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EBAY_APP_ID", "test-app-id")
    monkeypatch.setenv("EBAY_CLIENT_SECRET", "test-secret")
    monkeypatch.setenv("EBAY_RESULTS_COUNT", "5")
    s = Settings()
    assert s.ebay_app_id == "test-app-id"
    assert s.ebay_client_secret == "test-secret"
    assert s.ebay_results_count == 5
